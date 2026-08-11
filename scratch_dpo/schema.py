from dataclasses import dataclass, field
from typing import Any

@dataclass
class PreferenceExample:
    """
    Canonical raw preference example.

    An example consists of:
        x  = prompt
        yw = chosen response
        yl = rejected response
    """
    id: str
    prompt:str
    chosen: str
    rejected: str
    source: str
    split: str
    metadata: dict[str, Any] = field(default_factory=dict)


    def validate(self) -> None:
        """Validate the basic preference-example contract."""

        fields = {
            "id": self.id,
            "prompt": self.prompt,
            "chosen": self.chosen,
            "rejected": self.rejected,
            "source": self.source,
            "split": self.split,
        }

        for name, value in fields.items():
            if not isinstance(value, str):
                raise TypeError(
                    f"{name} must be str, got {type(value).__name__}"
                )
            if not value.strip():
                raise ValueError(f"{name} must not be empty")

        if not isinstance(self.metadata, dict):
            raise TypeError(
                f"metadata must be dict, got {type(self.metadata).__name__}"
            )

        if self.chosen == self.rejected:
            raise ValueError(
                "chosen and rejected responses must be different"
            )