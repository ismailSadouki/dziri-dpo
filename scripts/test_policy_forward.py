import torch
from pathlib import Path
import sys


sys.path.append(str(Path(__file__).resolve().parent.parent))

from scratch_dpo.modeling import build_quantization_config, load_tokenizer, load_policy, attach_lora
from scratch_dpo.reference import reference_forward


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"



def get_vram_mb() -> tuple[float, float]:
    allocated = torch.cuda.memory_allocated() / 1024**2
    reserved = torch.cuda.memory_reserved() / 1024**2

    return allocated, reserved


def main():

    tokenizer = load_tokenizer(MODEL_NAME)

    model = load_policy(MODEL_NAME)
    model = attach_lora(model)

    model.eval()

    inputs = tokenizer(
        "Hello, how are you?",
        return_tensors="pt",
    ).to(model.device)

    print("=== Model configuration ===")
    print("Model:", MODEL_NAME)
    print("Device:", model.device)

    print(
        "Quantization:"
    )


    quant_config = build_quantization_config()

    print("load_in_4bit:", quant_config.load_in_4bit)
    print("quant_type:", quant_config.bnb_4bit_quant_type)
    print("compute_dtype:", quant_config.bnb_4bit_compute_dtype)
    print("double_quant:", quant_config.bnb_4bit_use_double_quant)
    # --------------------------------------------------
    # Reset memory statistics before the first batch.
    # --------------------------------------------------

    torch.cuda.reset_peak_memory_stats()
    torch.cuda.synchronize()

    # --------------------------------------------------
    # Policy forward
    # --------------------------------------------------

    with torch.no_grad():
        policy_outputs = model(**inputs)

    # --------------------------------------------------
    # Reference forward
    # Adapter is disabled inside reference_forward().
    # --------------------------------------------------
    with torch.no_grad():
        reference_outputs = reference_forward( # uses no_graad too inside of it 
                model,
                inputs,
            )

    torch.cuda.synchronize()

    # --------------------------------------------------
    # Shapes
    # --------------------------------------------------

    print("input_ids shape:", inputs["input_ids"].shape)

    print(
        "Policy logits:",
        policy_outputs.logits.shape,
    )

    print(
        "Reference logits:",
        reference_outputs.logits.shape,
    )

    # --------------------------------------------------
    # Policy/reference numerical comparison
    # --------------------------------------------------

    difference = (
        policy_outputs.logits
        - reference_outputs.logits
    ).abs().max()

    print(
        "Max policy/reference difference:",
        difference.item(),
    )

    # --------------------------------------------------
    # VRAM
    # --------------------------------------------------

    allocated_mb, reserved_mb = get_vram_mb()

    peak_mb = (
        torch.cuda.max_memory_allocated()
        / 1024**2
    )

    print(f"Allocated VRAM: {allocated_mb:.2f} MB")
    print(f"Reserved VRAM:  {reserved_mb:.2f} MB")
    print(f"Peak VRAM:      {peak_mb:.2f} MB")





if __name__ == "__main__":
    main()