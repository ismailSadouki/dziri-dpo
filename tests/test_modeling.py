import torch


from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))



from scratch_dpo.modeling import (
    load_tokenizer,
    load_policy,
    attach_lora,
)
from scratch_dpo.reference import reference_forward


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


def test_policy_forward():

    tokenizer = load_tokenizer(MODEL_NAME)

    model = load_policy(MODEL_NAME)
    model = attach_lora(model)

    model.eval()

    inputs = tokenizer(
        "Hello, how are you?",
        return_tensors="pt",
    ).to(model.device)

    with torch.no_grad():
        outputs = model(**inputs)

    B, T = inputs["input_ids"].shape

    assert outputs.logits.shape[:2] == (B, T)
    assert outputs.logits.shape[2] == model.config.vocab_size



def test_lora_has_trainable_parameters():

    model = load_policy(MODEL_NAME)
    model = attach_lora(model)

    trainable = [
        p for p in model.parameters()
        if p.requires_grad
    ]

    assert len(trainable) > 0