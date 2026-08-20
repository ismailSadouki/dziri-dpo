#load tokenizer
#      ↓
#load quantized base model
#      ↓
#attach LoRA
#      ↓
#return policy


# then: policy + adapter disabled -> reference model


from __future__ import annotations

from dataclasses import dataclass

import torch
from peft import prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from transformers import PreTrainedModel, PreTrainedTokenizerBase


from peft import LoraConfig, get_peft_model

@dataclass
class ModelBundle:
    model: PreTrainedModel
    tokenizer: PreTrainedTokenizerBase



def load_tokenizer(model_name: str):
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        use_fast=True,
        padding_side="right"
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return tokenizer


def build_quantization_config():
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )



def load_policy(model_name: str):
    quantization_config = build_quantization_config()

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quantization_config,
        device_map="auto",
    )

    return model

def attach_lora(model):
    model = prepare_model_for_kbit_training(model)
    config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj"
        ]
    )


    model = get_peft_model(model, config)

    model.print_trainable_parameters()

    return model


def count_parameters(model):
    totla = 0
    trainable = 0
    for parameter in model.parameters():
        n = parameter.numel()
        total += n
        if parameter.requires_grad:
            trainable += n
    return total, trainable

