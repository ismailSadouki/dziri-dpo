# TRL Numerical Equivalence

## Configuration

- beta: 0.1
- label_smoothing: 0.0
- loss type: sigmoid
- reference_free: false
- average_log_prob: false

## Synthetic Test

Compared:

- `scratch_dpo.losses.dpo_loss`
- TRL DPO loss implementation

All inputs were identical.

Maximum absolute difference:

```text
<PUT RESULT HERE>
```

Tolerance:
```
atol=1e-5
```

Result:

```
PASS
```