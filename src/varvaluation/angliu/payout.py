"""Compustat payout-ratio change and the CRSP value-weighted market.

Ang and Liu construct Δp from Compustat earnings. The public recipe proxies
earnings growth with the capital-gains return. This module rebuilds the
paper's object on the CRSP VW market (and, optionally, SIC industry bags).
It does not claim to reconstruct Ken French BE/ME decile earnings.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from varvaluation.angliu.spec import INDUSTRY_SIC
from varvaluation.data.portfolio import compute_payout_ratio_change
from varvaluation.wrds.load import (
    load_ccm_link,
    load_compustat_annual,
    load_crsp_monthly,
    load_crsp_msi,
    merge_firm_panel,
)


def crsp_vw_returns(
    start: str = "1960-01",
    end: str = "2026-12-31",
    *,
    use_cache: bool = True,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Value-weighted market as (total, ex-div) frames with a ``MKT`` column."""
    msi = load_crsp_msi(start=start, end=end, use_cache=use_cache)
    msi = msi.with_columns(pl.col("date").dt.month_end())
    total = msi.select(["date", pl.col("vwretd").alias("MKT")])
    cap = msi.select(["date", pl.col("vwretx").alias("MKT")])
    return total, cap


def market_compustat_dpo(
    start: str = "1960-01",
    end: str = "2000-12-31",
    *,
    use_cache: bool = True,
) -> pl.DataFrame:
    """Aggregate Δp_t = Δ log(TTM dividends / TTM earnings) on CRSP–Compustat.

    Dividends are the CRSP ``ret − retx`` gap times lagged market equity.
    Earnings are last-reported annual NI, positive only, summed across firms
    in the linked universe. This is a market object, not a French decile.
    """
    crsp = load_crsp_monthly(start=start, end=end, use_cache=use_cache)
    comp = load_compustat_annual(start="1950-01", end=end, use_cache=use_cache)
    link = load_ccm_link(use_cache=use_cache)
    panel = merge_firm_panel(crsp, comp, link)
    return _aggregate_dpo(panel)


def industry_compustat_dpo(
    sic: tuple[tuple[int, int], ...],
    start: str = "1960-01",
    end: str = "2000-12-31",
    *,
    use_cache: bool = True,
) -> pl.DataFrame:
    """Same aggregate Δp, restricted to SIC ranges (not Ken French names)."""
    crsp = load_crsp_monthly(start=start, end=end, use_cache=use_cache)
    comp = load_compustat_annual(start="1950-01", end=end, use_cache=use_cache)
    link = load_ccm_link(use_cache=use_cache)
    panel = merge_firm_panel(crsp, comp, link)
    sic_col = "sic" if "sic" in panel.columns else "siccd"
    mask = pl.lit(False)
    for lo, hi in sic:
        mask = mask | pl.col(sic_col).is_between(lo, hi)
    return _aggregate_dpo(panel.filter(mask))


def _aggregate_dpo(panel: pl.DataFrame) -> pl.DataFrame:
    work = panel.sort(["permno", "date"])
    work = work.with_columns(
        (pl.col("prc").abs() * pl.col("shrout")).alias("me"),
        pl.col("ni").cast(pl.Float64),
        (pl.col("ret") - pl.col("retx")).alias("dp"),
    )
    work = work.with_columns(pl.col("me").shift(1).over("permno").alias("me_lag"))
    work = work.with_columns((pl.col("dp") * pl.col("me_lag")).alias("div_m"))
    # Positive earnings only, as in a payout ratio.
    work = work.with_columns(
        pl.when(pl.col("ni") > 0.0).then(pl.col("ni")).otherwise(None).alias("earn")
    )
    monthly = (
        work.group_by("date")
        .agg(
            pl.col("div_m").sum().alias("div_m"),
            pl.col("earn").sum().alias("earn"),
        )
        .sort("date")
    )
    monthly = monthly.with_columns(
        pl.col("div_m").rolling_sum(window_size=12, min_samples=12).alias("div_ttm"),
        pl.col("earn").rolling_sum(window_size=12, min_samples=12).alias("earn_ttm"),
    )
    monthly = monthly.with_columns(
        pl.when(
            pl.col("div_ttm").is_not_null()
            & pl.col("earn_ttm").is_not_null()
            & (pl.col("div_ttm") > 0.0)
            & (pl.col("earn_ttm") > 0.0)
        )
        .then((pl.col("div_ttm") / pl.col("earn_ttm")).log())
        .otherwise(None)
        .alias("log_payout")
    )
    monthly = monthly.with_columns(
        (pl.col("log_payout") - pl.col("log_payout").shift(12)).alias("dpo")
    )
    return monthly.select(["date", "dpo", "div_ttm", "earn_ttm"]).drop_nulls(subset=["dpo"])


def proxy_vs_compustat(
    total: pl.DataFrame,
    capgains: pl.DataFrame,
    compustat: pl.DataFrame,
    *,
    portfolio: str = "MKT",
) -> dict[str, float]:
    """Correlation and scale of the capital-gains proxy vs Compustat Δp."""
    proxy = compute_payout_ratio_change(
        total[portfolio].to_numpy().astype(float),
        capgains[portfolio].to_numpy().astype(float),
    )
    left = pl.DataFrame({"date": total["date"], "proxy": proxy}).drop_nulls()
    joined = left.join(compustat.select(["date", "dpo"]), on="date", how="inner")
    if joined.height < 24:
        return {"nobs": float(joined.height), "corr": float("nan")}
    a = joined["proxy"].to_numpy()
    b = joined["dpo"].to_numpy()
    ok = np.isfinite(a) & np.isfinite(b)
    return {
        "nobs": float(ok.sum()),
        "corr": float(np.corrcoef(a[ok], b[ok])[0, 1]) if ok.sum() > 2 else float("nan"),
        "proxy_sd": float(np.std(a[ok], ddof=1)),
        "compustat_sd": float(np.std(b[ok], ddof=1)),
        "proxy_mean": float(np.mean(a[ok])),
        "compustat_mean": float(np.mean(b[ok])),
    }


def attach_compustat_dpo(state: pl.DataFrame, dpo: pl.DataFrame) -> pl.DataFrame:
    """Replace the ``dpo`` column with the Compustat series (inner join)."""
    rest = [c for c in state.columns if c != "dpo"]
    return (
        state.select(rest)
        .join(dpo.select(["date", "dpo"]), on="date", how="inner")
        .drop_nulls()
        .sort("date")
    )


def sic_for(name: str) -> tuple[tuple[int, int], ...] | None:
    return INDUSTRY_SIC.get(name)
