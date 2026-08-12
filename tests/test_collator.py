import torch

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))


from scratch_dpo.collator import DPODataCollator
from scratch_dpo.data import TokenizedPreference


def make_example(
    chosen_length: int,
    rejected_length: int,
):
    return TokenizedPreference(
        chosen_input_ids=list(range(chosen_length)),
        chosen_loss_mask=[
            0, 0, 1, 1, 1
        ][:chosen_length],
        rejected_input_ids=list(
            range(100, 100 + rejected_length)
        ),
        rejected_loss_mask=[
            0, 0, 1, 1
        ][:rejected_length],
        chosen_response_start=2,
        rejected_response_start=2,
    )


def test_collator_handles_unequal_lengths():

    examples = [
        make_example(5, 4),
        make_example(3, 5),
    ]

    collator = DPODataCollator(
        pad_token_id=999
    )

    batch = collator(examples)

    assert batch["chosen_input_ids"].shape == (2, 5)
    assert batch["rejected_input_ids"].shape == (2, 5)

    assert batch["chosen_attention_mask"].shape == (2, 5)
    assert batch["rejected_attention_mask"].shape == (2, 5)

    assert batch["chosen_loss_mask"].shape == (2, 5)
    assert batch["rejected_loss_mask"].shape == (2, 5)


def test_padding_has_zero_loss_mask():

    examples = [
        make_example(5, 3),
        make_example(3, 5),
    ]

    collator = DPODataCollator(
        pad_token_id=999
    )

    batch = collator(examples)

    chosen_pad = (
        batch["chosen_attention_mask"] == 0
    )

    rejected_pad = (
        batch["rejected_attention_mask"] == 0
    )

    assert torch.all(
        batch["chosen_loss_mask"][chosen_pad] == 0
    )

    assert torch.all(
        batch["rejected_loss_mask"][rejected_pad] == 0
    )


def test_attention_mask_and_loss_mask_are_different():

    examples = [
        make_example(5, 5),
    ]

    collator = DPODataCollator(
        pad_token_id=999
    )

    batch = collator(examples)

    assert torch.equal(
        batch["chosen_attention_mask"],
        torch.tensor([[1, 1, 1, 1, 1]])
    )

    assert torch.equal(
        batch["chosen_loss_mask"],
        torch.tensor([[0, 0, 1, 1, 1]])
    )