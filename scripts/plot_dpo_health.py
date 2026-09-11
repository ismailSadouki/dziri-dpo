from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


REQUIRED_FIELDS = {
    "loss",
    "reward_accuracy",
    "margin",
    "chosen_kl_proxy",
    "rejected_kl_proxy",
    "policy_chosen_logp",
    "policy_rejected_logp",
    "reference_chosen_logp",
    "reference_rejected_logp",
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
        raise ValueError(f"No metric rows found in {path}")

    fields = set(rows[0])
    missing = REQUIRED_FIELDS - fields

    if missing:
        raise ValueError(
            "Metrics file is missing required fields:\n"
            + "\n".join(f"  - {field}" for field in sorted(missing))
        )

    return rows


def save_plot(
    steps,
    series,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    plt.figure(figsize=(9, 5))

    for values, label in series:
        plt.plot(steps, values, label=label)

    plt.xlabel("Training step")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)

    if len(series) > 1:
        plt.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot DPO training health metrics."
    )
    parser.add_argument(
        "--metrics",
        type=Path,
        default=Path("outputs/dpo_english_m4_2/metrics.jsonl"),
        help="Path to metrics.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for generated plots. "
        "Defaults to <metrics parent>/health",
    )

    args = parser.parse_args()

    rows = load_metrics(args.metrics)

    output_dir = (
        args.output_dir
        if args.output_dir is not None
        else args.metrics.parent / "health"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    steps = [row["step"] for row in rows]

    # 1. Loss
    save_plot(
        steps,
        [
            ([row["loss"] for row in rows], "DPO loss"),
        ],
        title="DPO training loss",
        ylabel="Loss",
        output_path=output_dir / "loss.png",
    )

    # 2. Reward accuracy
    save_plot(
        steps,
        [
            (
                [row["reward_accuracy"] for row in rows],
                "Reward accuracy",
            ),
        ],
        title="DPO reward accuracy",
        ylabel="Reward accuracy",
        output_path=output_dir / "reward_accuracy.png",
    )

    # 3. Margin
    save_plot(
        steps,
        [
            ([row["margin"] for row in rows], "Margin"),
        ],
        title="DPO preference margin",
        ylabel="Margin",
        output_path=output_dir / "margin.png",
    )

    # 4. KL proxy
    save_plot(
        steps,
        [
            (
                [row["chosen_kl_proxy"] for row in rows],
                "Chosen KL proxy",
            ),
            (
                [row["rejected_kl_proxy"] for row in rows],
                "Rejected KL proxy",
            ),
        ],
        title="Policy/reference log-ratio proxies",
        ylabel="Sequence-level KL proxy",
        output_path=output_dir / "kl_proxy.png",
    )

    # 5. Policy/reference log probabilities
    save_plot(
        steps,
        [
            (
                [row["policy_chosen_logp"] for row in rows],
                "Policy chosen",
            ),
            (
                [row["policy_rejected_logp"] for row in rows],
                "Policy rejected",
            ),
            (
                [row["reference_chosen_logp"] for row in rows],
                "Reference chosen",
            ),
            (
                [row["reference_rejected_logp"] for row in rows],
                "Reference rejected",
            ),
        ],
        title="Policy and reference sequence log probabilities",
        ylabel="Sequence log probability",
        output_path=output_dir / "policy_logps.png",
    )

    # 6. Response length
    save_plot(
        steps,
        [
            (
                [row["chosen_length"] for row in rows],
                "Chosen response length",
            ),
            (
                [row["rejected_length"] for row in rows],
                "Rejected response length",
            ),
        ],
        title="Response length during DPO training",
        ylabel="Tokens",
        output_path=output_dir / "response_length.png",
    )

    print(f"Loaded {len(rows)} metric rows.")
    print(f"Saved plots to: {output_dir}")

    for path in sorted(output_dir.glob("*.png")):
        print(f"  {path}")


if __name__ == "__main__":
    main()