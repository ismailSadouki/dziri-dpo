import torch
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from scratch_dpo.logps import get_batch_logps_from_logits


def test_hand_computed_logps():

    # B=1, T=3, V=3
    #
    # token sequence:
    # [0, 1, 2]
    #
    # logits at position 0 predict token 1
    # logits at position 1 predict token 2

    logits = torch.tensor(
        [
            [
                [0.0, 2.0, 0.0],
                [0.0, 0.0, 3.0],
                [3.0, 0.0, 0.0],
            ]
        ]
    )

    labels = torch.tensor(
        [[0, 1, 2]]
    )

    loss_mask = torch.tensor(
        [[0, 1, 1]]
    )

    result = get_batch_logps_from_logits(
        logits,
        labels,
        loss_mask,
    )

    expected = (
        torch.log_softmax(logits[0, 0], dim=-1)[1]
        +
        torch.log_softmax(logits[0, 1], dim=-1)[2]
    )

    assert torch.allclose(
        result,
        expected.unsqueeze(0),
    )


def test_prompt_tokens_are_excluded():

    torch.manual_seed(0)

    logits = torch.randn(1, 5, 10)

    labels = torch.tensor(
        [[0, 1, 2, 3, 4]]
    )

    # Only tokens 3 and 4 are response tokens.
    loss_mask = torch.tensor(
        [[0, 0, 0, 1, 1]]
    )

    result = get_batch_logps_from_logits(
        logits,
        labels,
        loss_mask,
    )

    expected = (
        torch.log_softmax(logits[0, 2], dim=-1)[3]
        +
        torch.log_softmax(logits[0, 3], dim=-1)[4]
    )

    assert torch.allclose(
        result[0],
        expected,
    )


def test_padding_contributes_zero():

    logits = torch.randn(1, 5, 10)

    labels = torch.tensor(
        [[0, 1, 2, 3, 0]]
    )

    loss_mask = torch.tensor(
        [[0, 1, 1, 1, 0]]
    )

    result = get_batch_logps_from_logits(
        logits,
        labels,
        loss_mask,
    )

    expected = (
        torch.log_softmax(logits[0, 0], dim=-1)[1]
        +
        torch.log_softmax(logits[0, 1], dim=-1)[2]
        +
        torch.log_softmax(logits[0, 2], dim=-1)[3]
    )

    assert torch.allclose(
        result[0],
        expected,
    )

def test_ignore_index_100():

    logits = torch.randn(1, 4, 10)

    labels = torch.tensor(
        [[0, -100, 2, 3]]
    )

    loss_mask = torch.tensor(
        [[0, 0, 1, 1]]
    )

    result = get_batch_logps_from_logits(
        logits,
        labels,
        loss_mask,
    )

    assert result.shape == (1,)
    assert torch.isfinite(result).all()


def test_sum_and_average_differ():

    logits = torch.randn(1, 5, 10)

    labels = torch.tensor(
        [[0, 1, 2, 3, 4]]
    )

    loss_mask = torch.tensor(
        [[0, 1, 1, 1, 1]]
    )

    summed = get_batch_logps_from_logits(
        logits,
        labels,
        loss_mask,
        average_log_prob=False,
    )

    averaged = get_batch_logps_from_logits(
        logits,
        labels,
        loss_mask,
        average_log_prob=True,
    )

    assert torch.allclose(
        averaged,
        summed / 4,
    )

    