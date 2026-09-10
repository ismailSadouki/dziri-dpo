from __future__ import annotations
from pathlib import Path
import random
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))


import json
import numpy as np
import yaml
import torch
from torch.utils.data import DataLoader
from peft import PeftModel

from scratch_dpo.collator import DPODataCollator
from scratch_dpo.data import tokenize_pair
from scratch_dpo.dataset import load_hh_preferences
from scratch_dpo.forward import (
    concatenated_forward,
    reference_concatenated_forward,
)
from scratch_dpo.losses import dpo_loss
from scratch_dpo.modeling import (
    attach_lora,
    load_policy,
    load_tokenizer,
)


def load_config(path: str | Path) -> dict:
    """
    Load a YAML training configuration.
    """
    path = Path(path)

    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError(
            f"Expected YAML mapping, got {type(config).__name__}"
        )

    return config

def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)



def get_trainable_parameters(
        model: torch.nn.Module,
) -> list[torch.nn.Parameter]:
    return [
        parameter
        for parameter in model.parameters()
        if parameter.requires_grad
    ]



def build_training_dataset(
        tokenizer,
        max_examples: int,
        max_length: int,
        tiny_overfit: bool = False,
):
    if tiny_overfit:
        rows = load_tiny_preferences()
        rejected = []
    else:
        rows, rejected = load_hh_preferences(
            n_examples=max_examples,
        )

    if not rows:
        raise ValueError(
            "No valid preference examples were loaded."
        )

    tokenized = []


    for row in rows:
        try:
            example = tokenize_pair(
                tokenizer=tokenizer,
                prompt=row["prompt"],
                chosen=row["chosen"],
                rejected=row["rejected"],
                max_length=max_length,
            )

            tokenized.append(example)

        except ValueError as exc:
            rejected.append(
                {
                    "id": row.get("id"),
                    "reason": str(exc),
                }
            )


    if not tokenized:
        raise ValueError(
            "No examples remained after tokenization."
        )


    return tokenized, rejected

def build_dataloader(
        tokenized_dataset,
        tokenizer,
        batch_size: int,
        shuffle: bool = True
):
    collater = DPODataCollator(
        pad_token_id=tokenizer.pad_token_id
    )


    return DataLoader(
        tokenized_dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        collate_fn=collater
    )


def load_tiny_preferences(
    path: str | Path = "tests/fixtures/tiny_preferences.jsonl",
) -> list[dict]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Tiny preference dataset not found: {path}"
        )

    rows = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            rows.append(json.loads(line))

    if not rows:
        raise ValueError(
            f"No examples found in {path}"
        )

    return rows

def training_step(
        model: torch.nn.Module,
        batch: dict[str, torch.Tensor],
        # optimizer: torch.optim.Optimizer,
        beta: float,
        loss_scale: float = 1.0,
        # max_grad_norm: float
) -> dict[str, float]:
    """
    Execute the forward/backward portion of one DPO batch.

    Those operations belong to the outer training loop so that
    gradient accumulation can be implemented correctly.

    Args:
        model:
            LoRA policy model.

        batch:
            Collated DPO preference batch.

        beta:
            DPO beta parameter.

        loss_scale:
            Scaling factor used for gradient accumulation.
            For accumulation_steps = N:

                loss_scale = 1 / N
    Returns:
        Scalar health metrics for this batch.
    """

    if loss_scale <= 0:
        raise ValueError(
            f"loss_scale must be positive, got {loss_scale}"
        )

    
    model.train()

    #policy forward
    policy_chosen_logps, policy_rejected_logps = (
        concatenated_forward(
            model=model,
            batch=batch,
        )
    )

    if policy_chosen_logps.shape != policy_rejected_logps.shape:
        raise RuntimeError(
            "Policy chosen/rejected logprob shapes do not match."
        )

    # reference forward
    (
        reference_chosen_logps,
        reference_rejected_logps,
    ) = reference_concatenated_forward(
        model=model,
        batch=batch,
    )



    # DPO loss
    (
        losses, # [B]
        chosen_rewards,
        rejected_rewards, 
        margin,
        reward_accuracy,
    ) = dpo_loss(
        policy_chosen_logps,
        policy_rejected_logps,
        reference_chosen_logps,
        reference_rejected_logps,
        beta=beta,
    )

    # dpo_loss intentionally returns [B].
    # Optimization requires a scalar.
    loss_mean = losses.mean()


    # Gradient accumulation
    # If accumulation_steps = N, the caller supplies:
    #     loss_scale = 1 / N

    scaled_loss = loss_mean * loss_scale
    # backword step
    scaled_loss.backward()  


    chosen_log_ratio = (
        policy_chosen_logps.detach()
        - reference_chosen_logps
    )

    rejected_log_ratio = (
        policy_rejected_logps.detach()
        - reference_rejected_logps
    )




    chosen_length = (
        batch['chosen_loss_mask']
        .sum(dim=1)
        .float()
        .mean()
    )
    rejected_length = (
        batch['rejected_loss_mask']
        .sum(dim=1)
        .float()
        .mean()
    )

    return {
        "loss": loss_mean.detach().item(),

        "reward_accuracy": reward_accuracy.detach().item(),

        "margin": margin.detach().mean().item(),

        "chosen_reward": chosen_rewards.detach().mean().item(),

        "rejected_reward": rejected_rewards.detach().mean().item(),

        "policy_chosen_logp": (
            policy_chosen_logps.detach().mean().item()
        ),

        "policy_rejected_logp": (
            policy_rejected_logps.detach().mean().item()
        ),
        "reference_chosen_logp": (
            reference_chosen_logps.detach().mean().item()
        ),

        "reference_rejected_logp": (
            reference_rejected_logps.detach().mean().item()
        ),

        "chosen_kl_proxy": (
            chosen_log_ratio.mean().item()
        ),

        "rejected_kl_proxy": (
            rejected_log_ratio.mean().item()
        ),



        "chosen_length": chosen_length.item(),

        "rejected_length": rejected_length.item(),

    }



def build_optimizer(
        model: torch.nn.Module,
        learning_rate: float,
        weight_decay: float
) -> torch.optim.Optimizer:
    """
    Construct AdamW using only trainable policy parameters.
    """

    trainable_parameters = get_trainable_parameters(model)

    if not trainable_parameters:
        raise ValueError(
            "No trainable parameters in model."
        )

    return torch.optim.AdamW(
        trainable_parameters,
        lr=learning_rate,
        weight_decay=weight_decay
    )


def optimizer_step(
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        max_grad_norm: float
) -> float:
    """
    Clip gradients of trainable parameters and perform one
    optimizer update

    Returns:
        Total gradient norm before clipping.
    """

    trainable_parameters = get_trainable_parameters(model)

    if not trainable_parameters:
        raise ValueError(
            "No trainable parameters found."
        )

    grad_norm = torch.nn.utils.clip_grad_norm_(
        trainable_parameters,
        max_grad_norm
    )

    optimizer.step()

    return float(grad_norm)



def append_metrics(
    path: str | Path,
    metrics: dict[str, float],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(metrics, ensure_ascii=False)
            + "\n"
        )

def save_checkpoint(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    output_dir: Path,
    step: int,
    microstep: int,
    config: dict,
    seed: int,
) -> None:
    checkpoint_dir = output_dir / f"checkpoint-{step}"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # Save PEFT adapter weights and configuration.
    model.save_pretrained(
        checkpoint_dir,
        safe_serialization=True,
    )

    # Save optimizer state.
    torch.save(
        optimizer.state_dict(),
        checkpoint_dir / "optimizer.pt",
    )

    # Save trainer state.
    trainer_state = {
        "global_step": step,
        "microstep": microstep,
        "seed": seed,
    }

    with (checkpoint_dir / "trainer_state.json").open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            trainer_state,
            f,
            indent=2,
        )

    # Save the exact configuration used for the run.
    with (checkpoint_dir / "config.yaml").open(
        "w",
        encoding="utf-8",
    ) as f:
        yaml.safe_dump(
            config,
            f,
            sort_keys=False,
        )

    print(
        f"Saved checkpoint: {checkpoint_dir}"
    )


def load_checkpoint(
    checkpoint_dir: str | Path,
    model_name: str,
):
    checkpoint_dir = Path(checkpoint_dir)

    if not checkpoint_dir.exists():
        raise FileNotFoundError(
            f"Checkpoint does not exist: {checkpoint_dir}"
        )

    # Load the same 4-bit base model used during training.
    base_model = load_policy(model_name)

    # Load the saved LoRA adapter.
    model = PeftModel.from_pretrained(
        base_model,
        checkpoint_dir,
        is_trainable=True,
    )

    return model

def load_checkpoint_state(
    checkpoint_dir: str | Path,
) -> dict:
    checkpoint_dir = Path(checkpoint_dir)

    state_path = checkpoint_dir / "trainer_state.json"

    if not state_path.exists():
        raise FileNotFoundError(
            f"Missing trainer state: {state_path}"
        )

    with state_path.open("r", encoding="utf-8") as f:
        state = json.load(f)

    required = {
        "global_step",
        "microstep",
        "seed",
    }

    missing = required - state.keys()

    if missing:
        raise ValueError(
            f"Checkpoint state missing fields: {sorted(missing)}"
        )

    return state
def train(
    config: dict,
    resume_from: str | None = None,
) -> list[dict[str, float]]:
    seed = int(config.get("seed", 42))
    set_seed(seed)


    model_name = config['model']['name']


    training_config = config["training"]
    output_dir = Path(
        training_config["output_dir"]
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    metrics_path = output_dir / "metrics.jsonl"
    if metrics_path.exists():
        metrics_path.unlink()

    data_config = config["data"]

    tokenizer = load_tokenizer(model_name)


    if resume_from is None:
        model = load_policy(model_name)
        model = attach_lora(model)
    else:
        checkpoint_dir = Path(resume_from)

        if not checkpoint_dir.exists():
            raise FileNotFoundError(
                f"Checkpoint does not exist: {checkpoint_dir}"
            )

        model = load_policy(model_name)

        model = PeftModel.from_pretrained(
            model,
            checkpoint_dir,
            is_trainable=True,
        )

    model.train()

    device = model.device



    tiny_overfit = bool(
        training_config.get("tiny_overfit", False)
    )
    tokenized_dataset, rejected = build_training_dataset(
        tokenizer=tokenizer,
        max_examples=int(
            data_config.get("max_train_examples", 2000)
        ),
        max_length=int(data_config["max_length"]),
        tiny_overfit=tiny_overfit,
    )

    if rejected:
        print(
            f"Rejected {len(rejected)} invalid examples."
        )

    dataloader = build_dataloader(
        tokenized_dataset=tokenized_dataset,
        tokenizer=tokenizer,
        batch_size=int(training_config["batch_size"]),
        shuffle=True
    )

    optimizer = build_optimizer(
        model=model,
        learning_rate=float(training_config["learning_rate"]),
        weight_decay=float(training_config["weight_decay"]),
    )

    if resume_from is not None:
        optimizer_path = (
            Path(resume_from) / "optimizer.pt"
        )

        if not optimizer_path.exists():
            raise FileNotFoundError(
                f"Missing optimizer checkpoint: {optimizer_path}"
            )

        optimizer_state = torch.load(
            optimizer_path,
            map_location="cpu",
            weights_only=False,
        )

        optimizer.load_state_dict(optimizer_state)

        print(
            f"Loaded optimizer state from: "
            f"{optimizer_path}"
        )


    gradient_accumulation_steps = int(
        training_config["gradient_accumulation_steps"]
    )

    beta = float(training_config["beta"])

    max_grad_norm = float(
        training_config["max_grad_norm"]
    )

    max_steps = int(
        training_config["max_steps"]
    )

    log_every_steps = int(
        training_config["log_every_steps"]
    )

    save_every_steps = int(
        training_config["save_every_steps"]
    )

    optimizer.zero_grad(set_to_none=True)

    if resume_from is None:
        global_step = 0
        microstep = 0
    else:
        trainer_state = load_checkpoint_state(
            resume_from
        )

        global_step = int(
            trainer_state["global_step"]
        )

        microstep = int(
            trainer_state["microstep"]
        )

        print(
            f"Resuming from step={global_step}, "
            f"microstep={microstep}"
        )

    history = []

    while global_step < max_steps:
        for batch in dataloader:
            batch = {
                key: value.to(device)
                for key, value in batch.items()
            }

            microstep += 1

            metrics = training_step(
                model=model,
                batch=batch,
                beta=beta,
                loss_scale=(
                    1.0 / gradient_accumulation_steps
                )
            )

            accumulation_boundary = (
                microstep % gradient_accumulation_steps == 0
            )

            if not accumulation_boundary:
                continue

            grad_norm = optimizer_step(
                model=model,
                optimizer=optimizer,
                max_grad_norm=max_grad_norm,
            )

            optimizer.zero_grad(set_to_none=True)

            global_step += 1

            metrics["grad_norm"] = grad_norm
            metrics["step"] = global_step
            metrics["learning_rate"] = optimizer.param_groups[0]["lr"]

            metrics["gpu_memory_allocated_mb"] = (
                torch.cuda.memory_allocated() / 1024**2
            )
            metrics["gpu_memory_reserved_mb"] = (
                torch.cuda.memory_reserved() / 1024**2
            )


            append_metrics(
                metrics_path,
                metrics,
            )
    
            history.append(metrics)

            if (
                global_step % log_every_steps == 0
            ):

                print(
                    f"step={global_step:04d} "
                    f"loss={metrics['loss']:.4f} "
                    f"reward_acc={metrics['reward_accuracy']:.3f} "
                    f"margin={metrics['margin']:.4f} "
                    f"grad_norm={grad_norm:.4f}"
                )

            if global_step % save_every_steps == 0:
                save_checkpoint(
                    model=model,
                    optimizer=optimizer,
                    output_dir=output_dir,
                    step=global_step,
                    microstep=microstep,
                    config=config,
                    seed=seed,
                )

            if global_step >= max_steps:
                break

    return history


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--resume-from",
        type=str,
        default=None,
    )

    args = parser.parse_args()

    config = load_config(args.config)

    train(
        config,
        resume_from=args.resume_from,
    )





