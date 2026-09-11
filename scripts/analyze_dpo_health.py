from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_FIELDS = {
    "loss",
    "reward_accuracy",
    "margin",
    "chosen_reward",
    "rejected_reward",
    "chosen_kl_proxy",
    "rejected_kl_proxy",
    "chosen_length",
    "rejected_length",
    "step",
}


def load_metrics(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {path}")

    rows = [
        json.loads(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]

    if not rows:
        raise ValueError("No metric rows found.")

    missing = REQUIRED_FIELDS - set(rows[0])

    if missing:
        raise ValueError(
            "Missing required fields:\n"
            + "\n".join(f"  - {x}" for x in sorted(missing))
        )

    return rows


def mean(rows: list[dict], key: str) -> float:
    return sum(row[key] for row in rows) / len(rows)


def summarize_period(name: str, rows: list[dict]) -> None:
    print(f"\n{name.upper()}")
    print("-" * len(name))

    for key in [
        "loss",
        "reward_accuracy",
        "margin",
        "chosen_reward",
        "rejected_reward",
        "chosen_kl_proxy",
        "rejected_kl_proxy",
        "chosen_length",
        "rejected_length",
    ]:
        print(f"{key:24s}: {mean(rows, key):.6f}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze DPO training health metrics."
    )

    parser.add_argument(
        "--metrics",
        type=Path,
        default=Path(
            "outputs/dpo_english_m4_2/metrics.jsonl"
        ),
    )

    args = parser.parse_args()

    rows = load_metrics(args.metrics)

    n = len(rows)

    early_end = max(1, n // 3)
    middle_end = max(early_end + 1, 2 * n // 3)

    early = rows[:early_end]
    middle = rows[early_end:middle_end]
    late = rows[middle_end:]

    print(f"Rows: {n}")
    print(f"Steps: {rows[0]['step']} → {rows[-1]['step']}")

    # ---------------------------------------------------------
    # Initial / final
    # ---------------------------------------------------------

    first = rows[0]
    last = rows[-1]

    print("\nINITIAL → FINAL")
    print("----------------")

    for key in [
        "loss",
        "reward_accuracy",
        "margin",
        "chosen_reward",
        "rejected_reward",
        "chosen_kl_proxy",
        "rejected_kl_proxy",
        "chosen_length",
        "rejected_length",
    ]:
        print(
            f"{key:24s}: "
            f"{first[key]:.6f} → {last[key]:.6f}"
        )

    # ---------------------------------------------------------
    # Period summaries
    # ---------------------------------------------------------

    summarize_period("Early", early)
    summarize_period("Middle", middle)
    summarize_period("Late", late)

    # ---------------------------------------------------------
    # Extremes
    # ---------------------------------------------------------

    margins = [row["margin"] for row in rows]
    chosen_kl = [row["chosen_kl_proxy"] for row in rows]
    rejected_kl = [row["rejected_kl_proxy"] for row in rows]

    chosen_lengths = [row["chosen_length"] for row in rows]
    rejected_lengths = [row["rejected_length"] for row in rows]

    print("\nEXTREMES")
    print("--------")

    print(f"margin min:             {min(margins):.6f}")
    print(f"margin max:             {max(margins):.6f}")

    print(f"chosen KL proxy min:    {min(chosen_kl):.6f}")
    print(f"chosen KL proxy max:    {max(chosen_kl):.6f}")

    print(f"rejected KL proxy min:  {min(rejected_kl):.6f}")
    print(f"rejected KL proxy max:  {max(rejected_kl):.6f}")

    print(f"chosen length min:      {min(chosen_lengths):.2f}")
    print(f"chosen length max:      {max(chosen_lengths):.2f}")

    print(f"rejected length min:    {min(rejected_lengths):.2f}")
    print(f"rejected length max:    {max(rejected_lengths):.2f}")

    # ---------------------------------------------------------
    # Preference diagnostics
    # ---------------------------------------------------------

    negative_margin_steps = sum(
        row["margin"] < 0
        for row in rows
    )

    reward_inversion_steps = sum(
        row["chosen_reward"] < row["rejected_reward"]
        for row in rows
    )

    zero_margin_steps = sum(
        row["margin"] == 0
        for row in rows
    )

    print("\nPREFERENCE DIAGNOSTICS")
    print("----------------------")

    print(
        f"negative-margin steps: "
        f"{negative_margin_steps}/{n}"
    )

    print(
        f"chosen-reward < rejected-reward: "
        f"{reward_inversion_steps}/{n}"
    )

    print(
        f"zero-margin steps: "
        f"{zero_margin_steps}/{n}"
    )

    # ---------------------------------------------------------
    # Length drift
    # ---------------------------------------------------------

    chosen_length_change = (
        last["chosen_length"]
        - first["chosen_length"]
    )

    rejected_length_change = (
        last["rejected_length"]
        - first["rejected_length"]
    )

    print("\nLENGTH DRIFT")
    print("------------")

    print(
        f"chosen:   "
        f"{first['chosen_length']:.2f} → "
        f"{last['chosen_length']:.2f} "
        f"({chosen_length_change:+.2f})"
    )

    print(
        f"rejected: "
        f"{first['rejected_length']:.2f} → "
        f"{last['rejected_length']:.2f} "
        f"({rejected_length_change:+.2f})"
    )


if __name__ == "__main__":
    main()