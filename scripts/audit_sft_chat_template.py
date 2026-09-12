import json
from pathlib import Path

from transformers import AutoTokenizer


DATA_PATH = Path("data/instruction_dataset.jsonl")
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"


def main():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    if tokenizer.chat_template is None:
        raise RuntimeError("Tokenizer has no chat template")

    with DATA_PATH.open(encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]

    print("CHAT TEMPLATE AUDIT")
    print("-------------------")
    print(f"Model: {MODEL_NAME}")
    print(f"Rows audited: {len(rows)}")
    print("Chat template: PRESENT")

    for row in rows:
        messages = row["messages"]

        rendered = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )

        if not rendered.strip():
            raise RuntimeError(
                f"{row['id']}: rendered chat template is empty"
            )

        tokenized = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=False,
        )

        if len(tokenized) == 0:
            raise RuntimeError(
                f"{row['id']}: tokenized sequence is empty"
            )

    print("Rendered examples: PASS")
    print("Tokenization: PASS")
    print("CHAT TEMPLATE AUDIT: PASS")


if __name__ == "__main__":
    main()