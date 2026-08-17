"""Identities for the residual-income term structure (no network)."""

import numpy as np
import pytest

from varvaluation import (
    CCAPMSpec,
    NonStationaryVARError,
    ResidualIncome,
    StateSpec,
    TermStructureError,
    TermStructureModel,
    flat_annuity_value,
    paper_state_spec,
    valuation_discrepancy,
)


def _stationary_system(seed: int = 20260817):
    rng = np.random.default_rng(seed)
    spec = paper_state_spec(horizon=1)
    K = spec.K
    Phi = rng.normal(scale=0.15, size=(K, K))
    Phi *= 0.65 / np.max(np.abs(np.linalg.eigvals(Phi)))
    c = np.array([0.08, 0.04, 0.15, 0.01])
    A = rng.normal(size=(K, K))
    Sigma = 0.002 * (A @ A.T / K + np.eye(K))
    model = TermStructureModel(
        spec, Phi, c, Sigma, ResidualIncome(), CCAPMSpec()
    )
    return spec, model


def test_paper_state_spec_layout():
    spec = paper_state_spec()
    assert spec.names == ("roe", "g", "beta", "mrp")
    assert spec.horizon == 4
    assert spec.cashflow == "g"


def test_ccapm_theta_is_beta_times_mrp():
    spec = paper_state_spec(horizon=1)
    theta = CCAPMSpec().theta(spec)
    X = np.array([0.1, 0.05, 0.8, 0.06])
    assert X @ theta @ X == pytest.approx(0.8 * 0.06)
    np.testing.assert_allclose(theta, theta.T)


def test_tau1_equals_ccapm():
    _, model = _stationary_system()
    X = np.array([0.12, 0.05, 0.70, 0.05])
    y1 = 0.03
    rho = model.cost_of_capital(X, y1, n=1)
    assert rho[0] == pytest.approx(model.flat_ccapm_rate(X, y1), rel=1e-10)
    assert rho[0] == pytest.approx(y1 + X[2] * X[3], rel=1e-10)


def test_zero_theta_recovers_the_yield_curve():
    spec, model = _stationary_system()
    model.Theta[:] = 0.0
    X = model.unconditional_mean()
    y = np.linspace(0.02, 0.05, 12)
    rho = model.cost_of_capital(X, y, n=12)
    np.testing.assert_allclose(rho, y, rtol=1e-10, atol=1e-12)
    A7, B7, C7, D7 = model.unpriced_coefficients(8)
    A8, B8, C8, D8, G8 = model.priced_coefficients(8)
    np.testing.assert_allclose(A7[1:], A8[1:], rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(B7[1:], B8[1:], rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(C7[1:], C8[1:], rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(D7[1:], D8[1:], rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(G8, 0.0, atol=1e-12)


def test_unconditional_curve_is_cost_at_mean():
    _, model = _stationary_system()
    y = 0.025
    xbar = model.unconditional_mean()
    np.testing.assert_allclose(
        model.unconditional_curve(y, n=10),
        model.cost_of_capital(xbar, y, n=10),
        rtol=1e-12,
    )


def test_expected_cashflow_is_difference_of_moments():
    _, model = _stationary_system()
    X = model.unconditional_mean()
    A, B, C, D = model.unpriced_coefficients(6)
    cf = model.expected_cashflow(X, 6)
    for k in range(1, 7):
        direct = np.exp(A[k] + B[k] @ X) - np.exp(C[k] + D[k] @ X)
        assert cf[k - 1] == pytest.approx(direct, rel=1e-12)


def test_shut_book_growth_makes_second_moment_one():
    spec = paper_state_spec(horizon=1)
    Phi = np.diag([0.4, 0.0, 0.5, 0.5])
    c = np.array([0.06, 0.0, 0.2, 0.02])
    Sigma = np.diag([0.001, 1e-12, 0.002, 0.0004])
    model = TermStructureModel(spec, Phi, c, Sigma, ResidualIncome(), CCAPMSpec())
    model.e_g[:] = 0.0
    A, B, C, D = model.unpriced_coefficients(5)
    X = np.array([0.1, 0.0, 0.6, 0.04])
    for k in range(1, 6):
        assert np.exp(C[k] + D[k] @ X) == pytest.approx(1.0, abs=1e-9)


def test_nonstationary_raises():
    spec = paper_state_spec(horizon=1)
    Phi = np.eye(4) * 1.1
    with pytest.raises(NonStationaryVARError):
        TermStructureModel(
            spec, Phi, np.zeros(4), np.eye(4) * 0.01, ResidualIncome(), CCAPMSpec()
        )


def test_annuity_and_discrepancy():
    _, model = _stationary_system()
    X = model.unconditional_mean()
    y = 0.03
    v_ts = model.annuity_value(X, y, n=30)
    rho1 = model.cost_of_capital(X, y, n=1)[0]
    v_flat = flat_annuity_value(rho1, n=30)
    disc = valuation_discrepancy(v_ts, v_flat)
    assert v_ts > 0
    assert v_flat > 0
    assert disc == pytest.approx((v_flat - v_ts) / v_ts)


def test_unknown_residual_name_raises():
    spec = StateSpec(names=("roe", "g", "beta", "mrp"), cashflow="g")
    with pytest.raises(Exception):
        ResidualIncome(roe="profit").bind(spec)


def test_yield_length_must_match():
    _, model = _stationary_system()
    X = model.unconditional_mean()
    with pytest.raises(ValueError, match="length-5"):
        model.cost_of_capital(X, np.ones(3), n=5)
