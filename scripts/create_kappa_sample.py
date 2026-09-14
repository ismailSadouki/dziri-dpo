import argparse
import csv
import random
from collections import Counter, defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Create balanced 100-pair double-annotation sample"
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

    parser.add_argument(
        "--per-category",
        type=int,
        default=9,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    args = parser.parse_args()

    with args.input.open(
        encoding="utf-8",
        newline="",
    ) as f:
        rows = list(csv.DictReader(f))

    # Only use pairs that received a human preference label.
    rows = [
        row
        for row in rows
        if row["preference_label"].strip()
        in {"chosen", "rejected", "tie"}
    ]

    if len(rows) < 100:
        raise ValueError(
            f"Only {len(rows)} reviewed pairs; "
            "need at least 100."
        )

    by_category = defaultdict(list)

    for row in rows:
        by_category[row["category"]].append(row)

    categories = sorted(by_category)

    if len(categories) != 11:
        raise ValueError(
            f"Expected 11 categories, found {len(categories)}"
        )

    rng = random.Random(args.seed)

    selected = []

    # 9 from each of 11 categories = 99.
    for category in categories:
        candidates = by_category[category]

        if len(candidates) < args.per_category:
            raise ValueError(
                f"{category}: only {len(candidates)} "
                f"reviewed pairs"
            )

        selected.extend(
            rng.sample(
                candidates,
                args.per_category,
            )
        )

    # Add one extra pair.
    selected_ids = {
        row["id"]
        for row in selected
    }

    remaining = [
        row
        for row in rows
        if row["id"] not in selected_ids
    ]

    selected.append(rng.choice(remaining))

    rng.shuffle(selected)

    fields = [
        "id",
        "category",
        "script",
        "prompt",
        "chosen",
        "rejected",
        "annotator_a_label",
        "annotator_a_reason",
        "annotator_a_notes",
        "annotator_b_label",
        "annotator_b_reason",
        "annotator_b_notes",
    ]

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
            fieldnames=fields,
        )

        writer.writeheader()

        for row in selected:
            writer.writerow({
                "id": row["id"],
                "category": row["category"],
                "script": row["script"],
                "prompt": row["prompt"],
                "chosen": row["chosen"],
                "rejected": row["rejected"],
                "annotator_a_label": "",
                "annotator_a_reason": "",
                "annotator_a_notes": "",
                "annotator_b_label": "",
                "annotator_b_reason": "",
                "annotator_b_notes": "",
            })

    counts = Counter(
        row["category"]
        for row in selected
    )

    print("KAPPA SAMPLE CREATED")
    print(f"Reviewed source pairs: {len(rows)}")
    print(f"Sample size: {len(selected)}")
    print()
    print("Category distribution:")

    for category in categories:
        print(
            f"  {category}: {counts[category]}"
        )


if __name__ == "__main__":
    main()