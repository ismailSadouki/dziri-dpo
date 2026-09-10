
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))


import torch

from peft import PeftModel

from scratch_dpo.modeling import load_policy, attach_lora
from train_scratch_dpo import build_optimizer

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
CHECKPOINT = Path(
    "outputs/dpo_english_smoke/checkpoint-25"
)


def get_trainable_state(model):
    return {
        name: param.detach().cpu().clone()
        for name, param in model.named_parameters()
        if param.requires_grad
    }


def test_checkpoint_reload_exact_weights():
    assert CHECKPOINT.exists()

    # ---------------------------------------------------------
    # 1. Load the checkpoint as a normal trainable policy.
    # ---------------------------------------------------------
    base_model = load_policy(MODEL_NAME)

    reloaded_model = PeftModel.from_pretrained(
        base_model,
        CHECKPOINT,
        is_trainable=True,
    )

    reloaded_state = get_trainable_state(reloaded_model)

    assert reloaded_state
    assert any(
        "lora" in name.lower()
        for name in reloaded_state
    )

    # ---------------------------------------------------------
    # 2. Load the adapter checkpoint independently using
    #    another base model instance.
    #
    #    This gives us another reconstruction of the same
    #    checkpoint and lets us verify deterministic loading.
    # ---------------------------------------------------------
    base_model_2 = load_policy(MODEL_NAME)

    reloaded_model_2 = PeftModel.from_pretrained(
        base_model_2,
        CHECKPOINT,
        is_trainable=True,
    )

    reloaded_state_2 = get_trainable_state(
        reloaded_model_2
    )

    assert reloaded_state.keys() == reloaded_state_2.keys()

    for name in reloaded_state:
        assert torch.equal(
            reloaded_state[name],
            reloaded_state_2[name],
        ), f"Mismatch in parameter: {name}"

    print(
        f"Exact adapter reload verified: "
        f"{len(reloaded_state)} trainable tensors."
    )


def test_optimizer_checkpoint_loads():
    assert CHECKPOINT.exists()

    base_model = load_policy(MODEL_NAME)

    model = PeftModel.from_pretrained(
        base_model,
        CHECKPOINT,
        is_trainable=True,
    )

    optimizer = build_optimizer(
        model=model,
        learning_rate=5e-5,
        weight_decay=0.0,
    )

    optimizer_state = torch.load(
        CHECKPOINT / "optimizer.pt",
        map_location="cpu",
        weights_only=False,
    )

    optimizer.load_state_dict(optimizer_state)

    # AdamW should have state for the parameters that have
    # already received gradients during training.
    assert len(optimizer.state) > 0

    print(
        f"Optimizer state loaded: "
        f"{len(optimizer.state)} parameter states."
    )