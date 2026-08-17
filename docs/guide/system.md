# One system

[Ang and Liu (2004)](../references.md#ang-liu-2004) summarise cash flows
and expected returns by a state vector $X_t$. In the leading case

$$
X_t = (g_t,\; \beta_t,\; z_t')',
$$

where $g_t$ is cash-flow growth, $\beta_t$ is the conditional beta, and
$z_t$ holds instruments that predict growth, betas, or the market
premium (short rate, $\mathit{cay}$, inflation, …).

A VAR(1) is the law of motion:

$$
X_{t+1} = c + \Phi X_t + u_{t+1},
\qquad
u \sim N(0,\Sigma).
$$

Nothing in that system is labelled “numerator” or “denominator”.
The two readings come from **which coordinates you ask about**, and
from how the one-period expected return is written as a function of
$X_t$.

## What a VAR is, concretely

With two variables $x$ and $y$, a VAR(1) is literally two regressions:

$$
\begin{aligned}
x_{t+1} &= a_1 + b_{11}x_t + b_{12}y_t + u_{t+1}, \\
y_{t+1} &= a_2 + b_{21}x_t + b_{22}y_t + v_{t+1}.
\end{aligned}
$$

Stacked into matrices: $X_{t+1} = c + \Phi X_t + \varepsilon_{t+1}$.
Three named objects, each with a job:

| Object | Job |
|---|---|
| $c$ | Pulls everything toward long-run averages |
| $\Phi$ | Persistence: diagonal = own memory; off-diagonal = cross-forecasts |
| $\Sigma$ | Shock covariance: which variables get hit together |

Forecasting is recursive bookkeeping. One step ahead:
$E_t[X_{t+1}] = c + \Phi X_t$. By $j$ steps, today's state dies out at
the speed of $\Phi^j$. The unconditional mean is $(I-\Phi)^{-1}c$,
provided every eigenvalue of $\Phi$ lies inside the unit circle.

!!! note "Why a VAR is the right tool here"
    1. **Jointness by construction.** One $\Sigma$ generates shocks to
       cash flows *and* expected returns together. The covariance the
       price needs cannot be set to zero by accident.
    2. **Mean reversion for free.** A stable $\Phi$ delivers rates that
       glide back to their long-run mean. The flat-forever discount rate
       is the special case $\Phi = 0$.
    3. **Predictability is testable.** Coefficients of $\Phi$ have
       standard errors; cross-forecasts can be rejected.
    4. **Gaussian linearity makes the price closed-form.** Linear
       dynamics + normal shocks ⇒ every cumulated sum is conditionally
       normal ⇒ $E[e^{\cdot}]$ is analytic.

## Cash-flow growth

Write cash flows in growth form:

$$
g_{t+i} = \log\frac{C_{t+i}}{C_{t+i-1}},
\qquad
C_{t+n} = C_t\,\exp\!\Bigl(\sum_{i=1}^{n} g_{t+i}\Bigr).
$$

Then

$$
\frac{E_t[C_{t+n}]}{C_t}
  = E_t\!\left[\exp\!\Bigl(\sum_{i=1}^{n} g_{t+i}\Bigr)\right].
$$

This is **not** $\exp(E_t[\sum g])$. Because $g$ is random, Jensen
adds a variance term. Under the Gaussian VAR that expectation is
exponential-affine in today’s state — the **cash-flow recursion** of
the next page.

$g_t$ is one coordinate of $X_t$ (or an affine function of $X_t$).
Every other coordinate can forecast it through $\Phi$.

## Expected returns

The one-period expected return is a conditional CAPM:

$$
\mu_t = \alpha + r_t + \beta_t\,\lambda_t.
$$

When $\beta_t$ and $\lambda_t$ both move with $X_t$, the product
$\beta_t\lambda_t$ is **quadratic** in the state:

$$
\mu_t = \alpha + \xi'X_t + X_t'\Lambda X_t.
$$

If either beta or the premium is constant, $\Lambda = 0$ and $\mu_t$
is affine — the earlier affine present-value class. Letting **both**
move at once is what the $H(n)$ recursion in the next page is for.

$r_t$ (the short rate) may sit inside $X_t$, or a full Treasury curve
may be kept outside the VAR and supplied as data. The package supports
both.

## Why they share the VAR

The cash-flow reading uses the $g$ row of $\Phi$. The discount-rate
reading uses the rows that drive $\beta$ and $\lambda$. Off-diagonal
cells are the covariances: how a shock to the premium changes expected
growth, how a shock to growth changes expected beta. Those cells are
identified only if the regressions are estimated **together**.

Estimate cash in one model and the rate in another, and those cells are
gone. The product $E[e^{-\sum\mu}C]$ is then missing its covariance.

## In code

```python
from varvaluation import StateSpec, estimate_var

# name the coordinates of X_t; mark which row is cash-flow growth
spec = StateSpec(names=("g", "beta", "mrp", ...), cashflow="g", horizon=1)
fit = estimate_var(state, spec)   # → Φ, c, Σ
```

The next page turns $(\Phi, c, \Sigma)$ and $(\alpha, \xi, \Lambda)$ into
the two Ang–Liu recursions and the spot curve $\mu_t(n)$.
