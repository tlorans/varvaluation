import numpy as np
import polars as pl
import pytest

from varvaluation.cosemans import (
    fit_characteristic_beta,
    fitted_characteristic_beta,
    posterior_beta,
    rolling_window_beta,
)


def test_rolling_window_beta_recovers_known_slope():
    rng = np.random.default_rng(2)
    n = 200
    rf = np.full(n, 0.0001)
    mkt = 0.0004 + 0.01 * rng.normal(size=n)
    ret = rf + 1.3 * (mkt - rf) + 0.002 * rng.normal(size=n)
    beta, var = rolling_window_beta(ret, rf, mkt, window=125)
    later = beta[130:]
    assert np.nanmean(later) == pytest.approx(1.3, abs=0.15)
    assert np.all(var[130:] > 0)


def test_characteristic_and_posterior_shrink():
    rows = []
    for permno, true_beta in ((1, 0.5), (2, 1.2)):
        for t in range(20):
            rows.append(
                {
                    "permno": permno,
                    "date": t,
                    "beta_rw": true_beta + 0.05 * np.sin(t),
                    "defspr": 0.01,
                    "div": 0.03,
                    "rf_ann": 0.04,
                    "term": 0.01,
                    "mktvol": 0.15,
                    "size": 8.0 + 0.1 * permno,
                    "bm": 0.8,
                    "beta_lag": true_beta,
                }
            )
    panel = pl.DataFrame(rows)
    fit = fit_characteristic_beta(panel)
    assert fit.gamma.shape == (3,)
    scored = fitted_characteristic_beta(panel, fit)
    assert scored["beta_fc"].null_count() == 0
    var_fc = np.full(scored.height, 0.04)
    var_rw = np.full(scored.height, 0.01)
    post, w = posterior_beta(
        scored["beta_fc"].to_numpy(), var_fc, scored["beta_rw"].to_numpy(), var_rw
    )
    # RW more precise → weight on FC is V_RW / (V_FC+V_RW) = 0.2
    assert w[0] == pytest.approx(0.2)
    assert np.isfinite(post).all()
