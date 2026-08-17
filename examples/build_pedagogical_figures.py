"""Offline pedagogical figures for the worked-example page (synthetic state only).

Produces SVG so the figures can be versioned cleanly.
Run from the package root:

    uv run python examples/build_pedagogical_figures.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from varvaluation import ExpectedReturnSpec, ValuationModel, estimate_var
from varvaluation.news import simulate_return_var

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "figures"

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.7,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.bbox": "tight",
        "savefig.dpi": 160,
    }
)


def _save(fig, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    fig.savefig(path, format="svg")
    plt.close(fig)
    print("wrote", path)


def main() -> None:
    df, spec = simulate_return_var(nobs=400, seed=7)
    fit = estimate_var(df, spec)
    xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(
        spec, {"b0": 0.01}
    )
    alpha = 0.04
    model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=alpha)
    X = fit.X_lag[-1]
    n = 15
    rates = model.spot_rates(X, n=n)
    cf = model.cashflow_expectation(X, n=n)

    ret = df["ret"].to_numpy()
    g = df["g"].to_numpy()
    t = np.arange(len(ret))
    fig, axes = plt.subplots(2, 1, figsize=(6.8, 4.2), sharex=True)
    axes[0].plot(t, 100 * ret, color="#1d4e89", lw=0.9)
    axes[0].axhline(100 * ret.mean(), color="0.5", ls="--", lw=0.8)
    axes[0].set_ylabel(r"$r_t$ (%)")
    axes[0].set_title("Simulated state (seed=7) — what the VAR is estimated on")
    axes[1].plot(t, 100 * g, color="#b04a3a", lw=0.9)
    axes[1].axhline(100 * g.mean(), color="0.5", ls="--", lw=0.8)
    axes[1].set_ylabel(r"$g_t$ (%)")
    axes[1].set_xlabel("month")
    fig.tight_layout()
    _save(fig, "simulated_state.svg")

    u = fit.residuals
    idx = np.linspace(0, len(u) - 1, 120).astype(int)
    fig, ax = plt.subplots(figsize=(4.6, 4.0))
    ax.scatter(100 * u[idx, 1], 100 * u[idx, 0], s=14, alpha=0.6, color="#1d4e89", edgecolors="none")
    slope = float(np.linalg.lstsq(u[:, 1:2], u[:, 0], rcond=None)[0][0])
    xs = np.linspace(u[:, 1].min(), u[:, 1].max(), 40)
    ax.plot(100 * xs, 100 * slope * xs, color="#b04a3a", lw=1.5, label=rf"slope ≈ {slope:.2f}")
    ax.axhline(0, color="0.6", lw=0.6)
    ax.axvline(0, color="0.6", lw=0.6)
    ax.set_xlabel(r"growth residual $u^g$ (%)")
    ax.set_ylabel(r"return residual $u^{ret}$ (%)")
    ax.set_title(r"Shock covariance $\Sigma$ (contemporaneous)")
    ax.legend(frameon=False, loc="upper left")
    _save(fig, "var_residuals.svg")

    K = fit.Phi.shape[0]
    eye = np.eye(K)
    Phi = fit.Phi
    c = fit.c
    horizons = np.arange(0, 25)
    EX = np.zeros((len(horizons), K))
    for i, h in enumerate(horizons):
        if h == 0:
            EX[i] = X
        else:
            Phi_h = np.linalg.matrix_power(Phi, h)
            EX[i] = (eye - Phi_h) @ np.linalg.solve(eye - Phi, c) + Phi_h @ X
    mu_path = alpha + EX @ xi

    fig, axes = plt.subplots(3, 1, figsize=(6.2, 5.4), sharex=True)
    axes[0].plot(horizons, 100 * EX[:, 0], "o-", color="#1d4e89", ms=3, lw=1.2)
    axes[0].axhline(100 * float(np.linalg.solve(eye - Phi, c)[0]), color="0.5", ls="--", lw=0.8)
    axes[0].set_ylabel(r"$E_t[r_{t+h}]$ (%)")
    axes[0].set_title(r"Conditional expectations from the estimated VAR (starting at last $X_t$)")
    axes[1].plot(horizons, 100 * EX[:, 1], "o-", color="#b04a3a", ms=3, lw=1.2)
    axes[1].axhline(100 * float(np.linalg.solve(eye - Phi, c)[1]), color="0.5", ls="--", lw=0.8)
    axes[1].set_ylabel(r"$E_t[g_{t+h}]$ (%)")
    axes[2].plot(horizons, 100 * mu_path, "o-", color="#2f6f4e", ms=3, lw=1.2)
    axes[2].axhline(100 * float(alpha + xi @ np.linalg.solve(eye - Phi, c)), color="0.5", ls="--", lw=0.8)
    axes[2].set_ylabel(r"$E_t[\mu_{t+h}]$ (%)")
    axes[2].set_xlabel(r"horizon $h$ (months)")
    fig.tight_layout()
    _save(fig, "var_expectations.svg")

    mat = np.arange(1, n + 1)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4))
    axes[0].plot(mat, cf, "o-", color="#1d4e89", ms=4, lw=1.4)
    axes[0].axhline(1.0, color="0.6", ls=":", lw=0.8)
    axes[0].set_xlabel(r"maturity $n$")
    axes[0].set_ylabel(r"$E_t[C_{t+n}]/C_t$")
    axes[0].set_title("Cash-flow recursion")
    axes[1].plot(mat, 100 * rates, "o-", color="#b04a3a", ms=4, lw=1.4, label=r"$\mu_t(n)$")
    axes[1].axhline(100 * rates[0], color="0.5", ls="--", lw=1.0, label=r"flat at $\mu_t(1)$")
    axes[1].set_xlabel(r"maturity $n$")
    axes[1].set_ylabel(r"spot rate (%)")
    axes[1].set_title("Spot curve (priced / cash-flow)")
    axes[1].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    _save(fig, "recursions.svg")

    curve_disc = np.exp(-mat * rates)
    flat_disc = np.exp(-mat * rates[0])
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    ax.plot(mat, curve_disc, "o-", color="#1d4e89", ms=4, lw=1.4, label="curve discount factors")
    ax.plot(mat, flat_disc, "s--", color="#b04a3a", ms=4, lw=1.2, label=r"flat at $\mu_t(1)$")
    ax.fill_between(mat, curve_disc, flat_disc, where=(flat_disc > curve_disc), alpha=0.2, color="#b04a3a")
    ax.set_xlabel(r"maturity $n$")
    ax.set_ylabel(r"discount factor $e^{-n\mu}$")
    ax.set_title(r"Why flat > curve PV: rising $\mu_t(n)$ discounts distant strips harder")
    ax.legend(frameon=False, fontsize=8)
    gap = (flat_disc.sum() - curve_disc.sum()) / curve_disc.sum()
    ax.text(
        0.98,
        0.05,
        f"15y unit annuity gap: {100 * gap:+.1f}%",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7"),
    )
    _save(fig, "flat_vs_curve_factors.svg")

    print("done")


if __name__ == "__main__":
    main()
