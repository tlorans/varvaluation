"""Offline six-state system with an Ang–Liu-like Dec-2000 shape."""

from __future__ import annotations

from datetime import date

import numpy as np
import polars as pl

from varvaluation.angliu.spec import paper_spec
from varvaluation.spec import StateSpec


def _month_ends(n: int, start: date = date(1965, 7, 1)) -> list[date]:
    dates: list[date] = []
    y, m = start.year, start.month
    for _ in range(n):
        if m == 12:
            nxt = date(y + 1, 1, 1)
        else:
            nxt = date(y, m + 1, 1)
        dates.append(date.fromordinal(nxt.toordinal() - 1))
        y, m = nxt.year, nxt.month
    return dates


def simulate_paper_state(
    nobs: int = 426,
    *,
    seed: int = 2000,
    beta_mean: float = 1.0,
) -> tuple[pl.DataFrame, StateSpec]:
    """Stationary six-state VAR whose last observation is a low-premium state.

    Designed so the fitted curve at the last date slopes up and sits below a
    historical CAPM rate — the December 2000 configuration in the paper.
    """
    spec = paper_spec(horizon=1, nw_lags=4)
    rng = np.random.default_rng(seed)
    # Order: g, beta, dpo, r, cay, pi
    # Unconditional: beta ≈ beta_mean, r ≈ 6%, cay ≈ 1%, so long-run μ sits
    # near a historical CAPM. The last observation is a compressed-premium
    # state (low r, negative cay) so μ_t(n) slopes up — December 2000.
    c = np.array([0.008, 0.15 * beta_mean, 0.0, 0.0048, 0.001, 0.004])
    Phi = np.diag([0.35, 0.85, 0.40, 0.92, 0.90, 0.80])
    Phi[0, 2] = 0.08
    vol = np.array([0.012, 0.08, 0.04, 0.003, 0.008, 0.004])
    X = np.zeros((nobs, 6))
    X[0] = np.array([0.01, beta_mean, 0.0, 0.06, 0.01, 0.03])
    for t in range(1, nobs):
        X[t] = c + Phi @ X[t - 1] + rng.normal(scale=vol)
    X[-1] = np.array([0.02, beta_mean, 0.0, 0.035, -0.05, 0.02])
    df = pl.DataFrame(
        {
            "date": _month_ends(nobs),
            "g": X[:, 0],
            "beta": X[:, 1],
            "dpo": X[:, 2],
            "r": X[:, 3],
            "cay": X[:, 4],
            "pi": X[:, 5],
        }
    )
    return df, spec
