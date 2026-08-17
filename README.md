# varvaluation

Cash-flow and discount-rate forecasts from one VAR.

You name a state $X_t$, estimate a VAR(1), and get expected cash flows
**and** a discount curve from the same system. `value` multiplies them.
Unexpected returns can be split into cash-flow news and discount-rate
news; cash-flow news is taken from the cash-flow equation, not from the
residual.

**Docs:** [tlorans.github.io/varvaluation](https://tlorans.github.io/varvaluation/).
The [worked application](https://tlorans.github.io/varvaluation/guide/walkthrough/)
runs the same recipe on Ken French, FRED, and WRDS and prints each step.

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

The real-data recipe is `uv run python examples/walkthrough.py`
([worked application](https://tlorans.github.io/varvaluation/guide/walkthrough/)).
The snippet below is the no-download toy.

## Ten-line path

```python
from varvaluation import (
    ExpectedReturnSpec,
    ValuationModel,
    estimate_var,
    news_decomposition,
)
from varvaluation.news import simulate_return_var

df, spec = simulate_return_var(nobs=400, seed=7)
fit = estimate_var(df, spec)

xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(
    spec, {"b0": 0.01}
)
model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.04)
X = fit.X_lag[-1]

rates = model.spot_rates(X, n=10)
cf = model.cashflow_expectation(X, n=10)
val = model.value(X, C=1.0, n=40)
news = news_decomposition(
    fit, df.select(["date", "ret"]), return_col="ret", return_state="ret"
)

print(f"spectral radius: {fit.spectral_radius:.3f}")
print(
    "spot mu(n) %      n=1, 5, 10:",
    ", ".join(f"{100 * rates[k]:.2f}" for k in (0, 4, 9)),
)
print(
    "E[C]/C            n=1, 5, 10:",
    ", ".join(f"{cf[k]:.3f}" for k in (0, 4, 9)),
)
print(f"value: {val.pv:.2f}")
print(f"news var  cf={news.shares.var_cf:.4f}  dr={news.shares.var_dr:.4f}")
```

```text
spectral radius: 0.409
spot mu(n) %      n=1, 5, 10: 2.37, 3.78, 4.09
E[C]/C            n=1, 5, 10: 0.999, 1.008, 1.021
value: 24.07
news var  cf=0.0002  dr=0.0001
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
