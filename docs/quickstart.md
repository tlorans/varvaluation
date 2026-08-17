# Quickstart

## From a prepared state frame

```python
from varvaluation import (
    StateSpec,
    ExpectedReturnSpec,
    estimate_var,
    AngLiuModel,
    news_decomposition,
)

spec = StateSpec(names=("g", "beta", "dpo", "r", "cay", "pi"), cashflow="g")
fit = estimate_var(df, spec)

xi, Lambda = ExpectedReturnSpec().xi_lambda(
    spec, {"b0": 0.05, "br": -0.15, "bcay": 2.0}
)
model = AngLiuModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.002)
rates = model.spot_rates(fit.X_lag[-1], n=30)
value = model.value(fit.X_lag[-1], n=80)
news = news_decomposition(fit, returns, xi=xi, Lambda=Lambda)
```

`news.frame["cf"]` is cash-flow news from the `g` equation. `news.frame["residual"]` is the identity leftover, not the definition of cash-flow news.

`treasury_test()` runs the Chen check: known cash flows ⇒ direct CF news ≈ 0.

## From Ken French

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

`load_macro()` always tries to bring FF3, the one-year rate, and inflation. Cay is optional: if the published file is missing, it is reconstructed from FRED.

A longer script that prints spot curves, perpetuities, news shares, climate scenarios, and a firm-level VAR is [`examples/run_application.py`](https://github.com/tlorans/varvaluation/blob/main/examples/run_application.py).
