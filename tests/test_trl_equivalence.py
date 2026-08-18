from __future__ import annotations

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))



import torch
import torch.nn.functional as F

from scratch_dpo.losses import dpo_loss

BETA = 0.1
ATOL = 1e-5


def make_inputs():
    """
    Synthetic sequence log-probabilities.

    Every tensor has shape [B].
    """

    policy_chosen = torch.tensor(
        [-2.0, -3.0, -1.5],
        dtype=torch.float32,
    )

    policy_rejected = torch.tensor(
        [-3.0, -2.5, -2.0],
        dtype=torch.float32,
    )

    reference_chosen = torch.tensor(
        [-2.2, -3.2, -1.8],
        dtype=torch.float32,
    )

    reference_rejected = torch.tensor(
        [-3.1, -2.7, -2.2],
        dtype=torch.float32,
    )
    
    return (
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
    )



def test_dpo_loss_has_expected_shapes():
    (
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
    ) = make_inputs()
    loss, chosen_rewards, rejected_rewards, margin, reward_accuracy = dpo_loss(
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
        beta=BETA,
    )

    assert loss.shape == (3,)
    assert chosen_rewards.shape == (3,)
    assert rejected_rewards.shape == (3,)
    assert margin.shape == (3,)

    assert reward_accuracy.ndim == 0


def test_dpo_loss_is_finite():
    inputs = make_inputs()

    loss, chosen_rewards, rejected_rewards, margin, reward_accuracy = dpo_loss(
        *inputs,
        beta=BETA,
    )

    assert torch.isfinite(loss).all()
    assert torch.isfinite(chosen_rewards).all()
    assert torch.isfinite(rejected_rewards).all()
    assert torch.isfinite(margin).all()
    assert torch.isfinite(reward_accuracy)


def test_manual_dpo_calculation():
    (
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
    ) = make_inputs()

    loss, _, _, _, _ = dpo_loss(
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
        beta=BETA,
    )

    expected_logits = BETA * (
        (policy_chosen - reference_chosen)
        - (policy_rejected - reference_rejected)
    )

    expected_loss = -torch.nn.functional.logsigmoid(
        expected_logits
    )

    assert torch.allclose(
        loss,
        expected_loss,
        atol=ATOL,
    )


def test_identical_pair_gives_log2():
    """
    If chosen and rejected have identical policy/reference
    differences, the DPO margin is zero.

    Therefore:

        -log(sigmoid(0)) = log(2)
    """

    policy_chosen = torch.tensor([-2.0])
    policy_rejected = torch.tensor([-2.0])

    reference_chosen = torch.tensor([-2.5])
    reference_rejected = torch.tensor([-2.5])

    loss, _, _, margin, _ = dpo_loss(
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
        beta=BETA,
    )

    assert torch.allclose(
        margin,
        torch.zeros(1),
        atol=ATOL,
    )

    assert torch.allclose(
        loss,
        torch.tensor([torch.log(torch.tensor(2.0))]),
        atol=ATOL,
    )


def test_reversed_preference_has_higher_loss():
    """
    If the policy prefers the rejected response,
    the DPO margin becomes negative and the loss increases.
    """

    policy_chosen = torch.tensor([-3.0])
    policy_rejected = torch.tensor([-2.0])

    reference_chosen = torch.tensor([-2.0])
    reference_rejected = torch.tensor([-3.0])

    loss, _, _, margin, reward_accuracy = dpo_loss(
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
        beta=BETA,
    )


    assert margin.item() < 0
    assert reward_accuracy.item() == 0.0

    assert loss.item() > torch.log(
        torch.tensor(2.0)
    ).item()




def test_huge_positive_margin_is_finite():
    policy_chosen = torch.tensor([1000.0])
    policy_rejected = torch.tensor([-1000.0])

    reference_chosen = torch.tensor([0.0])
    reference_rejected = torch.tensor([0.0])

    loss, _, _, _, _ = dpo_loss(
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
        beta=BETA,
    )

    assert torch.isfinite(loss).all()

def test_huge_negative_margin_is_finite():
    policy_chosen = torch.tensor([-1000.0])
    policy_rejected = torch.tensor([1000.0])

    reference_chosen = torch.tensor([0.0])
    reference_rejected = torch.tensor([0.0])

    loss, _, _, _, _ = dpo_loss(
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
        beta=BETA,
    )

    assert torch.isfinite(loss).all()



def test_rewards_are_detached():
    policy_chosen = torch.tensor(
        [-2.0],
        requires_grad=True,
    )

    policy_rejected = torch.tensor(
        [-3.0],
        requires_grad=True,
    )

    reference_chosen = torch.tensor(
        [-2.5],
        requires_grad=True,
    )

    reference_rejected = torch.tensor(
        [-3.5],
        requires_grad=True,
    )

    _, chosen_rewards, rejected_rewards, _, _ = dpo_loss(
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
        beta=BETA,
    )
    assert not chosen_rewards.requires_grad
    assert not rejected_rewards.requires_grad


def test_beta_zero_gives_log2():
    policy_chosen = torch.tensor([-2.0])
    policy_rejected = torch.tensor([-1.0])

    reference_chosen = torch.tensor([-3.0])
    reference_rejected = torch.tensor([-4.0])

    loss, _, _, margin, _ = dpo_loss(
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
        beta=0.0,
    )

    # beta * margin = 0
    # -log(sigmoid(0)) = log(2)

    assert torch.allclose(
        margin,
        torch.tensor([-2.0]),
        atol=ATOL,
    )

    assert torch.allclose(
        loss,
        torch.tensor([torch.log(torch.tensor(2.0))]),
        atol=ATOL,
    )


def test_gradient_flows_through_policy():
    policy_chosen = torch.tensor(
        [-2.0],
        requires_grad=True,
    )

    policy_rejected = torch.tensor(
        [-3.0],
        requires_grad=True,
    )

    reference_chosen = torch.tensor(
        [-2.5],
        requires_grad=False,
    )

    reference_rejected = torch.tensor(
        [-3.5],
        requires_grad=False,
    )

    loss, _, _, _, _ = dpo_loss(
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
        beta=BETA,
    )

    loss.mean().backward()

    assert policy_chosen.grad is not None
    assert policy_rejected.grad is not None

    assert torch.isfinite(policy_chosen.grad).all()
    assert torch.isfinite(policy_rejected.grad).all()

    assert reference_chosen.grad is None
    assert reference_rejected.grad is None




def trl_dpo_loss(
    policy_chosen_logps,
    policy_rejected_logps,
    reference_chosen_logps,
    reference_rejected_logps,
    beta,
):
    """
    Reproduce TRL's standard sigmoid DPO loss.

    This is NOT our implementation.
    It is the reference/oracle implementation used
    only for numerical verification.
    """

    chosen_logratios = (
        policy_chosen_logps
        - reference_chosen_logps
    )

    rejected_logratios = (
        policy_rejected_logps
        - reference_rejected_logps
    )

    delta = (
        chosen_logratios
        - rejected_logratios
    )

    losses = -F.logsigmoid(
        beta * delta
    )

    chosen_rewards = (
        beta * chosen_logratios
    ).detach()

    rejected_rewards = (
        beta * rejected_logratios
    ).detach()

    return (
        losses,
        chosen_rewards,
        rejected_rewards,
    )


def test_dpo_loss_matches_trl():
    (
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
    ) = make_inputs()

    # ---------------------------------------------
    # Our implementation
    # ---------------------------------------------

    (
        our_loss,
        our_chosen_rewards,
        our_rejected_rewards,
        _,
        _,
    ) = dpo_loss(
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
        beta=BETA,
    )

    # ---------------------------------------------
    # TRL oracle
    # ---------------------------------------------

    (
        trl_loss,
        trl_chosen_rewards,
        trl_rejected_rewards,
    ) = trl_dpo_loss(
        policy_chosen,
        policy_rejected,
        reference_chosen,
        reference_rejected,
        beta=BETA,
    )

    # ---------------------------------------------
    # Compare
    # ---------------------------------------------

    loss_diff = torch.max(
        torch.abs(our_loss - trl_loss)
    )

    chosen_reward_diff = torch.max(
        torch.abs(
            our_chosen_rewards
            - trl_chosen_rewards
        )
    )

    rejected_reward_diff = torch.max(
        torch.abs(
            our_rejected_rewards
            - trl_rejected_rewards
        )
    )


    print(f"loss max_abs_diff: {loss_diff.item():.10e}")
    print(
        f"chosen reward max_abs_diff: "
        f"{chosen_reward_diff.item():.10e}"
    )
    print(
        f"rejected reward max_abs_diff: "
        f"{rejected_reward_diff.item():.10e}"
    )



    assert loss_diff <= ATOL
    assert chosen_reward_diff <= ATOL
    assert rejected_reward_diff <= ATOL
    torch.testing.assert_close(
        our_loss,
        trl_loss,
        atol=ATOL,
        rtol=0.0,
    )