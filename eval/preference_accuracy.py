from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
import sys

import torch
from peft import PeftModel
from torch.utils.data import DataLoader

sys.path.append(str(Path(__file__).resolve().parent.parent))

from scratch_dpo.collator import DPODataCollator
from scratch_dpo.data import tokenize_pair
from scratch_dpo.dataset import load_preference_jsonl
from scratch_dpo.forward import (
    concatenated_forward,
    reference_concatenated_forward,
)
from scratch_dpo.modeling import (
    attach_lora,
    load_policy,
    load_tokenizer,
)


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
PAD_TOKEN_ID = None


def tokenize_examples(
    tokenizer,
    rows: list[dict],
    max_length: int,
):
    tokenized = []

    for row in rows:
        example = tokenize_pair(
            tokenizer=tokenizer,
            prompt=row["prompt"],
            chosen=row["chosen"],
            rejected=row["rejected"],
            max_length=max_length,
        )

        tokenized.append(example)

    return tokenized


def evaluate_checkpoint(
    model,
    tokenizer,
    rows: list[dict],
    max_length: int,
    batch_size: int = 1,
):
    tokenized = tokenize_examples(
        tokenizer=tokenizer,
        rows=rows,
        max_length=max_length,
    )

    collator = DPODataCollator(
        pad_token_id=tokenizer.pad_token_id,
    )

    dataloader = DataLoader(
        tokenized,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collator,
    )

    model.eval()

    correct = 0
    ties = 0
    total = 0

    margins = []
    chosen_rewards = []
    rejected_rewards = []

    beta = 0.1

    with torch.no_grad():
        for batch in dataloader:
            batch = {
                key: value.to(model.device)
                for key, value in batch.items()
            }

            policy_chosen, policy_rejected = concatenated_forward(
                model,
                batch,
            )

            reference_chosen, reference_rejected = (
                reference_concatenated_forward(
                    model,
                    batch,
                )
            )

            policy_logratio = (
                policy_chosen - policy_rejected
            )

            reference_logratio = (
                reference_chosen - reference_rejected
            )

            margin = (
                policy_logratio
                - reference_logratio
            )

            chosen_reward = beta * (
                policy_chosen - reference_chosen
            )

            rejected_reward = beta * (
                policy_rejected - reference_rejected
            )

            correct += (
                margin > 0
            ).sum().item()

            ties += (
                margin == 0
            ).sum().item()

            total += margin.numel()

            margins.extend(
                margin.detach().cpu().tolist()
            )

            chosen_rewards.extend(
                chosen_reward.detach().cpu().tolist()
            )

            rejected_rewards.extend(
                rejected_reward.detach().cpu().tolist()
            )

    non_ties = total - ties

    accuracy = correct / total

    if non_ties > 0:
        non_tie_accuracy = correct / non_ties
    else:
        non_tie_accuracy = None

    tie_rate = ties / total

    return {
        "examples": total,
        "preference_accuracy": accuracy,
        "non_tie_accuracy": non_tie_accuracy,
        "ties": ties,
        "tie_rate": tie_rate,
        "mean_margin": statistics.mean(margins),
        "median_margin": statistics.median(margins),
        "mean_chosen_reward": statistics.mean(chosen_rewards),
        "mean_rejected_reward": statistics.mean(rejected_rewards),
    }


def load_checkpoint_model(
    model_name: str,
    checkpoint_dir: str | Path,
):
    base_model = load_policy(model_name)

    model = PeftModel.from_pretrained(
        base_model,
        checkpoint_dir,
        is_trainable=False,
    )

    return model


def load_step0_model(model_name: str):
    model = load_policy(model_name)
    model = attach_lora(model)
    return model


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--eval-path",
        type=str,
        default="data/english/hh_rlhf_helpful-base_200_eval.jsonl",
    )

    parser.add_argument(
        "--checkpoint",
        type=str,
        action="append",
        required=True,
        help="Checkpoint directory. Can be specified multiple times.",
    )
    parser.add_argument(
        "--step-0",
        action="store_true",
        help="Evaluate the freshly initialized LoRA policy before training.",
    )

    parser.add_argument(
        "--max-length",
        type=int,
        default=512,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--output",
        type=str,
        default="outputs/dpo_english_m4_2/preference_accuracy.json",
    )

    args = parser.parse_args()

    tokenizer = load_tokenizer(MODEL_NAME)

    rows = load_preference_jsonl(args.eval_path)

    print(f"Evaluation examples: {len(rows)}")
    print(f"Max length:          {args.max_length}")
    print(f"Batch size:          {args.batch_size}")

    results = []

    if args.step_0:
        print()
        print("Evaluating: step-0")

        model = load_step0_model(MODEL_NAME)

        metrics = evaluate_checkpoint(
            model=model,
            tokenizer=tokenizer,
            rows=rows,
            max_length=args.max_length,
            batch_size=args.batch_size,
        )

        result = {
            "checkpoint": "step-0",
            **metrics,
        }

        results.append(result)

        print(
            f"examples={metrics['examples']} "
            f"accuracy={metrics['preference_accuracy']:.4f} "
            f"mean_margin={metrics['mean_margin']:.4f} "
            f"median_margin={metrics['median_margin']:.4f}"
        )

        print(
            f"mean_chosen_reward="
            f"{metrics['mean_chosen_reward']:.4f} "
            f"mean_rejected_reward="
            f"{metrics['mean_rejected_reward']:.4f}"
        )

        del model

        if torch.cuda.is_available():
            torch.cuda.empty_cache()


    for checkpoint_dir in args.checkpoint:
        print()
        print(f"Evaluating: {checkpoint_dir}")

        model = load_checkpoint_model(
            MODEL_NAME,
            checkpoint_dir,
        )

        metrics = evaluate_checkpoint(
            model=model,
            tokenizer=tokenizer,
            rows=rows,
            max_length=args.max_length,
            batch_size=args.batch_size,
        )

        result = {
            "checkpoint": checkpoint_dir,
            **metrics,
        }

        results.append(result)

        non_tie_accuracy = metrics["non_tie_accuracy"]

        if non_tie_accuracy is None:
            non_tie_accuracy_text = "N/A"
        else:
            non_tie_accuracy_text = f"{non_tie_accuracy:.4f}"

        print(
            f"examples={metrics['examples']} "
            f"accuracy={metrics['preference_accuracy']:.4f} "
            f"non_tie_accuracy={non_tie_accuracy_text} "
            f"tie_rate={metrics['tie_rate']:.4f} "
            f"mean_margin={metrics['mean_margin']:.4f} "
            f"median_margin={metrics['median_margin']:.4f}"
        )

        print(
            f"mean_chosen_reward="
            f"{metrics['mean_chosen_reward']:.4f} "
            f"mean_rejected_reward="
            f"{metrics['mean_rejected_reward']:.4f}"
        )

        del model

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "model": MODEL_NAME,
                "eval_path": args.eval_path,
                "max_length": args.max_length,
                "batch_size": args.batch_size,
                "results": results,
            },
            f,
            indent=2,
        )

    print()
    print(f"Saved evaluation results: {output_path}")


if __name__ == "__main__":
    main()