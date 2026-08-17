import pytest

from varvaluation.climate import (
    load_scenario_parameters,
    scenario_dynamics,
)


def test_parameters_include_net_zero():
    params = load_scenario_parameters()
    names = params["scenario"].to_list()
    assert "Net Zero 2050" in names
    assert "Current Policies" in names


def test_scenario_dynamics_stationary_and_distinct():
    nz = scenario_dynamics("Net Zero 2050", n_paths=40, horizon_years=8, seed=1)
    cp = scenario_dynamics("Current Policies", n_paths=40, horizon_years=8, seed=1)
    assert abs(nz.phi) < 1.0
    assert abs(cp.phi) < 1.0
    assert nz.sigma > 0
    assert nz.T_final != pytest.approx(cp.T_final, rel=1e-3)
