"""Synthetic walk-through: estimate, value, and decompose news. No downloads."""

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
