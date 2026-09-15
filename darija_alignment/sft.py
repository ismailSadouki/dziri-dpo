from typing import Any


def format_sft_example(
    tokenizer,
    messages: list[dict[str, Any]],
    max_length: int = 512,
) -> dict[str, list[int]]:
    if not messages:
        raise ValueError("messages cannot be empty")
    if messages[-1]["role"] != "assistant":
        raise ValueError("last message must be an assistant message")

    full_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )
    prompt_text = tokenizer.apply_chat_template(
        messages[:-1],
        tokenize=False,
        add_generation_prompt=True,
    )

    full_ids = tokenizer(
        full_text,
        add_special_tokens=False,
    )["input_ids"]

    prompt_ids = tokenizer(
        prompt_text,
        add_special_tokens=False,
    )["input_ids"]

    prompt_len = len(prompt_ids)

    if full_ids[:prompt_len] != prompt_ids:
        raise ValueError("prompt/full token boundary mismatch")

    if prompt_len >= len(full_ids):
        raise ValueError("assistant response contains no tokens")


    full_ids = full_ids[:max_length]

    if prompt_len >= len(full_ids):
        raise ValueError(
            "max_length truncates the entire assistant response"
        )

    labels = [-100] * prompt_len + full_ids[prompt_len:]

    attention_mask = [1] * len(full_ids)

    return {
        "input_ids": full_ids,
        "attention_mask": attention_mask,
        "labels": labels,
    }