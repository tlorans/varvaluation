"""Flat rate versus the fitted curve. No downloads.

Companion to examples/quickstart.py — isolates the valuation gap
that a constant WACC produces when expected returns move.
"""

from __future__ import annotations

import numpy as np

from varvaluation import ExpectedReturnSpec, ValuationModel, estimate_var
from varvaluation.news import simulate_return_var


def flat_vs_curve(*, seed: int = 7, n: int = 15) -> tuple[float, float, float, float]:
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
    return float(rates[0]), float(rates[-1]), float(gap), float(curve_pv)


if __name__ == "__main__":
    mu1, muN, gap, curve = flat_vs_curve()
    print("Flat rate versus Ang–Liu curve (synthetic state, seed=7)")
    print(f"  μ_t(1)              {100 * mu1:.2f}%")
    print(f"  μ_t(15)             {100 * muN:.2f}%")
    print(f"  15-year unit PV     curve={curve:.4f}")
    print(f"  flat PV vs curve    {100 * gap:+.1f}%")
    print()
    print("  The gap is the covariance channel: a flat rate locked at")
    print("  μ_t(1) ignores the term structure that the joint VAR produces.")
