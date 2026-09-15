import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel


BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTER = "outputs/sft_smoke"


def main():
    # Load tokenizer from the adapter directory
    tokenizer = AutoTokenizer.from_pretrained(ADAPTER)

    # Load base model in the same 4-bit configuration as training

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

    # Attach trained adapter
    model = PeftModel.from_pretrained(
        base_model,
        ADAPTER,
    )

    model.eval()

    # Test prompts

    prompts = [
        "تقدر تشرحلي كيفاش نحسبو مساحة المثلث؟",
        "واش نقدر ندير باش ننظم وقتي بين القراية والراحة؟",
        "علاش السماء تبان زرقاء؟",
    ]

    for i, prompt in enumerate(prompts, 1):
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

        # Transformers may return a tensor or BatchEncoding depending
        # on the tokenizer configuration.
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

        print(f"\n{'=' * 60}")
        print(f"TEST {i}")
        print(f"{'=' * 60}")
        print("PROMPT:")
        print(prompt)
        print("\nRESPONSE:")
        print(response)


if __name__ == "__main__":
    main()