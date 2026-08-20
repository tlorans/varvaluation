"""Two-state Ang–Liu walkthrough: every n=1 and n=2 term in numpy.

The six-variable paper state is too large to compute by hand. This script
is the same two recursions on a 2×2 affine toy, then the quadratic
βλ product that produces H(n).

Run::

    uv run python examples/numerical_toy.py
"""

from __future__ import annotations

import numpy as np
from numpy.linalg import det, eigvals, inv


def affine_economy():
    """Annual 2-state VAR. X = (g, λ). μ_t = α + λ_t."""
    Phi = np.array(
        [
            [0.40, -0.50],
            [0.00, 0.50],
        ],
        dtype=float,
    )
    X_bar = np.array([0.02, 0.06])
    c = (np.eye(2) - Phi) @ X_bar
    Sigma = np.array(
        [
            [0.0040, -0.0010],
            [-0.0010, 0.0025],
        ],
        dtype=float,
    )
    alpha = 0.03
    xi = np.array([0.0, 1.0])
    Lambda = np.zeros((2, 2))
    # Today: growth at its mean, premium compressed — the Dec 2000 picture.
    X = np.array([0.02, 0.03])
    e_g = np.array([1.0, 0.0])
    return Phi, c, Sigma, alpha, xi, Lambda, X, e_g, X_bar


def quadratic_economy():
    """3-state VAR. X = (g, β, λ). μ_t = α + β_t λ_t."""
    Phi = np.array(
        [
            [0.40, 0.00, -0.50],
            [0.00, 0.70, 0.00],
            [0.00, 0.00, 0.50],
        ],
        dtype=float,
    )
    X_bar = np.array([0.02, 1.00, 0.06])
    c = (np.eye(3) - Phi) @ X_bar
    Sigma = np.diag([0.0040, 0.0100, 0.0025]).astype(float)
    Sigma[0, 2] = Sigma[2, 0] = -0.0010
    alpha = 0.03
    xi = np.zeros(3)
    Lambda = np.zeros((3, 3))
    Lambda[1, 2] = Lambda[2, 1] = 0.5
    X = np.array([0.02, 1.20, 0.03])
    e_g = np.array([1.0, 0.0, 0.0])
    return Phi, c, Sigma, alpha, xi, Lambda, X, e_g, X_bar


def cashflow_n1(c, Sigma, Phi, e_g):
    bar_a = float(e_g @ c + 0.5 * e_g @ Sigma @ e_g)
    bar_b = Phi.T @ e_g
    return bar_a, bar_b


def priced_n1(c, Sigma, Phi, e_g, alpha, xi, Lambda):
    a = float(-alpha + e_g @ c + 0.5 * e_g @ Sigma @ e_g)
    b = -xi + Phi.T @ e_g
    H = -Lambda
    return a, b, H


def cashflow_step(bar_a, bar_b, c, Sigma, Phi, e_g):
    eb = e_g + bar_b
    bar_a_next = float(bar_a + e_g @ c + bar_b @ c + 0.5 * eb @ Sigma @ eb)
    bar_b_next = Phi.T @ eb
    return bar_a_next, bar_b_next


def priced_step(a, b, H, c, Sigma, Phi, e_g, alpha, xi, Lambda):
    K = c.shape[0]
    D = e_g + b + 2 * H @ c
    M = inv(inv(Sigma) - 2 * H)
    det_arg = float(det(np.eye(K) - 2 * Sigma @ H))
    a_next = float(
        a
        - alpha
        + (e_g + b) @ c
        + c @ H @ c
        - 0.5 * np.log(det_arg)
        + 0.5 * D @ M @ D
    )
    b_next = -xi + Phi.T @ (e_g + b) + 2 * Phi.T @ H @ c + 2 * Phi.T @ H @ M @ D
    H_next = -Lambda + Phi.T @ H @ Phi + 2 * Phi.T @ H @ M @ H @ Phi
    return a_next, b_next, H_next, det_arg, D, M


def strip(a, b, H, X):
    return float(np.exp(a + b @ X + X @ H @ X))


def cf_ratio(bar_a, bar_b, X):
    return float(np.exp(bar_a + bar_b @ X))


def spot(bar_a, bar_b, a, b, H, X, n):
    A = (bar_a - a) / n
    B = (bar_b - b) / n
    G = -H / n
    return float(A + B @ X + X @ G @ X)


def main() -> int:
    np.set_printoptions(precision=4, suppress=True)
    Phi, c, Sigma, alpha, xi, Lambda, X, e_g, X_bar = affine_economy()

    print("=" * 64)
    print("A 2-state Ang–Liu toy, computed with numpy")
    print("=" * 64)
    print()
    print("State X = (g, λ)")
    print("  g  log cash-flow growth")
    print("  λ  equity premium")
    print("  μ  = α + λ          (risk-free α = 3%, affine: Λ = 0)")
    print()
    print("VAR   X_{t+1} = c + Φ X_t + u_{t+1}")
    print("Φ =")
    print(Phi)
    print("c =", c)
    print("Σ =")
    print(Sigma)
    print(f"spectral radius = {max(abs(eigvals(Phi))):.2f}  (< 1, stationary)")
    print()
    print("Read the cells")
    print("  Φ[g,g]  =  0.40   growth mean-reverts")
    print("  Φ[g,λ]  = −0.50   high premium today → lower growth tomorrow")
    print("  Φ[λ,λ]  =  0.50   premium is persistent")
    print("  Φ[λ,g]  =  0      growth does not forecast the premium")
    print("  Σ[g,λ]  = −0.001  growth and premium shocks move against each other")
    print()
    print("Unconditional mean  E[X] =", X_bar)
    print("Unconditional μ     E[μ] =", alpha + X_bar[1], "  (3% + 6%)")
    print("Today's state       X_t  =", X)
    print("Today's μ_t               =", alpha + X[1], "  (premium compressed)")
    print()

    print("─" * 64)
    print("Step 1 · Cash-flow recursion, n = 1")
    print("─" * 64)
    print("  ā(1) = e_g'c + ½ e_g'Σ e_g")
    print("  b̄(1) = Φ' e_g")
    bar_a1, bar_b1 = cashflow_n1(c, Sigma, Phi, e_g)
    print(f"  e_g'c              = {e_g @ c:.4f}")
    print(f"  ½ e_g'Σ e_g        = {0.5 * e_g @ Sigma @ e_g:.4f}   (Jensen)")
    print(f"  ā(1)               = {bar_a1:.4f}")
    print(f"  b̄(1)               = {bar_b1}")
    cf1 = cf_ratio(bar_a1, bar_b1, X)
    print(f"  E_t[C_{{t+1}}]/C_t   = exp(ā + b̄'X) = {cf1:.4f}")
    print()
    g_mean = float(e_g @ (c + Phi @ X))
    print(f"  Check: E[g_{{t+1}}]  = e_g'(c+ΦX) = {g_mean:.4f}")
    print(f"         exp(E[g]+½σ²) = {np.exp(g_mean + 0.5 * Sigma[0, 0]):.4f}")
    print()

    print("─" * 64)
    print("Step 2 · Priced recursion, n = 1")
    print("─" * 64)
    print("  a(1) = −α + e_g'c + ½ e_g'Σ e_g")
    print("  b(1) = −ξ + Φ' e_g")
    print("  H(1) = −Λ                         (zero here: affine μ)")
    a1, b1, H1 = priced_n1(c, Sigma, Phi, e_g, alpha, xi, Lambda)
    print(f"  a(1) = {a1:.4f}")
    print(f"  b(1) = {b1}")
    print(f"  H(1) = 0")
    st1 = strip(a1, b1, H1, X)
    print(f"  strip = exp(a + b'X) = {st1:.4f}")
    print(f"  e^{{-μ_t}} × E[C]/C    = {np.exp(-(alpha + X[1])) * cf1:.4f}")
    print("  (they match: at n=1 the discount factor is known today)")
    print()

    print("─" * 64)
    print("Step 3 · Spot rate μ_t(1)")
    print("─" * 64)
    mu1 = spot(bar_a1, bar_b1, a1, b1, H1, X, n=1)
    mu_direct = float(alpha + xi @ X + X @ Lambda @ X)
    print("  μ_t(n) is the rate that satisfies")
    print("    E[C_{t+n}]/C  /  exp(n μ_t(n))  =  priced strip")
    print(f"  μ_t(1)              = {100 * mu1:.2f}%")
    print(f"  α + ξ'X + X'ΛX      = {100 * mu_direct:.2f}%")
    print("  Identity holds. The one-period spot is just today's μ_t.")
    print()

    print("─" * 64)
    print("Step 4 · One more year: n = 2")
    print("─" * 64)
    print("  Future μ_{t+1} is random, so the product covariance appears.")
    print()
    print("  Cash-flow update")
    print("    ā(n+1) = ā(n) + e_g'c + b̄(n)'c + ½ (e_g+b̄(n))'Σ(e_g+b̄(n))")
    print("    b̄(n+1) = Φ'(e_g + b̄(n))")
    bar_a2, bar_b2 = cashflow_step(bar_a1, bar_b1, c, Sigma, Phi, e_g)
    eb = e_g + bar_b1
    print(f"    e_g + b̄(1)        = {eb}")
    print(f"    e_g'c              = {e_g @ c:.4f}")
    print(f"    b̄(1)'c             = {bar_b1 @ c:.4f}")
    print(f"    ½ (e+b̄)'Σ(e+b̄)    = {0.5 * eb @ Sigma @ eb:.6f}")
    print(f"    ā(2)               = {bar_a2:.6f}")
    print(f"    b̄(2)               = {bar_b2}")
    cf2 = cf_ratio(bar_a2, bar_b2, X)
    print(f"    E_t[C_{{t+2}}]/C_t   = {cf2:.4f}")
    print()
    print("  Priced update with H=0 collapses to")
    print("    a(n+1) = a(n) − α + (e_g+b(n))'c + ½ (e_g+b(n))'Σ(e_g+b(n))")
    print("    b(n+1) = −ξ + Φ'(e_g + b(n))")
    a2, b2, H2, det_arg, D, M = priced_step(
        a1, b1, H1, c, Sigma, Phi, e_g, alpha, xi, Lambda
    )
    print(f"    D = e_g + b(1)     = {D}")
    print(f"    det(I − 2ΣH)       = {det_arg:.1f}   (H=0 ⇒ det I = 1)")
    print(f"    (e_g+b)'c          = {(e_g + b1) @ c:.4f}")
    print(f"    ½ D'Σ D            = {0.5 * D @ M @ D:.6f}")
    print(f"    a(2)               = {a2:.6f}")
    print(f"    b(2)               = {b2}")
    print(f"    H(2)               = 0")
    st2 = strip(a2, b2, H2, X)
    print(f"    strip n=2          = {st2:.4f}")
    mu2 = spot(bar_a2, bar_b2, a2, b2, H2, X, n=2)
    print(f"    μ_t(2)             = {100 * mu2:.3f}%")
    print(f"    check strip        = E[C]/C / e^{{2μ}} = {cf2 * np.exp(-2 * mu2):.4f}")
    print()

    print("─" * 64)
    print("Step 5 · The curve")
    print("─" * 64)
    bar_a, bar_b, a, b, H = bar_a2, bar_b2, a2, b2, H2
    print(f"  {'n':>3}  {'μ_t(n)':>8}  {'E[C]/C':>8}  {'strip':>8}")
    rows = [(1, mu1, cf1, st1), (2, mu2, cf2, st2)]
    for n in range(3, 11):
        bar_a, bar_b = cashflow_step(bar_a, bar_b, c, Sigma, Phi, e_g)
        a, b, H, *_ = priced_step(a, b, H, c, Sigma, Phi, e_g, alpha, xi, Lambda)
        mu = spot(bar_a, bar_b, a, b, H, X, n)
        cf = cf_ratio(bar_a, bar_b, X)
        st = strip(a, b, H, X)
        rows.append((n, mu, cf, st))
    for n, mu, cf, st in rows:
        print(f"  {n:3d}  {100 * mu:7.3f}%  {cf:8.4f}  {st:8.4f}")
    print()
    print("  The curve slopes up: λ_t is 3%, the long-run mean is 6%.")
    print("  As X mean-reverts, the strip rate climbs toward the long-run spot.")
    print("  That long-run spot is not E[μ]=9%. Jensen and Cov(g,μ) sit")
    print("  inside the product, so the rate that prices a long strip is lower.")
    print()

    print("─" * 64)
    print("Step 6 · Why E[product] ≠ E[discount] × E[cash flow]")
    print("─" * 64)
    rng = np.random.default_rng(0)
    N = 200_000
    L = np.linalg.cholesky(Sigma)
    U1 = L @ rng.standard_normal((2, N))
    U2 = L @ rng.standard_normal((2, N))
    X1 = c[:, None] + Phi @ X[:, None] + U1
    X2 = c[:, None] + Phi @ X1 + U2
    g1, lam1 = X1[0], X1[1]
    g2 = X2[0]
    mu_t = alpha + X[1]
    mu_tp1 = alpha + lam1
    product = np.exp(-mu_t - mu_tp1 + g1 + g2)
    cf_path = np.exp(g1 + g2)
    disc_path = np.exp(-mu_t - mu_tp1)
    mc_prod = float(product.mean())
    mc_cf = float(cf_path.mean())
    mc_d = float(disc_path.mean())
    separate = mc_d * mc_cf
    cov_g_mu = float(np.cov(g1 + g2, mu_t + mu_tp1, ddof=1)[0, 1])
    print(f"  Monte Carlo n=2, {N:,} draws (seed 0)")
    print(f"    E[ e^{{-μ_t-μ_{{t+1}}}} C_{{t+2}}/C ]   = {mc_prod:.4f}")
    print(f"    closed-form strip                 = {st2:.4f}")
    print(f"    E[discount] × E[cash flow]        = {separate:.4f}")
    print(f"    E[product] / (E[D] E[C])          = {mc_prod / separate:.4f}")
    print(f"    Cov(g_{{t+1}}+g_{{t+2}}, μ_t+μ_{{t+1}}) = {cov_g_mu:.4f}")
    print()
    print("  Φ[g,λ] = −0.5 and Σ[g,λ] < 0: high premium comes with low growth.")
    print("  For lognormals, E[e^{g-μ}] = E[e^g] E[e^{-μ}] exp(−Cov(g,μ)).")
    print("  Cov(g,μ) < 0, so the extra factor is greater than 1: the joint")
    print("  law raises the strip relative to two separate forecasts.")
    print()

    print("─" * 64)
    print("Step 7 · Quadratic μ = α + βλ  (this is why H(n) exists)")
    print("─" * 64)
    Phi3, c3, Sigma3, alpha3, xi3, Lam3, X3, e3, _ = quadratic_economy()
    print("  State X = (g, β, λ)")
    print("  μ_t = 0.03 + β_t λ_t     a product of two moving pieces")
    print(f"  Today  β={X3[1]:.2f}, λ={X3[2]:.2f}  →  μ_t = {alpha3 + X3[1] * X3[2]:.3f}")
    print()
    bar_a1, bar_b1 = cashflow_n1(c3, Sigma3, Phi3, e3)
    a1, b1, H1 = priced_n1(c3, Sigma3, Phi3, e3, alpha3, xi3, Lam3)
    print("  H(1) = −Λ")
    print(H1)
    print(f"  X'H(1)X = {X3 @ H1 @ X3:.3f}  =  −βλ = {-X3[1] * X3[2]:.3f}")
    mu1_q = spot(bar_a1, bar_b1, a1, b1, H1, X3, n=1)
    print(f"  μ_t(1) = {100 * mu1_q:.2f}%  = α + βλ  (identity still holds)")
    a2, b2, H2, *_ = priced_step(a1, b1, H1, c3, Sigma3, Phi3, e3, alpha3, xi3, Lam3)
    print("  H(2) is no longer −Λ: Φ carries the quadratic term forward")
    print(H2)
    print()

    print("─" * 64)
    print("Step 8 · Same 2-state toy through ValuationModel")
    print("─" * 64)
    from varvaluation import StateSpec, ValuationModel

    spec = StateSpec(names=("g", "lam"), cashflow="g")
    Phi, c, Sigma, alpha, xi, Lambda, X, _, _ = affine_economy()
    model = ValuationModel(spec, Phi, c, Sigma, xi, Lambda, alpha)
    rates = model.spot_rates(X, n=15)
    print(f"  library μ(1), μ(2), μ(5), μ(10) = "
          f"{100 * rates[0]:.3f}%, {100 * rates[1]:.3f}%, "
          f"{100 * rates[4]:.3f}%, {100 * rates[9]:.3f}%")
    val = model.value(X, C=1.0, n=40)
    print(f"  strip-sum value (C=1, n=40) = {val.pv:.2f}")
    mat = np.arange(1, 16)
    curve_pv = float(np.exp(-mat * rates).sum())
    flat_pv = float(np.exp(-mat * rates[0]).sum())
    print(f"  15y unit annuity, curve     = {curve_pv:.3f}")
    print(f"  15y unit annuity, flat μ(1) = {flat_pv:.3f}")
    print(f"  flat vs curve               = {100 * (flat_pv / curve_pv - 1):+.1f}%")
    print()
    print("  Locking the rate at today's 6% overvalues the claim: the curve")
    print("  is already on its way up. That is the December 2000 argument,")
    print("  on two states instead of six.")
    print()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
