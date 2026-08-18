"""Offline check — Polars state → one VAR → Polars curve and value.

Run::

    python examples/quickstart.py
"""

from __future__ import annotations

import numpy as np

from varvaluation import ExpectedReturnSpec, ValuationModel, estimate_var, simulate_state


def main() -> int:
    print("=" * 60)
    print("Cash flows and discount rates from one VAR")
    print("=" * 60)
    print()
    print("Mental map")
    print("  1. Product     value = E[discount path × cash flow]")
    print("  2. Covariance  Cov(∑g, ∑μ) enters the *price level*")
    print("  3. One VAR     both forecasts share (Φ, c, Σ)")
    print()

    print("─" * 60)
    print("Step 1 — Polars state → estimate_var")
    print("─" * 60)
    df, spec = simulate_state(nobs=400, seed=7)
    fit = estimate_var(df, spec)
    print(f"  state names     : {spec.names}")
    print(f"  cash-flow row   : {spec.cashflow!r}")
    print(f"  nobs            : {fit.nobs}")
    print(f"  spectral radius : {fit.spectral_radius:.3f}")
    print(f"  Φ:\n{np.array2string(fit.Phi, precision=3)}")
    print()

    print("─" * 60)
    print("Step 2 — Expected-return loadings")
    print("─" * 60)
    xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(
        spec, {"b0": 0.01}
    )
    model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.04)
    X = fit.X_lag[-1]
    print(f"  X (last lag): {np.array2string(X, precision=4)}")
    print()

    print("─" * 60)
    print("Step 3 — Polars spot curve")
    print("─" * 60)
    curve = model.spot_curve(X, n=15)
    print(curve.filter(pl_col_in := None) if False else curve.filter(
        curve["maturity"].is_in([1, 5, 10, 15])
    ))
    # simpler print without filter helper issues:
    for n in (1, 5, 10, 15):
        row = curve.row(n - 1)
        print(f"  n={n:2d}  μ={100 * row[1]:.2f}%  E[C]/C={row[2]:.3f}")
    print()

    print("─" * 60)
    print("Step 4 — Present value")
    print("─" * 60)
    val = model.value(X, C=1.0, n=40)
    rates = model.spot_rates(X, n=15)
    mat = np.arange(1, 16)
    curve_pv = float(np.exp(-mat * rates).sum())
    flat_pv = float(np.exp(-mat * rates[0]).sum())
    print(f"  strip-sum value : {val.pv:.2f}")
    print(f"  flat vs curve   : {100 * (flat_pv / curve_pv - 1):+.1f}%")
    print()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
