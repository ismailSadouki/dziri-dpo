from __future__ import annotations

import json
from pathlib import Path


BETAS = ("0.05", "0.1", "0.3", "0.5")
ROOT = Path("outputs")
OUT = Path("reports/darija_alignment")


def load_summary(beta: str) -> dict:
    path = ROOT / f"dpo_beta_{beta}" / "run_summary.json"

    if not path.exists():
        raise FileNotFoundError(path)

    return json.loads(path.read_text(encoding="utf-8"))


def extract(beta: str, summary: dict) -> dict:
    beta_value = float(beta)

    eval_history = summary["eval_history"]

    rows = []

    for row in eval_history:
        chosen_reward = row["eval_rewards/chosen"]
        rejected_reward = row["eval_rewards/rejected"]

        rows.append(
            {
                "beta": beta_value,
                "step": row["step"],
                "eval_loss": row["eval_loss"],
                "reward_accuracy": row["eval_rewards/accuracies"],
                "margin": row["eval_rewards/margins"],
                "chosen_reward": chosen_reward,
                "rejected_reward": rejected_reward,

                # DPO reward:
                # beta * (policy_logp - reference_logp)
                #
                # Therefore reward / beta is the
                # sequence-level policy/reference log-ratio.
                "chosen_kl_proxy": chosen_reward / beta_value,
                "rejected_kl_proxy": rejected_reward / beta_value,

                "policy_chosen_logp": row["eval_logps/chosen"],
                "policy_rejected_logp": row["eval_logps/rejected"],

                "eval_entropy": row["eval_entropy"],
                "eval_num_tokens": row["eval_num_tokens"],
            }
        )

    return {
        "beta": beta_value,
        "model_name": summary["model_name"],
        "sft_checkpoint": summary["sft_checkpoint"],
        "eval_dataset": summary["eval_dataset"],
        "eval_rows": summary["eval_rows"],
        "rows": rows,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    all_results = {}

    for beta in BETAS:
        result = extract(beta, load_summary(beta))
        all_results[beta] = result

        path = OUT / f"beta_{beta}.json"
        path.write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )

        print(
            f"beta={beta}: "
            f"{len(result['rows'])} eval rows -> {path}"
        )

    combined = OUT / "beta_metrics.json"
    combined.write_text(
        json.dumps(all_results, indent=2),
        encoding="utf-8",
    )

    # Print final-step summary.
    print("\nFINAL EVAL METRICS")
    print("=" * 90)

    header = (
        f"{'beta':>6} "
        f"{'acc':>8} "
        f"{'margin':>10} "
        f"{'chosen Δlogp':>14} "
        f"{'rejected Δlogp':>16} "
        f"{'chosen logp':>14}"
    )
    print(header)
    print("-" * len(header))

    for beta in BETAS:
        row = all_results[beta]["rows"][-1]

        print(
            f"{float(beta):6.2f} "
            f"{row['reward_accuracy']:8.4f} "
            f"{row['margin']:10.4f} "
            f"{row['chosen_kl_proxy']:14.4f} "
            f"{row['rejected_kl_proxy']:16.4f} "
            f"{row['policy_chosen_logp']:14.3f}"
        )

    print(f"\nSaved combined metrics: {combined}")


if __name__ == "__main__":
    main()