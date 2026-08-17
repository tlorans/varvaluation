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

## What to trust at the portfolio level

The paper’s portfolio path is the **perpetuity** (cash flow held at 1). Activating the cash-flow recursion on a near-unit-root $g$ equation (value portfolios) can explode the full PV. Check $\Phi_{g,g}$ and prefer `perpetuity` when that loading is near one.

## Channel isolation

A counterfactual, not news:

```python
from varvaluation import isolate_channels

iso = isolate_channels(model, X, shut=("Y",), on="cashflow")
iso = isolate_channels(model, X, shut=("Y",), on="discount")
iso = isolate_channels(model, X, shut=("Y",), on="both")  # unmodified
```

`on="cashflow"` zeros $\Phi[\text{cashflow}, s]$ for each shut name. `on="discount"` zeros those names in every *other* row of $\Phi$ and in $\Lambda$.
