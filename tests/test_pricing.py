import datetime as dt

import numpy as np
import polars as pl
import pytest

from varvaluation import ExpectedReturnSpec, ValuationModel, estimate_var
from varvaluation.news import simulate_return_var
from varvaluation.pricing import calibrate_alpha, pricing_errors


def _model(seed=3):
    df, spec = simulate_return_var(nobs=400, seed=seed)
    fit = estimate_var(df, spec)
    xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(
        spec, {"b0": 0.01}
    )
    model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.04)
    return fit, spec, model, xi, Lambda


def _frame(model, spec, X_rows, *, me_scale: float) -> pl.DataFrame:
    rows = []
    for i, X in enumerate(X_rows):
        pv = model.value(X, C=1.0, n=20).pv
        rows.append(
            {
                "permno": i,
                "date": dt.date(2019, 1, 1),
                **{n: float(X[j]) for j, n in enumerate(spec.names)},
                "div": 1.0,
                "me": pv * me_scale,
            }
        )
    return pl.DataFrame(rows)


def test_pricing_errors_perfect_match():
    fit, spec, model, _, _ = _model()
    err = pricing_errors(model, _frame(model, spec, fit.X_lag[-8:], me_scale=1.0), n=20)
    assert err.n == 8
    assert err.median_pv_me == pytest.approx(1.0, abs=1e-6)
    assert err.rmse_log_pv_me == pytest.approx(0.0, abs=1e-8)
    assert err.corr_log == pytest.approx(1.0, abs=1e-6)
    assert err.share_within_2x == pytest.approx(1.0)


def test_pricing_errors_detects_level_bias():
    fit, spec, model, _, _ = _model()
    err = pricing_errors(model, _frame(model, spec, fit.X_lag[-8:], me_scale=0.5), n=20)
    assert err.median_pv_me == pytest.approx(2.0, abs=1e-6)
    assert err.corr_log == pytest.approx(1.0, abs=1e-6)


def test_calibrate_alpha_centers_median_ratio():
    fit, spec, model, xi, Lambda = _model()
    state = _frame(model, spec, fit.X_lag[-8:], me_scale=1 / 3)
    alpha_star, err = calibrate_alpha(fit, xi, Lambda, state, n=20, alpha0=0.04)
    assert err.median_pv_me == pytest.approx(1.0, abs=0.05)
    assert alpha_star != pytest.approx(0.04, abs=1e-6)
