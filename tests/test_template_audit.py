import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))


from transformers import AutoTokenizer


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
FIXTURE_PATH = Path("tests/fixtures/tiny_preferences.jsonl")


def test_chosen_and_rejected_share_prompt_rendering():
    row = json.loads(
        next(
            line
            for line in FIXTURE_PATH.read_text().splitlines()
            if line.strip()
        )
    )

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=True,
    )

    prompt_messages = [
        {
            "role": "user",
            "content": row["prompt"],
        }
    ]

    chosen_messages = [
        *prompt_messages,
        {
            "role": "assistant",
            "content": row["chosen"],
        },
    ]

    rejected_messages = [
        *prompt_messages,
        {
            "role": "assistant",
            "content": row["rejected"],
        },
    ]

    prompt = tokenizer.apply_chat_template(
        prompt_messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    chosen = tokenizer.apply_chat_template(
        chosen_messages,
        tokenize=False,
        add_generation_prompt=False,
    )

    rejected = tokenizer.apply_chat_template(
        rejected_messages,
        tokenize=False,
        add_generation_prompt=False,
    )

    assert chosen.startswith(prompt)
    assert rejected.startswith(prompt)
    assert chosen != rejected