"""Pedagogical offline worked example — product → covariance → one VAR.

No downloads. Runs a synthetic state through the full Ang–Liu path:

  1. Estimate one joint VAR (Φ, c, Σ)
  2. Cash-flow recursion  → E[C_{t+n}]/C_t
  3. Priced recursion     → strips of the price–cash-flow ratio
  4. Spot curve μ_t(n)
  5. Strip-sum present value vs a flat rate at μ_t(1)

Run::

    python examples/quickstart.py
"""

from __future__ import annotations

import numpy as np

from varvaluation import ExpectedReturnSpec, ValuationModel, estimate_var
from varvaluation.news import simulate_return_var


def main() -> int:
    print("=" * 60)
    print("Worked example — cash flows and discount rates from one VAR")
    print("=" * 60)
    print()
    print("Mental map")
    print("  1. Product     value = E[discount path × cash flow]")
    print("  2. Covariance  Cov(∑g, ∑μ) enters the *price level*")
    print("  3. One VAR     both forecasts share (Φ, c, Σ)")
    print()

    # ── Step 3 of the map: one joint system ────────────────────────
    print("─" * 60)
    print("Step 1 — Estimate one joint VAR")
    print("─" * 60)
    df, spec = simulate_return_var(nobs=400, seed=7)
    fit = estimate_var(df, spec)
    print(f"  state names     : {spec.names}")
    print(f"  cash-flow row   : {spec.cashflow!r}")
    print(f"  nobs            : {fit.nobs}")
    print(f"  spectral radius : {fit.spectral_radius:.3f}  (< 1 ⇒ stationary)")
    print()
    print("  Φ (companion):")
    for i, name in enumerate(spec.names):
        row = "  ".join(f"{fit.Phi[i, j]:+.3f}" for j in range(len(spec.names)))
        print(f"    {name:>4}  {row}")
    print(f"  c (intercept)   : {np.array2string(fit.c, precision=4, floatmode='fixed')}")
    print(f"  Σ diagonal      : {np.array2string(np.diag(fit.Sigma), precision=5)}")
    print()
    print("  Off-diagonal cells of Φ and Σ carry the covariance")
    print("  that the product identity requires.")
    print()

    # ── Expected-return loadings ───────────────────────────────────
    print("─" * 60)
    print("Step 2 — Expected-return loadings (α, ξ, Λ)")
    print("─" * 60)
    xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(
        spec, {"b0": 0.01}
    )
    alpha = 0.04
    print(f"  α               : {alpha:.3f}")
    print(f"  ξ               : {np.array2string(xi, precision=3)}")
    print(f"  Λ               : {np.array2string(Lambda, precision=3)}")
    print("  μ_t = α + ξ'X + X'ΛX")
    print()

    model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=alpha)
    X = fit.X_lag[-1]
    print(f"  state X (last lag): {np.array2string(X, precision=4)}")
    print()

    # ── Cash-flow recursion ────────────────────────────────────────
    print("─" * 60)
    print("Step 3 — Cash-flow recursion  E_t[C_{t+n}]/C_t")
    print("─" * 60)
    n = 15
    cf = model.cashflow_expectation(X, n=n)
    print(f"  {'n':>4}  {'E[C]/C':>10}")
    for k in (0, 4, 9, 14):
        print(f"  {k + 1:4d}  {cf[k]:10.3f}")
    print()

    # ── Spot curve ─────────────────────────────────────────────────
    print("─" * 60)
    print("Step 4 — Spot curve μ_t(n)  (priced recursion / cash-flow)")
    print("─" * 60)
    rates = model.spot_rates(X, n=n)
    mu1_direct = float(alpha + xi @ X + X @ Lambda @ X)
    print(f"  identity check: μ_t(1) = {100 * rates[0]:.4f}%")
    print(f"                  α+ξ'X+X'ΛX = {100 * mu1_direct:.4f}%  "
          f"{'✓' if abs(rates[0] - mu1_direct) < 1e-10 else '✗'}")
    print()
    print(f"  {'n':>4}  {'μ_t(n) %':>10}")
    for k in (0, 4, 9, 14):
        print(f"  {k + 1:4d}  {100 * rates[k]:10.2f}")
    print()
    print("  The curve is not flat. A single WACC at μ_t(1) misprices")
    print("  every longer strip.")
    print()

    # ── Present value ──────────────────────────────────────────────
    print("─" * 60)
    print("Step 5 — Present value = sum of strips")
    print("─" * 60)
    val = model.value(X, C=1.0, n=40)
    maturities = np.arange(1, n + 1)
    curve_pv = float(np.sum(np.exp(-maturities * rates)))
    flat_pv = float(np.sum(np.exp(-maturities * rates[0])))
    gap = (flat_pv - curve_pv) / curve_pv
    print(f"  strip-sum value (C=1, n=40) : {val.pv:.2f}")
    print(f"  15-year unit annuity, curve : {curve_pv:.4f}")
    print(f"  15-year unit annuity, flat  : {flat_pv:.4f}")
    print(f"  flat vs curve               : {100 * gap:+.1f}%")
    print()
    print("  The gap is the object the handbook is about: how much a")
    print("  constant-rate DCF misses when expected returns move.")
    print()

    # ── News (optional diagnostic) ─────────────────────────────────
    from varvaluation import news_decomposition

    news = news_decomposition(
        fit, df.select(["date", "ret"]), return_col="ret", return_state="ret"
    )
    print("─" * 60)
    print("Diagnostic — news variance shares")
    print("─" * 60)
    print(f"  var(cash-flow news)     : {news.shares.var_cf:.4f}")
    print(f"  var(discount-rate news) : {news.shares.var_dr:.4f}")
    print()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
