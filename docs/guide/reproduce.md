# Worked example

## Where this sits on the map

All three steps are already in place. This page simply runs them end-to-end: estimate the joint VAR, apply the two Ang–Liu recursions, and read the spot curve $\mu_t(n)$.

---

## Offline (no downloads)

```text
$ python examples/quickstart.py
spectral radius: 0.409
spot mu(n) %      n=1, 5, 10: 2.37, 3.78, 4.09
E[C]/C            n=1, 5, 10: 0.999, 1.008, 1.021
value: 24.07
news var  cf=0.0002  dr=0.0001
```

```text
$ python examples/flat_vs_curve.py
mu(1)  2.37%
mu(10) 4.09%
flat PV vs curve  +8.0%
```

| Maturity $n$ | $\mu_t(n)$ (%) | $E_t[C_{t+n}]/C_t$ |
|---:|---:|---:|
| 1 | 2.37 | 0.999 |
| 5 | 3.78 | 1.008 |
| 10 | 4.09 | 1.021 |
| 15 | 4.19 | 1.034 |

The curve rises; a flat rate at $\mu_t(1)$ overstates present value by about 8 % on this draw.

Minimal path in code:

```python
from varvaluation import (
    AngLiuModel,
    estimate_var,
    simulate_paper_state,
)

state, spec = simulate_paper_state(nobs=160, seed=11)
fit = estimate_var(state, spec)
model = AngLiuModel.from_var(fit)   # supply xi, Lambda, alpha as needed

X = model.unconditional_mean() if hasattr(model, "unconditional_mean") else None
# preferred, once loadings are set:
# spots = model.spot_rates(X, n=30)
# cf    = model.cashflow_expectation(X, n=30)
# V     = model.value(X, C0=1.0)
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
  15      9.24      5.50      9.26      9.28
  20      9.23      5.50      9.26      9.28
  25      9.23      5.50      9.26      9.28
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

1. Run the offline example and obtain a spot curve and a strip-sum value.
2. Verify that $\mu_t(1)$ matches the one-period expected return.
3. Explain why the difference between the Ang–Liu curve and a flat CAPM rate is precisely the covariance channel the handbook is about.

The next page changes only the universe that is averaged into $X_t$.
