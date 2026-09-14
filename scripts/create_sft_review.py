import argparse
import csv
import json
from pathlib import Path


FIELDS = [
    "candidate_id",
    "category",
    "script",
    "user_text",
    "assistant_text",
    "decision",
    "dialect_ok",
    "factual_ok",
    "instruction_ok",
    "natural_ok",
    "edited_user_text",
    "edited_assistant_text",
    "notes",
]


def main():
    parser = argparse.ArgumentParser(
        description="Create SFT human-review CSV from candidate JSONL"
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Input normalized candidate JSONL",
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output review CSV",
    )

    args = parser.parse_args()

    input_path = args.input
    output_path = args.output

    if not input_path.exists():
        raise FileNotFoundError(input_path)

    rows = []

    with input_path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Line {line_no}: invalid JSON: {exc}"
                )

            rows.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=FIELDS,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow({
                "candidate_id": row["candidate_id"],
                "category": row["category"],
                "script": row["script"],
                "user_text": row["messages"][0]["content"],
                "assistant_text": row["messages"][1]["content"],
                "decision": "",
                "dialect_ok": "",
                "factual_ok": "",
                "instruction_ok": "",
                "natural_ok": "",
                "edited_user_text": "",
                "edited_assistant_text": "",
                "notes": "",
            })

    print("REVIEW SHEET: PASS")
    print(f"Candidates: {len(rows)}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()