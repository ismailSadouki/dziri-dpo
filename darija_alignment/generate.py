import gc
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

import torch
from peft import PeftModel
from transformers import AutoTokenizer

from darija_alignment.model.loading import load_sft_model


BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
SFT_CHECKPOINT = "outputs/sft_stage4_data100/checkpoint-100"

BETAS = ["0.05", "0.1", "0.3", "0.5"]

TEST_PATH = Path("data/preference_splits/test.jsonl")
OUTPUT_DIR = Path("reports/darija_alignment/generations")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_NEW_TOKENS = 256
SEED = 42


def load_prompts():
    rows = [
        json.loads(line)
        for line in TEST_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    return [
        {
            "id": i,
            "prompt": row["prompt"],
        }
        for i, row in enumerate(rows)
    ]


def load_checkpoint(adapter_path):
    model = load_sft_model(
        BASE_MODEL,
        mode="qlora_nf4",
        gradient_checkpointing=False,
    )

    model = PeftModel.from_pretrained(
        model,
        adapter_path,
        is_trainable=False,
    )

    model.eval()
    return model

def generate(model, tokenizer, prompt):
    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
        return_dict=True,
    )

    inputs = {
        key: value.to(model.device)
        for key, value in inputs.items()
    }

    input_length = inputs["input_ids"].shape[-1]

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    generated_ids = outputs[0, input_length:]
    generated_tokens = generated_ids.shape[-1]

    response = tokenizer.decode(
        generated_ids,
        skip_special_tokens=True,
    ).strip()

    hit_max_length = (
        generated_tokens >= MAX_NEW_TOKENS
        and (
            generated_tokens == 0
            or generated_ids[-1].item() != tokenizer.eos_token_id
        )
    )

    return {
        "response": response,
        "generated_tokens": generated_tokens,
        "hit_max_length": hit_max_length,
    }


def run_condition(condition_name, adapter_path, prompts):
    print(f"\n{'=' * 80}")
    print(f"Generating: {condition_name}")
    print(f"{'=' * 80}")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    model = load_checkpoint(adapter_path)

    results = []

    for i, item in enumerate(prompts):
        result = generate(
            model,
            tokenizer,
            item["prompt"],
        )

        row = {
            "id": item["id"],
            "prompt": item["prompt"],
            "condition": condition_name,
            **result,
            "generation_config": {
                "do_sample": False,
                "max_new_tokens": MAX_NEW_TOKENS,
                "seed": SEED,
            },
        }

        results.append(row)

        print(
            f"[{i + 1:02d}/{len(prompts)}] "
            f"tokens={result['generated_tokens']:3d} "
            f"max={result['hit_max_length']}"
        )

    output_path = OUTPUT_DIR / f"{condition_name}.json"
    output_path.write_text(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Saved: {output_path}")

    del model
    del tokenizer

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return results


def summarize(all_results):
    summary = {}

    for condition, rows in all_results.items():
        lengths = [
            row["generated_tokens"]
            for row in rows
        ]

        truncated = [
            row
            for row in rows
            if row["hit_max_length"]
        ]

        summary[condition] = {
            "n_prompts": len(rows),
            "mean_generated_tokens": sum(lengths) / len(lengths),
            "min_generated_tokens": min(lengths),
            "max_generated_tokens": max(lengths),
            "max_length_hits": len(truncated),
            "max_length_hit_rate": len(truncated) / len(rows),
        }

    output_path = OUTPUT_DIR / "generation_summary.json"

    output_path.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n" + "=" * 80)
    print("GENERATION LENGTH SUMMARY")
    print("=" * 80)

    print(
        f"{'condition':<12}"
        f"{'mean':>10}"
        f"{'min':>10}"
        f"{'max':>10}"
        f"{'truncated':>12}"
    )

    for condition, stats in summary.items():
        print(
            f"{condition:<12}"
            f"{stats['mean_generated_tokens']:>10.1f}"
            f"{stats['min_generated_tokens']:>10}"
            f"{stats['max_generated_tokens']:>10}"
            f"{stats['max_length_hits']:>12}"
        )

    print(f"\nSaved: {output_path}")


def main():
    torch.manual_seed(SEED)

    prompts = load_prompts()

    print(f"Loaded {len(prompts)} test prompts.")

    all_results = {}

    # SFT baseline
    all_results["sft"] = run_condition(
        "sft",
        SFT_CHECKPOINT,
        prompts,
    )

    # DPO beta checkpoints
    for beta in BETAS:
        all_results[f"beta_{beta}"] = run_condition(
            f"beta_{beta}",
            f"outputs/dpo_beta_{beta}/checkpoint-50",
            prompts,
        )

    summarize(all_results)


if __name__ == "__main__":
    main()