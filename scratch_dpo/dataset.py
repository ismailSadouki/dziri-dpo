from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from datasets import load_dataset


SOURCE = "Anthropic/hh-rlhf"
SUBSET = "helpful-base"
SPLIT = "train"
SEED = 42
N_EXAMPLES = 2000
TRAIN_EXAMPLES = 1800
EVAL_EXAMPLES = 200
TOTAL_VALID_EXAMPLES = TRAIN_EXAMPLES + EVAL_EXAMPLES



def parse_hh_conversation(text: str) -> tuple[str, str]:
    """
    Convert HH-RLHF conversation text into:

        prompt, response

    Expected format:

        Human: ...
        
        Assistant: ...

        Human: ...
        
        Assistant: ...
    """

    if not text or not text.strip():
        raise ValueError("Empty conversation")

    text = text.strip()

    # Find the final Assistant turn rather than assuming
    # that splitting on "\n\n" produces the correct structure.
    assistant_marker = "\n\nAssistant:"

    last_assistant = text.rfind(assistant_marker)

    if last_assistant == -1:
        # Also handle a conversation that starts directly
        # with Assistant: or has unusual spacing.
        if text.startswith("Assistant:"):
            raise ValueError("Conversation contains no Human prompt")

        raise ValueError("No final Assistant turn found")

    prompt = text[:last_assistant].strip()
    response = text[
        last_assistant + len(assistant_marker):
    ].strip()

    if not prompt:
        raise ValueError("Empty prompt")

    if not response:
        raise ValueError("Empty response")

    return prompt, response

def canonicalize_example(
        example: dict[str, Any],
        index: int
) -> dict[str, Any]:
    prompt_chosen, chosen = parse_hh_conversation(
        example["chosen"]
    )
    prompt_rejected, rejected = parse_hh_conversation(
        example["rejected"]
    )

    if prompt_chosen != prompt_rejected:
        raise ValueError(
            f"Prompt mismatch: {prompt_chosen} != {prompt_rejected} at example {index}"
        )


    return {
        "id": f"hh_helpful_{index:06d}",
        "prompt": prompt_chosen,
        "chosen": chosen,
        "rejected": rejected,
        "source": SOURCE,
        "split": SPLIT,
        "metadata": {
            "subset": SUBSET,
        },
    }

def load_hh_preferences(
        n_examples: int = N_EXAMPLES,
        seed: int = SEED
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    dataset = load_dataset(
        SOURCE,
        # SUBSET,
        split=SPLIT,
        
    )
    dataset = dataset.shuffle(seed=seed)
    # dataset = dataset.select(
    #     range(min(n_examples, len(dataset)))
    # )


    rows = []
    rejected = []

    for index, example in enumerate(dataset):
        try:
            row = canonicalize_example(example, index)

            if row["chosen"].strip() == row["rejected"].strip():
                raise ValueError(
                    "chosen and rejected responses are identical"
                )
            
            rows.append(row)

            if len(rows) >= n_examples:
                break
        except ValueError as exc:
            rejected.append({
                "index": index,
                "reason": str(exc),
            })

    if len(rows) < n_examples:
        raise RuntimeError(
            f"Could only collect {len(rows)} valid examples "
            f"out of requested {n_examples}."
        )

    return rows, rejected

def load_preference_jsonl(
    path: str | Path,
) -> list[dict[str, Any]]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(path)

    rows = []

    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at {path}:{line_number}"
                ) from exc

            rows.append(row)

    if not rows:
        raise ValueError(
            f"No preference examples found in {path}"
        )

    return rows

def load_hh_train_eval(
    train_examples: int = TRAIN_EXAMPLES,
    eval_examples: int = EVAL_EXAMPLES,
    seed: int = SEED,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    total = train_examples + eval_examples

    rows, rejected = load_hh_preferences(
        n_examples=total,
        seed=seed,
    )

    train_rows = rows[:train_examples]
    eval_rows = rows[train_examples:total]

    train_ids = {row["id"] for row in train_rows}
    eval_ids = {row["id"] for row in eval_rows}

    overlap = train_ids & eval_ids

    if overlap:
        raise RuntimeError(
            f"Train/eval ID overlap detected: {sorted(overlap)[:10]}"
        )

    if len(train_rows) != train_examples:
        raise RuntimeError(
            f"Expected {train_examples} train examples, "
            f"got {len(train_rows)}."
        )

    if len(eval_rows) != eval_examples:
        raise RuntimeError(
            f"Expected {eval_examples} eval examples, "
            f"got {len(eval_rows)}."
        )

    return train_rows, eval_rows, rejected

def write_jsonl(
        rows: list[dict[str, Any]],
        path: str | Path
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    rows, rejected = load_hh_preferences()

    output_path = Path(
        f"data/english/hh_rlhf_{SUBSET}_{N_EXAMPLES}.jsonl"
    )

    write_jsonl(rows, output_path)

    rejected_path = Path(
        "data/english/hh_rlhf_rejected.jsonl"
    )

    write_jsonl(rejected, rejected_path)

    print(f"Requested: {N_EXAMPLES}")
    print(f"Valid:     {len(rows)}")
    print(f"Rejected:  {len(rejected)}")
    print(f"Output:    {output_path}")
    print(f"Rejected:  {rejected_path}")




