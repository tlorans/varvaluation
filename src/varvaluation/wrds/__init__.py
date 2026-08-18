"""WRDS extra: CRSP–Compustat firm panel."""

from importlib.util import find_spec

from varvaluation.exceptions import ExtraNotInstalled

if find_spec("wrds") is None:
    raise ExtraNotInstalled(
        "varvaluation.wrds requires the [wrds] extra. "
        "Install with: uv add 'varvaluation[wrds]'"
    )

from varvaluation.wrds.beta import attach_posterior_beta, quarter_end_betas
from varvaluation.wrds.firm import (
    compute_book_to_market,
    compute_firm_dividend_growth,
    compute_roe,
    filter_firms,
    prepare_firm_state,
)
from varvaluation.wrds.load import (
    load_ccm_link,
    load_compustat_annual,
    load_compustat_quarterly,
    load_crsp_daily,
    load_crsp_dsi,
    load_crsp_monthly,
    load_crsp_msi,
    load_firm_panel,
    merge_firm_panel,
    merge_quarterly_panel,
)

__all__ = [
    "attach_posterior_beta",
    "compute_book_to_market",
    "compute_firm_dividend_growth",
    "compute_roe",
    "filter_firms",
    "load_ccm_link",
    "load_compustat_annual",
    "load_compustat_quarterly",
    "load_crsp_daily",
    "load_crsp_dsi",
    "load_crsp_monthly",
    "load_crsp_msi",
    "load_firm_panel",
    "merge_firm_panel",
    "merge_quarterly_panel",
    "prepare_firm_state",
    "quarter_end_betas",
]
