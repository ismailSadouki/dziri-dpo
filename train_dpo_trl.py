
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
import yaml
from datasets import Dataset
from peft import PeftModel
from transformers import AutoTokenizer
from trl import DPOConfig, DPOTrainer

from darija_alignment.model.loading import load_sft_model


def load_jsonl(path: str) -> list[dict]:
    rows = []
    with Path(path).open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at {path}:{line_number}"
                ) from exc
    return rows


def build_preference_dataset(path: str) -> Dataset:
    rows = load_jsonl(path)
    required = {"prompt", "chosen", "rejected"}

    formatted = []
    for i, row in enumerate(rows):
        missing = required - row.keys()
        if missing:
            raise ValueError(f"Row {i} missing fields: {sorted(missing)}")

        prompt = row["prompt"]
        chosen = row["chosen"]
        rejected = row["rejected"]

        if not all(isinstance(x, str) and x.strip()
                   for x in (prompt, chosen, rejected)):
            raise ValueError(f"Row {i} has an empty or non-string field")

        # Conversational format lets TRL apply the tokenizer's chat template.
        formatted.append({
            "prompt": [{"role": "user", "content": prompt}],
            "chosen": [{"role": "assistant", "content": chosen}],
            "rejected": [{"role": "assistant", "content": rejected}],
        })

    if not formatted:
        raise ValueError(f"No preference rows found in {path}")

    return Dataset.from_list(formatted)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/dpo/beta_0.1.yaml",
    )
    args = parser.parse_args()

    with Path(args.config).open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    torch.manual_seed(cfg["seed"])
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(cfg["seed"])

    tokenizer = AutoTokenizer.from_pretrained(
        cfg["model_name"],
        trust_remote_code=False,
    )
    if tokenizer.pad_token is None:
        if tokenizer.eos_token is None:
            raise ValueError("Tokenizer has neither pad_token nor eos_token")
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    train_dataset = build_preference_dataset(
        cfg["train_dataset"]
    )

    eval_dataset = build_preference_dataset(
        cfg["eval_dataset"]
    )

    # Load the quantized base and attach the selected, trained SFT adapter.
    model = load_sft_model(
        cfg["model_name"],
        mode="qlora_nf4",
        gradient_checkpointing=cfg["gradient_checkpointing"],
    )
    model = PeftModel.from_pretrained(
        model,
        cfg["sft_checkpoint"],
        is_trainable=True,
    )
    model.set_adapter("default")
    model.config.use_cache = False

    dpo_args = DPOConfig(
        output_dir=cfg["output_dir"],
        beta=cfg["beta"],
        max_steps=cfg["max_steps"],

        per_device_train_batch_size=cfg["per_device_train_batch_size"],
        per_device_eval_batch_size=cfg["per_device_eval_batch_size"],
        gradient_accumulation_steps=cfg["gradient_accumulation_steps"],

        learning_rate=cfg["learning_rate"],
        max_length=cfg["max_length"],

        seed=cfg["seed"],

        bf16=cfg["bf16"],
        fp16=False,

        gradient_checkpointing=cfg["gradient_checkpointing"],

        logging_strategy="steps",
        logging_steps=cfg["logging_steps"],

        eval_strategy=cfg["eval_strategy"],
        eval_steps=cfg["eval_steps"],

        save_strategy=cfg["save_strategy"],
        save_steps=cfg["save_steps"],
        save_total_limit=cfg["save_total_limit"],

        remove_unused_columns=False,
        report_to="none",
        disable_dropout=True,
    )


    trainer = DPOTrainer(
        model=model,
        ref_model=None,
        args=dpo_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
    )

    # Print one processed example's key lengths before training.
    print(f"Train rows: {len(train_dataset)}")
    print(f"Eval rows: {len(eval_dataset)}")

    example = trainer.train_dataset[0]

    print("Processed dataset columns:", trainer.train_dataset.column_names)

    for key in ("prompt_ids", "chosen_ids", "rejected_ids"):
        value = example[key]
        print(f"{key} token length: {len(value)}")

    trainer.train()
    trainer.save_model(cfg["output_dir"])
    tokenizer.save_pretrained(cfg["output_dir"])

    eval_history = [
        x for x in trainer.state.log_history
        if "eval_loss" in x
    ]

    train_history = [
        x for x in trainer.state.log_history
        if "loss" in x and "eval_loss" not in x
    ]

    summary = {
        "model_name": cfg["model_name"],
        "sft_checkpoint": cfg["sft_checkpoint"],
        "train_dataset": cfg["train_dataset"],
        "eval_dataset": cfg["eval_dataset"],
        "beta": cfg["beta"],
        "max_steps": cfg["max_steps"],
        "seed": cfg["seed"],
        "train_rows": len(train_dataset),
        "eval_rows": len(eval_dataset),
        "train_history": train_history,
        "eval_history": eval_history,
    }
    output_path = Path(cfg["output_dir"]) / "run_summary.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved run summary: {output_path}")


if __name__ == "__main__":
    main()