"""Minimal synthetic state for offline checks and documentation."""

from __future__ import annotations

from datetime import date

import numpy as np
import polars as pl

from varvaluation.spec import StateSpec


def _month_ends(n: int, start: date = date(1960, 1, 1)) -> list[date]:
    dates: list[date] = []
    y, m = start.year, start.month
    for _ in range(n):
        if m == 12:
            nxt = date(y + 1, 1, 1)
        else:
            nxt = date(y, m + 1, 1)
        dates.append(nxt.fromordinal(nxt.toordinal() - 1))
        y, m = nxt.year, nxt.month
    return dates


def simulate_state(
    nobs: int = 400,
    *,
    seed: int = 0,
    group: str | None = None,
    n_groups: int = 1,
) -> tuple[pl.DataFrame, StateSpec]:
    """Simulate a two-state (ret, g) series as a Polars frame.

    When ``group`` is set, stacks ``n_groups`` independent paths so
    ``estimate_var_panel`` can be exercised offline.
    """
    rng = np.random.default_rng(seed)
    names = ("ret", "g")
    spec = StateSpec(
        names=names,
        cashflow="g",
        horizon=1,
        nw_lags=2,
        group=group,
    )
    Phi = np.array([[0.3, 0.05], [0.0, 0.4]])
    c = np.array([0.006, 0.002])

    frames: list[pl.DataFrame] = []
    n_paths = n_groups if group is not None else 1
    for g in range(n_paths):
        X = np.zeros((nobs, 2))
        for t in range(1, nobs):
            shock = np.array([rng.normal(scale=0.02), rng.normal(scale=0.01)])
            X[t] = c + Phi @ X[t - 1] + shock
        cols: dict = {
            "date": _month_ends(nobs),
            "ret": X[:, 0],
            "g": X[:, 1],
        }
        if group is not None:
            cols[group] = [f"firm_{g}"] * nobs
        frames.append(pl.DataFrame(cols))

    df = pl.concat(frames) if len(frames) > 1 else frames[0]
    return df, spec
