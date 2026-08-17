"""Industry portfolios and the paper's Table 2–4 statistics.

SIC presets match Giacotto, Lin, and Zhao (2020). The same helpers
accept any range, so the insurance tables are a special case of a
general industry pipeline.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import polars as pl

from varvaluation.schemas import validate_state
from varvaluation.spec import StateSpec, paper_state_spec

# Inclusive SIC ranges, as in the paper section 4.
INSURANCE: dict[str, tuple[tuple[int, int], ...]] = {
    "all": ((6300, 6399),),
    "pc": ((6330, 6331),),
    "life": ((6310, 6319),),
    "health": ((6320, 6329),),
}

# Compustat universe excluding insurers. A reserved key, not a range.
INSURANCE_EX = "ex"

SicSpec = tuple[tuple[int, int], ...] | str


def select_sic(
    frame: pl.DataFrame,
    sic: SicSpec,
    *,
    sic_col: str = "sic",
    exclude: tuple[tuple[int, int], ...] | None = None,
) -> pl.DataFrame:
    """Keep rows whose SIC falls in ``sic``.

    ``sic`` is a tuple of inclusive ``(lo, hi)`` ranges, or the string
    ``"ex"`` for every firm outside 6300–6399. ``exclude`` drops extra
    ranges after the keep filter.
    """
    col = pl.col(sic_col)
    if sic == INSURANCE_EX or sic == "ex":
        keep = frame.filter(~col.is_between(6300, 6399))
    else:
        mask = pl.lit(False)
        for lo, hi in sic:
            mask = mask | col.is_between(lo, hi)
        keep = frame.filter(mask)
    if exclude:
        for lo, hi in exclude:
            keep = keep.filter(~col.is_between(lo, hi))
    return keep


def winsorize(frame: pl.DataFrame, column: str, level: float = 0.01) -> pl.DataFrame:
    """Clip ``column`` at the ``level`` and ``1-level`` sample quantiles."""
    lo = frame.select(pl.col(column).quantile(level)).item()
    hi = frame.select(pl.col(column).quantile(1.0 - level)).item()
    if lo is None or hi is None:
        return frame
    return frame.with_columns(pl.col(column).clip(lo, hi).alias(column))


def log1p_positive(ratio: pl.Expr) -> pl.Expr:
    """ln(1 + x) when 1+x > 0, else null."""
    return (
        pl.when(ratio.is_not_null() & (ratio > -1.0))
        .then((1.0 + ratio).log())
        .otherwise(None)
    )


def attach_size_bm(
    panel: pl.DataFrame,
    *,
    book: str = "ceqq",
    price: str = "prccq",
    shares: str = "cshoq",
) -> pl.DataFrame:
    """Market equity, log size, and book-to-market from quarterly files.

    Compustat ``prccq * cshoq`` is in millions, same units as ``ceqq``.
    """
    me = pl.col(price).abs() * pl.col(shares)
    df = panel.with_columns(me.alias("me"))
    return df.with_columns(
        pl.when(pl.col("me") > 0).then(pl.col("me").log()).otherwise(None).alias("size"),
        pl.when((pl.col("me") > 0) & (pl.col(book) > 0))
        .then(pl.col(book) / pl.col("me"))
        .otherwise(None)
        .alias("bm"),
    )


def compute_quarterly_roe(
    panel: pl.DataFrame,
    *,
    group: str = "permno",
    earnings: str = "ibq",
    book: str = "ceqq",
) -> pl.DataFrame:
    """Annualized log ROE from four-quarter earnings over lagged book.

    Paper section 4: (E_t + E_{t-1/4} + E_{t-1/2} + E_{t-3/4}) / B_{t-1}.
    We then store ``ln(1 + simple)`` so the clean-surplus identity holds.
    """
    df = panel.sort([group, "date"])
    trail = (
        pl.col(earnings).cast(pl.Float64).rolling_sum(4).over(group).alias("earn_4q")
    )
    lagged_book = pl.col(book).cast(pl.Float64).shift(1).over(group).alias("book_lag")
    df = df.with_columns(trail, lagged_book)
    simple = pl.col("earn_4q") / pl.col("book_lag")
    return df.with_columns(
        pl.when(
            pl.col("book_lag").is_not_null()
            & (pl.col("book_lag") > 0)
            & pl.col("earn_4q").is_not_null()
        )
        .then(log1p_positive(simple))
        .otherwise(None)
        .alias("roe")
    )


def compute_book_growth(
    panel: pl.DataFrame,
    *,
    group: str = "permno",
    book: str = "ceqq",
    lags: int = 4,
) -> pl.DataFrame:
    """Annual log book growth, ``ln(B_t / B_{t-4})`` on a quarterly file."""
    df = panel.sort([group, "date"])
    lagged = pl.col(book).cast(pl.Float64).shift(lags).over(group)
    return df.with_columns(
        pl.when(
            pl.col(book).is_not_null()
            & (pl.col(book) > 0)
            & lagged.is_not_null()
            & (lagged > 0)
        )
        .then((pl.col(book).cast(pl.Float64) / lagged).log())
        .otherwise(None)
        .alias("g")
    )


def value_weighted_state(
    panel: pl.DataFrame,
    names: Sequence[str],
    *,
    weight: str = "me",
    date: str = "date",
) -> pl.DataFrame:
    """Value-weighted industry averages of ``names`` on each date."""
    if weight not in panel.columns:
        raise ValueError(f"value-weight column {weight!r} is missing")
    w = pl.col(weight).cast(pl.Float64)
    aggs = []
    for name in names:
        aggs.append(
            ((pl.col(name).cast(pl.Float64) * w).sum() / w.sum()).alias(name)
        )
    return panel.group_by(date).agg(aggs).sort(date)


def prepare_industry_state(
    panel: pl.DataFrame,
    macro: pl.DataFrame,
    spec: StateSpec | None = None,
    *,
    sic: SicSpec = INSURANCE["all"],
    sic_col: str = "sic",
    weight: str = "me",
    group: str = "permno",
    earnings: str = "ibq",
    book: str = "ceqq",
    winsor_bm: float | None = 0.01,
) -> pl.DataFrame:
    """Build the industry VAR state (ROE, g, β, MRP) from a firm-quarter panel.

    Constructs ``roe`` and ``g`` when those names are in the spec and the
    raw columns exist. ``beta`` is taken from the panel (already Cosemans
    or rolling). ``mrp`` and any other name are joined from ``macro``.
    """
    spec = spec or paper_state_spec()
    df = select_sic(panel, sic, sic_col=sic_col)
    if "bm" in df.columns and winsor_bm is not None:
        df = winsorize(df, "bm", level=winsor_bm)
    names = set(spec.names)
    if "roe" in names and "roe" not in df.columns:
        df = compute_quarterly_roe(df, group=group, earnings=earnings, book=book)
    if "g" in names and "g" not in df.columns:
        df = compute_book_growth(df, group=group, book=book)
    firm_names = [n for n in spec.names if n in df.columns and n != "mrp"]
    if not firm_names:
        raise ValueError("panel has none of the spec names after construction")
    needed = [group, spec.date, *firm_names]
    if weight in df.columns:
        needed.append(weight)
    industry = value_weighted_state(
        df.select(needed).drop_nulls(),
        firm_names,
        weight=weight,
        date=spec.date,
    )
    extra = [n for n in spec.names if n not in industry.columns]
    if extra:
        missing = [c for c in extra if c not in macro.columns]
        if missing:
            raise ValueError(f"macro is missing columns required by spec: {missing}")
        industry = industry.join(macro.select([spec.date, *extra]), on=spec.date, how="left")
    industry = industry.drop_nulls()
    return validate_state(industry, spec)


@dataclass(frozen=True)
class MeanTest:
    """One row of the paper's Table 2 or 3."""

    tau: int
    mean: float
    tstat: float
    pvalue: float
    lower: float
    upper: float


def _mean_t(x: np.ndarray) -> tuple[float, float, float, float, float]:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 2:
        return float("nan"), float("nan"), float("nan"), float("nan"), float("nan")
    mean = float(np.mean(x))
    se = float(np.std(x, ddof=1) / np.sqrt(n))
    tstat = mean / se if se > 0 else float("nan")
    # Normal reference; the paper reports a t-stat and a p-value.
    from math import erfc

    pvalue = float(erfc(abs(tstat) / np.sqrt(2.0)))
    half = 1.96 * se
    return mean, tstat, pvalue, mean - half, mean + half


def capm_tests(
    rho: np.ndarray,
    capm: np.ndarray,
    taus: Sequence[int] = (1, 5, 10, 15, 20, 25, 30),
) -> list[MeanTest]:
    """Table 2: H0 that the mean ρ(τ) equals the mean CAPM rate.

    ``rho`` is T × N (dates × maturities), ``capm`` is length T.
    """
    rho = np.asarray(rho, dtype=float)
    capm = np.asarray(capm, dtype=float)
    out: list[MeanTest] = []
    for tau in taus:
        if tau < 1 or tau > rho.shape[1]:
            raise ValueError(f"τ={tau} is outside 1..{rho.shape[1]}")
        diff = rho[:, tau - 1] - capm
        mean, tstat, pvalue, lo, hi = _mean_t(diff)
        # Report the mean of ρ(τ), not of the difference — Table 2's first row.
        rho_mean = float(np.nanmean(rho[:, tau - 1]))
        out.append(
            MeanTest(
                tau=tau,
                mean=rho_mean,
                tstat=tstat,
                pvalue=pvalue,
                lower=rho_mean + (lo - mean) if np.isfinite(mean) else float("nan"),
                upper=rho_mean + (hi - mean) if np.isfinite(mean) else float("nan"),
            )
        )
    return out


def slope_tests(
    rho: np.ndarray,
    taus: Sequence[int] = (5, 10, 15, 20, 25, 30),
) -> list[MeanTest]:
    """Table 3: H0 that mean ρ(τ) equals mean ρ(1)."""
    rho = np.asarray(rho, dtype=float)
    out: list[MeanTest] = []
    short = rho[:, 0]
    for tau in taus:
        if tau < 1 or tau > rho.shape[1]:
            raise ValueError(f"τ={tau} is outside 1..{rho.shape[1]}")
        slope = rho[:, tau - 1] - short
        mean, tstat, pvalue, lo, hi = _mean_t(slope)
        out.append(
            MeanTest(tau=tau, mean=mean, tstat=tstat, pvalue=pvalue, lower=lo, upper=hi)
        )
    return out


def curve_panel(
    model,
    state: pl.DataFrame,
    y,
    n: int = 30,
) -> np.ndarray:
    """Evaluate ``cost_of_capital`` on every row of ``state``. Shape T × n.

    ``y`` is a scalar, a length-``n`` array, or a T × n array (one curve
    per date).
    """
    spec: StateSpec = model.spec
    X = state.select(list(spec.names)).to_numpy().astype(float)
    y_arr = np.asarray(y, dtype=float)
    out = np.zeros((X.shape[0], n))
    from varvaluation.exceptions import TermStructureError

    for t in range(X.shape[0]):
        yt = y_arr[t] if y_arr.ndim == 2 else y
        try:
            out[t] = model.cost_of_capital(X[t], yt, n)
        except TermStructureError:
            out[t] = np.nan
    return out
