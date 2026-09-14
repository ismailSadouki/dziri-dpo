import argparse
import json
from pathlib import Path


REQUIRED_FIELDS = {
    "id",
    "prompt",
    "chosen",
    "rejected",
    "source",
    "generation_method",
    "category",
    "script",
    "metadata",
}

VALID_SCRIPTS = {"arabic", "arabizi", "mixed"}

VALID_PREFERENCE_REASONS = {
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
    records = []

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

            records.append((line_no, row))

    return records


def validate_candidate(line_no, row):
    missing = REQUIRED_FIELDS - row.keys()

    if missing:
        raise ValueError(
            f"Line {line_no}: missing fields: "
            f"{sorted(missing)}"
        )

    for field in [
        "id",
        "prompt",
        "chosen",
        "rejected",
        "source",
        "generation_method",
        "category",
        "script",
    ]:
        if (
            not isinstance(row[field], str)
            or not row[field].strip()
        ):
            raise ValueError(
                f"Line {line_no}: empty/invalid field: {field}"
            )

    if row["script"] not in VALID_SCRIPTS:
        raise ValueError(
            f"Line {line_no}: invalid script: "
            f"{row['script']!r}"
        )

    prompt = row["prompt"].strip()
    chosen = row["chosen"].strip()
    rejected = row["rejected"].strip()

    if not chosen:
        raise ValueError(
            f"Line {line_no}: chosen response is empty"
        )

    if not rejected:
        raise ValueError(
            f"Line {line_no}: rejected response is empty"
        )

    if chosen == rejected:
        raise ValueError(
            f"Line {line_no}: chosen and rejected are identical"
        )

    metadata = row["metadata"]

    if not isinstance(metadata, dict):
        raise ValueError(
            f"Line {line_no}: metadata must be an object"
        )

    dialect = metadata.get("dialect")

    if dialect != "algerian_darija":
        raise ValueError(
            f"Line {line_no}: metadata.dialect must be "
            f"'algerian_darija', got {dialect!r}"
        )

    preference_reason = metadata.get(
        "preference_reason"
    )

    if preference_reason not in VALID_PREFERENCE_REASONS:
        raise ValueError(
            f"Line {line_no}: invalid preference_reason: "
            f"{preference_reason!r}"
        )

    rejected_failure_mode = metadata.get(
        "rejected_failure_mode"
    )

    if (
        not isinstance(rejected_failure_mode, str)
        or not rejected_failure_mode.strip()
    ):
        raise ValueError(
            f"Line {line_no}: missing rejected_failure_mode"
        )

    # Prompt must not be empty or accidentally identical
    # to either response.
    if prompt == chosen:
        raise ValueError(
            f"Line {line_no}: prompt identical to chosen"
        )

    if prompt == rejected:
        raise ValueError(
            f"Line {line_no}: prompt identical to rejected"
        )


def normalize_candidate(row):
    metadata = dict(row["metadata"])

    metadata["human_review"] = False
    metadata.setdefault(
        "quality_status",
        "candidate",
    )

    return {
        "id": row["id"].strip(),
        "prompt": row["prompt"].strip(),
        "chosen": row["chosen"].strip(),
        "rejected": row["rejected"].strip(),
        "source": row["source"].strip(),
        "generation_method": row[
            "generation_method"
        ].strip(),
        "category": row["category"].strip(),
        "script": row["script"].strip(),
        "metadata": metadata,
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Validate and normalize preference "
            "candidate pairs"
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Raw preference candidate JSONL",
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Normalized preference candidate JSONL",
    )

    args = parser.parse_args()

    input_path = args.input
    output_path = args.output

    if not input_path.exists():
        raise FileNotFoundError(input_path)

    records = load_jsonl(input_path)

    seen_ids = set()
    seen_pairs = set()
    candidates = []

    for line_no, row in records:
        validate_candidate(line_no, row)

        candidate_id = row["id"].strip()

        if candidate_id in seen_ids:
            raise ValueError(
                f"Line {line_no}: duplicate id: "
                f"{candidate_id}"
            )

        seen_ids.add(candidate_id)

        pair = (
            row["prompt"].strip(),
            row["chosen"].strip(),
            row["rejected"].strip(),
        )

        if pair in seen_pairs:
            raise ValueError(
                f"Line {line_no}: duplicate preference pair: "
                f"{candidate_id}"
            )

        seen_pairs.add(pair)

        candidates.append(
            normalize_candidate(row)
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        for row in candidates:
            f.write(
                json.dumps(
                    row,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print("PREFERENCE CANDIDATE VALIDATION: PASS")
    print(f"Candidates: {len(candidates)}")
    print(f"Unique IDs: {len(seen_ids)}")
    print(f"Unique preference triples: {len(seen_pairs)}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()