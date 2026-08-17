"""Public-data extra: Ken French, FRED, Lettau–Ludvigson cay."""

from importlib.util import find_spec

from varvaluation.exceptions import ExtraNotInstalled

if find_spec("pandas_datareader") is None:
    raise ExtraNotInstalled(
        "varvaluation.data requires the [data] extra. "
        "Install with: uv add 'varvaluation[data]'"
    )

from varvaluation.data.cache import cache_dir
from varvaluation.data.french import load_bm_deciles, load_ff3, load_industry49
from varvaluation.data.macro import (
    load_cay,
    load_cay_from_fred,
    load_cpi,
    load_gs1,
    load_macro,
)
from varvaluation.data.portfolio import (
    BETA_WINDOW,
    compute_dividend_growth,
    compute_payout_ratio_change,
    compute_rolling_betas,
    prepare_portfolio_state,
)
from varvaluation.data.premium import (
    PremiumFit,
    annualize_rf,
    attach_mrp,
    dividend_yield_from_returns,
    fit_mrp,
    load_paper_macro,
    paper_predictors,
)
from varvaluation.data.yields import (
    TREASURY_TENORS,
    interpolate_yields,
    load_corporate_spread,
    load_treasury_curve,
    yield_curve_frame,
)

__all__ = [
    "BETA_WINDOW",
    "PremiumFit",
    "TREASURY_TENORS",
    "annualize_rf",
    "attach_mrp",
    "cache_dir",
    "compute_dividend_growth",
    "compute_payout_ratio_change",
    "compute_rolling_betas",
    "dividend_yield_from_returns",
    "fit_mrp",
    "interpolate_yields",
    "load_bm_deciles",
    "load_cay",
    "load_cay_from_fred",
    "load_corporate_spread",
    "load_cpi",
    "load_ff3",
    "load_gs1",
    "load_industry49",
    "load_macro",
    "load_paper_macro",
    "load_treasury_curve",
    "paper_predictors",
    "prepare_portfolio_state",
    "yield_curve_frame",
]
