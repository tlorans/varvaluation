# Worked example

## Where this sits on the map

The three claims have already been illustrated on the preceding pages (product identity and the flat-rate gap, the joint VAR and its residual cloud, the two recursions and the rising spot curve). This page simply runs the whole path end-to-end on the same synthetic state and prints the terminal output you can reproduce offline.

```text
python examples/quickstart.py
```

---

## One laboratory, five numbers

```python
from varvaluation.news import simulate_return_var
from varvaluation import ExpectedReturnSpec, ValuationModel, estimate_var

df, spec = simulate_return_var(nobs=400, seed=7)
fit = estimate_var(df, spec)
xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(spec, {"b0": 0.01})
model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.04)
X = fit.X_lag[-1]
```

| Object | Value (seed 7) | Where it was introduced |
|---|---|---|
| Spectral radius of $\Phi$ | 0.409 | [One system](system.md) |
| $\mu_t(1)$ | 2.37 % | [The two recursions](curve.md) |
| $\mu_t(15)$ | 4.19 % | [The two recursions](curve.md) |
| Strip-sum value ($C=1$, $n=40$) | 24.07 | [The two recursions](curve.md) |
| Flat vs curve 15-year annuity | **+12.8 %** | [The problem](problem.md) |

Identity check that must hold:

```text
μ_t(1) = 2.3709%
α + ξ'X + X'ΛX = 2.3709%  ✓
```

---

## Full terminal sprint

```text
============================================================
Worked example — cash flows and discount rates from one VAR
============================================================

Mental map
  1. Product     value = E[discount path × cash flow]
  2. Covariance  Cov(∑g, ∑μ) enters the *price level*
  3. One VAR     both forecasts share (Φ, c, Σ)

────────────────────────────────────────────────────────────
Step 1 — Estimate one joint VAR
────────────────────────────────────────────────────────────
  state names     : ('ret', 'g')
  cash-flow row   : 'g'
  nobs            : 399
  spectral radius : 0.409  (< 1 ⇒ stationary)

  Φ (companion):
     ret  +0.295  +0.124
       g  +0.006  +0.402
  c (intercept)   : [0.0027 0.0015]
  Σ diagonal      : [3.59765e-04 8.85390e-05]

  Off-diagonal cells of Φ and Σ carry the covariance
  that the product identity requires.

────────────────────────────────────────────────────────────
Step 2 — Expected-return loadings (α, ξ, Λ)
────────────────────────────────────────────────────────────
  α               : 0.040
  ξ               : [1.   0.01]
  Λ               : [[0. 0.]
 [0. 0.]]
  μ_t = α + ξ'X + X'ΛX

  state X (last lag): [-0.0162 -0.0051]

────────────────────────────────────────────────────────────
Step 3 — Cash-flow recursion  E_t[C_{t+n}]/C_t
────────────────────────────────────────────────────────────
     n      E[C]/C
     1       0.999
     5       1.008
    10       1.021
    15       1.034

────────────────────────────────────────────────────────────
Step 4 — Spot curve μ_t(n)  (priced recursion / cash-flow)
────────────────────────────────────────────────────────────
  identity check: μ_t(1) = 2.3709%
                  α+ξ'X+X'ΛX = 2.3709%  ✓

     n    μ_t(n) %
     1        2.37
     5        3.78
    10        4.09
    15        4.19

  The curve is not flat. A single WACC at μ_t(1) misprices
  every longer strip.

────────────────────────────────────────────────────────────
Step 5 — Present value = sum of strips
────────────────────────────────────────────────────────────
  strip-sum value (C=1, n=40) : 24.07
  15-year unit annuity, curve : 11.0631
  15-year unit annuity, flat  : 12.4737
  flat vs curve               : +12.8%

  The gap is the object the handbook is about: how much a
  constant-rate DCF misses when expected returns move.

────────────────────────────────────────────────────────────
Diagnostic — news variance shares
────────────────────────────────────────────────────────────
  var(cash-flow news)     : 0.0002
  var(discount-rate news) : 0.0001

Done.
```

---

## Flat vs curve in isolation

```text
$ python examples/flat_vs_curve.py
Flat rate versus Ang–Liu curve (synthetic state, seed=7)
  μ_t(1)              2.37%
  μ_t(15)             4.19%
  15-year unit PV     curve=11.0631
  flat PV vs curve    +12.8%
```

---

## Minimal code path

```python
from varvaluation import ExpectedReturnSpec, ValuationModel, estimate_var
from varvaluation.news import simulate_return_var

df, spec = simulate_return_var(nobs=400, seed=7)
fit = estimate_var(df, spec)
xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(
    spec, {"b0": 0.01}
)
model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.04)
X = fit.X_lag[-1]

spots = model.spot_rates(X, n=15)
cf    = model.cashflow_expectation(X, n=15)
V     = model.value(X, C=1.0, n=40)
```

| Check | Why |
|---|---|
| $\mu_t(1)$ equals the one-period $\mu_t$ | Definition of the spot curve |
| $\Lambda = 0$ ⇒ $H(n)\equiv 0$ | Affine special case |
| Spectral radius of $\Phi$ $< 1$ | Otherwise `from_var` refuses |
| Tail of `value` uses $\mu_t(N)$ | Gordon only as special case 1 |

---

## How the pedagogical figures are built

The charts on [The problem](problem.md), [One system](system.md), and [The two recursions](curve.md) are generated offline from the **same** synthetic state (seed 7). From the package root:

```text
python examples/build_pedagogical_figures.py
```

Core of that script:

```python
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from varvaluation import ExpectedReturnSpec, ValuationModel, estimate_var
from varvaluation.news import simulate_return_var

OUT = Path("docs/assets/figures")

df, spec = simulate_return_var(nobs=400, seed=7)
fit = estimate_var(df, spec)
xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(
    spec, {"b0": 0.01}
)
model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.04)
X = fit.X_lag[-1]

rates = model.spot_rates(X, n=15)
cf    = model.cashflow_expectation(X, n=15)

# 1. Simulated paths of ret and g  → simulated_state.svg
# 2. Residual scatter (Σ)          → var_residuals.svg
# 3. Multi-step E_t[X_{t+h}]       → var_expectations.svg
# 4. Cash-flow ratio + spot curve  → recursions.svg
# 5. Flat vs curve discount factors → flat_vs_curve_factors.svg
```

Each figure is written as SVG under `docs/assets/figures/`. The documentation build runs this script before `mkdocs build`, so the images on the conceptual pages always match the numbers in the terminal sprint above.

---

## After this page

You should be able to:

1. Reproduce the five numbers in the table above with a single offline script.
2. Point back to the figure on each conceptual page that already showed the same object.
3. Rebuild the pedagogical figures from the same seed.
4. Switch the universe that enters $X_t$ without touching the recursions (next page).
