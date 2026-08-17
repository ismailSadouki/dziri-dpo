
from __future__ import annotations


import torch


def get_batch_logps_from_logits(
        logits: torch.Tensor,
        labels: torch.Tensor,
        loss_mask: torch.Tensor,
        average_log_prob: bool = False,
) -> torch.Tensor:
    """
    Compute per-sequence autoregressive log probabilities.

    Args:
        logits:    [B, T, V]
        labels:    [B, T]
        loss_mask: [B, T]
        average_log_prob:
            False -> sum log probabilities
            True  -> mean over scored tokens

    Returns:
        [B]
    """


    # --------------------------------------------------
    # Shape checks
    # --------------------------------------------------
    if logits.ndim != 3:
        raise ValueError(
            f"logits must have shape [B, T, V], got {logits.shape}"
        )

    if labels.ndim != 2:
        raise ValueError(
            f"labels must have shape [B, T], got {labels.shape}"
        )

    if loss_mask.ndim != 2:
        raise ValueError(
            f"loss_mask must have shape [B, T], got {loss_mask.shape}"
        )

    B, T, V = logits.shape

    if labels.shape != (B, T):
        raise ValueError(
            f"labels shape {labels.shape} != {(B, T)}"
        )

    if loss_mask.shape != (B, T):
        raise ValueError(
            f"loss_mask shape {loss_mask.shape} != {(B, T)}"
        )

    # Autoregressive shift
    # logits[:, t] predicts labels[:, t + 1]
    # --------------------------------------------------
    shift_logits = logits[:, :-1, :] #[B, T-1, V]
    shift_labels = labels[:, 1:]     #[B, T-1]
    shift_mask = loss_mask[:, 1:]    #[B, T-1]

    # -100 cannot be passed to gather()
    safe_labels = shift_labels.clone()
    safe_labels[safe_labels == -100] = 0

    # Convert logits -> log probabilities
    log_probs = torch.log_softmax(shift_logits, dim=-1) 

    # Select probability of the actual next token
    token_log_probs = torch.gather(
        log_probs,
        dim=-1,
        index=safe_labels.unsqueeze(-1)
    ).squeeze(-1)

    token_log_probs = token_log_probs * shift_mask

    

    # Sum / average per sequence
    if average_log_prob:
        denominator = shift_mask.sum(dim=-1).clamp_min(1)
        return token_log_probs.sum(dim=-1) / denominator

    return token_log_probs.sum(dim=-1)