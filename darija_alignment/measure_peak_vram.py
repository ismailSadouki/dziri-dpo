from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter

import torch


@contextmanager
def measure_peak_vram():
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for VRAM measurement.")

    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    start_time = perf_counter()

    metrics: dict[str, float] = {}

    try:
        yield metrics
    finally:
        torch.cuda.synchronize()

        metrics["elapsed_time_sec"] = perf_counter() - start_time
        metrics["peak_allocated_gb"] = (
            torch.cuda.max_memory_allocated() / (1024**3)
        )
        metrics["peak_reserved_gb"] = (
            torch.cuda.max_memory_reserved() / (1024**3)
        )

        print("\nVRAM measurement")
        print("=" * 40)
        print(f"Elapsed time:   {metrics['elapsed_time_sec']:.2f} s")
        print(f"Peak allocated: {metrics['peak_allocated_gb']:.2f} GB")
        print(f"Peak reserved:  {metrics['peak_reserved_gb']:.2f} GB")