"""Portfolio-level state construction (growth, beta, payout, macro)."""

from __future__ import annotations

from datetime import date

import numpy as np
import polars as pl

from varvaluation.betas import BETA_WINDOW, compute_rolling_betas
from varvaluation.schemas import validate_state
from varvaluation.spec import StateSpec


def compute_monthly_dividends(
    total_ret: np.ndarray, capgains_ret: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Monthly dividend level and price index from total and capital-gains returns."""
    dp_monthly = total_ret - capgains_ret
    price_level = np.cumprod(1 + capgains_ret)
    p_prev = np.concatenate([[1.0], price_level[:-1]])
    return dp_monthly * p_prev, price_level


def _safe_log_ratio(numer: np.ndarray, denom: np.ndarray) -> np.ndarray:
    ratio = numer / denom
    ok = np.isfinite(ratio) & (ratio > 0)
    out = np.full(ratio.shape, np.nan)
    out[ok] = np.log(ratio[ok])
    return out


def compute_dividend_growth(
    total_ret: np.ndarray, capgains_ret: np.ndarray
) -> np.ndarray:
    """Annual log dividend growth, sampled monthly (Hodrick trailing sum)."""
    monthly_div, _ = compute_monthly_dividends(total_ret, capgains_ret)
    n = len(monthly_div)
    annual_div = np.full(n, np.nan)
    for i in range(11, n):
        annual_div[i] = monthly_div[i - 11 : i + 1].sum()
    g = _safe_log_ratio(annual_div, np.roll(annual_div, 12))
    g[:12] = np.nan
    return g


def compute_payout_ratio_change(
    total_ret: np.ndarray, capgains_ret: np.ndarray
) -> np.ndarray:
    """Change in the log payout ratio, dpo = g - capital-gains growth."""
    monthly_div, price_level = compute_monthly_dividends(total_ret, capgains_ret)
    n = len(monthly_div)
    annual_div = np.full(n, np.nan)
    for i in range(11, n):
        annual_div[i] = monthly_div[i - 11 : i + 1].sum()
    g = _safe_log_ratio(annual_div, np.roll(annual_div, 12))
    g[:12] = np.nan
    annual_cap = _safe_log_ratio(price_level, np.roll(price_level, 12))
    annual_cap[:12] = np.nan
    return g - annual_cap


def _parse_bound(value: str | date | None, *, end: bool) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    year, month = int(value[:4]), int(value[5:7])
    if end:
        if month == 12:
            return date(year + 1, 1, 1).fromordinal(date(year + 1, 1, 1).toordinal() - 1)
        return date(year, month + 1, 1).fromordinal(date(year, month + 1, 1).toordinal() - 1)
    return date(year, month, 1)


def prepare_portfolio_state(
    total: pl.DataFrame,
    capgains: pl.DataFrame,
    macro: pl.DataFrame,
    spec: StateSpec,
    *,
    portfolio: str,
    start: str | date | None = None,
    end: str | date | None = None,
    beta_window: int = BETA_WINDOW,
) -> pl.DataFrame:
    """Build the named state frame for one Ken French-style portfolio.

    Constructs ``g``, ``beta``, and ``dpo`` when those names appear in
    ``spec.names``. Every other name is taken from ``macro`` by column.
    """
    if portfolio not in total.columns or portfolio not in capgains.columns:
        raise ValueError(f"portfolio {portfolio!r} not in the return frames")
    if "date" not in total.columns:
        raise ValueError("total returns must have a date column")

    dates = total["date"].to_list()
    tot = total[portfolio].to_numpy().astype(float)
    cap = capgains[portfolio].to_numpy().astype(float)

    constructed: dict[str, np.ndarray] = {}
    names = set(spec.names)
    if "g" in names:
        constructed["g"] = compute_dividend_growth(tot, cap)
    if "dpo" in names:
        constructed["dpo"] = compute_payout_ratio_change(tot, cap)
    if "beta" in names:
        if "rf" not in macro.columns or "mkt" not in macro.columns:
            raise ValueError("macro must contain rf and mkt to build beta")
        joined = (
            pl.DataFrame({"date": dates})
            .join(macro.select(["date", "rf", "mkt"]), on="date", how="left")
        )
        constructed["beta"] = compute_rolling_betas(
            tot,
            joined["rf"].to_numpy().astype(float),
            joined["mkt"].to_numpy().astype(float),
            window=beta_window,
        )

    frame = pl.DataFrame({"date": dates, **constructed})
    extra = [c for c in spec.names if c not in constructed]
    if extra:
        missing = [c for c in extra if c not in macro.columns]
        if missing:
            raise ValueError(f"macro is missing columns required by spec: {missing}")
        frame = frame.join(macro.select(["date", *extra]), on="date", how="left")

    start_d = _parse_bound(start, end=False)
    end_d = _parse_bound(end, end=True)
    if start_d is not None:
        frame = frame.filter(pl.col("date") >= start_d)
    if end_d is not None:
        frame = frame.filter(pl.col("date") <= end_d)
    numeric = [c for c in frame.columns if c != spec.date]
    if numeric:
        frame = frame.with_columns(pl.col(numeric).fill_nan(None))
    frame = frame.drop_nulls()
    return validate_state(frame, spec)
