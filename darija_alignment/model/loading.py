from __future__ import annotations

import torch
from peft import prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, BitsAndBytesConfig


MODEL_MODES = {"lora_bf16", "qlora_nf4"}


def load_sft_model(
    model_name: str,
    mode: str,
    *,
    revision: str = "main",
    trust_remote_code: bool = False,
    gradient_checkpointing: bool = True,
):
    """Load a BF16 LoRA or 4-bit NF4 QLoRA base model."""

    if mode not in MODEL_MODES:
        raise ValueError(
            f"Unsupported mode {mode!r}. Expected one of {sorted(MODEL_MODES)}"
        )

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for these SFT experiments.")

    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("This experiment requires BF16 support.")

    quantization_config = None

    if mode == "qlora_nf4":
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        revision=revision,
        trust_remote_code=trust_remote_code,
        torch_dtype=torch.bfloat16,
        quantization_config=quantization_config,
        device_map="auto",
    )

    model.config.use_cache = False

    if mode == "qlora_nf4":
        model = prepare_model_for_kbit_training(
            model,
            use_gradient_checkpointing=gradient_checkpointing,
        )

    return model
