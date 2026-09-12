#!/usr/bin/env python

import json

from pathlib import Path
import sys


sys.path.append(str(Path(__file__).resolve().parent.parent))



from darija_alignment.model.metadata import build_run_metadata


def main():
    metadata = build_run_metadata(
        run_id="b0_smoke_qwen15b",
        model_name="Qwen/Qwen2.5-1.5B-Instruct",
        model_revision="main",
        tokenizer_name="Qwen/Qwen2.5-1.5B-Instruct",
        tokenizer_revision="main",
        seed=42,
        adapter_config={
            "method": "lora",
            "r": 16,
            "alpha": 32,
            "dropout": 0.05,
            "target_modules": [
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
            ],
        },
        data_version=None,
        peak_allocated_gib=1.09,
        peak_reserved_gib=1.12,
    )

    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()