import numpy as np
import pytest

from varvaluation import StateSpec, estimate_var
from varvaluation.climate import AR1Dynamics, override_var
from varvaluation.news import simulate_return_var


def test_override_var_replaces_named_row_only():
    df, spec = simulate_return_var(nobs=200, seed=1)
    # add a disconnected Y
    y = np.zeros(len(df))
    y[0] = 0.1
    for i in range(1, len(y)):
        y[i] = 0.5 * y[i - 1]
    df = df.with_columns(Y=y)
    spec = StateSpec(names=("ret", "g", "Y"), cashflow="g", horizon=1, nw_lags=1)
    fit = estimate_var(df, spec)
    dyn = AR1Dynamics(intercept=0.01, phi=0.8, sigma=0.05, mean=0.05, scenario="test")
    Phi, c, Sigma = override_var(fit, dyn, "Y")
    i = spec.index("Y")
    assert Phi[i, i] == pytest.approx(0.8)
    assert np.allclose(Phi[i, :i], 0.0)
    assert c[i] == pytest.approx(0.01)
    assert Sigma[i, i] == pytest.approx(0.05**2)
    assert np.allclose(Sigma[i, :i], 0.0)
    # other rows unchanged
    assert np.allclose(Phi[0], fit.Phi[0])
    assert np.allclose(c[0], fit.c[0])


def test_override_unknown_state_raises():
    df, spec = simulate_return_var(nobs=80, seed=2)
    fit = estimate_var(df, spec)
    with pytest.raises(Exception, match="Y"):
        override_var(fit, {"c_Y": 0.0, "phi_Y": 0.5, "sigma_Y": 0.1}, "Y")
