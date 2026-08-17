


from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))



import torch
from torch import nn
from contextlib import nullcontext
from scratch_dpo.forward import concatenated_forward, reference_concatenated_forward
from scratch_dpo.logps import get_batch_logps_from_logits


class DummyCausalLM(nn.Module):
    def __init__(self, vocab_size: int = 10):
        super().__init__()
        self.vocab_size = vocab_size

    def forward(self, input_ids, attention_mask=None):
        B, T = input_ids.shape

        # Deterministic logits.
        logits = torch.zeros(
            B,
            T,
            self.vocab_size,
        )

        # Make the logits depend on the input token.
        for b in range(B):
            for t in range(T):
                token_id = input_ids[b, t].item()
                logits[b, t, token_id] = 5.0

        return type(
            "Output",
            (),
            {"logits": logits},
        )()


def test_concatenated_forward_matches_separate_forwards():

    model = DummyCausalLM()

    batch = {
        "chosen_input_ids": torch.tensor([
            [1, 2, 3, 4],
            [5, 6, 7, 0],
        ]),

        "chosen_attention_mask": torch.tensor([
            [1, 1, 1, 1],
            [1, 1, 1, 0],
        ]),

        "chosen_loss_mask": torch.tensor([
            [0, 0, 1, 1],
            [0, 1, 1, 0],
        ]),

        "rejected_input_ids": torch.tensor([
            [1, 2, 8, 9],
            [5, 6, 2, 0],
        ]),

        "rejected_attention_mask": torch.tensor([
            [1, 1, 1, 1],
            [1, 1, 1, 0],
        ]),

        "rejected_loss_mask": torch.tensor([
            [0, 0, 1, 1],
            [0, 1, 1, 0],
        ]),
    }

    # ---------------------------------------------
    # Separate forwards
    # ---------------------------------------------

    chosen_outputs = model(
        input_ids=batch["chosen_input_ids"],
        attention_mask=batch["chosen_attention_mask"],
    )

    rejected_outputs = model(
        input_ids=batch["rejected_input_ids"],
        attention_mask=batch["rejected_attention_mask"],
    )

    chosen_separate = get_batch_logps_from_logits(
        logits=chosen_outputs.logits,
        labels=batch["chosen_input_ids"],
        loss_mask=batch["chosen_loss_mask"],
    )

    rejected_separate = get_batch_logps_from_logits(
        logits=rejected_outputs.logits,
        labels=batch["rejected_input_ids"],
        loss_mask=batch["rejected_loss_mask"],
    )

    # ---------------------------------------------
    # Concatenated forward
    # ---------------------------------------------

    chosen_concat, rejected_concat = concatenated_forward(
        model,
        batch,
    )

    # ---------------------------------------------
    # Correct shapes
    # ---------------------------------------------

    assert chosen_concat.shape == torch.Size([2])
    assert rejected_concat.shape == torch.Size([2])

    # ---------------------------------------------
    # Numerical equivalence
    # ---------------------------------------------

    assert torch.allclose(
        chosen_concat,
        chosen_separate,
    )

    assert torch.allclose(
        rejected_concat,
        rejected_separate,
    )

class DummyCausalLM(torch.nn.Module):

    def __init__(self, vocab_size=10):
        super().__init__()
        self.vocab_size = vocab_size

    def forward(self, input_ids, attention_mask=None):
        B, T = input_ids.shape

        logits = torch.zeros(
            B,
            T,
            self.vocab_size,
        )

        return type(
            "Output",
            (),
            {"logits": logits},
        )()

    def disable_adapter(self):
        return nullcontext()

def test_reference_forward_is_detached():

    model = DummyCausalLM()

    batch = {
        "chosen_input_ids": torch.tensor([
            [1, 2, 3, 4],
            [5, 6, 7, 0],
        ]),

        "chosen_attention_mask": torch.tensor([
            [1, 1, 1, 1],
            [1, 1, 1, 0],
        ]),

        "chosen_loss_mask": torch.tensor([
            [0, 0, 1, 1],
            [0, 1, 1, 0],
        ]),

        "rejected_input_ids": torch.tensor([
            [1, 2, 8, 9],
            [5, 6, 2, 0],
        ]),

        "rejected_attention_mask": torch.tensor([
            [1, 1, 1, 1],
            [1, 1, 1, 0],
        ]),

        "rejected_loss_mask": torch.tensor([
            [0, 0, 1, 1],
            [0, 1, 1, 0],
        ]),
    }

    chosen_ref, rejected_ref = reference_concatenated_forward(
        model,
        batch,
    )

    assert chosen_ref.shape == torch.Size([2])
    assert rejected_ref.shape == torch.Size([2])

    assert not chosen_ref.requires_grad
    assert not rejected_ref.requires_grad