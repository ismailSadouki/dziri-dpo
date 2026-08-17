# DPO Loss Derivation

## 1. Objective

Direct Preference Optimization (DPO) learns a policy directly from preference pairs without training a separate reward model.

Each training example contains:

- $x$: prompt
- $y_w$: chosen / preferred response
- $y_l$: rejected response
- $\pi_\theta$: trainable policy
- $\pi_{\mathrm{ref}}$: frozen reference policy
- $\beta > 0$: DPO temperature / KL regularization parameter

The preference dataset is:

$$
\mathcal{D}
=
\{(x_i, y_{w,i}, y_{l,i})\}_{i=1}^{N}
$$

---

## 2. Sequence log-probabilities

For an autoregressive language model, the probability of a response is the product of the probabilities of its tokens:

$$
\pi_\theta(y|x)
=
\prod_{t=1}^{T}
\pi_\theta(y_t \mid x,y_{<t})
$$

Taking the logarithm converts the product into a sum:

$$
\log \pi_\theta(y|x)
=
\sum_{t=1}^{T}
\log
\pi_\theta(y_t \mid x,y_{<t})
$$

Our `get_batch_logps_from_logits()` function computes this quantity for every sequence in a batch.

The function returns:

$$
\mathbf{L} \in \mathbb{R}^{B}
$$

where $B$ is the batch size.

Therefore:

$$
L_i
=
\log \pi_\theta(y_i|x_i)
$$

Each position in the returned tensor corresponds to **one complete sequence**.

For example, if:

$$
B=4
$$

then:

$$
\mathbf{L}
=
\begin{bmatrix}
\log\pi(y_1|x_1) \\
\log\pi(y_2|x_2) \\
\log\pi(y_3|x_3) \\
\log\pi(y_4|x_4)
\end{bmatrix}
\in \mathbb{R}^{4}
$$

Only response tokens contribute to these values.

Prompt tokens have mask value $0$, and padding tokens have mask value $0$.

---

# 3. Policy and reference log-probabilities

For every preference pair, we calculate four sequence log-probabilities.

### Policy chosen

$$
\log \pi_\theta(y_w|x)
$$

Code variable:

~~~python
policy_chosen_logps
~~~

Shape:

$$
[B]
$$

---

### Policy rejected

$$
\log \pi_\theta(y_l|x)
$$

Code variable:

~~~python
policy_rejected_logps
~~~

Shape:

$$
[B]
$$

---

### Reference chosen

$$
\log \pi_{\mathrm{ref}}(y_w|x)
$$

Code variable:

~~~python
ref_chosen_logps
~~~

Shape:

$$
[B]
$$

---

### Reference rejected

$$
\log \pi_{\mathrm{ref}}(y_l|x)
$$

Code variable:

~~~python
ref_rejected_logps
~~~

Shape:

$$
[B]
$$

---

# 4. From DPO's reward parameterization

DPO starts from the KL-regularized reward objective.

The optimal policy can be expressed in terms of the reference policy and a reward function:

$$
r(x,y)
=
\beta
\log
\frac{\pi_\theta(y|x)}
{\pi_{\mathrm{ref}}(y|x)}
+
\beta \log Z(x)
$$

where $Z(x)$ is a normalization term that depends only on $x$.

For a preference comparison between two responses to the same prompt, the normalization terms cancel.

For the chosen response:

$$
r(x,y_w)
=
\beta
\log
\frac{\pi_\theta(y_w|x)}
{\pi_{\mathrm{ref}}(y_w|x)}
+
\beta\log Z(x)
$$

For the rejected response:

$$
r(x,y_l)
=
\beta
\log
\frac{\pi_\theta(y_l|x)}
{\pi_{\mathrm{ref}}(y_l|x)}
+
\beta\log Z(x)
$$

Subtracting:

$$
r(x,y_w)-r(x,y_l)
=
\beta
\left[
\log
\frac{\pi_\theta(y_w|x)}
{\pi_{\mathrm{ref}}(y_w|x)}
-
\log
\frac{\pi_\theta(y_l|x)}
{\pi_{\mathrm{ref}}(y_l|x)}
\right]
$$

The $\log Z(x)$ terms disappear.

---

# 5. Bradley-Terry preference model

DPO assumes preferences follow a Bradley-Terry model.

The probability that the chosen response is preferred over the rejected response is:

$$
P(y_w \succ y_l|x)
=
\sigma
\left(
r(x,y_w)-r(x,y_l)
\right)
$$

where:

$$
\sigma(z)
=
\frac{1}{1+e^{-z}}
$$

Substituting the DPO reward parameterization gives:

$$
P(y_w \succ y_l|x)
=
\sigma
\left(
\beta
\left[
\log
\frac{\pi_\theta(y_w|x)}
{\pi_{\mathrm{ref}}(y_w|x)}
-
\log
\frac{\pi_\theta(y_l|x)}
{\pi_{\mathrm{ref}}(y_l|x)}
\right]
\right)
$$

Using:

$$
\log\frac{a}{b}
=
\log a-\log b
$$

we obtain:

$$
P(y_w \succ y_l|x)
=
\sigma
\left(
\beta
\left[
\log\pi_\theta(y_w|x)
-
\log\pi_\theta(y_l|x)
-
\log\pi_{\mathrm{ref}}(y_w|x)
+
\log\pi_{\mathrm{ref}}(y_l|x)
\right]
\right)
$$

---

# 6. DPO logit

Define the policy preference difference:

$$
\Delta_\theta
=
\log\pi_\theta(y_w|x)
-
\log\pi_\theta(y_l|x)
$$

and the reference preference difference:

$$
\Delta_{\mathrm{ref}}
=
\log\pi_{\mathrm{ref}}(y_w|x)
-
\log\pi_{\mathrm{ref}}(y_l|x)
$$

Then the DPO logit becomes:

$$
z
=
\beta
\left(
\Delta_\theta-\Delta_{\mathrm{ref}}
\right)
$$

Expanding:

$$
z
=
\beta
\left[
\log\pi_\theta(y_w|x)
-
\log\pi_\theta(y_l|x)
-
\log\pi_{\mathrm{ref}}(y_w|x)
+
\log\pi_{\mathrm{ref}}(y_l|x)
\right]
$$

In code:

~~~python
chosen_reward = policy_chosen_logps - ref_chosen_logps
rejected_reward = policy_rejected_logps - ref_rejected_logps

logits = beta * (chosen_reward - rejected_reward)
~~~

Equivalently:

~~~python
logits = beta * (
    policy_chosen_logps
    - policy_rejected_logps
    - ref_chosen_logps
    + ref_rejected_logps
)
~~~

The shape is:

$$
z \in \mathbb{R}^{B}
$$

There is one DPO logit for each preference example.

---

# 7. DPO loss

The negative log-likelihood of the preferred response is:

$$
\mathcal{L}_{\mathrm{DPO}}
=
-\log
\sigma(z)
$$

Substituting the DPO logit:

$$
\mathcal{L}_{\mathrm{DPO}}
=
-\log
\sigma
\left(
\beta
\left[
\log\pi_\theta(y_w|x)
-
\log\pi_\theta(y_l|x)
-
\log\pi_{\mathrm{ref}}(y_w|x)
+
\log\pi_{\mathrm{ref}}(y_l|x)
\right]
\right)
$$

For a batch of $B$ examples, we usually take the mean:

$$
\mathcal{L}_{\mathrm{DPO}}
=
\frac{1}{B}
\sum_{i=1}^{B}
-\log
\sigma(z_i)
$$

---

# 8. Why `F.logsigmoid` is used

Instead of implementing:

~~~python
-log(torch.sigmoid(logits))
~~~

we use:

~~~python
-F.logsigmoid(logits)
~~~

because `logsigmoid` is implemented in a numerically stable way.

Therefore:

~~~python
losses = -torch.nn.functional.logsigmoid(logits)
loss = losses.mean()
~~~

The returned `losses` tensor has shape:

$$
[B]
$$

and the final scalar loss is:

$$
\mathcal{L}\in\mathbb{R}
$$

---

# 9. Equation-to-code mapping

| Mathematical quantity | Meaning | Code variable |
|---|---|---|
| $x$ | Prompt | `prompt` |
| $y_w$ | Chosen response | `chosen_*` |
| $y_l$ | Rejected response | `rejected_*` |
| $\pi_\theta$ | Trainable policy | `model` |
| $\pi_{\mathrm{ref}}$ | Reference policy | adapter-disabled `model` |
| $\log\pi_\theta(y_w|x)$ | Policy chosen log-probability | `policy_chosen_logps` |
| $\log\pi_\theta(y_l|x)$ | Policy rejected log-probability | `policy_rejected_logps` |
| $\log\pi_{\mathrm{ref}}(y_w|x)$ | Reference chosen log-probability | `ref_chosen_logps` |
| $\log\pi_{\mathrm{ref}}(y_l|x)$ | Reference rejected log-probability | `ref_rejected_logps` |
| $\Delta_\theta$ | Policy preference difference | `policy_chosen_logps - policy_rejected_logps` |
| $\Delta_{\mathrm{ref}}$ | Reference preference difference | `ref_chosen_logps - ref_rejected_logps` |
| $\beta$ | DPO scaling / KL regularization parameter | `beta` |
| $z$ | DPO logit | `logits` |
| $\sigma(z)$ | Probability chosen is preferred | `torch.sigmoid(logits)` |
| $-\log\sigma(z)$ | Per-example DPO loss | `-F.logsigmoid(logits)` |
| $\mathcal{L}$ | Batch loss | `losses.mean()` |

---

# 10. Important distinction: logits vs sequence log-probabilities

There are two different quantities in the implementation.

The language model produces token-level logits:

$$
\text{logits}
\in
\mathbb{R}^{B\times T\times V}
$$

where:

- $B$ = batch size
- $T$ = sequence length
- $V$ = vocabulary size

These are **not** the quantities used directly by the DPO loss.

`get_batch_logps_from_logits()` converts them into sequence log-probabilities:

$$
\log\pi(y|x)
\in
\mathbb{R}^{B}
$$

DPO operates on these sequence-level log-probabilities.

Therefore:

$$
[B,T,V]
\rightarrow
[B]
\rightarrow
\text{DPO loss}
$$

---

# 11. Sign sanity

The important quantity is:

$$
z
=
\beta
\left[
(\log\pi_\theta(y_w|x)-\log\pi_\theta(y_l|x))
-
(\log\pi_{\mathrm{ref}}(y_w|x)-\log\pi_{\mathrm{ref}}(y_l|x))
\right]
$$

Suppose the policy increasingly favors the chosen response relative to the rejected response.

Then:

$$
\log\pi_\theta(y_w|x)
-
\log\pi_\theta(y_l|x)
$$

becomes larger.

Therefore $z$ becomes larger.

Since:

$$
\sigma(z)
\rightarrow 1
\quad\text{as}\quad
z\rightarrow+\infty
$$

the loss:

$$
-\log\sigma(z)
$$

becomes smaller.

Therefore:

> A larger chosen-vs-rejected advantage under the policy should produce a lower DPO loss.

This is the primary sign sanity check.

---

# 12. What happens when the chosen and rejected responses are identical?

Suppose:

$$
y_w=y_l
$$

Then:

$$
\log\pi_\theta(y_w|x)
=
\log\pi_\theta(y_l|x)
$$

and:

$$
\log\pi_{\mathrm{ref}}(y_w|x)
=
\log\pi_{\mathrm{ref}}(y_l|x)
$$

Therefore:

$$
z=0
$$

The loss becomes:

$$
-\log\sigma(0)
$$

Since:

$$
\sigma(0)=\frac{1}{2}
$$

we obtain:

$$
\mathcal{L}
=
-\log\left(\frac{1}{2}\right)
=
\log 2
$$

Therefore the expected loss for an identical chosen/rejected pair is:

$$
\boxed{\mathcal{L}=\log 2}
$$

Numerically:

$$
\log 2\approx0.693147
$$

This is an important unit-test sanity check.

---

# 13. What happens when $\beta=0$?

The DPO logit is:

$$
z
=
\beta
\left(
\Delta_\theta-\Delta_{\mathrm{ref}}
\right)
$$

If:

$$
\beta=0
$$

then:

$$
z=0
$$

regardless of the policy or reference log-probabilities.

Therefore:

$$
\mathcal{L}
=
-\log\sigma(0)
=
\log2
$$

So:

$$
\boxed{\beta=0\Rightarrow\mathcal{L}=\log2}
$$

This is another useful sanity test.

---

# 14. Interpretation of $\beta$

$\beta$ controls how strongly the policy's preference difference is scaled relative to the reference policy.

The DPO logit is:

$$
z=\beta(\Delta_\theta-\Delta_{\mathrm{ref}})
$$

A larger $\beta$ magnifies differences between the policy and reference preference margins.

A smaller $\beta$ makes the DPO logit less sensitive to those differences.

In the limit:

$$
\beta\rightarrow0
$$

we get:

$$
z\rightarrow0
$$

and therefore:

$$
\mathcal{L}\rightarrow\log2
$$

The exact interpretation should not be reduced to simply "beta is the learning rate." It is a parameter in the DPO objective controlling the scale of the policy/reference log-ratio preference signal.

---

# 15. Final implementation form

The complete DPO computation can be represented as:

$$
\Delta_\theta
=
\log\pi_\theta(y_w|x)
-
\log\pi_\theta(y_l|x)
$$

$$
\Delta_{\mathrm{ref}}
=
\log\pi_{\mathrm{ref}}(y_w|x)
-
\log\pi_{\mathrm{ref}}(y_l|x)
$$

$$
z
=
\beta
\left(
\Delta_\theta-\Delta_{\mathrm{ref}}
\right)
$$

$$
\mathcal{L}
=
-\log\sigma(z)
$$

In code:

~~~python
chosen_reward = policy_chosen_logps - ref_chosen_logps
rejected_reward = policy_rejected_logps - ref_rejected_logps

logits = beta * (chosen_reward - rejected_reward)

losses = -torch.nn.functional.logsigmoid(logits)

loss = losses.mean()
~~~

Shapes:

$$
\texttt{policy\_chosen\_logps}
\in\mathbb{R}^{B}
$$

$$
\texttt{policy\_rejected\_logps}
\in\mathbb{R}^{B}
$$

$$
\texttt{ref\_chosen\_logps}
\in\mathbb{R}^{B}
$$

$$
\texttt{ref\_rejected\_logps}
\in\mathbb{R}^{B}
$$

Therefore:

$$
\texttt{logits}\in\mathbb{R}^{B}
$$

$$
\texttt{losses}\in\mathbb{R}^{B}
$$

and:

$$
\texttt{loss}\in\mathbb{R}
$$

---
