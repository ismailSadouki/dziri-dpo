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
    dataset = dataset.select(
        range(min(n_examples, len(dataset)))
    )


    rows = []
    rejected = []

    for index, example in enumerate(dataset):
        try:
            row = canonicalize_example(example, index)
            rows.append(row)

        except ValueError as exc:
            rejected.append({
                "index": index,
                "reason": str(exc),
            })

    return rows, rejected


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