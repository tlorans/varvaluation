"""Cash-flow expectations and discount rates from one VAR.

Bring a Polars state frame, estimate one system, read the spot curve
and present value as Polars frames. Optional firm panel via
``estimate_var_panel``.
"""

from varvaluation.estimate import VARFit, estimate_var, estimate_var_panel, spectral_radius
from varvaluation.exceptions import (
    EstimationError,
    NonStationaryVARError,
    PerpetuityDivergesError,
    RecursionDivergedError,
    SchemaError,
    StateSpecError,
    VarValuationError,
)
from varvaluation.model import ValuationModel
from varvaluation.simulate import simulate_state
from varvaluation.spec import ExpectedReturnSpec, StateSpec
from varvaluation.valuation import ValuationResult

# Back-compat alias
AngLiuModel = ValuationModel

__version__ = "0.2.0"

__all__ = [
    "AngLiuModel",
    "EstimationError",
    "ExpectedReturnSpec",
    "NonStationaryVARError",
    "PerpetuityDivergesError",
    "RecursionDivergedError",
    "SchemaError",
    "StateSpec",
    "StateSpecError",
    "VARFit",
    "ValuationModel",
    "ValuationResult",
    "VarValuationError",
    "estimate_var",
    "estimate_var_panel",
    "simulate_state",
    "spectral_radius",
]
