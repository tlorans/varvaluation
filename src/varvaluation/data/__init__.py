"""Public-data extra: Ken French, FRED, Lettau–Ludvigson cay, GISTEMP."""

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
    load_cpi,
    load_gs1,
    load_macro,
    load_temperature,
)
from varvaluation.data.portfolio import (
    BETA_WINDOW,
    compute_dividend_growth,
    compute_payout_ratio_change,
    compute_rolling_betas,
    prepare_portfolio_state,
)

__all__ = [
    "BETA_WINDOW",
    "cache_dir",
    "compute_dividend_growth",
    "compute_payout_ratio_change",
    "compute_rolling_betas",
    "load_bm_deciles",
    "load_cay",
    "load_cpi",
    "load_ff3",
    "load_gs1",
    "load_industry49",
    "load_macro",
    "load_temperature",
    "prepare_portfolio_state",
]
