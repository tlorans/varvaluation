# Worked example

## Where this sits on the map

All three steps are already in place. This page simply runs them end-to-end: estimate the joint VAR, apply the two Ang–Liu recursions, and read the spot curve $\mu_t(n)$.

---

## Offline (no downloads)

```text
uv run python examples/reproduce_glz2020.py
```

(The script name is historical; it draws a synthetic state, fits the VAR, and prints the curve and a strip-sum valuation. No external data.)

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

## Live data

```text
uv add "varvaluation[data,wrds]"
# WRDS_USERNAME / WRDS_PASSWORD in the environment or a .env file
uv run python examples/reproduce_glz2020.py --wrds
```

Compustat quarterly, CRSP daily for rolling betas, FRED Treasuries and credit spreads, Ken French factors. Queries cache under `~/.cache/varvaluation`.

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
