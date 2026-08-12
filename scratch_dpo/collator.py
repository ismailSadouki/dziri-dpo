from dataclasses import dataclass

import torch
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from scratch_dpo.data import TokenizedPreference


@dataclass
class DPODataCollator:
    pad_token_id: int

    def _pad(
        self,
        sequences: list[list[int]],
        max_length: int,
        pad_value: int,
    ) -> torch.Tensor:
        padded = [
            seq + [pad_value] * (max_length - len(seq))
            for seq in sequences
        ]

        return torch.tensor(
            padded,
            dtype=torch.long,
        )

    def _pad_mask(
        self,
        masks: list[list[int]],
        max_length: int,
    ) -> torch.Tensor:
        padded = [
            mask + [0] * (max_length - len(mask))
            for mask in masks
        ]

        return torch.tensor(
            padded,
            dtype=torch.long,
        )

    def __call__(
        self,
        examples: list[TokenizedPreference],
    ) -> dict[str, torch.Tensor]:

        chosen_ids = [
            example.chosen_input_ids
            for example in examples
        ]

        rejected_ids = [
            example.rejected_input_ids
            for example in examples
        ]

        chosen_masks = [
            example.chosen_loss_mask
            for example in examples
        ]

        rejected_masks = [
            example.rejected_loss_mask
            for example in examples
        ]

        # --------------------------------------------------
        # One shared sequence length for BOTH branches.
        # --------------------------------------------------

        max_length = max(
            max(len(x) for x in chosen_ids),
            max(len(x) for x in rejected_ids),
        )

        # --------------------------------------------------
        # Pad input IDs to the SAME max_length.
        # --------------------------------------------------

        chosen_input_ids = self._pad(
            chosen_ids,
            max_length,
            self.pad_token_id,
        )

        rejected_input_ids = self._pad(
            rejected_ids,
            max_length,
            self.pad_token_id,
        )

        # --------------------------------------------------
        # Pad loss masks to the SAME max_length.
        # --------------------------------------------------

        chosen_loss_mask = self._pad_mask(
            chosen_masks,
            max_length,
        )

        rejected_loss_mask = self._pad_mask(
            rejected_masks,
            max_length,
        )

        # --------------------------------------------------
        # attention_mask:
        #
        # 1 = real token
        # 0 = padding
        # --------------------------------------------------

        chosen_attention_mask = (
            chosen_input_ids != self.pad_token_id
        ).long()

        rejected_attention_mask = (
            rejected_input_ids != self.pad_token_id
        ).long()

        # --------------------------------------------------
        # Padding must NEVER contribute to DPO loss.
        #
        # loss_mask:
        #   1 = response token
        #   0 = prompt OR padding
        # --------------------------------------------------

        chosen_loss_mask = (
            chosen_loss_mask * chosen_attention_mask
        )

        rejected_loss_mask = (
            rejected_loss_mask * rejected_attention_mask
        )

        # --------------------------------------------------
        # Shape invariants.
        # --------------------------------------------------

        assert chosen_input_ids.shape == (
            chosen_attention_mask.shape
        )

        assert chosen_input_ids.shape == (
            chosen_loss_mask.shape
        )

        assert rejected_input_ids.shape == (
            rejected_attention_mask.shape
        )

        assert rejected_input_ids.shape == (
            rejected_loss_mask.shape
        )

        assert chosen_input_ids.shape == rejected_input_ids.shape

        # Padding can never have loss_mask = 1.
        assert torch.all(
            chosen_loss_mask[chosen_attention_mask == 0] == 0
        )

        assert torch.all(
            rejected_loss_mask[rejected_attention_mask == 0] == 0
        )

        return {
            "chosen_input_ids": chosen_input_ids,
            "chosen_attention_mask": chosen_attention_mask,
            "chosen_loss_mask": chosen_loss_mask,
            "rejected_input_ids": rejected_input_ids,
            "rejected_attention_mask": rejected_attention_mask,
            "rejected_loss_mask": rejected_loss_mask,
        }