#!/usr/bin/env python

import argparse
from pathlib import Path

import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def print_environment() -> None:
    print("=== Environment ===")
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"CUDA version: {torch.version.cuda}")

    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        print(f"GPU: {props.name}")
        print(f"VRAM: {props.total_memory / 1024**3:.2f} GiB")
        print(f"BF16 supported: {torch.cuda.is_bf16_supported()}")

    print()


def build_quantization_config(config: dict):
    qcfg = config["quantization"] 

    if not qcfg["enabled"]:
        return None

    compute_dtype_name = qcfg["bnb_4bit_compute_dtype"]

    if compute_dtype_name == "bfloat16":
        compute_dtype = torch.bfloat16
    elif compute_dtype_name == "float16":
        compute_dtype = torch.float16
    else:
        raise ValueError(
            f"Unsupported compute dtype: {compute_dtype_name}"
        )

    return BitsAndBytesConfig(
        load_in_4bit=qcfg["load_in_4bit"],
        bnb_4bit_quant_type=qcfg["bnb_4bit_quant_type"],
        bnb_4bit_use_double_quant=qcfg["bnb_4bit_use_double_quant"],
        bnb_4bit_compute_dtype=compute_dtype,
    )


def load_model_and_tokenizer(config: dict):
    model_cfg = config["model"]

    model_name = model_cfg["name"]
    revision = model_cfg["revision"]
    tokenizer_name = model_cfg["tokenizer_name"]
    tokenizer_revision = model_cfg["tokenizer_revision"]

    print(f"Model: {model_name}")
    print(f"Model revision: {revision}")
    print(f"Tokenizer: {tokenizer_name}")
    print(f"Tokenizer revision: {tokenizer_revision}")

    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_name,
        revision=tokenizer_revision,
        trust_remote_code=model_cfg["trust_remote_code"],
    )

    quantization_config = build_quantization_config(config)

    model_kwargs = {
        "revision": revision,
        "trust_remote_code": model_cfg["trust_remote_code"],
        "device_map": "auto",
    }

    if quantization_config is not None:
        model_kwargs["quantization_config"] = quantization_config
    else:
        model_kwargs["dtype"] = torch.bfloat16

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        **model_kwargs,
    )

    return model, tokenizer


def count_parameters(model):
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )

    return total, trainable

def smoke_generate(model, tokenizer):
    messages = [
        {
            "role": "user",
            "content": (
                "واش تقدر تشرحلي باختصار شنو هو overfitting "
                "بالدارجة الجزائرية؟"
            ),
        }
    ]

    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
        return_dict=True,
    )

    input_device = model.get_input_embeddings().weight.device
    inputs = {
        key: value.to(input_device)
        for key, value in inputs.items()
        if torch.is_tensor(value)
    }

    input_tokens = inputs["input_ids"].shape[-1]

    print()
    print("=== Generation smoke test ===")
    print("Input tokens:", input_tokens)

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=64,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated = outputs[0, input_tokens:]

    text = tokenizer.decode(
        generated,
        skip_special_tokens=True,
    )

    print()
    print("Generated:")
    print(text)
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/model.yaml",
    )
    args = parser.parse_args()

    config_path = Path(args.config)

    if not config_path.exists():
        raise FileNotFoundError(config_path)

    config = load_config(str(config_path))

    print_environment()

    model, tokenizer = load_model_and_tokenizer(config)

    total, trainable = count_parameters(model)

    print()
    print("=== Architecture ===")
    print("Model class:", model.__class__.__name__)
    print("model_type:", getattr(model.config, "model_type", None))
    print("architectures:", getattr(model.config, "architectures", None))
    print("hidden_size:", getattr(model.config, "hidden_size", None))
    print("num_hidden_layers:", getattr(model.config, "num_hidden_layers", None))
    print(
        "num_attention_heads:",
        getattr(model.config, "num_attention_heads", None),
    )
    print(
        "num_key_value_heads:",
        getattr(model.config, "num_key_value_heads", None),
    )
    print("vocab_size:", getattr(model.config, "vocab_size", None))
    print("torch_dtype:", getattr(model.config, "torch_dtype", None))

    print()
    print("=== Model ===")
    print(f"Total parameters: {total:,}")
    print(f"Trainable parameters: {trainable:,}")
    print(f"Tokenizer vocab size: {len(tokenizer):,}")
    print(
        "Chat template present:",
        tokenizer.chat_template is not None,
    )

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    smoke_generate(model, tokenizer)

    if torch.cuda.is_available():
        peak = torch.cuda.max_memory_allocated() / 1024**3
        reserved = torch.cuda.max_memory_reserved() / 1024**3

        print("=== Peak GPU memory ===")
        print(f"Allocated: {peak:.2f} GiB")
        print(f"Reserved:  {reserved:.2f} GiB")


if __name__ == "__main__":
    main()