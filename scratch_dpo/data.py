from dataclasses import dataclass
from typing import Any

from transformers import PreTrainedTokenizerBase

@dataclass
class TokenizedPreference:
    chosen_input_ids: list[int]
    chosen_loss_mask: list[int]

    rejected_input_ids: list[int]
    rejected_loss_mask: list[int]


    chosen_response_start: int
    rejected_response_start: int


def format_prompt_only(
    tokenizer: PreTrainedTokenizerBase,
    prompt: str,
) -> str:
    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

def format_prompt_response(
    tokenizer: PreTrainedTokenizerBase,
    prompt: str,
    response: str,
) -> str:
    messages = [
        {
            "role": "user",
            "content": prompt,
        },
        {
            "role": "assistant",
            "content": response,
        },
    ]

    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )



def tokenize_pair(
        tokenizer: PreTrainedTokenizerBase,
        prompt: str,
        chosen: str,
        rejected: str,
        max_length: int = 512
) -> TokenizedPreference:


    prompt_text = format_prompt_only(
        tokenizer,
        prompt,
    )

    chosen_text = format_prompt_response(
        tokenizer,
        prompt,
        chosen,
    )

    rejected_text = format_prompt_response(
        tokenizer,
        prompt,
        rejected,
    )

    prompt_ids = tokenizer(
        prompt_text,
        add_special_tokens=False
    )["input_ids"]

    chosen_ids = tokenizer(
        chosen_text,
        add_special_tokens=False,
    )["input_ids"]

    rejected_ids = tokenizer(
        rejected_text,
        add_special_tokens=False,
    )["input_ids"]



    chosen_response_start = len(prompt_ids)
    rejected_response_start = len(prompt_ids)


    chosen_loss_mask = (
        [0] * chosen_response_start
        + [1] * (
            len(chosen_ids) - chosen_response_start
        )
    )
    rejected_loss_mask = (
        [0] * rejected_response_start
        + [1] * (
            len(rejected_ids) - rejected_response_start
        )
    )


    if chosen_response_start >= len(chosen_ids):
        raise ValueError(
            "Chosen response contains no tokens."
        )

    if rejected_response_start >= len(rejected_ids):
        raise ValueError(
            "Rejected response contains no tokens."
        )




    if chosen_ids[:chosen_response_start] != prompt_ids:
        raise AssertionError(
            "Chosen prompt tokens do not match prompt-only tokens."
        )

    if rejected_ids[:rejected_response_start] != prompt_ids:
        raise AssertionError(
            "Rejected prompt tokens do not match prompt-only tokens."
        )

    if len(prompt_ids) >= max_length:
        raise ValueError(
            "Prompt exceeds max_length; "
            "prompt truncation is forbidden."
        )


    chosen_ids = chosen_ids[:max_length]
    rejected_ids = rejected_ids[:max_length]

    chosen_loss_mask = chosen_loss_mask[:max_length]
    rejected_loss_mask = rejected_loss_mask[:max_length]

    assert len(chosen_ids) == len(chosen_loss_mask)
    assert len(rejected_ids) == len(rejected_loss_mask)

    
    if not any(chosen_loss_mask):
        raise ValueError(
            "Chosen response contains no tokens."
        )

    if not any(rejected_loss_mask):
        raise ValueError(
            "Rejected response contains no tokens."
        )

    return TokenizedPreference(
        chosen_input_ids=chosen_ids,
        chosen_loss_mask=chosen_loss_mask,

        rejected_input_ids=rejected_ids,
        rejected_loss_mask=rejected_loss_mask,

        chosen_response_start=chosen_response_start,
        rejected_response_start=rejected_response_start
    )



def decoded_mask_audit(
        tokenizer: PreTrainedTokenizerBase,
        input_ids: list[int],
        loss_mask: list[int]
):
    lines = []

    for position, (token_id, mask) in enumerate(
        zip(input_ids, loss_mask)
    ):
        token_text = tokenizer.decode(
            [token_id],
            skip_special_tokens=False
        )

        token_text = (
            token_text.replace("\n", "\\n").replace("\t", "\\t") 
        )

        region = "R" if mask == 1 else "P"

        lines.append(
            f"{position:04d} | {region} | "
            f"{token_id:6d} | {token_text!r}"
        )

    return "\n".join(lines)



        