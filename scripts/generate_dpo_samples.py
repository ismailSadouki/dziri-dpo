from __future__ import annotations
import argparse
import json
import random
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))



import numpy as np
import torch


from peft import PeftModel

from scratch_dpo.modeling import (
    attach_lora,
    load_policy,
    load_tokenizer,
)


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
SEED = 42
MAX_NEW_TOKENS = 128
TEMPERATURE = 0.7
TOP_P = 0.9





PROMPTS = [
    "Explain why regularization can help prevent overfitting in machine learning.",
    "What is the difference between correlation and causation?",
    "Give me three practical ways to improve the quality of a dataset.",
    "Explain gradient descent in simple terms.",
    "What are the main advantages of using a validation set?",
    "Why can a model have high training accuracy but poor test accuracy?",
    "Explain what a confidence interval means in statistics.",
    "What is the purpose of normalization in machine learning?",
]

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="LoRA checkpoint directory. Omit for step-0.",
    )

    parser.add_argument(
        "--step",
        type=int,
        default=0,
        help="Training step represented by this generation.",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/dpo_english_m4_2/samples",
    )

    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def load_generation_model(
    model_name: str,
    checkpoint: str | None,
):
    model = load_policy(model_name)

    if checkpoint is None:
        model = attach_lora(model)
    else:
        model = PeftModel.from_pretrained(
            model,
            checkpoint,
            is_trainable=False,
        )

    return model

def generate_response(
    model,
    tokenizer,
    prompt: str,
) -> str:
    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(
        text,
        return_tensors="pt",
    )

    device = next(model.parameters()).device

    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }


    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=True,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    generated_tokens = outputs[
        0,
        inputs["input_ids"].shape[1]:,
    ]

    return tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True,
    ).strip()

def main() -> None:
    args = parse_args()

    set_seed(SEED)

    tokenizer = load_tokenizer(MODEL_NAME)

    model = load_generation_model(
        model_name=MODEL_NAME,
        checkpoint=args.checkpoint,
    )

    model.eval()

    samples = []

    for index, prompt in enumerate(PROMPTS):
        response = generate_response(
            model=model,
            tokenizer=tokenizer,
            prompt=prompt,
        )

        samples.append(
            {
                "index": index,
                "step": args.step,
                "seed": SEED,
                "prompt": prompt,
                "response": response,
                "generation_config": {
                    "max_new_tokens": MAX_NEW_TOKENS,
                    "temperature": TEMPERATURE,
                    "top_p": TOP_P,
                    "do_sample": True,
                },
                "model": MODEL_NAME,
                "checkpoint": args.checkpoint,
            }
        )

    output_path = (
        Path(args.output_dir)
        / f"step-{args.step:04d}.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            samples,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"Saved {len(samples)} samples to: {output_path}"
    )

if __name__ == "__main__":
    main()