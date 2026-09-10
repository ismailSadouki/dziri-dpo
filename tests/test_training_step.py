from __future__ import annotations

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

import torch

from scratch_dpo.data import tokenize_pair
from scratch_dpo.collator import DPODataCollator
from scratch_dpo.modeling import (
    load_tokenizer,
    load_policy,
    attach_lora,
)
from train_scratch_dpo import (
    build_optimizer,
    training_step,
    optimizer_step,
)


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


def test_one_optimizer_step_updates_only_trainable_parameters():
    tokenizer = load_tokenizer(MODEL_NAME)

    model = load_policy(MODEL_NAME)
    model = attach_lora(model)

    model.train()

    examples = [
        {
            "prompt": "What is the capital of France?",
            "chosen": "The capital of France is Paris.",
            "rejected": "The capital of France is Berlin.",
        },
        {
            "prompt": "What color is the sky on a clear day?",
            "chosen": "The sky is usually blue on a clear day.",
            "rejected": "The sky is usually green on a clear day.",
        },
    ]

    tokenized_examples = [
        tokenize_pair(
            tokenizer=tokenizer,
            prompt=example["prompt"],
            chosen=example["chosen"],
            rejected=example["rejected"],
            max_length=128,
        )
        for example in examples
    ]

    collator = DPODataCollator(
        pad_token_id=tokenizer.pad_token_id,
    )
    batch = collator(tokenized_examples)

    device = model.device

    batch = {
        key: value.to(device)
        for key, value in batch.items()
    }

    optimizer = build_optimizer(
        model=model,
        learning_rate=5e-5,
        weight_decay=0.0,
    )

    trainable_before = {
        name: parameter.detach().clone()
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    }

    frozen_before = {
        name: parameter.detach().clone()
        for name, parameter in model.named_parameters()
        if not parameter.requires_grad
    }

    optimizer.zero_grad(set_to_none=True)

    metrics = training_step(
        model=model,
        batch=batch,
        beta=0.1,
        loss_scale=1.0,
    )

    assert torch.isfinite(
        torch.tensor(metrics["loss"])
    )

    grad_norm = optimizer_step(
        model=model,
        optimizer=optimizer,
        max_grad_norm=1.0,
    )

    assert torch.isfinite(
        torch.tensor(grad_norm)
    )

    trainable_changed = False

    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            if not torch.equal(
                parameter.detach(),
                trainable_before[name],
            ):
                trainable_changed = True

    assert trainable_changed, (
        "No trainable parameter changed after "
        "the optimizer step."
    )

    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            assert torch.equal(
                parameter.detach(),
                frozen_before[name],
            ), f"Frozen parameter changed: {name}"

    optimizer.zero_grad(set_to_none=True)