from __future__ import annotations


import torch

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))



from scratch_dpo.logps import get_batch_logps_from_logits


def concatenate_batch(
    batch: dict[str, torch.Tensor],
) -> dict[str, torch.Tensor]:
    """
    Concatenate chosen and rejected sequences along the batch dimension.

    Input:
        chosen_*:   [B, T]
        rejected_*: [B, T]

    Output:
        concatenated_*: [2B, T]
    """

    input_ids = torch.cat(
        [
            batch["chosen_input_ids"],
            batch["rejected_input_ids"],
        ],
        dim=0,
    )

    attention_mask = torch.cat(
        [
            batch["chosen_attention_mask"],
            batch["rejected_attention_mask"],
        ],
        dim=0,
    )

    loss_mask = torch.cat(
        [
            batch["chosen_loss_mask"],
            batch["rejected_loss_mask"],
        ],
        dim=0,
    )

    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "loss_mask": loss_mask,
    }


def concatenated_forward(
    model,
    batch: dict[str, torch.Tensor],
) -> tuple[torch.Tensor, torch.Tensor]:

    concatenated = concatenate_batch(batch)

    outputs = model(
        input_ids=concatenated["input_ids"],
        attention_mask=concatenated["attention_mask"],
    )

    all_logps = get_batch_logps_from_logits(
        logits=outputs.logits,
        labels=concatenated["input_ids"],
        loss_mask=concatenated["loss_mask"],
    )

    B = batch["chosen_input_ids"].shape[0]

    chosen_logps = all_logps[:B]
    rejected_logps = all_logps[B:]

    return chosen_logps, rejected_logps



def reference_concatenated_forward(
        model,
        batch: dict[str, torch.Tensor]
) -> tuple[torch.Tensor, torch.Tensor]:
    concatenated = concatenate_batch(batch)

    with torch.no_grad():
        with model.disable_adapter():
            outputs = model(
                input_ids=concatenated["input_ids"],
                attention_mask=concatenated["attention_mask"],
            )

    all_logps = get_batch_logps_from_logits(
        logits=outputs.logits,
        labels=concatenated["input_ids"],
        loss_mask=concatenated["loss_mask"],
    )

    # no_grad() means all_logps has no autograd graph.
    all_logps = all_logps.detach()

    B = batch["chosen_input_ids"].shape[0]

    reference_chosen_logps = all_logps[:B]
    reference_rejected_logps = all_logps[B:]

    return reference_chosen_logps, reference_rejected_logps