import json
from pathlib import Path

from transformers import AutoTokenizer


from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from scratch_dpo.data import (
    tokenize_pair,
    decoded_mask_audit,
)


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

FIXTURE_PATH = Path(
    "tests/fixtures/tiny_preferences.jsonl"
)

REPORT_PATH = Path(
    "reports/response_mask_audit.md"
)


def load_examples():
    rows = []

    for line in FIXTURE_PATH.read_text(
        encoding="utf-8"
    ).splitlines():
        if line.strip():
            rows.append(json.loads(line))

    return rows


def main():
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=True,
    )

    examples = load_examples()

    sections = [
        "# Response Mask Audit",
        "",
        f"Model: `{MODEL_NAME}`",
        "",
        "The audit verifies that prompt tokens receive "
        "`mask=0` and response tokens receive `mask=1`.",
        "",
    ]

    for example in examples:

        result = tokenize_pair(
            tokenizer=tokenizer,
            prompt=example["prompt"],
            chosen=example["chosen"],
            rejected=example["rejected"],
            max_length=512,
        )

        sections.extend([
            f"## Example: {example['id']}",
            "",
            "### Raw example",
            "",
            "**Prompt**",
            "",
            "```text",
            example["prompt"],
            "```",
            "",
            "**Chosen**",
            "",
            "```text",
            example["chosen"],
            "```",
            "",
            "**Rejected**",
            "",
            "```text",
            example["rejected"],
            "```",
            "",
            "### Chosen response boundary",
            "",
            f"- `response_start`: "
            f"`{result.chosen_response_start}`",
            f"- sequence length: "
            f"`{len(result.chosen_input_ids)}`",
            "",
            "```text",
            "pos  | region | token_id | decoded",
            "-----|--------|----------|--------",
            result.chosen_loss_mask and
            decoded_mask_audit(
                tokenizer,
                result.chosen_input_ids,
                result.chosen_loss_mask,
            ),
            "```",
            "",
            "### Rejected response boundary",
            "",
            f"- `response_start`: "
            f"`{result.rejected_response_start}`",
            f"- sequence length: "
            f"`{len(result.rejected_input_ids)}`",
            "",
            "```text",
            "pos  | region | token_id | decoded",
            "-----|--------|----------|--------",
            decoded_mask_audit(
                tokenizer,
                result.rejected_input_ids,
                result.rejected_loss_mask,
            ),
            "```",
            "",
        ])

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_PATH.write_text(
        "\n".join(sections),
        encoding="utf-8",
    )

    print(f"Audit written to {REPORT_PATH}")


if __name__ == "__main__":
    main()