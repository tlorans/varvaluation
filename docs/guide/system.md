# One system, two readings

The state is four numbers:

$$
x_t' = \bigl(\mathrm{ROE}_t,\; g_t,\; \beta_t,\; \mathrm{MRP}_t\bigr).
$$

A VAR(1) is four ordinary regressions run at the same time — each
variable on a lag of all four:

$$
x_{t+1} = c + \Phi x_t + \varepsilon_{t+1},
\qquad
\varepsilon \sim N(0,\Sigma).
$$

Nothing in that system is labelled “numerator” or “denominator”.
The two readings come from **which coordinates you ask about**.

## What a VAR is, concretely

With two variables $x$ and $y$, a VAR(1) is literally two regressions:

$$
\begin{aligned}
x_{t+1} &= a_1 + b_{11}x_t + b_{12}y_t + u_{t+1}, \\
y_{t+1} &= a_2 + b_{21}x_t + b_{22}y_t + v_{t+1}.
\end{aligned}
$$

Stacked into matrices, that is $X_{t+1} = c + \Phi X_t + \varepsilon_{t+1}$.
Three named objects, each with a job:

| Object | Job |
|---|---|
| $c$ | Pulls everything toward long-run averages |
| $\Phi$ | Persistence: diagonal = own memory; off-diagonal = cross-forecasts |
| $\Sigma$ | Shock covariance: which variables get hit together |

Forecasting is recursive bookkeeping. One step ahead:
$E_t[X_{t+1}] = c + \Phi X_t$. Two steps: plug that back in.
By $j$ steps, today's state dies out at the speed of $\Phi^j$.
The unconditional mean is $(I-\Phi)^{-1}c$, provided the eigenvalues
of $\Phi$ lie inside the unit circle.

!!! note "Why a VAR is the right tool here"
    Four requirements, four matches:

    1. **Jointness by construction.** One $\Sigma$ generates shocks to
       cash flows *and* expected returns together. The covariance the
       price needs cannot be set to zero by accident.
    2. **Mean reversion for free.** A stable $\Phi$ delivers rates that
       glide back to their long-run mean. The flat-forever discount rate
       is the special case $\Phi = 0$.
    3. **Predictability is testable.** Do premiums forecast growth?
       Does ROE forecast beta? These are coefficients of $\Phi$, with
       standard errors.
    4. **Gaussian linearity makes the price closed-form.** Linear
       dynamics + normal shocks ⇒ every cumulated sum is conditionally
       normal ⇒ $E[e^{\cdot}]$ is a two-line formula.

## Reading 1 — cash, from clean surplus

[Feltham and Ohlson (1995)](../references.md#feltham-ohlson-1995)
require that cash equal earnings minus the change in book. In logs,

$$
g_{t+1} = \ln(B_{t+1}/B_t),
\qquad
\mathrm{ROE}_{t+1} = \ln\bigl(1 + \mathrm{NI}_{t+1}/B_t\bigr),
$$

and the identity is

$$
C_{t+1} = B_t\bigl(e^{\mathrm{ROE}_{t+1}} - e^{g_{t+1}}\bigr).
$$

A cash flow $\tau$ years out is the same identity at a future book:

$$
\frac{C_{t+\tau}}{B_t}
= \exp\bigl(g_{t+1}+\cdots+g_{t+\tau-1}+\mathrm{ROE}_{t+\tau}\bigr)
- \exp\bigl(g_{t+1}+\cdots+g_{t+\tau}\bigr).
$$

Both exponentials are functions of $x$. Their expectations are closed
form because $x$ is Gaussian. That is `expected_cashflow`.

Profitability (`roe`) is a *level*. Book growth (`g`) is a *growth
rate*. Neither one alone is the cash-flow path. The **difference** is.

## Reading 2 — the required return, from the CCAPM

The one-period equilibrium rate is

$$
\mu_t = R_{f,t} + \beta_t \cdot \mathrm{MRP}_t.
$$

$\beta_t$ and $\mathrm{MRP}_t$ are the other two coordinates of $x$.
$R_{f,t}$ is **not**. The paper keeps the Treasury curve $y(\tau)_t$
outside the VAR. That is a modelling choice: it drops many parameters
and lets $y(\tau)$ come from FRED. The risk in $\mu_t$ is the
quadratic form $x_t'\Theta x_t$, with $\Theta$ zero except the
symmetric $\beta$–MRP cell.

Year one's cost of capital is then just

$$
\rho(1)_t = y(1)_t + \beta_t \cdot \mathrm{MRP}_t.
$$

That is `flat_ccapm_rate`. Years further out are **not** this number,
because $\beta$ and the premium mean-revert and because cash and the
rate move together.

## Why they have to share the VAR

The first reading uses the ROE and $g$ equations of $\Phi$. The second
uses the $\beta$ and MRP equations. Off-diagonal cells of $\Phi$ are
the covariances: how a shock to the premium today changes expected book
growth next year, how a shock to ROE changes expected beta. Those cells
are identified only if the four regressions are estimated **together**.

Estimate cash in one model and the rate in another, and those cells are
gone. The product $E[e^{-\sum\mu}C]$ is then missing its covariance.

## The four names in code

```python
from varvaluation import paper_state_spec

spec = paper_state_spec()          # names = (roe, g, beta, mrp)
# quarterly observations of annualized variables;
# horizon=4 makes each VAR step one year.
```

`ResidualIncome(roe="roe", book_growth="g")` is the first reading.
`CCAPMSpec(beta="beta", premium="mrp")` is the second.
The next page turns a fitted `spec` into $\rho(\tau)$.
