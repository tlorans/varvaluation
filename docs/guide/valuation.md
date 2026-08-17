# Valuation

`AngLiuModel` is the quadratic-Gaussian engine of Ang and Liu (2004). Given a fitted VAR and

$$
\mu_t = \alpha + \xi' X_t + X_t' \Lambda X_t,
$$

it is exact. The cash-flow basis vector is `spec.cashflow`, not slot 0.

```python
from varvaluation import AngLiuModel

model = AngLiuModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=alpha)
rates = model.spot_rates(X, n=30)          # μ_t(1), …, μ_t(30)
cf = model.cashflow_expectation(X, n=30)   # E_t[C_{t+n}] / C_t
value = model.value(X, C=1.0, n=80)        # both recursions + tail
perp = model.perpetuity(X, n=80)           # unit cash flow
```

`from_var` refuses a companion with spectral radius $\ge 1$ (`NonStationaryVARError`). Negative *short* rates are allowed. A non-positive *terminal* rate raises `PerpetuityDivergesError`.

If $\Lambda = 0$, $H(n)\equiv 0$ and the solution is exponential-affine (the course playground). Same class; no second solver.

## The numerator: expected cash flows

Ang and Liu (2004) **carry** a cash-flow recursion and **do not use it**. They value a unit perpetuity: $\mathbb{E}_t[D_{t+n}] = 1$ at every horizon. All reported variation is then the discount curve. That is `model.perpetuity(X)`.

The course and this library activate the recursion they left idle. Cash flows are written in growth form. Let $g$ be the named cash-flow variable (`spec.cashflow`: log dividend growth at the portfolio, log ROE at the firm):

$$
C_{t+n} = C_t \exp\!\Bigl(\sum_{i=1}^{n} g_{t+i}\Bigr).
$$

Because $g$ is the corresponding row of the Gaussian VAR, the expectation has a closed form. It is **affine** in the state (no discounting enters):

$$
\frac{\mathbb{E}_t[C_{t+n}]}{C_t}
= \exp\!\bigl(\bar a(n) + \bar b(n)'X_t\bigr).
$$

That is `model.cashflow_expectation(X, n)`. The coefficients start at

$$
\bar a(1) = e_1'c + \tfrac12 e_1'\Sigma e_1, \qquad
\bar b(1) = \Phi'e_1
$$

and iterate

$$
\bar a(n+1) = \bar a(n) + e_1'c + \bar b(n)'c
  + \tfrac12(e_1+\bar b(n))'\Sigma(e_1+\bar b(n)),
$$

$$
\bar b(n+1) = \Phi'(e_1 + \bar b(n)).
$$

`e_1` is the unit vector for `spec.cashflow`, not “column 0”. $\bar b(n)$ accumulates the forecast of growth along the path $X$ is expected to travel. The $\tfrac12$ terms are Jensen: $E[e^{S}] = \exp(E[S]+\tfrac12\mathrm{Var}[S])$.

`model.value(X, C)` pairs the two recursions:

$$
V_t = \sum_{n=1}^{N}
  C_t\cdot\frac{\mathbb{E}_t[C_{t+n}]/C_t}{\exp\!\bigl(n\,\mu_t(n)\bigr)}
  + \text{tail at }\mu_t(N).
$$

Both sides are functions of the **same** $X_t$ and the **same** $(\Phi,c,\Sigma)$. You do not paste a spreadsheet of cash flows into the numerator. Expected cash flow is a modelling object, as the course says at Step 02.

If a named state does not load on the cash-flow equation ($\Phi[\texttt{cashflow}, s] = 0$), it does not move the numerator. `isolate_channels(..., on="cashflow")` zeros those loadings on purpose.

When $\Phi_{g,g}$ is near one (value portfolios), $\bar b(n)$ keeps accumulating growth that barely mean-reverts and the full PV explodes. That is why Ang and Liu held the numerator at 1, and why `perpetuity` is the object to trust at the portfolio level. The recursion becomes usable when cash-flow growth is estimated at the **firm**, where $g$ is replaced by ROE and mean reversion is stronger.

![Spot discount curves](../assets/figures/spot_curves.png)
<p class="figure-caption">Term structure of $\mu_t(n)$ for growth (D1), mid (D6), and value (D10) at the last state in the 1965–2024 sample.</p>

![Variance decomposition, D10](../assets/figures/variance_decomp_d10.png)
<p class="figure-caption">Share of spot-rate variance by state variable, value decile. On this sample $\mathit{cay}$ and $\beta$ dominate; cash-flow growth $g$ is negligible in the <em>discount curve</em>.</p>

## What to trust at the portfolio level

The paper’s portfolio path is the **perpetuity** (cash flow held at 1). Activating the cash-flow recursion on a near-unit-root $g$ equation (value portfolios) can explode the full PV. Check $\Phi_{g,g}$ and prefer `perpetuity` when that loading is near one.

## Channel isolation

A counterfactual, not news:

```python
from varvaluation import isolate_channels

iso = isolate_channels(model, X, shut=("cay",), on="cashflow")
iso = isolate_channels(model, X, shut=("cay",), on="discount")
iso = isolate_channels(model, X, shut=("cay",), on="both")  # unmodified
```

`on="cashflow"` zeros $\Phi[\text{cashflow}, s]$ for each shut name. `on="discount"` zeros those names in every *other* row of $\Phi$ and in $\Lambda$.
