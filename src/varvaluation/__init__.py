"""Cash-flow expectations and discount rates from one VAR."""

from varvaluation.estimate import VARFit, estimate_var, estimate_var_panel, spectral_radius
from varvaluation.exceptions import (
    EstimationError,
    ExtraNotInstalled,
    NonStationaryVARError,
    PerpetuityDivergesError,
    RecursionDivergedError,
    SchemaError,
    StateSpecError,
    TermStructureError,
    VarValuationError,
)
from varvaluation.industry import (
    INSURANCE,
    INSURANCE_EX,
    capm_tests,
    curve_panel,
    prepare_industry_state,
    select_sic,
    slope_tests,
)
from varvaluation.model import AngLiuModel
from varvaluation.news import (
    NewsResult,
    NewsShares,
    news_decomposition,
    treasury_test,
)
from varvaluation.pricing import PricingFit, calibrate_alpha, pricing_errors
from varvaluation.residual import (
    ResidualIncomeModel,
    TermStructureModel,
    flat_annuity_value,
    simulate_paper_state,
    valuation_discrepancy,
)
from varvaluation.schemas import returns_schema, state_schema
from varvaluation.spec import (
    CCAPMSpec,
    ExpectedReturnSpec,
    ResidualIncome,
    StateSpec,
    paper_state_spec,
)
from varvaluation.valuation import ValuationResult, isolate_channels

ValuationModel = AngLiuModel

__version__ = "0.1.0"

__all__ = [
    "AngLiuModel",
    "CCAPMSpec",
    "INSURANCE",
    "INSURANCE_EX",
    "EstimationError",
    "ExpectedReturnSpec",
    "ExtraNotInstalled",
    "NewsResult",
    "NewsShares",
    "NonStationaryVARError",
    "PerpetuityDivergesError",
    "PricingFit",
    "RecursionDivergedError",
    "ResidualIncome",
    "ResidualIncomeModel",
    "SchemaError",
    "StateSpec",
    "StateSpecError",
    "TermStructureError",
    "TermStructureModel",
    "VARFit",
    "ValuationModel",
    "ValuationResult",
    "VarValuationError",
    "calibrate_alpha",
    "capm_tests",
    "curve_panel",
    "estimate_var",
    "estimate_var_panel",
    "flat_annuity_value",
    "isolate_channels",
    "news_decomposition",
    "paper_state_spec",
    "prepare_industry_state",
    "pricing_errors",
    "select_sic",
    "slope_tests",
    "simulate_paper_state",
    "returns_schema",
    "spectral_radius",
    "state_schema",
    "treasury_test",
    "valuation_discrepancy",
]
