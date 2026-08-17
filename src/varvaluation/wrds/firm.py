"""Firm-level state construction (g, roe, bm, rolling beta).

``g`` is log growth of trailing twelve-month dividends implied by
CRSP ``ret`` and ``retx``. ``roe`` is log(NI / lagged book equity),
not Vuolteenaho's ``e_t = log(1 + X/B)``.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import polars as pl

from varvaluation.betas import BETA_WINDOW, compute_rolling_betas
from varvaluation.schemas import validate_state
from varvaluation.spec import StateSpec

FIN_SIC = (6000, 6999)
UTIL_SIC = (4900, 4999)


def filter_firms(
    panel: pl.DataFrame,
    *,
    exclude_financials: bool = True,
    exclude_utilities: bool = True,
) -> pl.DataFrame:
    """Drop financials/utilities, require positive book equity and shares."""
    df = panel
    sic_src = "sic" if "sic" in df.columns else "siccd"
    df = df.with_columns(
        pl.when(pl.col(sic_src).is_null())
        .then(pl.col("siccd") if "siccd" in df.columns else pl.lit(None))
        .otherwise(pl.col(sic_src))
        .alias("sic_eff")
    )
    if exclude_financials:
        df = df.filter(~pl.col("sic_eff").is_between(FIN_SIC[0], FIN_SIC[1]))
    if exclude_utilities:
        df = df.filter(~pl.col("sic_eff").is_between(UTIL_SIC[0], UTIL_SIC[1]))

    be = (
        pl.when(pl.col("seq").is_not_null() & (pl.col("seq") > 0))
        .then(pl.col("seq"))
        .otherwise(
            pl.when(pl.col("ceq").is_not_null() & (pl.col("ceq") > 0))
            .then(pl.col("ceq"))
            .otherwise(None)
        )
    )
    df = df.with_columns(be.alias("book_equity"))
    df = df.filter(pl.col("csho").is_not_null() & (pl.col("csho") > 0))
    if "ret" in df.columns:
        df = df.filter(pl.col("ret").is_not_null())
    return df


def compute_firm_dividend_growth(panel: pl.DataFrame) -> pl.DataFrame:
    """Hodrick trailing-year log dividend growth and the dollar TTM level.

    Monthly dollars are ``(ret - retx) * lagged |prc| * shrout``. ``g`` is
    ``log(TTM_t / TTM_{t-12})`` when both TTM levels are positive.
    ``div`` is that TTM level, in CRSP units (thousands of dollars).
    """
    if "retx" not in panel.columns:
        raise ValueError("panel must contain retx (ex-dividend return) to build g")
    if "ret" not in panel.columns or "prc" not in panel.columns or "shrout" not in panel.columns:
        raise ValueError("panel must contain ret, prc, and shrout to build g")

    parts: list[pl.DataFrame] = []
    for pn in panel["permno"].unique().sort().to_list():
        sub = panel.filter(pl.col("permno") == pn).sort("date")
        ret = sub["ret"].to_numpy().astype(float)
        retx = sub["retx"].to_numpy().astype(float)
        me = (sub["prc"].abs() * sub["shrout"]).to_numpy().astype(float)
        n = len(ret)
        me_lag = np.concatenate([[np.nan], me[:-1]])
        monthly = (ret - retx) * me_lag
        ttm = np.full(n, np.nan)
        g = np.full(n, np.nan)
        for i in range(11, n):
            window = monthly[i - 11 : i + 1]
            if np.isfinite(window).all():
                ttm[i] = float(window.sum())
        for i in range(23, n):
            now, prev = ttm[i], ttm[i - 12]
            if np.isfinite(now) and np.isfinite(prev) and now > 0 and prev > 0:
                g[i] = float(np.log(now / prev))
        parts.append(
            pl.DataFrame(
                {
                    "permno": [pn] * n,
                    "date": sub["date"].to_list(),
                    "g": g,
                    "div": ttm,
                }
            )
        )
    built = pl.concat(parts)
    return panel.join(built, on=["permno", "date"], how="left")


def compute_roe(panel: pl.DataFrame) -> pl.DataFrame:
    """Annual log ROE = log(NI / lagged book equity), forward-filled monthly."""
    df = panel.sort(["permno", "date"])
    annual = (
        df.group_by(["permno", "fyear"], maintain_order=True)
        .agg(
            pl.col("ni").first().alias("ni"),
            pl.col("book_equity").first().alias("be_current"),
            pl.col("date").min().alias("fy_date"),
        )
        .sort(["permno", "fyear"])
    )
    annual = annual.with_columns(pl.col("be_current").shift(1).over("permno").alias("be_lagged"))
    annual = annual.with_columns(
        pl.when(
            pl.col("ni").is_not_null()
            & pl.col("be_lagged").is_not_null()
            & (pl.col("be_lagged") > 0)
            & (pl.col("ni") > 0)
        )
        .then((pl.col("ni") / pl.col("be_lagged")).log())
        .otherwise(None)
        .alias("roe")
    )
    return df.join_asof(
        annual.select(["permno", "fy_date", "roe"]).rename({"fy_date": "date"}),
        by="permno",
        on="date",
        strategy="backward",
    )


def compute_book_to_market(panel: pl.DataFrame) -> pl.DataFrame:
    """log(book equity / market equity), Compustat $m vs CRSP prc * shrout."""
    df = panel.with_columns((pl.col("prc").abs() * pl.col("shrout")).alias("me"))
    return df.with_columns(
        pl.when(
            pl.col("book_equity").is_not_null()
            & (pl.col("book_equity") > 0)
            & (pl.col("me") > 0)
        )
        .then((pl.col("book_equity") * 1e3 / pl.col("me")).log())
        .otherwise(None)
        .alias("bm")
    )


def _parse_bound(value: str | date | None, *, end: bool) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    year, month = int(value[:4]), int(value[5:7])
    if end:
        if month == 12:
            nxt = date(year + 1, 1, 1)
        else:
            nxt = date(year, month + 1, 1)
        return date.fromordinal(nxt.toordinal() - 1)
    return date(year, month, 1)


def prepare_firm_state(
    panel: pl.DataFrame,
    macro: pl.DataFrame,
    spec: StateSpec,
    *,
    start: str | date | None = None,
    end: str | date | None = None,
    beta_window: int = BETA_WINDOW,
    exclude_financials: bool = True,
    exclude_utilities: bool = True,
) -> pl.DataFrame:
    """Build the named firm-level state panel.

    Constructs ``g``, ``roe``, ``bm``, and ``beta`` when those names
    are in ``spec.names``. Other names are joined from ``macro`` by
    column. ``spec.group`` should be ``permno``. When ``g`` is built,
    trailing twelve-month dividends stay on the frame as ``div``.
    """
    df = filter_firms(
        panel,
        exclude_financials=exclude_financials,
        exclude_utilities=exclude_utilities,
    )
    names = set(spec.names)
    if "g" in names:
        df = compute_firm_dividend_growth(df)
    if "roe" in names:
        df = compute_roe(df)
    if "bm" in names:
        df = compute_book_to_market(df)
    if "beta" in names:
        if "rf" not in macro.columns or "mkt" not in macro.columns:
            raise ValueError("macro must contain rf and mkt to build beta")
        df = df.join(macro.select(["date", "rf", "mkt"]), on="date", how="left")
        beta_frames = []
        for pn in df["permno"].unique().sort().to_list():
            sub = df.filter(pl.col("permno") == pn).sort("date")
            betas = compute_rolling_betas(
                sub["ret"].to_numpy().astype(float),
                sub["rf"].to_numpy().astype(float),
                sub["mkt"].to_numpy().astype(float),
                window=beta_window,
            )
            beta_frames.append(
                pl.DataFrame(
                    {
                        "permno": [pn] * len(sub),
                        "date": sub["date"].to_list(),
                        "beta": betas,
                    }
                )
            )
        df = df.join(pl.concat(beta_frames), on=["permno", "date"], how="left")

    keep = ["permno", "date", *[c for c in spec.names if c in df.columns]]
    if "div" in df.columns:
        keep.append("div")
    frame = df.select(keep)
    extra = [c for c in spec.names if c not in frame.columns]
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
    numeric = [c for c in frame.columns if c not in {spec.date, spec.group or "permno"}]
    if numeric:
        frame = frame.with_columns(pl.col(numeric).fill_nan(None))
    frame = frame.drop_nulls()
    return validate_state(frame, spec)
