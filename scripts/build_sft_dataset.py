import argparse
import csv
import json
from pathlib import Path


OUTPUT_PATH = Path("data/instruction_dataset_v1.jsonl")


def load_existing_dataset():
    existing_records = []
    existing_ids = set()
    existing_pairs = set()

    if not OUTPUT_PATH.exists():
        return existing_records, existing_ids, existing_pairs

    with OUTPUT_PATH.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Existing dataset line {line_no}: invalid JSON: {exc}"
                )

            existing_records.append(record)

            record_id = record["id"]

            if record_id in existing_ids:
                raise ValueError(
                    f"Duplicate ID already exists in dataset: {record_id}"
                )

            existing_ids.add(record_id)

            messages = record["messages"]

            pair = (
                messages[0]["content"].strip(),
                messages[1]["content"].strip(),
            )

            if pair in existing_pairs:
                raise ValueError(
                    f"Duplicate user/assistant pair already exists "
                    f"in dataset: {record_id}"
                )

            existing_pairs.add(pair)

    return existing_records, existing_ids, existing_pairs


def main():
    parser = argparse.ArgumentParser(
        description="Merge reviewed SFT examples into the main dataset"
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Input review CSV",
    )

    args = parser.parse_args()

    input_path = args.input

    if not input_path.exists():
        raise FileNotFoundError(input_path)

    kept = 0
    rejected = 0
    edited = 0
    duplicates = 0

    existing_records, existing_ids, existing_pairs = (
        load_existing_dataset()
    )

    with input_path.open(
        encoding="utf-8",
        newline="",
    ) as f:
        rows = list(csv.DictReader(f))

    new_records = []

    for row in rows:
        decision = row["decision"].strip().lower()

        if decision == "reject":
            rejected += 1
            continue

        if decision not in {"accept", "edit"}:
            raise ValueError(
                f"Invalid decision for {row['candidate_id']}: {decision!r}"
            )

        user_text = (
            row["edited_user_text"].strip()
            if decision == "edit"
            and row["edited_user_text"].strip()
            else row["user_text"].strip()
        )

        assistant_text = (
            row["edited_assistant_text"].strip()
            if decision == "edit"
            and row["edited_assistant_text"].strip()
            else row["assistant_text"].strip()
        )

        candidate_id = row["candidate_id"].strip()

        pair = (user_text, assistant_text)

        # Skip duplicate ID or duplicate user/assistant pair
        if candidate_id in existing_ids or pair in existing_pairs:
            duplicates += 1
            continue

        if decision == "edit":
            edited += 1

        record = {
            "id": candidate_id,
            "messages": [
                {
                    "role": "user",
                    "content": user_text,
                },
                {
                    "role": "assistant",
                    "content": assistant_text,
                },
            ],
            "category": row["category"],
            "script": row["script"],
            "source": "synthetic_then_human_verified",
            "license": "project-created",
            "metadata": {
                "dialect": "algerian_darija",
                "code_switching": "allowed",
                "quality_status": "accepted",
                "generation_method": "llm",
                "human_review": True,
                "review_decision": decision,
                "review_notes": row["notes"].strip(),
            },
        }

        new_records.append(record)

        # Update sets immediately so duplicates inside the current
        # review file are also detected.
        existing_ids.add(candidate_id)
        existing_pairs.add(pair)

        kept += 1

    # Append only genuinely new records.
    with OUTPUT_PATH.open("a", encoding="utf-8") as out:
        for record in new_records:
            out.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    final_size = len(existing_records) + kept

    print("SFT DATASET MERGE: PASS")
    print(f"Input rows: {len(rows)}")
    print(f"Added: {kept}")
    print(f"Edited: {edited}")
    print(f"Rejected: {rejected}")
    print(f"Duplicates skipped: {duplicates}")
    print(f"Total dataset size: {final_size}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()