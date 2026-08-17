# varvaluation

Cash-flow expectations and discount rates from one VAR.

A present value is the expectation of a product: each future cash flow
multiplied by the path of one-period required returns. Those two paths
have to be estimated together. The package implements the residual-income
term structure of Giacotto, Lin, and Zhao (2020) — insurance first, then
any industry — on top of the Ang and Liu (2004) recursions.

**Handbook:** [tlorans.github.io/varvaluation](https://tlorans.github.io/varvaluation/).

## Install

```text
uv add varvaluation
uv add "varvaluation[data]"   # Ken French / FRED Treasuries / DEF / TERM
uv add "varvaluation[wrds]"   # Compustat quarterly + CRSP daily
```

Python 3.11+. Managed with `uv`. `[data]` caches under
`~/.cache/varvaluation` (override with `VARVALUATION_CACHE`). WRDS
credentials: `WRDS_USERNAME` or `WRDS_USER`, and `WRDS_PASSWORD`.

## The four calls

```python
from varvaluation import (
    CCAPMSpec,
    ResidualIncome,
    TermStructureModel,
    estimate_var,
    simulate_paper_state,
)

state, spec = simulate_paper_state(nobs=160, seed=11)
fit = estimate_var(state, spec)
model = TermStructureModel.from_var(fit, ResidualIncome(), CCAPMSpec())
rho = model.unconditional_curve(0.055, n=30)
print(f"ρ(1) {100*rho[0]:.2f}%   ρ(10) {100*rho[9]:.2f}%   ρ(30) {100*rho[29]:.2f}%")
```

```text
ρ(1) 9.26%   ρ(10) 9.24%   ρ(30) 9.23%
```

`uv run python examples/reproduce_glz2020.py` prints Fig. 1 / Tables 2–4
for the five paper portfolios on a synthetic state. Add `--wrds` to
rebuild 1972Q4–2018Q4 from Compustat quarterly and CRSP daily.

## What is in 0.1

| Layer | Status |
|---|---|
| Residual-income term structure (eqs. 6–9) | shipped |
| CCAPM with the Treasury curve outside the VAR | shipped |
| Newey–West VAR(1) / panel VAR, named `StateSpec` | shipped |
| `[data]` FF3, FRED DEF / TERM / $y(\tau)$, MRP regression | shipped |
| `[wrds]` quarterly Compustat, 125-day / Cosemans beta, SIC industries | shipped (live query skipped in CI) |
| Dividend-growth Ang–Liu engine, news, pricing-to-market | still in the library, not the front of the handbook |

## License

MIT
