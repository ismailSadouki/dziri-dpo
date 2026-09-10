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


def make_batch(tokenizer, model):
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

    return {
        key: value.to(device)
        for key, value in batch.items()
    }


def test_gradient_accumulation_updates_only_at_boundary():
    tokenizer = load_tokenizer(MODEL_NAME)

    model = load_policy(MODEL_NAME)
    model = attach_lora(model)
    model.train()

    batch = make_batch(tokenizer, model)

    optimizer = build_optimizer(
        model=model,
        learning_rate=5e-5,
        weight_decay=0.0,
    )

    optimizer.zero_grad(set_to_none=True)

    trainable_before = {
        name: parameter.detach().clone()
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    }

    accumulation_steps = 2


    frozen_before = {
        name: parameter.detach().clone()
        for name, parameter in model.named_parameters()
        if not parameter.requires_grad
    }
    # First microbatch.
    metrics_1 = training_step(
        model=model,
        batch=batch,
        beta=0.1,
        loss_scale=1.0 / accumulation_steps,
    )

    assert torch.isfinite(
        torch.tensor(metrics_1["loss"])
    )

    # No optimizer step has happened yet.
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            assert torch.equal(
                parameter.detach(),
                trainable_before[name],
            ), f"Parameter changed before accumulation boundary: {name}"

    # Gradients should exist after the first backward pass.
    trainable_grads = [
        parameter.grad
        for parameter in model.parameters()
        if parameter.requires_grad
    ]

    assert any(
        grad is not None
        for grad in trainable_grads
    ), "No trainable gradients were produced."

    # Second microbatch.
    metrics_2 = training_step(
        model=model,
        batch=batch,
        beta=0.1,
        loss_scale=1.0 / accumulation_steps,
    )

    assert torch.isfinite(
        torch.tensor(metrics_2["loss"])
    )

    # Optimizer step happens only at the accumulation boundary.
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
        "the accumulated optimizer step."
    )

    # Frozen parameters must remain unchanged.
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            assert torch.equal(
                parameter.detach(),
                frozen_before[name],
            ), f"Frozen parameter changed: {name}"

    optimizer.zero_grad(set_to_none=True)