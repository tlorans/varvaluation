"""Climate extra: temperature state Y_t and scenario VAR overrides."""

from varvaluation.climate.override import override_fit, override_var
from varvaluation.climate.scenarios import (
    AR1Dynamics,
    all_scenario_dynamics,
    load_scenario_parameters,
    scenario_dynamics,
)
from varvaluation.climate.state import Y_BURN_IN, Y_PERSISTENCE, build_climate_state

__all__ = [
    "AR1Dynamics",
    "Y_BURN_IN",
    "Y_PERSISTENCE",
    "all_scenario_dynamics",
    "build_climate_state",
    "load_scenario_parameters",
    "override_fit",
    "override_var",
    "scenario_dynamics",
]
