# varvaluation

Cash-flow expectations and discount rates from one VAR.

A present value is the expectation of a **product**: each future cash flow multiplied by the path of one-period required returns. Those two paths have to be estimated together. The package implements closed-form cash-flow and priced recursions, and the term structure of spot discount rates $\mu_t(n)$, with an optional residual-income map for the numerator. The formulas follow [Ang and Liu (2004)](https://tlorans.github.io/varvaluation/references/#ang-liu-2004).

**Handbook:** [tlorans.github.io/varvaluation](https://tlorans.github.io/varvaluation/).

The handbook is written as a short course. Three claims, in order:

1. **Product** — value is $E[\text{discount path}\times\text{cash flow}]$.
2. **Covariance** — that product expands to a covariance term that enters the price level.
3. **One VAR** — cash-flow growth and expected returns must share one law of motion, or the covariance is missing.

Everything else (the two recursions, the spot curve, the strip-sum present value) follows from those three claims.

## Install

```text
uv add varvaluation
uv add "varvaluation[data]"   # Ken French / FRED Treasuries / DEF / TERM
uv add "varvaluation[wrds]"   # Compustat quarterly + CRSP daily
```

Python 3.11+. Managed with `uv`. `[data]` caches under `~/.cache/varvaluation` (override with `VARVALUATION_CACHE`). WRDS credentials: `WRDS_USERNAME` or `WRDS_USER`, and `WRDS_PASSWORD`.

## The core calls

```python
from varvaluation import ValuationModel, estimate_var
from varvaluation.news import simulate_return_var

state, spec = simulate_return_var(nobs=400, seed=7)
fit = estimate_var(state, spec)
model = ValuationModel.from_var(fit, xi=..., Lambda=..., alpha=...)
# spots = model.spot_rates(X, n=30)           # μ_t(n)
# cf    = model.cashflow_expectation(X, n=30) # cash-flow recursion
# V     = model.value(X, C=1.0)               # sum of strips + tail
```

`uv run python examples/quickstart.py` runs the synthetic laboratory end to end.

## What is in 0.1

| Layer | Status |
|---|---|
| Cash-flow and priced recursions, $\mu_t(n)$ | shipped |
| Quadratic $\mu_t = \alpha + \xi'X + X'\Lambda X$ (moving $\beta$ and premium) | shipped |
| Newey–West VAR(1) / panel VAR, named `StateSpec` | shipped |
| Optional residual-income numerator (clean surplus) | shipped |
| `[data]` FF3, FRED yields / DEF / TERM, MRP regression | shipped |
| `[wrds]` quarterly Compustat, rolling / Cosemans beta | shipped (live query skipped in CI) |
| News decomposition, pricing-to-market | in the library |

## License

MIT
