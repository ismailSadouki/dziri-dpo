import argparse
import csv
import json
from pathlib import Path


FIELDS = [
    "id",
    "category",
    "script",
    "prompt",
    "chosen",
    "rejected",
    "preference_label",
    "preference_reason",
    "annotator",
    "notes",
]


def load_jsonl(path):
    rows = []

    with path.open(encoding="utf-8") as f:
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

    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Create human preference review CSV"
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    rows = load_jsonl(args.input)

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with args.output.open(
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
                "id": row["id"],
                "category": row["category"],
                "script": row["script"],
                "prompt": row["prompt"],
                "chosen": row["chosen"],
                "rejected": row["rejected"],
                "preference_label": "",
                "preference_reason": "",
                "annotator": "",
                "notes": "",
            })

    print("PREFERENCE REVIEW CSV: CREATED")
    print(f"Rows: {len(rows)}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()