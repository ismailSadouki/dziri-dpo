from __future__ import annotations

from pathlib import Path
import sys


sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)


import torch
import torch.nn.functional as F

from scratch_dpo.modeling import (
    load_tokenizer,
    load_policy,
    attach_lora,
)

from scratch_dpo.forward import concatenate_batch, concatenated_forward
from scratch_dpo.losses import dpo_loss

from scratch_dpo.reference import reference_forward

from scratch_dpo.collator import DPODataCollator


from scratch_dpo.dataset import load_hh_preferences
from scratch_dpo.data import tokenize_pair
from scratch_dpo.logps import get_batch_logps_from_logits


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

BETA = 0.1
ATOL = 1e-5



def trl_dpo_loss(
    policy_chosen_logps,
    policy_rejected_logps,
    reference_chosen_logps,
    reference_rejected_logps,
    beta,
):
    """
    TRL-equivalent standard sigmoid DPO loss.
    """

    chosen_logratios = (
        policy_chosen_logps
        - reference_chosen_logps
    )

    rejected_logratios = (
        policy_rejected_logps
        - reference_rejected_logps
    )

    delta = (
        chosen_logratios
        - rejected_logratios
    )

    losses = -F.logsigmoid(
        beta * delta
    )

    chosen_rewards = (
        beta * chosen_logratios
    ).detach()

    rejected_rewards = (
        beta * rejected_logratios
    ).detach()


    return (
        losses,
        chosen_rewards,
        rejected_rewards
    )



def test_real_batch_trl_equivalence():



    model = load_policy(MODEL_NAME)
    model = attach_lora(model)
    tokenizer = load_tokenizer(MODEL_NAME)



    rows, rejected = load_hh_preferences(
        n_examples = 1,
        seed=42
    )

    row = rows[0]

    example = tokenize_pair(
        tokenizer=tokenizer,
        prompt=row["prompt"],
        chosen=row["chosen"],
        rejected=row["rejected"],

    )

    collator = DPODataCollator(
        pad_token_id=tokenizer.pad_token_id,
    )
    batch = collator(
        [example]
    )

    batch = {
        key: value.to(model.device)
        for key, value in batch.items()
    }
    policy_chosen_logps, policy_rejected_logps = (
        concatenated_forward(
            model,
            batch
        )
    ) # [B], [B]


    concatenated_batch = concatenate_batch(batch)

    model_inputs = {
        "input_ids": concatenated_batch["input_ids"],
        "attention_mask": concatenated_batch["attention_mask"],
    }

    model_inputs = {
        key: value.to(model.device)
        for key, value in model_inputs.items()
    }

    reference_outputs = (
        reference_forward(
            model,
            model_inputs,
        )
    ) # [B], [B]

    reference_logps = get_batch_logps_from_logits(
        reference_outputs.logits,
        concatenated_batch["input_ids"].to(model.device),
        concatenated_batch["loss_mask"].to(model.device),
    )

    B = batch["chosen_input_ids"].shape[0]

    reference_chosen_logps = reference_logps[:B]
    reference_rejected_logps = reference_logps[B:]


    our_loss, _, _, _, _ = dpo_loss(
        policy_chosen_logps,
        policy_rejected_logps,
        reference_chosen_logps,
        reference_rejected_logps,
        beta=BETA,
    )

    trl_loss, _, _ = trl_dpo_loss(
        policy_chosen_logps,
        policy_rejected_logps,
        reference_chosen_logps,
        reference_rejected_logps,
        beta=BETA,
    )


    max_abs_diff = (
        our_loss - trl_loss
    ).abs().max()

    print(
        "Real-batch max_abs_diff:",
        max_abs_diff.item(),
    )

    assert torch.allclose(
        our_loss,
        trl_loss,
        atol=ATOL,
    )