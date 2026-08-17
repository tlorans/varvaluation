# varvaluation

Cash-flow and discount-rate forecasts from one VAR.

You name a state $X_t$, estimate a VAR(1), and get expected cash flows
**and** a discount curve from the same system. `value` multiplies them.
Unexpected returns can be split into cash-flow news and discount-rate
news; cash-flow news is taken from the cash-flow equation, not from the
residual.

**Docs:** [tlorans.github.io/varvaluation](https://tlorans.github.io/varvaluation/).
The teaching course is [tlorans/var_valuation](https://github.com/tlorans/var_valuation).

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

## Ten-line path

```python
from varvaluation import (
    StateSpec,
    ExpectedReturnSpec,
    estimate_var,
    ValuationModel,
    news_decomposition,
)

spec = StateSpec(names=("g", "beta", "dpo", "r", "cay", "pi"), cashflow="g")
fit = estimate_var(df, spec)

xi, Lambda = ExpectedReturnSpec().xi_lambda(
    spec, {"b0": 0.05, "br": -0.15, "bcay": 2.0}
)
model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.002)
X = fit.X_lag[-1]
value = model.value(X, n=80)   # cash flows and rates from X
news  = news_decomposition(fit, returns, xi=xi, Lambda=Lambda)
```

`news.frame["cf"]` is the cash-flow-equation series. The identity leftover
is `news.frame["residual"]`, never the definition of cash-flow news.

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
