# varvaluation

Present value is the expectation of a product: each cash flow times a
path of one-period expected returns. One rate for every horizon is a
degeneracy, not a method. This package is the bench for the research
program that treats that product as something you can measure. The
closed forms are Ang and Liu (2004). Cash-flow news is the cash-flow
equation, not the residual.

**Handbook:** [tlorans.github.io/varvaluation](https://tlorans.github.io/varvaluation/).
The firm illustration is a software demonstration on a short
CRSP–Compustat window (2,673 prepared firms; a pooled companion on the
80 longest histories). It reports the discount curve, not firm present
values.

## Install

```text
uv add varvaluation
uv add "varvaluation[data]"   # Ken French / FRED / cay
uv add "varvaluation[wrds]"   # CRSP–Compustat firm panel
```

`[data]` loaders cache downloads under `~/.cache/varvaluation` (override
with `VARVALUATION_CACHE`). Pass `path=` to read a local file and skip the
network. `load_macro()` requires FF3, GS1, and CPI; **cay is optional**.
If the published Lettau–Ludvigson CSV is unavailable, `load_cay()`
reconstructs cay from FRED. WRDS credentials: `WRDS_USERNAME` or
`WRDS_USER`, and `WRDS_PASSWORD`, in the environment or a `.env` file.

Python 3.11+. Managed with `uv`.

The firm illustration is `uv run python examples/walkthrough.py`
([Three curves](https://tlorans.github.io/varvaluation/guide/walkthrough/)).

## Flat rate versus the curve

Year one and year ten do not share a rate. The snippet values a
ten-period unit claim two ways — the fitted curve, and a flat rate
equal to today's μ(1). No downloads.

```python
from varvaluation import ExpectedReturnSpec, ValuationModel, estimate_var
from varvaluation.news import simulate_return_var
import numpy as np

df, spec = simulate_return_var(nobs=400, seed=7)
fit = estimate_var(df, spec)
xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(
    spec, {"b0": 0.01}
)
model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.04)
X = fit.X_lag[-1]
rates = model.spot_rates(X, n=10)
n = np.arange(1, 11)
curve = float(np.sum(np.exp(-n * rates)))
flat = float(np.sum(np.exp(-n * rates[0])))
print(f"mu(1) {100*rates[0]:.2f}%   mu(10) {100*rates[-1]:.2f}%")
print(f"flat PV vs curve {(flat/curve - 1)*100:+.1f}%")
```

```text
mu(1) 2.37%   mu(10) 4.09%
flat PV vs curve +8.0%
```

`uv run python examples/flat_vs_curve.py` prints the same three numbers.
The synthetic check with news is `uv run python examples/quickstart.py`.

## Public data (`[data]`)

```python
from varvaluation import StateSpec, estimate_var
from varvaluation.data import load_bm_deciles, load_macro, prepare_portfolio_state

total, capgains = load_bm_deciles()
macro = load_macro()
spec = StateSpec(names=("g", "beta", "dpo", "r", "cay", "pi"), cashflow="g")
state = prepare_portfolio_state(
    total, capgains, macro, spec, portfolio="D10", start="1965-07"
)
fit = estimate_var(state, spec)
```

`g`, `beta`, and `dpo` are built when those names are in the spec.
Everything else is joined from `macro` by column name.

## Firm panel (`[wrds]`)

```python
from varvaluation import StateSpec, estimate_var_panel
from varvaluation.wrds import load_firm_panel, prepare_firm_state

panel = load_firm_panel(start="1965-07")
spec = StateSpec(
    names=("roe", "beta", "bm", "r", "cay", "pi"),
    cashflow="roe",
    group="permno",
)
state = prepare_firm_state(panel, macro, spec, start="1965-07")
fit = estimate_var_panel(state, spec)
```

`prepare_firm_state` also accepts a local panel (no live WRDS). `roe`,
`bm`, and `beta` are built when those names are in the spec.

## What is in 0.1

| Layer | Status |
|---|---|
| `StateSpec`, Pandera schemas, Newey–West VAR(1) / panel VAR | shipped |
| Spot curve, `value` (both sides from $X$), channel isolation | shipped |
| Cash-flow news from the cash-flow equation + Treasury diagnostic | shipped |
| `[data]` Ken French / FRED / cay | shipped |
| `[wrds]` CRSP–Compustat panel + firm state | shipped (live query skipped in CI) |

## License

MIT
