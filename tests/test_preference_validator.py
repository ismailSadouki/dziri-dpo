import pytest

from pathlib import Path

import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from scratch_dpo.validate_preference_data import (
    validate_preference_data,
)


def make_row(**overrides):
    row = {
        "id": "test_001",
        "prompt": "What is 2 + 2?",
        "chosen": "The answer is 4.",
        "rejected": "The answer is 5.",
        "source": "test",
        "split": "test",
        "metadata": {},
    }

    row.update(overrides)

    return row


def test_valid_example_passes():
    result = validate_preference_data(
        [make_row()]
    )

    assert len(result.valid) == 1
    assert len(result.rejected) == 0


def test_empty_prompt_is_rejected():
    result = validate_preference_data(
        [make_row(prompt="")]
    )

    assert len(result.valid) == 0
    assert "empty prompt" in result.rejected[0]["errors"]


def test_empty_chosen_is_rejected():
    result = validate_preference_data(
        [make_row(chosen="")]
    )

    assert len(result.valid) == 0
    assert "empty chosen response" in result.rejected[0]["errors"]


def test_empty_rejected_is_rejected():
    result = validate_preference_data(
        [make_row(rejected="")]
    )

    assert len(result.valid) == 0
    assert "empty rejected response" in result.rejected[0]["errors"]


def test_identical_responses_are_rejected():
    result = validate_preference_data(
        [
            make_row(
                chosen="same",
                rejected="same",
            )
        ]
    )

    assert len(result.valid) == 0
    assert (
        "chosen and rejected responses are identical"
        in result.rejected[0]["errors"]
    )


def test_duplicate_ids_are_rejected():
    result = validate_preference_data(
        [
            make_row(id="duplicate"),
            make_row(
                id="duplicate",
                prompt="Another prompt",
            ),
        ]
    )

    assert len(result.valid) == 1
    assert len(result.rejected) == 1
    assert "duplicate ID" in result.rejected[0]["errors"]