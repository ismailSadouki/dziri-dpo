import pytest
from transformers import AutoTokenizer


from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from scratch_dpo.data import (
    format_prompt_only,
    format_prompt_response,
    tokenize_pair,
)


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


@pytest.fixture(scope="module")
def tokenizer():
    return AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=True,
    )


def test_prompt_and_response_share_prompt_prefix(
    tokenizer,
):
    prompt = "What is 2 + 2?"
    response = "The answer is 4."

    prompt_text = format_prompt_only(
        tokenizer,
        prompt,
    )

    full_text = format_prompt_response(
        tokenizer,
        prompt,
        response,
    )

    prompt_ids = tokenizer(
        prompt_text,
        add_special_tokens=False,
    )["input_ids"]

    full_ids = tokenizer(
        full_text,
        add_special_tokens=False,
    )["input_ids"]

    assert full_ids[:len(prompt_ids)] == prompt_ids

def test_prompt_tokens_have_zero_mask(
    tokenizer,
):
    result = tokenize_pair(
        tokenizer=tokenizer,
        prompt="What is 2 + 2?",
        chosen="The answer is 4.",
        rejected="The answer is 5.",
    )

    start = result.chosen_response_start

    assert all(
        mask == 0
        for mask in result.chosen_loss_mask[:start]
    )

    assert all(
        mask == 1
        for mask in result.chosen_loss_mask[start:]
    )

def test_rejected_response_is_masked_correctly(
    tokenizer,
):
    result = tokenize_pair(
        tokenizer=tokenizer,
        prompt="What is 2 + 2?",
        chosen="The answer is 4.",
        rejected="The answer is 5.",
    )

    start = result.rejected_response_start

    assert all(
        mask == 0
        for mask in result.rejected_loss_mask[:start]
    )

    assert all(
        mask == 1
        for mask in result.rejected_loss_mask[start:]
    )


@pytest.mark.parametrize(
    "prompt,response",
    [
        ("Say hello.", "Hello!"),
        ("What is Python?", "Python is a programming language."),
        ("Return: OK", "OK."),
        ("Use the word 'cat'.", "cat."),
    ],
)
def test_punctuation_boundaries(
    tokenizer,
    prompt,
    response,
):
    result = tokenize_pair(
        tokenizer,
        prompt,
        response,
        "Something else.",
    )

    assert result.chosen_response_start > 0
    assert any(result.chosen_loss_mask)

@pytest.mark.parametrize(
    "prompt,response",
    [
        ("Write: <test>", "Done."),
        ("Use\nmultiple\nlines.", "Line one.\nLine two."),
        ("Use a tab\tcharacter.", "Done."),
    ],
)
def test_special_character_boundaries(
    tokenizer,
    prompt,
    response,
):
    result = tokenize_pair(
        tokenizer,
        prompt,
        response,
        "Rejected response.",
    )

    assert any(result.chosen_loss_mask)
    assert any(result.rejected_loss_mask)