import numpy as np
import pytest

from varvaluation import (
    AngLiuModel,
    ExpectedReturnSpec,
    NonStationaryVARError,
    StateSpec,
)


def _base(K_names=("g", "beta", "dpo", "r", "cay", "pi"), seed=20260813):
    rng = np.random.default_rng(seed)
    K = len(K_names)
    spec = StateSpec(names=K_names, cashflow="g")
    Phi = rng.normal(scale=0.2, size=(K, K))
    Phi *= 0.7 / np.max(np.abs(np.linalg.eigvals(Phi)))
    c = rng.normal(scale=0.01, size=K)
    A = rng.normal(size=(K, K))
    Sigma = 0.01 * (A @ A.T / K + np.eye(K))
    er = ExpectedReturnSpec()
    xi, Lam = er.xi_lambda(spec, {"b0": 0.047, "br": -0.150, "bcay": 2.189})
    return spec, dict(Phi=Phi, c=c, Sigma=Sigma, xi=xi, Lambda=Lam, alpha=0.002)


def test_spot_rate_n1_equals_mu():
    spec, p = _base()
    m = AngLiuModel(spec, **p)
    rng = np.random.default_rng(1)
    X = rng.normal(scale=0.05, size=spec.K)
    mu = p["alpha"] + p["xi"] @ X + X @ p["Lambda"] @ X
    assert m.spot_rates(X, 1)[0] == pytest.approx(mu, rel=1e-10)


def test_disconnected_state_does_not_change_curve():
    spec6, p6 = _base()
    m6 = AngLiuModel(spec6, **p6)
    names7 = spec6.names + ("Y",)
    spec7 = StateSpec(names=names7, cashflow="g")
    Phi = np.zeros((7, 7))
    Phi[:6, :6] = p6["Phi"]
    Phi[6, 6] = 0.5
    c = np.zeros(7)
    c[:6] = p6["c"]
    Sigma = np.zeros((7, 7))
    Sigma[:6, :6] = p6["Sigma"]
    Sigma[6, 6] = 1e-4
    xi = np.zeros(7)
    xi[:6] = p6["xi"]
    Lam = np.zeros((7, 7))
    Lam[:6, :6] = p6["Lambda"]
    m7 = AngLiuModel(spec7, Phi, c, Sigma, xi, Lam, p6["alpha"])
    rng = np.random.default_rng(2)
    X6 = rng.normal(scale=0.05, size=6)
    X7 = np.concatenate([X6, [0.3]])
    np.testing.assert_allclose(
        m7.spot_rates(X7, 40), m6.spot_rates(X6, 40), rtol=1e-10, atol=1e-12
    )


def test_lambda_zero_is_affine():
    spec, p = _base()
    p["Lambda"] = np.zeros((spec.K, spec.K))
    m = AngLiuModel(spec, **p)
    _, _, H = m.price_recursion(15)
    np.testing.assert_allclose(H, 0.0, atol=1e-12)


def test_nonstationary_raises():
    spec, p = _base()
    p["Phi"] = p["Phi"] * 1.05 / np.max(np.abs(np.linalg.eigvals(p["Phi"])))
    with pytest.raises(NonStationaryVARError):
        AngLiuModel(spec, **p)


def test_cashflow_expectation_positive():
    spec, p = _base()
    m = AngLiuModel(spec, **p)
    X = np.zeros(spec.K)
    assert np.all(m.cashflow_expectation(X, 10) > 0)


def test_variance_decomp_sums_to_total():
    spec, p = _base()
    m = AngLiuModel(spec, **p)
    decomp, total = m.variance_decomposition(12)
    np.testing.assert_allclose(decomp.sum(axis=1), total, rtol=1e-10)
    assert decomp.shape == (12, spec.K)
