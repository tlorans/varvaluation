# varvaluation

VAR-based valuation and cash-flow / discount-rate news for Python.

Given a named state vector, the library estimates a VAR(1), builds the Ang and Liu (2004) quadratic-Gaussian discount curve, and decomposes unexpected returns into **cash-flow news** and **discount-rate news**. Cash-flow news is taken from the cash-flow equation, not from the residual (Chen, Da, Zhao 2013).

This is the public library. The teaching course lives at [tlorans/var_valuation](https://github.com/tlorans/var_valuation).

## Install

```text
uv add varvaluation
uv add "varvaluation[data]"          # Ken French / FRED / cay / GISTEMP
uv add "varvaluation[wrds,climate]"  # firm panel + climate scenarios
```

`[data]` loaders cache downloads under `~/.cache/varvaluation` (override with `VARVALUATION_CACHE`). Pass `path=` to read a local file and skip the network — that is what the tests do. WRDS credentials: `WRDS_USERNAME` (or `WRDS_USER`) and `WRDS_PASSWORD` in the environment or a `.env` file.

Python 3.11+. Managed with `uv`.

## Ten-line path

```python
import numpy as np
import polars as pl
from varvaluation import (
    StateSpec,
    ExpectedReturnSpec,
    estimate_var,
    AngLiuModel,
    news_decomposition,
)

spec = StateSpec(names=("g", "beta", "dpo", "r", "cay", "pi"), cashflow="g")
fit = estimate_var(df, spec)  # Polars frame with date + those columns

xi, Lambda = ExpectedReturnSpec().xi_lambda(
    spec, {"b0": 0.05, "br": -0.15, "bcay": 2.0}
)
model = AngLiuModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.002)
rates = model.spot_rates(fit.X_lag[-1], n=30)
value = model.value(fit.X_lag[-1], n=80)
news = news_decomposition(fit, returns, xi=xi, Lambda=Lambda)
```

`news.frame["cf"]` is the cash-flow-equation series. The identity leftover is `news.frame["residual"]`, never the definition of cash-flow news. `treasury_test()` is the Chen check: known cash flows, direct CF news ≈ 0.

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

`g`, `beta`, and `dpo` are built when those names are in the spec. Everything else is joined from `macro` by column name.

## Climate (`[climate]`)

```python
from varvaluation import AngLiuModel
from varvaluation.climate import build_climate_state, scenario_dynamics, override_var

Y = build_climate_state(temp)                 # columns date, Y
dyn = scenario_dynamics("Net Zero 2050")
Phi_s, c_s, Sigma_s = override_var(fit, dyn, state="Y")
model_s = AngLiuModel(fit.spec, Phi_s, c_s, Sigma_s, xi, Lambda, alpha)
```

`override_var` is generic: it replaces the named state's own AR(1) and zeros its innovation covariances.

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

`prepare_firm_state` also accepts a local panel (no live WRDS). `roe`, `bm`, and `beta` are built when those names are in the spec.

## What is in 0.1

| Layer | Status |
|---|---|
| `StateSpec`, Pandera schemas, Newey–West VAR(1) / panel VAR | shipped |
| Ang–Liu spot curve, PV, named channel isolation | shipped |
| Chen-aware news + Treasury diagnostic | shipped |
| `[data]` Ken French / FRED / cay / GISTEMP | shipped |
| `[climate]` Y-state, NGFS scenarios, `override_var` | shipped |
| `[wrds]` CRSP–Compustat panel + firm state | shipped (live query skipped in CI) |

## References

- Ang, A. and J. Liu (2004), “How to Discount Cash Flows with Time-Varying Expected Returns,” *Journal of Finance* 59(6), 2745–2783.
- Ang, A. and J. Liu (2001), “A General Affine Earnings Valuation Model,” *Review of Accounting Studies* 6, 397–425.
- Campbell, J. Y. (1991), “A Variance Decomposition for Stock Returns,” *Economic Journal* 101, 157–179.
- Chen, L., Z. Da, and X. Zhao (2013), “What Drives Stock Price Movements?” *Review of Financial Studies* 26(4), 841–876.

## License

MIT
