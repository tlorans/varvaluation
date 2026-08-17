"""WRDS extra: CRSP–Compustat firm panel."""

from importlib.util import find_spec

from varvaluation.exceptions import ExtraNotInstalled

if find_spec("wrds") is None:
    raise ExtraNotInstalled(
        "varvaluation.wrds requires the [wrds] extra. "
        "Install with: uv add 'varvaluation[wrds]'"
    )

from varvaluation.wrds.firm import (
    compute_book_to_market,
    compute_roe,
    filter_firms,
    prepare_firm_state,
)
from varvaluation.wrds.load import load_firm_panel, merge_firm_panel

__all__ = [
    "compute_book_to_market",
    "compute_roe",
    "filter_firms",
    "load_firm_panel",
    "merge_firm_panel",
    "prepare_firm_state",
]
