import torch

@torch.inference_mode()
def reference_forward(model, inputs):
    model.eval()


    with model.disable_adapter():
            outputs = model(**inputs)

    return outputs