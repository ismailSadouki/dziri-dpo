import json
from pathlib import Path

import matplotlib.pyplot as plt


BASE = Path("outputs")
REPORT_DIR = Path("reports/darija_alignment")
PLOT_DIR = REPORT_DIR / "plots"
PLOT_DIR.mkdir(parents=True, exist_ok=True)

BETAS = ["0.05", "0.1", "0.3", "0.5"]


def load_summary(beta):
    path = BASE / f"dpo_beta_{beta}" / "run_summary.json"

    if not path.exists():
        raise FileNotFoundError(path)

    return json.loads(path.read_text(encoding="utf-8"))


def get_eval_history(summary):
    history = summary.get("eval_history", [])

    rows = []

    for row in history:
        if "step" not in row:
            continue

        rows.append(row)

    return rows


def get_generation_summary():
    path = REPORT_DIR / "generations" / "generation_summary.json"

    if not path.exists():
        raise FileNotFoundError(path)

    return json.loads(path.read_text(encoding="utf-8"))


def savefig(name):
    path = PLOT_DIR / name

    plt.tight_layout()
    plt.savefig(
        path,
        dpi=180,
        bbox_inches="tight",
    )
    plt.close()

    print(f"Saved: {path}")


def final_beta_plot(values, ylabel, filename, title):
    x = [float(beta) for beta in BETAS]
    y = [values[beta] for beta in BETAS]

    plt.figure(figsize=(7, 5))

    plt.plot(
        x,
        y,
        marker="o",
    )

    plt.xlabel("β")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.25)

    savefig(filename)


def main():
    # ------------------------------------------------------------------
    # Load training summaries
    # ------------------------------------------------------------------
    summaries = {
        beta: load_summary(beta)
        for beta in BETAS
    }

    eval_histories = {
        beta: get_eval_history(summaries[beta])
        for beta in BETAS
    }

    # ------------------------------------------------------------------
    # Inspect available metric names before plotting
    # ------------------------------------------------------------------
    print("\nAvailable evaluation metrics:")

    for beta in BETAS:
        keys = set()

        for row in eval_histories[beta]:
            keys.update(row.keys())

        print(f"β={beta}: {sorted(keys)}")

    # ------------------------------------------------------------------
    # Final evaluation values
    # ------------------------------------------------------------------
    final = {}

    for beta in BETAS:
        rows = eval_histories[beta]

        if not rows:
            raise RuntimeError(
                f"No eval history for beta={beta}"
            )

        final[beta] = rows[-1]

    print("\nFinal evaluation rows:")

    for beta in BETAS:
        print(f"β={beta}: {final[beta]}")

    # ------------------------------------------------------------------
    # Extract final metrics
    #
    # DPO reward:
    #
    # reward =
    #     beta * (
    #         log pi_policy(y|x)
    #         - log pi_reference(y|x)
    #     )
    #
    # Therefore:
    #
    # reward / beta =
    #     log pi_policy(y|x)
    #     - log pi_reference(y|x)
    #
    # This is a sequence-level reference-relative log-ratio proxy,
    # NOT an exact token-level KL divergence.
    # ------------------------------------------------------------------
    reward_accuracy = {}
    margin = {}
    eval_loss = {}
    chosen_reward = {}
    chosen_kl_proxy = {}
    chosen_logp = {}

    for beta in BETAS:
        row = final[beta]

        reward_accuracy[beta] = row.get(
            "eval_rewards/accuracies"
        )

        margin[beta] = row.get(
            "eval_rewards/margins"
        )

        eval_loss[beta] = row.get(
            "eval_loss"
        )

        chosen_reward[beta] = row.get(
            "eval_rewards/chosen"
        )

        if chosen_reward[beta] is not None:
            chosen_kl_proxy[beta] = (
                chosen_reward[beta] / float(beta)
            )
        else:
            chosen_kl_proxy[beta] = None

        # Actual policy log-probability of the chosen response.
        #
        # Do NOT fall back to reward here. They measure different things.
        chosen_logp[beta] = row.get(
            "eval_logps/chosen"
        )

    # ------------------------------------------------------------------
    # Validate required metrics
    # ------------------------------------------------------------------
    for beta in BETAS:
        required = {
            "reward_accuracy": reward_accuracy[beta],
            "margin": margin[beta],
            "eval_loss": eval_loss[beta],
            "chosen_reward": chosen_reward[beta],
            "chosen_kl_proxy": chosen_kl_proxy[beta],
            "chosen_logp": chosen_logp[beta],
        }

        missing = [
            name
            for name, value in required.items()
            if value is None
        ]

        if missing:
            raise RuntimeError(
                f"Missing final metrics for beta={beta}: "
                f"{missing}"
            )

    # ------------------------------------------------------------------
    # Response length
    # ------------------------------------------------------------------
    generation_summary = get_generation_summary()

    response_length = {}

    for beta in BETAS:
        key = f"beta_{beta}"

        if key not in generation_summary:
            raise KeyError(
                f"Missing generation summary for {key}"
            )

        response_length[beta] = generation_summary[key][
            "mean_generated_tokens"
        ]

    # ------------------------------------------------------------------
    # Final-value plots
    # ------------------------------------------------------------------
    final_beta_plot(
        reward_accuracy,
        "Reward accuracy",
        "beta_vs_reward_accuracy.png",
        "β vs reward accuracy",
    )

    final_beta_plot(
        chosen_kl_proxy,
        "Chosen sequence log-ratio proxy",
        "beta_vs_kl_proxy.png",
        "β vs reference-relative log-ratio proxy",
    )

    final_beta_plot(
        response_length,
        "Mean generated tokens",
        "beta_vs_response_length.png",
        "β vs response length",
    )

    final_beta_plot(
        margin,
        "Evaluation margin",
        "beta_vs_eval_margin.png",
        "β vs evaluation margin",
    )

    final_beta_plot(
        chosen_logp,
        "Evaluation logps/chosen",
        "beta_vs_logps_chosen.png",
        "β vs evaluation logps/chosen",
    )

    final_beta_plot(
        eval_loss,
        "Evaluation loss",
        "beta_vs_eval_loss.png",
        "β vs evaluation loss",
    )

    # ------------------------------------------------------------------
    # Combined final comparison
    # ------------------------------------------------------------------
    x = [float(beta) for beta in BETAS]

    fig, axes = plt.subplots(
        2,
        3,
        figsize=(15, 9),
    )

    plots = [
        (
            axes[0, 0],
            reward_accuracy,
            "Reward accuracy",
        ),
        (
            axes[0, 1],
            chosen_kl_proxy,
            "Chosen log-ratio proxy",
        ),
        (
            axes[0, 2],
            response_length,
            "Mean response tokens",
        ),
        (
            axes[1, 0],
            margin,
            "Eval margin",
        ),
        (
            axes[1, 1],
            chosen_logp,
            "Eval logps/chosen",
        ),
        (
            axes[1, 2],
            eval_loss,
            "Eval loss",
        ),
    ]

    for ax, values, ylabel in plots:
        ax.plot(
            x,
            [values[beta] for beta in BETAS],
            marker="o",
        )

        ax.set_xlabel("β")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.25)

    fig.suptitle(
        "B3.2 — Final β Sweep Health Summary",
        fontsize=16,
    )

    fig.tight_layout()

    fig.savefig(
        PLOT_DIR / "beta_sweep_final_summary.png",
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(
        f"Saved: "
        f"{PLOT_DIR / 'beta_sweep_final_summary.png'}"
    )

    # ------------------------------------------------------------------
    # Training-step curves
    # ------------------------------------------------------------------
    metric_specs = [
        (
            "eval_rewards/margins",
            "Evaluation margin",
            "training_margin_by_beta.png",
        ),
        (
            "eval_rewards/chosen",
            "Chosen reward",
            "training_chosen_reward_by_beta.png",
        ),
        (
            "eval_logps/chosen",
            "Policy logp/chosen",
            "training_logps_chosen_by_beta.png",
        ),
    ]

    for metric, ylabel, filename in metric_specs:
        plt.figure(figsize=(8, 5))

        plotted = False

        for beta in BETAS:
            rows = eval_histories[beta]

            steps = []
            values = []

            for row in rows:
                value = row.get(metric)

                if value is None:
                    continue

                steps.append(row["step"])
                values.append(value)

            if values:
                plt.plot(
                    steps,
                    values,
                    marker="o",
                    label=f"β={beta}",
                )

                plotted = True

        if not plotted:
            plt.close()

            print(
                f"Skipped {filename}: "
                f"metric '{metric}' not present."
            )

            continue

        plt.xlabel("Training step")
        plt.ylabel(ylabel)
        plt.title(f"{ylabel} over training")
        plt.legend()
        plt.grid(True, alpha=0.25)

        savefig(filename)

    # ------------------------------------------------------------------
    # Training-step reference-relative log-ratio proxy
    #
    # reward / beta
    # ------------------------------------------------------------------
    plt.figure(figsize=(8, 5))

    for beta in BETAS:
        rows = eval_histories[beta]

        steps = []
        values = []

        for row in rows:
            reward = row.get(
                "eval_rewards/chosen"
            )

            if reward is None:
                continue

            steps.append(row["step"])

            values.append(
                reward / float(beta)
            )

        if values:
            plt.plot(
                steps,
                values,
                marker="o",
                label=f"β={beta}",
            )

    plt.xlabel("Training step")
    plt.ylabel(
        "Chosen sequence log-ratio proxy"
    )
    plt.title(
        "Reference-relative log-ratio proxy over training"
    )
    plt.legend()
    plt.grid(True, alpha=0.25)

    savefig(
        "training_kl_proxy_by_beta.png"
    )

    # ------------------------------------------------------------------
    # Combined training health plot
    # ------------------------------------------------------------------
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(16, 5),
    )

    training_metrics = [
        (
            axes[0],
            "eval_rewards/margins",
            "Margin",
            False,
        ),
        (
            axes[1],
            "eval_rewards/chosen",
            "Chosen log-ratio proxy",
            True,
        ),
        (
            axes[2],
            "eval_logps/chosen",
            "logps/chosen",
            False,
        ),
    ]

    for ax, metric, ylabel, divide_beta in training_metrics:

        for beta in BETAS:
            steps = []
            values = []

            for row in eval_histories[beta]:
                value = row.get(metric)

                if value is None:
                    continue

                if divide_beta:
                    value = value / float(beta)

                steps.append(row["step"])
                values.append(value)

            if values:
                ax.plot(
                    steps,
                    values,
                    marker="o",
                    label=f"β={beta}",
                )

        ax.set_xlabel("Training step")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.25)

    axes[0].legend()

    fig.suptitle(
        "B3.2 — Training-Step DPO Health Curves",
        fontsize=16,
    )

    fig.tight_layout()

    fig.savefig(
        PLOT_DIR / "training_health_summary.png",
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(
        f"Saved: "
        f"{PLOT_DIR / 'training_health_summary.png'}"
    )

    # ------------------------------------------------------------------
    # Machine-readable summary
    # ------------------------------------------------------------------
    summary = {
        "beta": {
            beta: {
                "reward_accuracy": reward_accuracy[beta],
                "margin": margin[beta],
                "eval_loss": eval_loss[beta],
                "chosen_reward": chosen_reward[beta],
                "chosen_kl_proxy": chosen_kl_proxy[beta],
                "chosen_logp": chosen_logp[beta],
                "mean_generated_tokens": response_length[beta],
            }
            for beta in BETAS
        }
    }

    output = REPORT_DIR / "b3_2_plot_summary.json"

    output.write_text(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"Saved: {output}")


if __name__ == "__main__":
    main()