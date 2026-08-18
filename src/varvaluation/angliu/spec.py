"""Ang and Liu (2004) sample, state names, and focus portfolios."""

from __future__ import annotations

from datetime import date

from varvaluation.spec import StateSpec

STATE_NAMES: tuple[str, ...] = ("g", "beta", "dpo", "r", "cay", "pi")

# NBER WP 10042 / JF 2004 §III.
BM_START = "1965-07"
IND_START = "1964-01"
PAPER_END = "2000-12"
VALUATION_DATE = date(2000, 12, 31)

FOCUS_BM: tuple[str, ...] = ("D1", "D6", "D10")
BM_LABELS: dict[str, str] = {
    "D1": "Growth (D1)",
    "D6": "Neutral (D6)",
    "D10": "Value (D10)",
}

# Ken French 49-industry abbreviations that exist in the public file.
FOCUS_INDUSTRIES: tuple[str, ...] = (
    "Food",
    "Oil",
    "Util",
    "Rtail",
    "Banks",
    "Steel",
    "Softw",
)

# Approximate SIC bags used only for the WRDS Compustat-payout check.
# These are not Ken French breakpoints; the handbook page says so.
INDUSTRY_SIC: dict[str, tuple[tuple[int, int], ...]] = {
    "Food": ((2000, 2099),),
    "Oil": ((1310, 1389), (2911, 2911)),
    "Util": ((4900, 4999),),
    "Rtail": ((5200, 5999),),
    "Banks": ((6000, 6199),),
    "Steel": ((3310, 3317),),
    "Softw": ((7370, 7373),),
}


def paper_spec(*, horizon: int = 12, nw_lags: int = 12) -> StateSpec:
    """Six-state Ang–Liu layout on overlapping annual pairs."""
    return StateSpec(
        names=STATE_NAMES,
        cashflow="g",
        horizon=horizon,
        nw_lags=nw_lags,
    )
