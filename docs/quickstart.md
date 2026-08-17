# Synthetic check

Section 5 uses a CRSP–Compustat firm panel. The two-state draw below
reproduces both sides of the present value with no downloads. It is a
check on the implementation, not a substitute for the illustration.
[`examples/quickstart.py`](https://github.com/tlorans/varvaluation/blob/main/examples/quickstart.py):

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

``` text title="Terminal"
spectral radius: 0.409
spot mu(n) %      n=1, 5, 10: 2.37, 3.78, 4.09
E[C]/C            n=1, 5, 10: 0.999, 1.008, 1.021
value: 24.07
news var  cf=0.0002  dr=0.0001
```

Inspect `fit.Phi[spec.cashflow_index(), spec.cashflow_index()]` before you
publish a full PV. If the own-lag is near one, the growth forecast is not
yet usable; `perpetuity(X)` isolates the curve until it is. The argument
is on [Valuation](guide/valuation.md).

`news.frame["cf"]` is cash-flow news from the `g` equation.
`news.frame["residual"]` is the identity leftover, not the definition of
cash-flow news.

`treasury_test()` runs the known-cash-flow check: coupons known ⇒ direct
CF news ≈ 0.

## Illustration on market data

[Section 5](guide/walkthrough.md).
