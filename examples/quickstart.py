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
print(f"spectral radius: {fit.spectral_radius:.4f}  nobs={fit.nobs}")

xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(
    spec, {"b0": 0.01}
)
model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.04)
X = fit.X_lag[-1]
print("spot rates (years 1, 5, 10):", model.spot_rates(X, 10)[[0, 4, 9]])
print("value:", model.value(X, n=40).pv)

news = news_decomposition(
    fit, df.select(["date", "ret"]), return_col="ret", return_state="ret"
)
print(
    "news shares  cf={:.4f}  dr={:.4f}  residual_share={:.4f}".format(
        news.shares.var_cf, news.shares.var_dr, news.shares.residual_share
    )
)
