"""Table 2–4 objects on a synthetic industry state (offline)."""

import numpy as np
import pytest

from varvaluation import (
    CCAPMSpec,
    ResidualIncome,
    TermStructureModel,
    capm_tests,
    estimate_var,
    flat_annuity_value,
    simulate_paper_state,
    slope_tests,
    valuation_discrepancy,
)
from varvaluation.industry import curve_panel


def test_tau1_is_ccapm_on_fitted_var():
    state, spec = simulate_paper_state(nobs=120, seed=3)
    fit = estimate_var(state, spec)
    model = TermStructureModel.from_var(fit, ResidualIncome(), CCAPMSpec())
    X = fit.X_lag[-1]
    y1 = 0.04
    rho1 = model.cost_of_capital(X, y1, n=1)[0]
    assert rho1 == pytest.approx(model.flat_ccapm_rate(X, y1), rel=1e-8)


def test_tables_run_and_annuity_identity():
    state, spec = simulate_paper_state(nobs=140, seed=5, beta_mean=0.65)
    fit = estimate_var(state, spec)
    assert fit.spectral_radius < 1.0
    model = TermStructureModel.from_var(fit, ResidualIncome(), CCAPMSpec())
    y = 0.05
    rho_ts = curve_panel(model, state, y, n=30)
    assert rho_ts.shape == (state.height, 30)
    capm = y + state["beta"].to_numpy() * state["mrp"].to_numpy()
    t2 = capm_tests(rho_ts, capm)
    t3 = slope_tests(rho_ts)
    assert [r.tau for r in t2] == [1, 5, 10, 15, 20, 25, 30]
    assert t3[0].tau == 5
    xbar = model.unconditional_mean()
    v_ts = model.annuity_value(xbar, y, n=30)
    v_flat = flat_annuity_value(model.flat_ccapm_rate(xbar, y), n=30)
    disc = valuation_discrepancy(v_ts, v_flat)
    assert disc == pytest.approx((v_flat - v_ts) / v_ts)
    assert np.isfinite(model.unconditional_curve(y, n=30)).all()
