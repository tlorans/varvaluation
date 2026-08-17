import datetime as dt

import numpy as np
import polars as pl
import pytest

from varvaluation import EstimationError, StateSpec, estimate_var, estimate_var_panel


def _month_ends(n: int, start: dt.date = dt.date(1960, 1, 1)) -> list[dt.date]:
    dates = []
    y, m = start.year, start.month
    for _ in range(n):
        if m == 12:
            nxt = dt.date(y + 1, 1, 1)
        else:
            nxt = dt.date(y, m + 1, 1)
        dates.append(nxt.fromordinal(nxt.toordinal() - 1))
        y, m = nxt.year, nxt.month
    return dates


def _sim_var(n=800, seed=0):
    rng = np.random.default_rng(seed)
    Phi = np.array([[0.4, 0.1], [0.0, 0.7]])
    c = np.array([0.01, 0.0])
    X = np.zeros((n, 2))
    for t in range(1, n):
        X[t] = c + Phi @ X[t - 1] + rng.normal(scale=0.02, size=2)
    return X, Phi, c


def test_estimate_var_recovers_companion():
    X, Phi, c = _sim_var()
    n = len(X)
    df = pl.DataFrame({"date": _month_ends(n), "g": X[:, 0], "r": X[:, 1]})
    spec = StateSpec(names=("g", "r"), cashflow="g", horizon=1, nw_lags=2)
    fit = estimate_var(df, spec)
    np.testing.assert_allclose(fit.Phi, Phi, atol=0.05)
    np.testing.assert_allclose(fit.c, c, atol=0.02)
    assert fit.nobs == n - 1
    assert fit.spectral_radius < 1.0
    assert fit.residuals.shape == (n - 1, 2)
    assert len(fit.residual_dates) == n - 1


def test_panel_does_not_cross_groups():
    spec = StateSpec(
        names=("g", "r"), cashflow="g", group="permno", horizon=1, nw_lags=1
    )
    rows = []
    for permno, level in ((1, 0.0), (2, 10.0)):
        for i in range(5):
            rows.append(
                {
                    "permno": permno,
                    "date": dt.date(2000, i + 1, 1),
                    "g": level,
                    "r": 0.0,
                }
            )
    df = pl.DataFrame(rows)
    fit = estimate_var_panel(df, spec)
    assert fit.nobs == 8


def test_too_few_obs_raises():
    spec = StateSpec(names=("g", "r"), cashflow="g", horizon=12)
    df = pl.DataFrame(
        {
            "date": [dt.date(2000, 1, 31), dt.date(2000, 2, 29)],
            "g": [0.0, 0.0],
            "r": [0.0, 0.0],
        }
    )
    with pytest.raises(EstimationError):
        estimate_var(df, spec)


def test_phi_zeros_forces_restricted_entry():
    X, _, _ = _sim_var()
    n = len(X)
    df = pl.DataFrame({"date": _month_ends(n), "g": X[:, 0], "r": X[:, 1]})
    spec = StateSpec(names=("g", "r"), cashflow="g", horizon=1, nw_lags=2)
    fit = estimate_var(df, spec, phi_zeros=(("g", "r"),))
    assert fit.Phi[spec.index("g"), spec.index("r")] == 0.0
    assert fit.Phi[spec.index("r"), spec.index("g")] != 0.0
