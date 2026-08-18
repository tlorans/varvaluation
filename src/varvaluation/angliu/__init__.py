"""Ang and Liu (2004) reproduction recipe.

Helpers only. The engine stays in ``varvaluation.model``. Importing this
package does not require the ``[data]`` or ``[wrds]`` extra; the WRDS
payout construction lives in ``varvaluation.angliu.payout`` and is imported
by the example when ``--wrds`` is set.
"""

from varvaluation.angliu.premium import (
    PremiumResult,
    capm_alpha,
    expected_return_loadings,
    fit_premium,
    lambda_series,
)
from varvaluation.angliu.simulate import simulate_paper_state
from varvaluation.angliu.spec import (
    BM_LABELS,
    BM_START,
    FOCUS_BM,
    FOCUS_INDUSTRIES,
    IND_START,
    PAPER_END,
    STATE_NAMES,
    VALUATION_DATE,
    paper_spec,
)
from varvaluation.angliu.tables import (
    PortfolioResult,
    as_of_row,
    constant_capm_rate,
    curve_snapshot,
    fit_portfolio,
    identity_error,
    perpetuity_comparison,
    sample_moments,
    var_table,
    variance_share_table,
)
from varvaluation.angliu.targets import PAPER_CLAIMS, ShapeReport, check_shape

__all__ = [
    "BM_LABELS",
    "BM_START",
    "FOCUS_BM",
    "FOCUS_INDUSTRIES",
    "IND_START",
    "PAPER_CLAIMS",
    "PAPER_END",
    "STATE_NAMES",
    "VALUATION_DATE",
    "PortfolioResult",
    "PremiumResult",
    "ShapeReport",
    "as_of_row",
    "capm_alpha",
    "check_shape",
    "constant_capm_rate",
    "curve_snapshot",
    "expected_return_loadings",
    "fit_portfolio",
    "fit_premium",
    "identity_error",
    "lambda_series",
    "paper_spec",
    "perpetuity_comparison",
    "sample_moments",
    "simulate_paper_state",
    "var_table",
    "variance_share_table",
]
