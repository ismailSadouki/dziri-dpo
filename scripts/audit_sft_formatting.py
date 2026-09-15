import json
from collections import Counter
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from transformers import AutoTokenizer

from darija_alignment.sft import format_sft_example


MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

DATASETS = {
    "train": Path("data/splits/train.jsonl"),
    "validation": Path("data/splits/val.jsonl"),
}

MAX_LENGTH = 512


def load_rows(path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]



def main():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    for split, path in DATASETS.items():
        rows = load_rows(path)

        total = 0
        min_response = None
        max_response = 0
        truncated = 0
        category_counts = Counter()


        for row in rows:
            result = format_sft_example(
                tokenizer,
                row["messages"],
                max_length=MAX_LENGTH,
            )

            input_ids = result["input_ids"]
            labels = result["labels"]

            response_tokens = sum(
                label != -100
                for label in labels
            )

            total += 1
            min_response = (
                response_tokens
                if min_response is None
                else min(min_response, response_tokens)
            )

            max_response = max(max_response, response_tokens)
            category_counts[row["category"]] += 1

            # If the formatted sequence reached max_length,
            # check whether truncation actually occurred.
            full_text = tokenizer.apply_chat_template(
                row["messages"],
                tokenize=False,
                add_generation_prompt=False,
            )

            full_ids = tokenizer(
                full_text,
                add_special_tokens=False,
            )["input_ids"]

            if len(full_ids) > MAX_LENGTH:
                truncated += 1

        print(f"\n{split.upper()}")
        print("=" * 40)
        print(f"Examples:          {total}")
        print(f"Truncated:         {truncated}")
        print(f"Min response:      {min_response}")
        print(f"Max response:      {max_response}")
        print(f"Categories:        {dict(sorted(category_counts.items()))}")

        if min_response == 0:
            raise RuntimeError(f"{split}: example has zero response tokens")


if __name__ == "__main__":
    main()