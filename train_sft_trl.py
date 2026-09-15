import argparse
import json
import time
from pathlib import Path

import torch
import yaml
from datasets import Dataset
from peft import LoraConfig
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainerCallback,
)

from trl import SFTConfig, SFTTrainer

from darija_alignment.sft import format_sft_example

class ResponseOnlyCollator:
    """Pad already-tokenized response onlh SFT examples"""

    def __init__(self, pad_token_id: int):
        self.pad_token_id = pad_token_id

    def __call__(self, features):
        max_length = max(len(x["input_ids"]) for x in features)

        input_ids = []
        attention_mask = []
        labels = []


        for feature in features:
            length = len(feature["input_ids"])
            pad_length = max_length - length

            input_ids.append(
                feature["input_ids"] + [self.pad_token_id] * pad_length
            )

            attention_mask.append(
                feature["attention_mask"] + [0] * pad_length
            )

            labels.append(
                feature["labels"] + [-100] * pad_length
            )


        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }

class TrainingMetricsCallback(TrainerCallback):
    """Track throughput and peak VRAM."""

    def __init__(self):
        self.start_time = None
        self.last_time = None
        self.last_tokens = 0

    def on_train_begin(self, args, state, control, **kwargs):
        self.start_time = time.perf_counter()
        self.last_time = self.start_time
        self.last_tokens = 0

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()

    def on_log(self, args, state, control, logs=None, **kwargs):
        if not logs:
            return

        now = time.perf_counter()

        if "loss" in logs:
            logs["wall_time_sec"] = now - self.start_time

        # TRL reports cumulative tokens in `num_tokens`.
        if "num_tokens" in logs:
            current_tokens = float(logs["num_tokens"])
            delta_tokens = current_tokens - self.last_tokens
            delta_time = now - self.last_time

            if delta_time > 0 and delta_tokens > 0:
                logs["tokens_per_sec"] = delta_tokens / delta_time

            self.last_tokens = current_tokens
            self.last_time = now

        if torch.cuda.is_available():
            logs["peak_vram_gb"] = (
                torch.cuda.max_memory_allocated() / (1024**3)
            )

    def on_train_end(self, args, state, control, **kwargs):
        if self.start_time is None:
            return

        elapsed = time.perf_counter() - self.start_time

        print("\nTraining metrics")
        print("=" * 40)
        print(f"Wall time:      {elapsed:.2f} s")

        if torch.cuda.is_available():
            peak = torch.cuda.max_memory_allocated() / (1024**3)
            print(f"Peak VRAM:      {peak:.2f} GB")

def load_jsonl(path):
    rows = []

    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                rows.append(json.loads(line))

    return rows


def build_dataset(path, tokenizer, max_length):
    rows = load_jsonl(path)

    examples = []

    for row in rows:
        formatted = format_sft_example(
            tokenizer=tokenizer,
            messages=row["messages"],
            max_length=max_length,
        )

        examples.append(formatted)

    return Dataset.from_list(examples)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/sft_baseline.yaml",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Override config for smoke runs.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Override output directory.",
    )
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    seed = config["run"]["seed"]
    model_name = config["model"]["name"]

    max_length = config["data"]["max_length"]

    output_dir = (
        args.output_dir
        if args.output_dir is not None
        else config["output"]["root"]
    )


    tokenizer = AutoTokenizer.from_pretrained(model_name)

    if tokenizer.pad_token is None:
        raise RuntimeError(
            "Tokenizer has no pad token. Refusing to silently assign one."
        )


    train_dataset = build_dataset(
        config["data"]["train"],
        tokenizer,
        max_length,
    )

    eval_dataset = build_dataset(
        config["data"]["validation"],
        tokenizer,
        max_length,
    )

    print(f"Train examples: {len(train_dataset)}")
    print(f"Eval examples:  {len(eval_dataset)}")


    compute_dtype = torch.bfloat16

    compute_dtype = torch.bfloat16

    # 4-bit QLORA  
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=compute_dtype,
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quantization_config,
        torch_dtype=compute_dtype,
        device_map="auto",
    )

    model.config.use_cache = False

    # LoRa
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
        ],
    )



    # training config
    max_steps = (
        args.max_steps
        if args.max_steps is not None
        else config["training"]["max_steps"]
    )


    sft_config = SFTConfig(
        output_dir=output_dir,

        num_train_epochs=config["training"]["num_train_epochs"],
        max_steps=max_steps,

        per_device_train_batch_size=(
            config["training"]["per_device_train_batch_size"]
        ),
        per_device_eval_batch_size=(
            config["training"]["per_device_eval_batch_size"]
        ),
        gradient_accumulation_steps=(
            config["training"]["gradient_accumulation_steps"]
        ),
        learning_rate=config["training"]["learning_rate"],
        weight_decay=config["training"]["weight_decay"],
        max_grad_norm=config["training"]["max_grad_norm"],

        bf16=config["training"]["bf16"],
        fp16=False,

        gradient_checkpointing=(
            config["training"]["gradient_checkpointing"]
        ),

        logging_strategy="steps",
        logging_steps=config["training"]["logging_steps"],

        eval_strategy=config["training"]["eval_strategy"],
        eval_steps=config["training"]["eval_steps"],

        save_strategy=config["training"]["save_strategy"],
        save_steps=config["training"]["save_steps"],
        save_total_limit=config["training"]["save_total_limit"],

        seed=seed,

        max_length=max_length,
        packing=False,

        remove_unused_columns=False,

        # We already constructed labels ourselves.
        completion_only_loss=False,
        assistant_only_loss=False,

        report_to="none",

        # note: dataset is already tokenized and truncated.
        dataset_kwargs={
            "skip_prepare_dataset": True,
        },
    )
    collator = ResponseOnlyCollator(
        pad_token_id=tokenizer.pad_token_id,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
        data_collator=collator,
        peft_config=peft_config,
        callbacks=[TrainingMetricsCallback()],
    )

    batch = collator(
        [
            train_dataset[0],
            train_dataset[1],
        ]
    )

    print("\nBatch sanity check")
    print("=" * 40)
    print("input_ids:", tuple(batch["input_ids"].shape))
    print("labels:", tuple(batch["labels"].shape))
    print("attention_mask:", tuple(batch["attention_mask"].shape))

    supervised = (batch["labels"] != -100).sum().item()
    masked = (batch["labels"] == -100).sum().item()

    print("Supervised tokens:", supervised)
    print("Masked tokens:", masked)





    trainer.train()

    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    print(f"\nSaved SFT adapter to: {output_dir}")

if __name__ == "__main__":
    main()

