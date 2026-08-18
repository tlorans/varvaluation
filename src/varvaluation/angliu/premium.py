"""Conditional market premium of Ang and Liu (2004, §III)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import polars as pl
import statsmodels.api as sm

from varvaluation.spec import ExpectedReturnSpec, StateSpec


@dataclass(frozen=True)
class PremiumResult:
    """Overlapping annual regression y^m_{t+1} - r_t on (1, r, cay)."""

    coeffs: dict[str, float]
    stderrs: dict[str, float]
    tstats: dict[str, float]
    nobs: int
    r_squared: float
    sample: tuple[str, str]
    market: str


def _month_end(year: int, month: int) -> date:
    if month == 12:
        return date(year + 1, 1, 1).fromordinal(date(year + 1, 1, 1).toordinal() - 1)
    return date(year, month + 1, 1).fromordinal(date(year, month + 1, 1).toordinal() - 1)


def _parse_month(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return date(int(value[:4]), int(value[5:7]), 1)


def fit_premium(
    macro: pl.DataFrame,
    start: str | date,
    end: str | date,
    *,
    market: str = "mkt",
    rate: str = "r",
    cay: str = "cay",
    nw_lags: int = 12,
) -> PremiumResult:
    """Estimate λ_t = b0 + br r_t + bcay cay_t on overlapping annual market excess returns."""
    needed = [market, rate, cay]
    missing = [c for c in needed if c not in macro.columns]
    if missing:
        raise ValueError(f"fit_premium missing columns: {missing}")

    log_mkt = np.log(1.0 + macro[market].to_numpy().astype(float))
    frame = macro.with_columns(pl.Series("_log_mkt", log_mkt))
    frame = frame.with_columns(pl.col("_log_mkt").rolling_sum(12).shift(-12).alias("y_fwd"))
    frame = frame.with_columns((pl.col("y_fwd") - pl.col(rate)).alias("y"))
    lo = _parse_month(start)
    hi = _month_end(_parse_month(end).year, _parse_month(end).month)
    frame = (
        frame.filter(pl.col("date").ge(lo) & pl.col("date").le(hi))
        .select(["date", "y", rate, cay])
        .with_columns(pl.col(["y", rate, cay]).fill_nan(None))
        .drop_nulls()
        .sort("date")
    )
    if frame.height < 24:
        raise ValueError(f"only {frame.height} rows for the premium regression")

    y = frame["y"].to_numpy()
    X = np.column_stack(
        [np.ones(frame.height), frame[rate].to_numpy(), frame[cay].to_numpy()]
    )
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": nw_lags})
    keys = ("b0", "br", "bcay")
    return PremiumResult(
        coeffs={k: float(fit.params[i]) for i, k in enumerate(keys)},
        stderrs={k: float(fit.bse[i]) for i, k in enumerate(keys)},
        tstats={k: float(fit.tvalues[i]) for i, k in enumerate(keys)},
        nobs=int(fit.nobs),
        r_squared=float(fit.rsquared),
        sample=(str(frame["date"][0]), str(frame["date"][-1])),
        market=market,
    )


def expected_return_loadings(
    spec: StateSpec,
    premium: PremiumResult,
    *,
    rate: str = "r",
    beta: str = "beta",
) -> tuple[np.ndarray, np.ndarray]:
    """Map (b0, br, bcay) into (ξ, Λ) for μ_t = α + r_t + β_t λ_t."""
    return ExpectedReturnSpec(rate=rate, beta=beta, premium=("cay",)).xi_lambda(
        spec, premium.coeffs
    )


def capm_alpha(
    total: pl.DataFrame,
    macro: pl.DataFrame,
    portfolio: str,
    *,
    start: str | date | None = None,
    end: str | date | None = None,
) -> tuple[float, float]:
    """Annualised CAPM α and full-sample β from monthly log excess returns."""
    frame = total.select(["date", portfolio]).join(
        macro.select(["date", "rf", "mkt"]), on="date", how="inner"
    )
    if start is not None:
        frame = frame.filter(pl.col("date") >= _parse_month(start))
    if end is not None:
        hi = _month_end(_parse_month(end).year, _parse_month(end).month)
        frame = frame.filter(pl.col("date") <= hi)
    frame = frame.drop_nulls()
    y = np.log(1.0 + frame[portfolio].to_numpy()) - np.log(1.0 + frame["rf"].to_numpy())
    x = np.log(1.0 + frame["mkt"].to_numpy()) - np.log(1.0 + frame["rf"].to_numpy())
    ok = np.isfinite(y) & np.isfinite(x)
    design = np.column_stack([np.ones(int(ok.sum())), x[ok]])
    coeffs, *_ = np.linalg.lstsq(design, y[ok], rcond=None)
    return float(coeffs[0] * 12.0), float(coeffs[1])


def lambda_series(macro: pl.DataFrame, premium: PremiumResult) -> pl.DataFrame:
    """Attach λ_t = b0 + br r_t + bcay cay_t."""
    b = premium.coeffs
    return macro.with_columns(
        (b["b0"] + b["br"] * pl.col("r") + b["bcay"] * pl.col("cay")).alias("lam")
    )
