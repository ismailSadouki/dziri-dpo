from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from transformers import AutoTokenizer

from scratch_dpo.dataset import (
    EVAL_EXAMPLES,
    SEED,
    TRAIN_EXAMPLES,
    load_hh_train_eval,
    write_jsonl,
)

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
MAX_LENGTH = 512
TRAIN_PATH = Path(
    "data/english/hh_rlhf_helpful-base_1800_train.jsonl"
)

EVAL_PATH = Path(
    "data/english/hh_rlhf_helpful-base_200_eval.jsonl"
)
EVAL_CANDIDATES = 220

REJECTED_PATH = Path(
    "data/english/hh_rlhf_split_rejected.jsonl"
)

def filter_long_prompts(rows, tokenizer, max_length):
    kept = []
    rejected = []

    for row in rows:
        prompt_text = tokenizer.apply_chat_template(
            [
                {
                    "role": "user",
                    "content": row["prompt"],
                }
            ],
            tokenize=False,
            add_generation_prompt=True,
        )

        prompt_ids = tokenizer(
            prompt_text,
            add_special_tokens=False,
        )["input_ids"]

        if len(prompt_ids) >= max_length:
            rejected.append(
                {
                    "id": row["id"],
                    "reason": "Prompt exceeds max_length",
                    "prompt_tokens": len(prompt_ids),
                    "max_length": max_length,
                }
            )
        else:
            kept.append(row)

    return kept, rejected

def main():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


    train_rows, eval_rows, rejected = load_hh_train_eval(
        train_examples=TRAIN_EXAMPLES,
        eval_examples=EVAL_CANDIDATES,
        seed=SEED,
    )

    train_rows, train_long_prompt_rejected = filter_long_prompts(
        train_rows,
        tokenizer,
        MAX_LENGTH,
    )

    eval_rows, eval_long_prompt_rejected = filter_long_prompts(
        eval_rows,
        tokenizer,
        MAX_LENGTH,
    )

    rejected.extend(train_long_prompt_rejected)
    rejected.extend(eval_long_prompt_rejected)

    if len(eval_rows) < EVAL_EXAMPLES:
        raise RuntimeError(
            f"Only {len(eval_rows)} valid eval examples remain "
            f"after prompt filtering; need {EVAL_EXAMPLES}."
        )

    eval_rows = eval_rows[:EVAL_EXAMPLES]


    write_jsonl(train_rows, TRAIN_PATH)
    write_jsonl(eval_rows, EVAL_PATH)
    write_jsonl(rejected, REJECTED_PATH)

    print(f"Seed:              {SEED}")
    print(f"Original train:    {TRAIN_EXAMPLES}")
    print(f"Final train:       {len(train_rows)}")
    print(f"Eval:               {len(eval_rows)}")
    print(f"Rejected total:    {len(rejected)}")
    print(f"Max prompt length: {MAX_LENGTH}")
    print(f"Train:             {TRAIN_PATH}")
    print(f"Eval:              {EVAL_PATH}")
    print(f"Rejected:          {REJECTED_PATH}")


    train_ids = {row["id"] for row in train_rows}
    eval_ids = {row["id"] for row in eval_rows}

    assert len(train_ids) == (
        TRAIN_EXAMPLES - len(train_long_prompt_rejected)
    )
    assert len(eval_ids) == EVAL_EXAMPLES
    assert train_ids.isdisjoint(eval_ids)
    assert train_ids.isdisjoint(eval_ids)

    print("Split integrity: PASS")


if __name__ == "__main__":
    main()