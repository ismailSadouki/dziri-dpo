import argparse
import json
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel


BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"

PROMPTS = [
    "تقدر تشرحلي كيفاش نحسبو مساحة المثلث؟",
    "واش نقدر ندير باش ننظم وقتي بين القراية والراحة؟",
    "علاش السماء تبان زرقاء؟",
]


def generate_samples(adapter: str) -> list[dict[str, str]]:
    tokenizer = AutoTokenizer.from_pretrained(adapter)

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    model = PeftModel.from_pretrained(
        base_model,
        adapter,
    )

    model.eval()

    results = []

    for prompt in PROMPTS:
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
        )

        if hasattr(inputs, "input_ids"):
            input_ids = inputs.input_ids
            attention_mask = inputs.attention_mask
        else:
            input_ids = inputs
            attention_mask = torch.ones_like(input_ids)

        input_ids = input_ids.to(model.device)
        attention_mask = attention_mask.to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=100,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        generated_ids = outputs[0][input_ids.shape[1]:]

        response = tokenizer.decode(
            generated_ids,
            skip_special_tokens=True,
        )

        results.append(
            {
                "prompt": prompt,
                "response": response,
            }
        )

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    results = generate_samples(args.adapter)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(
            {
                "base_model": BASE_MODEL,
                "adapter": args.adapter,
                "max_new_tokens": 100,
                "do_sample": False,
                "samples": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    print(f"Saved generations to: {output_path}")


if __name__ == "__main__":
    main()