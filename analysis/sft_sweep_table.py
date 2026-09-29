from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass
class SFTSweepResult:
    target_set: str
    seed: int
    trainable_params: int
    trainable_percentage: float
    eval_loss: float
    eval_token_accuracy: float
    peak_vram_gb: float
    peak_reserved_gb: float
    tokens_per_sec: float
    wall_time_sec: float
    status: str


def make_result(
    *,
    target_set: str,
    seed: int,
    trainable_params: int,
    trainable_percentage: float,
    eval_loss: float,
    eval_token_accuracy: float,
    peak_vram_gb: float,
    peak_reserved_gb: float,
    tokens_per_sec: float,
    wall_time_sec: float,
    status: str = "PASS",
) -> SFTSweepResult:
    return SFTSweepResult(
        target_set=target_set,
        seed=seed,
        trainable_params=trainable_params,
        trainable_percentage=trainable_percentage,
        eval_loss=eval_loss,
        eval_token_accuracy=eval_token_accuracy,
        peak_vram_gb=peak_vram_gb,
        peak_reserved_gb=peak_reserved_gb,
        tokens_per_sec=tokens_per_sec,
        wall_time_sec=wall_time_sec,
        status=status,
    )


def write_results(results: list[SFTSweepResult], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w") as f:
        json.dump(
            [asdict(result) for result in results],
            f,
            indent=2,
        )