import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from transformers import AutoTokenizer

from darija_alignment.sft import format_sft_example


MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
DATA_PATH = Path("data/instruction_dataset_v1.jsonl")


def load_first_row():
    with DATA_PATH.open(encoding="utf-8") as f:
        return json.loads(next(f))


def test_response_only_labels():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    row = load_first_row()

    result = format_sft_example(
        tokenizer,
        row["messages"],
        max_length=512,
    )

    input_ids = result["input_ids"]
    labels = result["labels"]

    assert len(input_ids) == len(labels)
    assert len(input_ids) == len(result["attention_mask"])

    # Find the first supervised token.
    supervised_positions = [
        i for i, label in enumerate(labels)
        if label != -100
    ]

    assert supervised_positions

    first_supervised = supervised_positions[0]

    # Everything before the response is masked.
    assert all(
        label == -100
        for label in labels[:first_supervised]
    )

    # Every supervised label must equal its input token.
    assert all(
        labels[i] == input_ids[i]
        for i in supervised_positions
    )

    print("SFT FORMATTER: PASS")
    print(f"Total tokens:      {len(input_ids)}")
    print(f"Prompt tokens:     {first_supervised}")
    print(f"Response tokens:   {len(input_ids) - first_supervised}")


if __name__ == "__main__":
    test_response_only_labels()