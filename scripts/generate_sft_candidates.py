import argparse
import json
from pathlib import Path


REQUIRED_FIELDS = {
    "candidate_id",
    "messages",
    "category",
    "script",
    "generation_method",
    "generation_model",
}


def main():
    parser = argparse.ArgumentParser(
        description="Validate and normalize SFT candidate JSONL"
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Input candidate JSONL",
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output normalized JSONL",
    )

    args = parser.parse_args()

    input_path = args.input
    output_path = args.output

    if not input_path.exists():
        raise FileNotFoundError(input_path)

    candidates = []
    seen_ids = set()

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

            missing = REQUIRED_FIELDS - row.keys()

            if missing:
                raise ValueError(
                    f"Line {line_no}: missing fields: {sorted(missing)}"
                )

            candidate_id = row["candidate_id"]

            if candidate_id in seen_ids:
                raise ValueError(
                    f"Line {line_no}: duplicate candidate_id "
                    f"{candidate_id}"
                )

            seen_ids.add(candidate_id)

            messages = row["messages"]

            if not isinstance(messages, list) or len(messages) != 2:
                raise ValueError(
                    f"Line {line_no}: messages must contain "
                    f"exactly 2 messages"
                )

            if messages[0].get("role") != "user":
                raise ValueError(
                    f"Line {line_no}: first message must be user"
                )

            if messages[1].get("role") != "assistant":
                raise ValueError(
                    f"Line {line_no}: second message must be assistant"
                )

            for message in messages:
                content = message.get("content")

                if not isinstance(content, str) or not content.strip():
                    raise ValueError(
                        f"Line {line_no}: empty message content"
                    )

            candidates.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for row in candidates:
            f.write(
                json.dumps(
                    row,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print("CANDIDATE NORMALIZATION: PASS")
    print(f"Candidates: {len(candidates)}")
    print(f"Unique IDs: {len(seen_ids)}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()