from __future__ import annotations

import torch
import torch.nn.functional as F

def dpo_loss(
    policy_chosen_logps: torch.Tensor,
    policy_rejected_logps: torch.Tensor,
    reference_chosen_logps: torch.Tensor,
    reference_rejected_logps: torch.Tensor,
    beta: float,
) -> tuple[
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
]:
    """
    Compute the per-example DPO loss and reward metrics.

    Args:
        policy_chosen_logps:
            [B] log πθ(y_w | x)

        policy_rejected_logps:
            [B] log πθ(y_l | x)

        reference_chosen_logps:
            [B] log πref(y_w | x)

        reference_rejected_logps:
            [B] log πref(y_l | x)

        beta:
            DPO beta parameter.

    Returns:
        losses:
            [B] per-example DPO losses

        chosen_rewards:
            [B] detached implicit rewards for chosen responses

        rejected_rewards:
            [B] detached implicit rewards for rejected responses

        reward_accuracy:
            scalar tensor containing the fraction where
            chosen_reward > rejected_reward
    """

    if policy_chosen_logps.ndim != 1:
        raise ValueError(
            f"policy_chosen_logps must have shape [B], "
            f"got {policy_chosen_logps.shape}"
        )

    if policy_rejected_logps.shape != policy_chosen_logps.shape:
        raise ValueError(
            "policy chosen/rejected shapes must match"
        )

    if reference_chosen_logps.shape != policy_chosen_logps.shape:
        raise ValueError(
            "reference chosen shape must match policy chosen shape"
        )

    if reference_rejected_logps.shape != policy_chosen_logps.shape:
        raise ValueError(
            "reference rejected shape must match policy chosen shape"
        )

    policy_logratio = (
        policy_chosen_logps - policy_rejected_logps
    )
    reference_logratio = (
        reference_chosen_logps - reference_rejected_logps
    )

    # DPO preference margin
    #
    # h =
    #   (log πθ(chosen) - log πθ(rejected))
    #   -
    #   (log πref(chosen) - log πref(rejected))
    margin = (
        policy_logratio - reference_logratio
    )


    # DPO loss
    # loss = -log σ(beta * margin)
    logits = beta * margin
    losses = -F.logsigmoid(logits)


    # Implicit rewards
    chosen_rewards = (
        beta
        * (
            policy_chosen_logps
            - reference_chosen_logps
        )
    ).detach()

    rejected_rewards = (
        beta
        * (
            policy_rejected_logps
            - reference_rejected_logps
        )
    ).detach()

    # Reward accuracy
    # How often does the chosen response receive
    # a larger implicit reward than the rejected one?
    reward_accuracy = (
        chosen_rewards > rejected_rewards
    ).float().mean()

    return (
        losses,
        chosen_rewards,
        rejected_rewards,
        margin,
        reward_accuracy
    )