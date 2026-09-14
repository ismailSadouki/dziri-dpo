import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def load_jsonl(path):
    rows = []

    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    return rows


def load_review(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def char_len(text):
    return len(text.strip())


def word_len(text):
    return len(text.split())


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--candidates",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--review",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    candidates = load_jsonl(args.candidates)
    review = load_review(args.review)

    candidate_by_id = {
        row["id"]: row
        for row in candidates
    }

    total = 0
    valid = 0
    ties = 0
    longer_correct = 0

    chosen_lengths = []
    rejected_lengths = []

    print("PREFERENCE CONFOUND ANALYSIS")
    print("=" * 40)

    for row in review:
        label = row["preference_label"].strip()

        if not label:
            continue

        total += 1

        candidate = candidate_by_id[row["id"]]

        chosen = candidate["chosen"]
        rejected = candidate["rejected"]

        chosen_len = word_len(chosen)
        rejected_len = word_len(rejected)

        chosen_lengths.append(chosen_len)
        rejected_lengths.append(rejected_len)

        if label == "tie":
            ties += 1
            continue

        valid += 1

        if chosen_len > rejected_len:
            heuristic = "chosen"
        elif rejected_len > chosen_len:
            heuristic = "rejected"
        else:
            heuristic = "equal"

        if heuristic == label:
            longer_correct += 1

    print(f"Reviewed rows: {total}")
    print(f"Non-tie rows: {valid}")
    print(f"Ties: {ties}")

    if valid:
        accuracy = longer_correct / valid
        print(
            f"Longer-response heuristic accuracy: "
            f"{accuracy:.3f}"
        )

    if chosen_lengths:
        print()
        print("Length statistics (words)")
        print("-" * 40)
        print(
            f"Chosen   mean: "
            f"{sum(chosen_lengths) / len(chosen_lengths):.2f}"
        )
        print(
            f"Rejected mean: "
            f"{sum(rejected_lengths) / len(rejected_lengths):.2f}"
        )

        diffs = [
            c - r
            for c, r in zip(
                chosen_lengths,
                rejected_lengths,
            )
        ]

        print(
            f"Mean chosen-rejected difference: "
            f"{sum(diffs) / len(diffs):.2f}"
        )

        print(
            f"Chosen longer: "
            f"{sum(d > 0 for d in diffs)}"
        )
        print(
            f"Rejected longer: "
            f"{sum(d < 0 for d in diffs)}"
        )
        print(
            f"Equal length: "
            f"{sum(d == 0 for d in diffs)}"
        )

    print("\nCategory distribution")
    print("-" * 40)

    categories = Counter(
        row["category"]
        for row in candidates
    )

    for category, count in sorted(categories.items()):
        print(f"{category}: {count}")


if __name__ == "__main__":
    main()