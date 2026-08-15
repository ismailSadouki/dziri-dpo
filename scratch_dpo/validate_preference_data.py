import json
from dataclasses import dataclass
from pathlib import Path
import argparse
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from typing import List, Dict, Any,Union
import statistics


import random


@dataclass
class ValidationResult:
    valid: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]

REQUIRED_FIELD = {
    "id",
    "prompt",
    "chosen",
    "rejected",
    "source",
    "split",
    "metadata",
}


def load_raw_preferences(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Load raw preference examples from JSONL.

    Each line must contain one JSON object.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(path)

    rows = []

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue

        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON at line {line_number}: {exc}"
            ) from exc

        rows.append(row)

    return rows


def validate_preference_data(
        rows: List[Dict[str, Any]]
) -> ValidationResult:
    """
    Validate canonical preference examples.

    Invalid examples are returned separately instead of silently
    disappearing.
    """
    valid = []
    rejected = []


    seen_ids: set[str] = set()

    for index, row in enumerate(rows):
        errors : List[str] = []

        # -----------------------------------------------------
        # Schema
        # -----------------------------------------------------
        missing = REQUIRED_FIELD - set(row)
        if missing:
            errors.append(
                f"missing fields: {sorted(missing)}"
            )
        if errors:
            rejected.append(
                {
                    "index": index,
                    "row": row,
                    "errors": errors,
                }
            )
            continue

        example_id = row["id"]
        prompt = row["prompt"]
        chosen = row["chosen"]
        rejected_response = row["rejected"]

        # -----------------------------------------------------
        # Type checks
        # -----------------------------------------------------

        for field_name in (
            "id",
            "prompt",
            "chosen",
            "rejected",
            "source",
            "split",
        ):
            if not isinstance(row[field_name], str):
                errors.append(
                    f"{field_name} must be a string"
                )

        if not isinstance(row['metadata'], Dict):
            errors.append(
                f"metadata must be a Dict"
            )
        # -----------------------------------------------------
        # Empty checks
        # -----------------------------------------------------
        if isinstance(prompt, str) and not prompt.strip():
            errors.append("empty prompt")

        if isinstance(chosen, str) and not chosen.strip():
            errors.append("empty chosen response")

        if (
            isinstance(rejected_response, str)
            and not rejected_response.strip()
        ):
            errors.append("empty rejected response")

        # -----------------------------------------------------
        # Duplicate IDs
        # -----------------------------------------------------
        if isinstance(example_id, str):
            if example_id in seen_ids:
                errors.append("duplicate ID")
            else:
                seen_ids.add(example_id)
        # -----------------------------------------------------
        # Identical preference
        # -----------------------------------------------------

        if (
            isinstance(chosen, str)
            and isinstance(rejected_response, str)
            and chosen.strip() == rejected_response.strip()
        ):
            errors.append(
                "chosen and rejected responses are identical"
            )
        # -----------------------------------------------------
        # Final decision
        # -----------------------------------------------------

        if errors:
            rejected.append(
                {
                    "index": index,
                    "row": row,
                    "errors": errors,
                }
            )
        else:
            valid.append(row)

    return ValidationResult(
        valid=valid,
        rejected=rejected,
    )


def compute_length_stats(
    rows: List[Dict[str, Any]]
) -> List[Dict[str, int]]:
    stats = []    

    for row in rows:
        chosen_length = len(row["chosen"])
        rejected_length = len(row["rejected"])

        shorter = min(chosen_length, rejected_length)


        if shorter == 0:
            ratio = float("inf")
        else:
            ratio = max(chosen_length, rejected_length) / shorter
        stats.append(
            {
                "id": row["id"],
                "chosen_length": chosen_length,
                "rejected_length": rejected_length,
                "length_ratio": ratio
            }
        )

    return stats





def summarize_length_stats(
    stats: List[Dict[str, Any]],
) -> Dict[str, float]:
    if not stats:
        return {}

    chosen = [
        item["chosen_length"]
        for item in stats
    ]

    rejected = [
        item["rejected_length"]
        for item in stats
    ]

    ratios = [
        item["length_ratio"]
        for item in stats
        if item["length_ratio"] != float("inf")
    ]

    return {
        "num_examples": len(stats),
        "chosen_mean": statistics.mean(chosen),
        "chosen_median": statistics.median(chosen),
        "rejected_mean": statistics.mean(rejected),
        "rejected_median": statistics.median(rejected),
        "ratio_mean": statistics.mean(ratios),
        "ratio_median": statistics.median(ratios),
    }





def sample_for_manual_inspection(
    rows: List[Dict[str, Any]],
    n: int = 20,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    rng = random.Random(seed)

    if len(rows) <= n:
        return rows.copy()

    return rng.sample(rows, n)


def write_jsonl(
    rows: List[Dict[str, Any]],
    path: Union[str, Path],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(input_path: str):
    output_path = Path(
        "tests/fixtures/tiny_preferences_validated.jsonl"
    )
    report_path = Path(
        "reports/preference_data_audit.md"
    )

    rows = load_raw_preferences(input_path)

    result = validate_preference_data(rows)

    stats = compute_length_stats(result.valid)
    summary = summarize_length_stats(stats)

    manual_sample = sample_for_manual_inspection(
        result.valid,
        n=50,
        seed=42,
    )

    write_jsonl(
        result.valid,
        output_path,
    )

    # Count rejection reasons.
    rejection_reasons: Dict[str, int] = {}

    for item in result.rejected:
        for error in item["errors"]:
            rejection_reasons[error] = (
                rejection_reasons.get(error, 0) + 1
            )

    report_lines = [
        "# Preference Data Audit",
        "",
        "## Dataset summary",
        "",
        f"- Input examples: {len(rows)}",
        f"- Valid examples: {len(result.valid)}",
        f"- Rejected examples: {len(result.rejected)}",
        "",
        "## Filtering rules",
        "",
        "An example is rejected when:",
        "",
        "- required fields are missing",
        "- fields have invalid types",
        "- the prompt is empty",
        "- the chosen response is empty",
        "- the rejected response is empty",
        "- chosen and rejected responses are identical",
        "- the example ID is duplicated",
        "",
        "Invalid examples are not silently discarded; rejection "
        "reasons are recorded.",
        "",
        "## Rejection reasons",
        "",
    ]

    if rejection_reasons:
        for reason, count in rejection_reasons.items():
            report_lines.append(
                f"- `{reason}`: {count}"
            )
    else:
        report_lines.append(
            "- None"
        )

    report_lines.extend(
        [
            "",
            "## Length statistics",
            "",
            f"- Number of valid examples: "
            f"{summary.get('num_examples', 0)}",
            f"- Mean chosen length: "
            f"{summary.get('chosen_mean', 0):.2f} characters",
            f"- Median chosen length: "
            f"{summary.get('chosen_median', 0):.2f} characters",
            f"- Mean rejected length: "
            f"{summary.get('rejected_mean', 0):.2f} characters",
            f"- Median rejected length: "
            f"{summary.get('rejected_median', 0):.2f} characters",
            f"- Mean length ratio: "
            f"{summary.get('ratio_mean', 0):.2f}",
            f"- Median length ratio: "
            f"{summary.get('ratio_median', 0):.2f}",
            "",
            "## Manual inspection sample",
            "",
            "The following examples were sampled with seed `42`.",
            "",
        ]
    )

    for i, row in enumerate(manual_sample, start=1):
        report_lines.extend(
            [
                f"### Example {i} — `{row['id']}`",
                "",
                "**Prompt**",
                "",
                f"> {row['prompt']}",
                "",
                "**Chosen**",
                "",
                f"> {row['chosen']}",
                "",
                "**Rejected**",
                "",
                f"> {row['rejected']}",
                "",
                "**Manual decision:** TODO",
                "",
            ]
        )

    report_lines.extend(
        [
            "## Filtering decision",
            "",
            "TODO: record the final decision after manual inspection.",
            "",
        ]
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_path.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    print(f"Input:      {len(rows)}")
    print(f"Valid:      {len(result.valid)}")
    print(f"Rejected:   {len(result.rejected)}")
    print(f"Validated:  {output_path}")
    print(f"Report:     {report_path}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Validate canonical preference data."
    )
    parser.add_argument(
        "input_path",
        type=str,
        default="tests/fixtures/tiny_preferences.jsonl", # data/english/hh_rlhf_helpful-base_2000.jsonl
        help="Path to preference JSONL file",
    )

    args = parser.parse_args()

    main(args.input_path)



