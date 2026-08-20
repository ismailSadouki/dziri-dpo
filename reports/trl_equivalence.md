# TRL Numerical Equivalence

## Configuration

- beta: 0.1
- label_smoothing: 0.0
- loss type: sigmoid
- tolerance: 1e-5
- reference_free: false
- average_log_prob: false

## Synthetic Test

Compared:

- `scratch_dpo.losses.dpo_loss`
- TRL DPO loss implementation

All inputs were identical.

Synthetic test:
- loss max abs diff: 0.0
- chosen reward max abs diff: 0.0
- rejected reward max abs diff: 0.0

Real-batch test:

A real `Anthropic/hh-rlhf` preference example was passed through the
full tokenization → collation → policy/reference forward pipeline.

- loss max abs diff: 0.0
- chosen reward max abs diff: 0.0
- rejected reward max abs diff: 0.0

Tolerance:
```
atol=1e-5
```

Result:

```
11 test oassed.
```


The pure PyTorch DPO loss matches the TRL sigmoid DPO formulation
within the specified tolerance of 1e-5.

The maximum absolute difference between the scratch DPO loss and the
TRL-equivalent loss was:

$$
max∣ΔL∣=0.0
$$

which satisfies:

$$
0.0≤10^{-5}
$$



## Convention

Both implementations use the standard sigmoid DPO objective:

$$
\mathcal{L}
=
-\log\sigma
\left(
\beta
\left[
\left(
\log\pi_\theta(y_w \mid x)
-
\log\pi_{\mathrm{ref}}(y_w \mid x)
\right)
-
\left(
\log\pi_\theta(y_l \mid x)
-
\log\pi_{\mathrm{ref}}(y_l \mid x)
\right)
\right]
\right)
$$
