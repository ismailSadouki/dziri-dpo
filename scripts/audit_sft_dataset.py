import argparse
import json
import re
from collections import Counter
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


VALID_SCRIPTS = {"arabic", "arabizi", "mixed"}
VALID_REVIEW_DECISIONS = {"accept", "edit"}

NEAR_DUPLICATE_THRESHOLD = 0.85
SHORT_USER_CHARS = 10
SHORT_ASSISTANT_CHARS = 20
LONG_USER_CHARS = 500
LONG_ASSISTANT_CHARS = 1500


def load_dataset(path):
    records = []

    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Line {line_no}: invalid JSON: {exc}"
                )

            record["_line_no"] = line_no
            records.append(record)

    return records


def get_message(record, role):
    messages = record.get("messages")

    if not isinstance(messages, list):
        return ""

    for message in messages:
        if (
            isinstance(message, dict)
            and message.get("role") == role
        ):
            content = message.get("content")
            if isinstance(content, str):
                return content.strip()

    return ""


def normalize_text(text):
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def audit_structure(records):
    issues = []

    required_fields = {
        "id",
        "messages",
        "category",
        "script",
        "source",
        "license",
        "metadata",
    }

    ids = set()

    for record in records:
        line_no = record["_line_no"]
        record_id = record.get("id")

        missing = required_fields - record.keys()

        if missing:
            issues.append(
                f"Line {line_no}: missing fields: {sorted(missing)}"
            )

        if not record_id:
            issues.append(
                f"Line {line_no}: missing/empty id"
            )
        elif record_id in ids:
            issues.append(
                f"Line {line_no}: duplicate id: {record_id}"
            )

        ids.add(record_id)

        messages = record.get("messages")

        if not isinstance(messages, list):
            issues.append(
                f"Line {line_no}: messages is not a list"
            )
            continue

        if len(messages) != 2:
            issues.append(
                f"Line {line_no}: expected 2 messages, "
                f"got {len(messages)}"
            )
            continue

        if messages[0].get("role") != "user":
            issues.append(
                f"Line {line_no}: first message is not user"
            )

        if messages[1].get("role") != "assistant":
            issues.append(
                f"Line {line_no}: second message is not assistant"
            )

        for message in messages:
            content = message.get("content")

            if not isinstance(content, str) or not content.strip():
                issues.append(
                    f"Line {line_no}: empty message content"
                )

        category = record.get("category")

        if not isinstance(category, str) or not category.strip():
            issues.append(
                f"Line {line_no}: invalid category"
            )

        script = record.get("script")

        if script not in VALID_SCRIPTS:
            issues.append(
                f"Line {line_no}: invalid script: {script!r}"
            )

        metadata = record.get("metadata")

        if not isinstance(metadata, dict):
            issues.append(
                f"Line {line_no}: metadata is not an object"
            )
            continue

        if metadata.get("dialect") != "algerian_darija":
            issues.append(
                f"Line {line_no}: unexpected dialect metadata: "
                f"{metadata.get('dialect')!r}"
            )

        if metadata.get("human_review") is not True:
            issues.append(
                f"Line {line_no}: human_review is not True"
            )

        decision = metadata.get("review_decision")

        if decision not in VALID_REVIEW_DECISIONS:
            issues.append(
                f"Line {line_no}: invalid review_decision: "
                f"{decision!r}"
            )

    return issues


def audit_exact_duplicates(records):
    duplicate_pairs = []
    seen_pairs = {}

    for record in records:
        user = normalize_text(
            get_message(record, "user")
        )
        assistant = normalize_text(
            get_message(record, "assistant")
        )

        pair = (user, assistant)

        if pair in seen_pairs:
            duplicate_pairs.append(
                (
                    seen_pairs[pair],
                    record.get("id"),
                )
            )
        else:
            seen_pairs[pair] = record.get("id")

    return duplicate_pairs


def find_near_duplicates(records, field, threshold):
    texts = []

    for record in records:
        text = get_message(record, field)
        texts.append(normalize_text(text))

    if len(texts) < 2:
        return []

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
    )

    matrix = vectorizer.fit_transform(texts)
    similarities = cosine_similarity(matrix)

    matches = []

    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            score = similarities[i, j]

            if score >= threshold:
                matches.append(
                    (
                        records[i].get("id"),
                        records[j].get("id"),
                        float(score),
                    )
                )

    matches.sort(
        key=lambda x: x[2],
        reverse=True,
    )

    return matches


def audit_lengths(records):
    short_users = []
    short_assistants = []
    long_users = []
    long_assistants = []

    user_lengths = []
    assistant_lengths = []

    for record in records:
        record_id = record.get("id")

        user = get_message(record, "user")
        assistant = get_message(record, "assistant")

        user_len = len(user)
        assistant_len = len(assistant)

        user_lengths.append(user_len)
        assistant_lengths.append(assistant_len)

        if user_len < SHORT_USER_CHARS:
            short_users.append(
                (record_id, user_len, user)
            )

        if assistant_len < SHORT_ASSISTANT_CHARS:
            short_assistants.append(
                (record_id, assistant_len, assistant)
            )

        if user_len > LONG_USER_CHARS:
            long_users.append(
                (record_id, user_len)
            )

        if assistant_len > LONG_ASSISTANT_CHARS:
            long_assistants.append(
                (record_id, assistant_len)
            )

    return {
        "user_lengths": user_lengths,
        "assistant_lengths": assistant_lengths,
        "short_users": short_users,
        "short_assistants": short_assistants,
        "long_users": long_users,
        "long_assistants": long_assistants,
    }


def audit_repeated_responses(records):
    response_map = {}

    for record in records:
        response = normalize_text(
            get_message(record, "assistant")
        )

        if not response:
            continue

        response_map.setdefault(response, []).append(
            record.get("id")
        )

    repeated = []

    for response, ids in response_map.items():
        if len(ids) > 1:
            repeated.append(
                (ids, response)
            )

    repeated.sort(
        key=lambda x: len(x[0]),
        reverse=True,
    )

    return repeated


def print_distribution(records):
    categories = Counter(
        record.get("category")
        for record in records
    )

    scripts = Counter(
        record.get("script")
        for record in records
    )

    source = Counter(
        record.get("source")
        for record in records
    )

    print("\nCATEGORY DISTRIBUTION")
    print("-" * 40)

    for category, count in sorted(categories.items()):
        print(f"{category}: {count}")

    print("\nSCRIPT DISTRIBUTION")
    print("-" * 40)

    for script, count in sorted(scripts.items()):
        print(f"{script}: {count}")

    print("\nSOURCE DISTRIBUTION")
    print("-" * 40)

    for value, count in sorted(source.items()):
        print(f"{value}: {count}")


def print_length_summary(lengths):
    user_lengths = lengths["user_lengths"]
    assistant_lengths = lengths["assistant_lengths"]

    def summary(values):
        if not values:
            return {
                "min": 0,
                "max": 0,
                "avg": 0,
            }

        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
        }

    user_summary = summary(user_lengths)
    assistant_summary = summary(assistant_lengths)

    print("\nLENGTH SUMMARY")
    print("-" * 40)

    print(
        "User characters: "
        f"min={user_summary['min']}, "
        f"max={user_summary['max']}, "
        f"avg={user_summary['avg']:.1f}"
    )

    print(
        "Assistant characters: "
        f"min={assistant_summary['min']}, "
        f"max={assistant_summary['max']}, "
        f"avg={assistant_summary['avg']:.1f}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Audit SFT dataset quality without modifying it"
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Input SFT JSONL dataset",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=NEAR_DUPLICATE_THRESHOLD,
        help=(
            "Cosine similarity threshold for near-duplicate "
            "detection (default: 0.85)"
        ),
    )

    args = parser.parse_args()

    input_path = args.input

    if not input_path.exists():
        raise FileNotFoundError(input_path)

    if not 0 < args.threshold <= 1:
        raise ValueError(
            "--threshold must be between 0 and 1"
        )

    print("=" * 60)
    print("SFT DATASET AUDIT")
    print("=" * 60)

    print(f"Input: {input_path}")

    records = load_dataset(input_path)

    print(f"Rows: {len(records)}")

    if not records:
        raise ValueError("Dataset is empty")

    # ---------------------------------------------------------
    # Structural audit
    # ---------------------------------------------------------

    structure_issues = audit_structure(records)

    print("\nSTRUCTURE AUDIT")
    print("-" * 40)

    if structure_issues:
        print(f"ISSUES: {len(structure_issues)}")

        for issue in structure_issues:
            print(f"- {issue}")
    else:
        print("PASS")

    # ---------------------------------------------------------
    # Exact duplicates
    # ---------------------------------------------------------

    duplicate_pairs = audit_exact_duplicates(records)

    print("\nEXACT DUPLICATE AUDIT")
    print("-" * 40)

    if duplicate_pairs:
        print(
            f"FOUND: {len(duplicate_pairs)} duplicate pairs"
        )

        for first_id, duplicate_id in duplicate_pairs:
            print(
                f"- {first_id} <-> {duplicate_id}"
            )
    else:
        print("PASS: no duplicate user/assistant pairs")

    # ---------------------------------------------------------
    # Distributions
    # ---------------------------------------------------------

    print_distribution(records)

    # ---------------------------------------------------------
    # Length audit
    # ---------------------------------------------------------

    lengths = audit_lengths(records)

    print_length_summary(lengths)

    print("\nLENGTH WARNINGS")
    print("-" * 40)

    if lengths["short_users"]:
        print(
            f"Short user messages: "
            f"{len(lengths['short_users'])}"
        )

        for record_id, length, text in lengths[
            "short_users"
        ]:
            print(
                f"- {record_id}: {length} chars | {text!r}"
            )
    else:
        print("Short user messages: 0")

    if lengths["short_assistants"]:
        print(
            f"Short assistant messages: "
            f"{len(lengths['short_assistants'])}"
        )

        for record_id, length, text in lengths[
            "short_assistants"
        ]:
            print(
                f"- {record_id}: {length} chars | {text!r}"
            )
    else:
        print("Short assistant messages: 0")

    if lengths["long_users"]:
        print(
            f"Long user messages: "
            f"{len(lengths['long_users'])}"
        )

        for record_id, length in lengths[
            "long_users"
        ]:
            print(
                f"- {record_id}: {length} chars"
            )
    else:
        print("Long user messages: 0")

    if lengths["long_assistants"]:
        print(
            f"Long assistant messages: "
            f"{len(lengths['long_assistants'])}"
        )

        for record_id, length in lengths[
            "long_assistants"
        ]:
            print(
                f"- {record_id}: {length} chars"
            )
    else:
        print("Long assistant messages: 0")

    # ---------------------------------------------------------
    # Repeated responses
    # ---------------------------------------------------------

    repeated_responses = audit_repeated_responses(
        records
    )

    print("\nREPEATED RESPONSE AUDIT")
    print("-" * 40)

    if repeated_responses:
        print(
            f"Repeated responses: "
            f"{len(repeated_responses)}"
        )

        for ids, response in repeated_responses[:20]:
            print(
                f"- {ids}: {response!r}"
            )

        if len(repeated_responses) > 20:
            print(
                f"... and "
                f"{len(repeated_responses) - 20} more"
            )
    else:
        print("PASS: no repeated assistant responses")

    # ---------------------------------------------------------
    # Near-duplicate user prompts
    # ---------------------------------------------------------

    print("\nNEAR-DUPLICATE USER PROMPTS")
    print("-" * 40)

    user_near_duplicates = find_near_duplicates(
        records,
        "user",
        args.threshold,
    )

    if user_near_duplicates:
        print(
            f"FOUND: "
            f"{len(user_near_duplicates)} potential matches"
        )

        for id_a, id_b, score in user_near_duplicates[:30]:
            print(
                f"- {id_a} <-> {id_b}: "
                f"similarity={score:.3f}"
            )

        if len(user_near_duplicates) > 30:
            print(
                f"... and "
                f"{len(user_near_duplicates) - 30} more"
            )
    else:
        print("PASS: no near-duplicate user prompts")

    # ---------------------------------------------------------
    # Near-duplicate assistant responses
    # ---------------------------------------------------------

    print("\nNEAR-DUPLICATE ASSISTANT RESPONSES")
    print("-" * 40)

    assistant_near_duplicates = find_near_duplicates(
        records,
        "assistant",
        args.threshold,
    )

    if assistant_near_duplicates:
        print(
            f"FOUND: "
            f"{len(assistant_near_duplicates)} potential matches"
        )

        for id_a, id_b, score in (
            assistant_near_duplicates[:30]
        ):
            print(
                f"- {id_a} <-> {id_b}: "
                f"similarity={score:.3f}"
            )

        if len(assistant_near_duplicates) > 30:
            print(
                f"... and "
                f"{len(assistant_near_duplicates) - 30} more"
            )
    else:
        print("PASS: no near-duplicate assistant responses")

    # ---------------------------------------------------------
    # Final status
    # ---------------------------------------------------------

    critical_failures = (
        len(structure_issues)
        + len(duplicate_pairs)
    )

    print("\n" + "=" * 60)

    if critical_failures == 0:
        print("STRUCTURAL AUDIT: PASS")
    else:
        print(
            "STRUCTURAL AUDIT: FAIL "
            f"({critical_failures} critical issues)"
        )

    warnings = (
        len(lengths["short_users"])
        + len(lengths["short_assistants"])
        + len(lengths["long_users"])
        + len(lengths["long_assistants"])
        + len(user_near_duplicates)
        + len(assistant_near_duplicates)
        + len(repeated_responses)
    )

    print(f"Potential quality warnings: {warnings}")
    print("=" * 60)


if __name__ == "__main__":
    main()