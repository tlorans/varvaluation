"""Figures for the numerical walkthrough page.

    uv run python examples/build_numerical_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from varvaluation import StateSpec, ValuationModel

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "figures"
sys.path.insert(0, str(ROOT / "examples"))
from numerical_toy import affine_economy  # noqa: E402

BLUE = "#1d4e89"
RED = "#b04a3a"
GREY = "0.55"

plt.rcParams.update(
    {
        "font.family": "DejaVu Serif",
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


def _model():
    Phi, c, Sigma, alpha, xi, Lambda, X, _, X_bar = affine_economy()
    spec = StateSpec(names=("g", "lam"), cashflow="g")
    model = ValuationModel(spec, Phi, c, Sigma, xi, Lambda, alpha)
    return model, Phi, c, Sigma, alpha, xi, X, X_bar


def mean_reversion(Phi, X, X_bar) -> None:
    h = np.arange(0, 11)
    EX = np.vstack([X_bar + np.linalg.matrix_power(Phi, k) @ (X - X_bar) for k in h])
    fig, axes = plt.subplots(2, 1, figsize=(6.2, 4.6), sharex=True)
    axes[0].plot(h, 100 * EX[:, 0], "o-", color=BLUE, ms=4, lw=1.4, label="from today")
    axes[0].axhline(100 * X_bar[0], color=GREY, ls="--", lw=0.9, label="typical year")
    axes[0].plot(0, 100 * X[0], "o", color=BLUE, ms=8, zorder=3)
    axes[0].set_ylabel("growth (%)")
    axes[0].legend(frameon=False, fontsize=8, loc="upper right")
    axes[1].plot(h, 100 * EX[:, 1], "o-", color=RED, ms=4, lw=1.4, label="from today")
    axes[1].axhline(100 * X_bar[1], color=GREY, ls="--", lw=0.9, label="typical year")
    axes[1].plot(0, 100 * X[1], "o", color=RED, ms=8, zorder=3)
    axes[1].set_ylabel("premium (%)")
    axes[1].set_xlabel("years from today")
    axes[1].set_xticks(h)
    axes[1].legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    _save(fig, "numerical_paths.svg")


def curve_and_cash(model, X) -> np.ndarray:
    n = 15
    rates = model.spot_rates(X, n=n)
    cf = model.cashflow_expectation(X, n=n)
    mat = np.arange(1, n + 1)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4))
    axes[0].plot(mat, cf, "o-", color=BLUE, ms=4, lw=1.4)
    axes[0].axhline(1.0, color=GREY, ls=":", lw=0.8)
    axes[0].set_xlabel("year")
    axes[0].set_ylabel(r"$E_t[C_{t+n}]/C_t$")
    axes[1].plot(mat, 100 * rates, "o-", color=RED, ms=4, lw=1.4, label="curve")
    axes[1].axhline(100 * rates[0], color=GREY, ls="--", lw=1.0, label="this year's 6%")
    axes[1].set_xlabel("year")
    axes[1].set_ylabel("rate (%)")
    axes[1].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    _save(fig, "numerical_curve.svg")
    return rates


def annuity(rates: np.ndarray) -> None:
    mat = np.arange(1, len(rates) + 1)
    curve = np.exp(-mat * rates)
    flat = np.exp(-mat * rates[0])
    fig, ax = plt.subplots(figsize=(6.0, 3.5))
    ax.plot(mat, curve, "o-", color=BLUE, ms=4, lw=1.4, label="curve")
    ax.plot(mat, flat, "s--", color=RED, ms=4, lw=1.2, label="flat at 6%")
    ax.fill_between(mat, curve, flat, where=(flat > curve), alpha=0.18, color=RED)
    ax.set_xlabel("year")
    ax.set_ylabel("discount factor")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    _save(fig, "numerical_annuity.svg")


def shocks(Phi, c, Sigma, alpha, X) -> None:
    rng = np.random.default_rng(0)
    N = 2_500
    L = np.linalg.cholesky(Sigma)
    U1 = L @ rng.standard_normal((2, N))
    U2 = L @ rng.standard_normal((2, N))
    X1 = c[:, None] + Phi @ X[:, None] + U1
    X2 = c[:, None] + Phi @ X1 + U2
    g_sum = X1[0] + X2[0]
    mu_sum = (alpha + X[1]) + (alpha + X1[1])
    fig, ax = plt.subplots(figsize=(4.8, 4.0))
    ax.scatter(100 * g_sum, 100 * mu_sum, s=10, alpha=0.28, color=BLUE, edgecolors="none")
    A = np.column_stack([g_sum, np.ones_like(g_sum)])
    slope, intercept = np.linalg.lstsq(A, mu_sum, rcond=None)[0]
    xs = np.linspace(g_sum.min(), g_sum.max(), 40)
    ax.plot(100 * xs, 100 * (intercept + slope * xs), color=RED, lw=1.5)
    ax.set_xlabel("two-year growth (%)")
    ax.set_ylabel("two-year required return (%)")
    fig.tight_layout()
    _save(fig, "numerical_shocks.svg")


def main() -> None:
    model, Phi, c, Sigma, alpha, _, X, X_bar = _model()
    mean_reversion(Phi, X, X_bar)
    rates = curve_and_cash(model, X)
    annuity(rates)
    shocks(Phi, c, Sigma, alpha, X)
    print("done")


if __name__ == "__main__":
    main()
