from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch
import transformers
import trl
import peft
import bitsandbytes



def get_git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return "unknown"

def get_gpu_metadata() -> dict:
    if not torch.cuda.is_available():
        return {
            "available": False,
            "name": None,
            "vram_gib": None,
            "cuda": torch.version.cuda,
            "bf16_supported": False,
        }

    props = torch.cuda.get_device_properties(0)

    return {
        "available": True,
        "name": props.name,
        "vram_gib": round(props.total_memory / 1024**3, 2),
        "cuda": torch.version.cuda,
        "bf16_supported": torch.cuda.is_bf16_supported(),
    }


def build_run_metadata(
    *,
    run_id: str,
    model_name: str,
    model_revision: str,
    tokenizer_name: str,
    tokenizer_revision: str,
    seed: int,
    adapter_config: dict,
    data_version: str | None = None,
    peak_allocated_gib: float | None = None,
    peak_reserved_gib: float | None = None,
) -> dict:
    return {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "seed": seed,
        "model": {
            "name": model_name,
            "revision": model_revision,
        },
        "tokenizer": {
            "name": tokenizer_name,
            "revision": tokenizer_revision,
        },
        "adapter": adapter_config,
        "data": {
            "version": data_version,
        },
        "hardware": get_gpu_metadata(),
        "software": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "trl": trl.__version__,
            "peft": peft.__version__,
            "bitsandbytes": bitsandbytes.__version__,
        },
        "memory": {
            "peak_allocated_gib": peak_allocated_gib,
            "peak_reserved_gib": peak_reserved_gib,
        },
    }