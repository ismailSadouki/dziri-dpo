import json
import sys
from pathlib import Path

DATA_PATH = Path("data/instruction_dataset.jsonl")

VALID_CATEGORIES = {
    "education",
    "general_qa",
    "reasoning",
    "daily_life",
    "algerian_culture",
    "commerce",
    "translation",
    "code_switching",
    "technical",
    "safety",
    "humor",
}

VALID_SCRIPTS = {"arabic", "arabizi", "mixed"}

REQUIRED_FIELDS = {
    "id",
    "messages",
    "category",
    "script",
    "source",
    "license",
    "metadata",
}

MAX_CONTENT_CHARS = 5000


def fail(errors):
    print("SFT DATA VALIDATION: FAIL")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)


def main():
    if not DATA_PATH.exists():
        fail([f"File not found: {DATA_PATH}"])

    errors = []
    rows = []
    seen_ids = set()
    seen_pairs = set()

    with DATA_PATH.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(
                    f"line {line_no}: invalid JSON ({exc.msg})"
                )
                continue

            rows.append(row)

            missing = REQUIRED_FIELDS - row.keys()
            if missing:
                errors.append(
                    f"line {line_no}: missing fields: {sorted(missing)}"
                )
                continue

            row_id = row["id"]

            if not isinstance(row_id, str) or not row_id.strip():
                errors.append(
                    f"line {line_no}: invalid id"
                )
            elif row_id in seen_ids:
                errors.append(
                    f"line {line_no}: duplicate id: {row_id}"
                )
            else:
                seen_ids.add(row_id)

            messages = row["messages"]

            if not isinstance(messages, list) or len(messages) != 2:
                errors.append(
                    f"line {line_no}: messages must contain exactly "
                    f"2 messages"
                )
                continue

            expected_roles = ["user", "assistant"]

            for i, (message, expected_role) in enumerate(
                zip(messages, expected_roles)
            ):
                if not isinstance(message, dict):
                    errors.append(
                        f"line {line_no}: message {i} is not an object"
                    )
                    continue

                if message.get("role") != expected_role:
                    errors.append(
                        f"line {line_no}: message {i} must have "
                        f"role='{expected_role}'"
                    )

                content = message.get("content")

                if not isinstance(content, str) or not content.strip():
                    errors.append(
                        f"line {line_no}: message {i} has empty content"
                    )
                elif len(content) > MAX_CONTENT_CHARS:
                    errors.append(
                        f"line {line_no}: message {i} exceeds "
                        f"{MAX_CONTENT_CHARS} characters"
                    )

            category = row["category"]
            if category not in VALID_CATEGORIES:
                errors.append(
                    f"line {line_no}: invalid category: {category}"
                )

            script = row["script"]
            if script not in VALID_SCRIPTS:
                errors.append(
                    f"line {line_no}: invalid script: {script}"
                )

            if not isinstance(row["source"], str) or not row["source"].strip():
                errors.append(
                    f"line {line_no}: source must be non-empty"
                )

            if not isinstance(row["license"], str) or not row["license"].strip():
                errors.append(
                    f"line {line_no}: license must be non-empty"
                )

            metadata = row["metadata"]

            if not isinstance(metadata, dict):
                errors.append(
                    f"line {line_no}: metadata must be an object"
                )
                continue

            for field in [
                "dialect",
                "code_switching",
                "quality_status",
            ]:
                if field not in metadata:
                    errors.append(
                        f"line {line_no}: metadata missing '{field}'"
                    )

            if metadata.get("dialect") != "algerian_darija":
                errors.append(
                    f"line {line_no}: dialect must be "
                    f"'algerian_darija'"
                )

            if len(messages) == 2:
                pair = (
                    messages[0].get("content", "").strip(),
                    messages[1].get("content", "").strip(),
                )

                if pair in seen_pairs:
                    errors.append(
                        f"line {line_no}: duplicate user/assistant pair"
                    )
                else:
                    seen_pairs.add(pair)

    if errors:
        fail(errors)

    print("SFT DATA VALIDATION: PASS")
    print(f"Rows: {len(rows)}")
    print(f"Unique IDs: {len(seen_ids)}")
    print(f"Unique pairs: {len(seen_pairs)}")

    categories = {}
    scripts = {}

    for row in rows:
        categories[row["category"]] = categories.get(
            row["category"], 0
        ) + 1

        scripts[row["script"]] = scripts.get(
            row["script"], 0
        ) + 1

    print("Categories:", categories)
    print("Scripts:", scripts)


if __name__ == "__main__":
    main()