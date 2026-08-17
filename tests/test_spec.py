import numpy as np
import pytest

from varvaluation import ExpectedReturnSpec, StateSpec, StateSpecError


def test_index_and_cashflow():
    spec = StateSpec(names=("g", "beta", "r", "cay"), cashflow="g")
    assert spec.K == 4
    assert spec.index("cay") == 3
    assert spec.cashflow_index() == 0


def test_unknown_name_raises():
    spec = StateSpec(names=("g", "r"), cashflow="g")
    with pytest.raises(StateSpecError, match="zzz"):
        spec.index("zzz")


def test_cashflow_must_be_in_names():
    with pytest.raises(StateSpecError, match="cashflow"):
        StateSpec(names=("g", "r"), cashflow="roe")


def test_duplicate_names_raise():
    with pytest.raises(StateSpecError, match="duplicate"):
        StateSpec(names=("g", "g"), cashflow="g")


def test_empty_names_raise():
    with pytest.raises(StateSpecError, match="non-empty"):
        StateSpec(names=(), cashflow="g")


def test_xi_lambda_symmetry_and_slots():
    spec = StateSpec(names=("g", "beta", "r", "cay", "z"), cashflow="g")
    er = ExpectedReturnSpec(rate="r", beta="beta", premium=("cay", "z"))
    xi, Lam = er.xi_lambda(spec, {"b0": 0.05, "br": -0.2, "bcay": 2.0, "bz": 0.8})
    assert xi[spec.index("r")] == pytest.approx(1.0)
    assert xi[spec.index("beta")] == pytest.approx(0.05)
    assert Lam[spec.index("beta"), spec.index("z")] == pytest.approx(0.4)
    assert Lam[spec.index("z"), spec.index("beta")] == pytest.approx(0.4)
    np.testing.assert_allclose(Lam, Lam.T)
