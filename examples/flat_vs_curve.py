"""Flat rate versus the fitted curve. No downloads. Used on the landing page."""

import numpy as np

from varvaluation import ExpectedReturnSpec, ValuationModel, estimate_var
from varvaluation.news import simulate_return_var


def flat_vs_curve(*, seed: int = 7, n: int = 10) -> tuple[float, float, float]:
    df, spec = simulate_return_var(nobs=400, seed=seed)
    fit = estimate_var(df, spec)
    xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(
        spec, {"b0": 0.01}
    )
    model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.04)
    X = fit.X_lag[-1]
    rates = model.spot_rates(X, n=n)
    maturities = np.arange(1, n + 1)
    curve_pv = float(np.sum(np.exp(-maturities * rates)))
    flat_pv = float(np.sum(np.exp(-maturities * rates[0])))
    gap = (flat_pv - curve_pv) / curve_pv
    return float(rates[0]), float(rates[-1]), float(gap)


if __name__ == "__main__":
    mu1, mu10, gap = flat_vs_curve()
    print(f"mu(1)  {100 * mu1:.2f}%")
    print(f"mu(10) {100 * mu10:.2f}%")
    print(f"flat PV vs curve  {100 * gap:+.1f}%")
