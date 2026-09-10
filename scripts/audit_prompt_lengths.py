from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from statistics import mean, median

from transformers import AutoTokenizer

from scratch_dpo.dataset import load_preference_jsonl
from scratch_dpo.data import format_prompt_only


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
DATA_PATH = Path(
    "data/english/hh_rlhf_helpful-base_1800_train.jsonl"
)


def main():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    rows = load_preference_jsonl(DATA_PATH)

    lengths = []

    for row in rows:
        prompt_text = format_prompt_only(
            tokenizer,
            row["prompt"],
        )

        prompt_ids = tokenizer(
            prompt_text,
            add_special_tokens=False,
        )["input_ids"]

        lengths.append(len(prompt_ids))

    lengths.sort()

    def percentile(values, p):
        index = int((len(values) - 1) * p)
        return values[index]

    print(f"Examples: {len(lengths)}")
    print(f"Mean:     {mean(lengths):.1f}")
    print(f"Median:   {median(lengths):.1f}")
    print(f"P95:      {percentile(lengths, 0.95)}")
    print(f"P99:      {percentile(lengths, 0.99)}")
    print(f"Max:      {max(lengths)}")

    for limit in [512, 640, 768, 896, 1024, 1280, 1536]:
        count = sum(length > limit for length in lengths)
        print(
            f">{limit:4d}: {count:4d} "
            f"({100 * count / len(lengths):.2f}%)"
        )


if __name__ == "__main__":
    main()