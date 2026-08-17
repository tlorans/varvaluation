# Worked example

## Where this sits on the map

All three steps are already in place. This page runs them end-to-end on a synthetic state: estimate the joint VAR, apply the two Ang–Liu recursions, and read the spot curve $\mu_t(n)$.

```text
python examples/quickstart.py
```

---

## Full offline sprint

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

## What each step is doing

| Step | Object | Map claim |
|---|---|---|
| 1 | $\Phi$, $c$, $\Sigma$ | **One VAR** — joint law of motion |
| 2 | $\alpha$, $\xi$, $\Lambda$ | maps the state into $\mu_t$ |
| 3 | $\bar a(n),\bar b(n)$ | cash side of the **product** |
| 4 | $a(n),b(n),H(n)\to\mu_t(n)$ | priced side; **covariance** is inside |
| 5 | strip sum | $E[\text{product}]$ as a number |

Identity that must hold: $\mu_t(1)$ equals the one-period $\mu_t = \alpha + \xi'X + X'\Lambda X$. The script prints the check.

---

## Flat vs curve in isolation

```text
$ python examples/flat_vs_curve.py
Flat rate versus Ang–Liu curve (synthetic state, seed=7)
  μ_t(1)              2.37%
  μ_t(15)             4.19%
  15-year unit PV     curve=11.0631
  flat PV vs curve    +12.8%

  The gap is the covariance channel: a flat rate locked at
  μ_t(1) ignores the term structure that the joint VAR produces.
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

spots = model.spot_rates(X, n=15)            # μ_t(n)
cf    = model.cashflow_expectation(X, n=15)  # cash-flow recursion
V     = model.value(X, C=1.0, n=40)          # sum of strips + tail
```

Checks that should hold inside the model class:

| Check | Why |
|---|---|
| $\mu_t(1)$ equals the one-period $\mu_t$ | Definition of the spot curve |
| $\Lambda = 0$ ⇒ $H(n)\equiv 0$ | Affine special case |
| Spectral radius of $\Phi$ $< 1$ | Otherwise `from_var` refuses |
| Tail of `value` uses $\mu_t(N)$, not a hand-set $(r,g)$ | Gordon only as special case 1 |

---

## Synthetic industry curves

```text
$ python examples/reproduce_glz2020.py
Synthetic industry state (offline). Same API as the paper.

# All insurers
   τ      ρ(τ)      y(τ)     CCAPM      CAPM
   1      9.26      5.50      9.26      9.28
   5      9.25      5.50      9.26      9.28
  10      9.24      5.50      9.26      9.28
  …
  30      9.23      5.50      9.26      9.28

# Table 4  30-year $1 annuity at the long-run mean
  term structure 9.69
  CCAPM          9.67  discrepancy -0.17%
  CAPM           9.65  discrepancy -0.37%
```

(Other portfolios — P/C, Life, Health, ex-insurers — print the same blocks with their own $\beta$.)

The synthetic state is deliberately mild: the curve is almost flat and the valuation discrepancy is small. On real data the slope and the gap grow.

---

## Live data

```text
uv add "varvaluation[data,wrds]"
# WRDS_USERNAME / WRDS_PASSWORD in the environment or a .env file
uv run python examples/reproduce_glz2020.py --wrds
```

Compustat quarterly, CRSP daily for rolling betas, FRED Treasuries and credit spreads, Ken French factors. Queries cache under `~/.cache/varvaluation`.

On real portfolios the spot curves separate by style:

![Spot curves across BM deciles](../assets/figures/spot_curves.png)

---

## Reading the output

- **`cashflow_expectation(X, n)`** — the cash-flow recursion: $E_t[C_{t+k}]/C_t$ for $k=1,\ldots,n$.
- **`spot_rates(X, n)`** — $\mu_t(1),\ldots,\mu_t(n)$.
- **`value(X, C)`** — sum of strips under both recursions, plus the geometric tail at $\mu_t(N)$.

Compare the curve to a flat CAPM rate at the same date. The gap *is* the object Ang and Liu quantify: how much a constant-rate DCF misses when expected returns move.

---

## After this page

You should be able to:

1. Run `examples/quickstart.py` and obtain a spot curve, a cash-flow path, and a strip-sum value.
2. Verify that $\mu_t(1)$ matches $\alpha + \xi'X + X'\Lambda X$.
3. Explain why the flat-vs-curve gap is precisely the covariance channel the handbook is about.

The next page changes only the universe that is averaged into $X_t$.
