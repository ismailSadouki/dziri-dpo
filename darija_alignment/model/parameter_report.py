from __future__ import annotations

from typing import Any


def get_parameter_report(model: Any) -> dict[str, int | float]:
    """Return total/trainable parameter counts for a model."""

    total_params = 0
    trainable_params = 0


    for parameter in model.parameters():
        count = parameter.numel()

        total_params += count

        if parameter.requires_grad:
            trainable_params += count

    percentage = (
        100.0 * trainable_params / total_params
        if total_params > 0
        else 0.0
    )


    return {
        "trainable_params": trainable_params,
        "total_params": total_params,
        "trainable_percentage": percentage,
    }



def print_parameter_report(model: Any) -> dict[str, int | float]:
    """Print and return the model's parameter report."""

    report = get_parameter_report(model)

    print("\nTrainable parameter report")
    print("=" * 40)
    print(f"Trainable parameters: {report['trainable_params']:,}")
    print(f"Total parameters:     {report['total_params']:,}")
    print(f"Trainable percentage: {report['trainable_percentage']:.4f}%")

    return report