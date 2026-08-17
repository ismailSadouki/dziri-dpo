from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))


import torch

from scratch_dpo.losses import dpo_loss


def test_identical_pair_gives_log_two():
    """
    If policy and reference give exactly the same
    relative preference to chosen/rejected:

        margin = 0

    Therefore:

        loss = -log(sigmoid(0))
             = log(2)
    """

    policy_chosen = torch.tensor([0.0])
    policy_rejected = torch.tensor([0.0])

    reference_chosen = torch.tensor([0.0])
    reference_rejected = torch.tensor([0.0])

    losses, *_ = dpo_loss(
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
        beta=0.1,
    )

    expected = torch.log(torch.tensor(2.0))

    assert torch.allclose(
        losses,
        expected.expand_as(losses),
    )


def test_reversed_pair_has_higher_loss():
    """
    Positive margin:
        chosen is preferred -> lower loss

    Negative margin:
        rejected is preferred -> higher loss
    """

    positive_losses, *_ = dpo_loss(
        torch.tensor([0.0]),
        torch.tensor([-2.0]),
        torch.tensor([0.0]),
        torch.tensor([0.0]),
        beta=0.1,
    )

    negative_losses, *_ = dpo_loss(
        torch.tensor([-2.0]),
        torch.tensor([0.0]),
        torch.tensor([0.0]),
        torch.tensor([0.0]),
        beta=0.1,
    )

    assert negative_losses.item() > positive_losses.item()


def test_beta_zero_gives_log_two():
    """
    beta = 0

    => beta * margin = 0

    => loss = log(2)
    """

    losses, *_ = dpo_loss(
        torch.tensor([10.0]),
        torch.tensor([-10.0]),
        torch.tensor([2.0]),
        torch.tensor([-2.0]),
        beta=0.0,
    )

    expected = torch.log(torch.tensor(2.0))

    assert torch.allclose(
        losses,
        expected.expand_as(losses),
    )


def test_huge_positive_margin_is_finite():
    losses, *_ = dpo_loss(
        torch.tensor([10000.0]),
        torch.tensor([-10000.0]),
        torch.tensor([0.0]),
        torch.tensor([0.0]),
        beta=1.0,
    )

    assert torch.isfinite(losses).all()


def test_huge_negative_margin_is_finite():
    losses, *_ = dpo_loss(
        torch.tensor([-10000.0]),
        torch.tensor([10000.0]),
        torch.tensor([0.0]),
        torch.tensor([0.0]),
        beta=1.0,
    )

    assert torch.isfinite(losses).all()


def test_rewards_are_detached():
    policy_chosen = torch.tensor(
        [1.0],
        requires_grad=True,
    )

    policy_rejected = torch.tensor(
        [0.0],
        requires_grad=True,
    )

    reference_chosen = torch.tensor([0.0])
    reference_rejected = torch.tensor([0.0])

    (
        losses,
        chosen_rewards,
        rejected_rewards,
        margin,
        reward_accuracy,
    ) = dpo_loss(
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
        beta=0.1,
    )

    assert not chosen_rewards.requires_grad
    assert not rejected_rewards.requires_grad


def test_reward_accuracy():
    (
        losses,
        chosen_rewards,
        rejected_rewards,
        margin,
        reward_accuracy,
    ) = dpo_loss(
        policy_chosen_logps=torch.tensor(
            [0.0, -1.0, -2.0]
        ),
        policy_rejected_logps=torch.tensor(
            [-1.0, 0.0, -3.0]
        ),
        reference_chosen_logps=torch.tensor(
            [0.0, 0.0, 0.0]
        ),
        reference_rejected_logps=torch.tensor(
            [0.0, 0.0, 0.0]
        ),
        beta=0.1,
    )

    # Example 1:
    # chosen reward = 0
    # rejected reward = -0.1
    # chosen wins
    #
    # Example 2:
    # chosen reward = -0.1
    # rejected reward = 0
    # rejected wins
    #
    # Example 3:
    # chosen reward = -0.2
    # rejected reward = -0.3
    # chosen wins
    #
    # Therefore:
    # 2 / 3 = 0.666...

    assert torch.allclose(
        reward_accuracy,
        torch.tensor(2 / 3),
    )


def test_gradient_flows_through_loss():
    policy_chosen = torch.tensor(
        [0.0],
        requires_grad=True,
    )

    policy_rejected = torch.tensor(
        [-1.0],
        requires_grad=True,
    )

    reference_chosen = torch.tensor([0.0])
    reference_rejected = torch.tensor([0.0])

    losses, *_ = dpo_loss(
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
        beta=0.1,
    )

    loss = losses.mean()
    loss.backward()

    assert policy_chosen.grad is not None
    assert policy_rejected.grad is not None

    assert torch.isfinite(
        policy_chosen.grad
    ).all()

    assert torch.isfinite(
        policy_rejected.grad
    ).all()