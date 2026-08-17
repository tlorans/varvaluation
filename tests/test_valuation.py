import numpy as np
import pytest

from varvaluation import (
    AngLiuModel,
    ExpectedReturnSpec,
    PerpetuityDivergesError,
    StateSpec,
    isolate_channels,
)


def _model(alpha=0.12):
    spec = StateSpec(names=("g", "beta", "r", "cay", "Y"), cashflow="g")
    K = spec.K
    rng = np.random.default_rng(3)
    Phi = rng.normal(scale=0.15, size=(K, K))
    Phi *= 0.6 / np.max(np.abs(np.linalg.eigvals(Phi)))
    Phi[spec.index("g"), spec.index("Y")] = 0.2
    c = np.zeros(K)
    c[0] = 0.02
    Sigma = 0.01 * np.eye(K)
    xi, Lam = ExpectedReturnSpec(premium=("cay", "Y")).xi_lambda(
        spec, {"b0": 0.04, "br": -0.1, "bcay": 1.0, "bY": 0.5}
    )
    return AngLiuModel(spec, Phi, c, Sigma, xi, Lam, alpha), spec


def test_value_positive_finite():
    m, spec = _model()
    out = m.value(np.zeros(spec.K), n=30)
    assert np.isfinite(out.pv) and out.pv > 0
    assert out.n_used > 0


def test_nonpositive_tail_raises():
    m, spec = _model(alpha=-0.5)
    with pytest.raises(PerpetuityDivergesError):
        m.perpetuity(np.zeros(spec.K), n=10)


def test_shut_cashflow_changes_value():
    m, spec = _model()
    X = np.zeros(spec.K)
    X[spec.index("Y")] = 0.4
    both = isolate_channels(m, X, shut=("Y",), on="both", n=30)
    cf = isolate_channels(m, X, shut=("Y",), on="cashflow", n=30)
    assert both.pv != pytest.approx(cf.pv, rel=1e-8)
