"""Cash-flow and discount-rate forecasts from one VAR."""

from varvaluation.estimate import VARFit, estimate_var, estimate_var_panel, spectral_radius
from varvaluation.exceptions import (
    EstimationError,
    ExtraNotInstalled,
    NonStationaryVARError,
    PerpetuityDivergesError,
    RecursionDivergedError,
    SchemaError,
    StateSpecError,
    VarValuationError,
)
from varvaluation.model import AngLiuModel
from varvaluation.news import (
    NewsResult,
    NewsShares,
    news_decomposition,
    treasury_test,
)
from varvaluation.schemas import returns_schema, state_schema
from varvaluation.spec import ExpectedReturnSpec, StateSpec
from varvaluation.valuation import ValuationResult, isolate_channels

ValuationModel = AngLiuModel

__version__ = "0.1.0"

__all__ = [
    "AngLiuModel",
    "ValuationModel",
    "EstimationError",
    "ExpectedReturnSpec",
    "ExtraNotInstalled",
    "NewsResult",
    "NewsShares",
    "NonStationaryVARError",
    "PerpetuityDivergesError",
    "RecursionDivergedError",
    "SchemaError",
    "StateSpec",
    "StateSpecError",
    "VARFit",
    "ValuationResult",
    "VarValuationError",
    "estimate_var",
    "estimate_var_panel",
    "isolate_channels",
    "news_decomposition",
    "returns_schema",
    "spectral_radius",
    "state_schema",
    "treasury_test",
]
