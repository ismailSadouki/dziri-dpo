import argparse
import json
from collections import Counter
from pathlib import Path


VALID_SCRIPTS = {"arabic", "arabizi", "mixed"}

VALID_REASONS = {
    "instruction_adherence",
    "factual_correctness",
    "dialect_authenticity",
    "fluency",
    "safety",
    "cultural_appropriateness",
    "helpfulness",
    "conciseness",
}


def load_jsonl(path):
    rows = []

    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue

            row = json.loads(line)
            rows.append((line_no, row))

    return rows


def validate(rows):
    errors = []
    ids = set()
    pairs = set()
    categories = Counter()
    scripts = Counter()

    for line_no, row in rows:
        required = [
            "id",
            "prompt",
            "chosen",
            "rejected",
            "source",
            "generation_method",
            "category",
            "script",
            "metadata",
        ]

        for field in required:
            if field not in row:
                errors.append(
                    f"Line {line_no}: missing field {field}"
                )

        if any(field not in row for field in required):
            continue

        row_id = row["id"]
        prompt = row["prompt"].strip()
        chosen = row["chosen"].strip()
        rejected = row["rejected"].strip()

        if row_id in ids:
            errors.append(
                f"Line {line_no}: duplicate id {row_id}"
            )
        ids.add(row_id)

        pair = (prompt, chosen, rejected)

        if pair in pairs:
            errors.append(
                f"Line {line_no}: duplicate preference pair"
            )
        pairs.add(pair)

        if not prompt:
            errors.append(
                f"Line {line_no}: empty prompt"
            )

        if not chosen:
            errors.append(
                f"Line {line_no}: empty chosen"
            )

        if not rejected:
            errors.append(
                f"Line {line_no}: empty rejected"
            )

        if chosen == rejected:
            errors.append(
                f"Line {line_no}: chosen == rejected"
            )

        if prompt == chosen:
            errors.append(
                f"Line {line_no}: prompt == chosen"
            )

        if prompt == rejected:
            errors.append(
                f"Line {line_no}: prompt == rejected"
            )

        script = row["script"]

        if script not in VALID_SCRIPTS:
            errors.append(
                f"Line {line_no}: invalid script {script}"
            )

        categories[row["category"]] += 1
        scripts[script] += 1

        metadata = row["metadata"]

        if not isinstance(metadata, dict):
            errors.append(
                f"Line {line_no}: metadata is not an object"
            )
            continue

        if metadata.get("dialect") != "algerian_darija":
            errors.append(
                f"Line {line_no}: invalid dialect metadata"
            )

        reason = metadata.get("preference_reason")

        if reason not in VALID_REASONS:
            errors.append(
                f"Line {line_no}: invalid preference_reason "
                f"{reason!r}"
            )

        if not metadata.get("rejected_failure_mode"):
            errors.append(
                f"Line {line_no}: missing rejected_failure_mode"
            )

    return errors, ids, pairs, categories, scripts


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    rows = load_jsonl(args.input)

    errors, ids, pairs, categories, scripts = validate(rows)

    print("PREFERENCE DATA VALIDATION")
    print(f"Rows: {len(rows)}")
    print(f"Unique IDs: {len(ids)}")
    print(f"Unique preference triples: {len(pairs)}")
    print(f"Categories: {dict(categories)}")
    print(f"Scripts: {dict(scripts)}")

    if errors:
        print(f"\nFAIL: {len(errors)} issue(s)")
        for error in errors:
            print("-", error)
        raise SystemExit(1)

    print("\nPASS")


if __name__ == "__main__":
    main()