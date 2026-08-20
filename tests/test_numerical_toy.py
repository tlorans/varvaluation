"""Pin the 2-state pedagogical toy so the handbook numbers cannot drift."""

from __future__ import annotations

import numpy as np
import pytest

from varvaluation import StateSpec, ValuationModel


def _affine():
    Phi = np.array([[0.40, -0.50], [0.00, 0.50]], dtype=float)
    X_bar = np.array([0.02, 0.06])
    c = (np.eye(2) - Phi) @ X_bar
    Sigma = np.array([[0.0040, -0.0010], [-0.0010, 0.0025]], dtype=float)
    xi = np.array([0.0, 1.0])
    Lambda = np.zeros((2, 2))
    X = np.array([0.02, 0.03])
    spec = StateSpec(names=("g", "lam"), cashflow="g")
    model = ValuationModel(spec, Phi, c, Sigma, xi, Lambda, alpha=0.03)
    return model, X


def test_toy_one_period_identity():
    model, X = _affine()
    assert model.spot_rates(X, 1)[0] == pytest.approx(0.06, rel=0, abs=1e-12)


def test_toy_handbook_spots_and_cashflows():
    model, X = _affine()
    rates = model.spot_rates(X, 10)
    cf = model.cashflow_expectation(X, 10)
    assert rates[0] == pytest.approx(0.06000, abs=1e-8)
    assert rates[1] == pytest.approx(0.06555, abs=1e-8)
    assert rates[4] == pytest.approx(0.070573, abs=1e-6)
    assert rates[9] == pytest.approx(0.072025, abs=1e-6)
    assert cf[0] == pytest.approx(1.037693, abs=1e-6)
    assert cf[1] == pytest.approx(1.078350, abs=1e-6)


def test_toy_strip_recovers_from_spot():
    model, X = _affine()
    rates = model.spot_rates(X, 2)
    cf = model.cashflow_expectation(X, 2)
    a, b, H = model.price_recursion(2)
    strip2 = float(np.exp(a[2] + b[2] @ X + X @ H[2] @ X))
    assert cf[1] * np.exp(-2 * rates[1]) == pytest.approx(strip2, rel=1e-12)
