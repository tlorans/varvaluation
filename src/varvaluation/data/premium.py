"""Market risk premium: DIV, DEF, Rf, TERM (Giacotto–Lin–Zhao eq. 13)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import polars as pl

from varvaluation.data.portfolio import compute_monthly_dividends


@dataclass(frozen=True)
class PremiumFit:
    """OLS of next-period excess market return on DIV, DEF, Rf, TERM."""

    intercept: float
    coef: dict[str, float]
    nobs: int
    r2: float

    def predict(self, frame: pl.DataFrame) -> pl.DataFrame:
        mrp = pl.lit(self.intercept)
        for name, value in self.coef.items():
            mrp = mrp + pl.col(name) * value
        return frame.with_columns(mrp.alias("mrp"))


def dividend_yield_from_returns(
    total: np.ndarray,
    capgains: np.ndarray,
    dates,
) -> pl.DataFrame:
    """Trailing-12m dividends over the price twelve months earlier.

    That is the CRSP value-weighted dividend yield used in the paper.
    ``total`` and ``capgains`` are simple monthly returns of the same index.
    """
    monthly_div, price = compute_monthly_dividends(total, capgains)
    n = len(monthly_div)
    div = np.full(n, np.nan)
    for i in range(12, n):
        window = monthly_div[i - 11 : i + 1]
        p_start = price[i - 12]
        if np.isfinite(window).all() and np.isfinite(p_start) and p_start > 0:
            div[i] = float(window.sum() / p_start)
    return pl.DataFrame({"date": list(dates), "div": div})


def annualize_rf(rf: np.ndarray) -> np.ndarray:
    """Monthly simple T-bill → continuously compounded annual rate."""
    rf = np.asarray(rf, dtype=float)
    out = np.full(rf.shape, np.nan)
    ok = np.isfinite(rf) & (rf > -1.0)
    out[ok] = 12.0 * np.log(1.0 + rf[ok])
    return out


def fit_mrp(
    frame: pl.DataFrame,
    *,
    market: str = "mkt",
    rf: str = "rf",
    predictors: tuple[str, ...] = ("div", "defspr", "rf_ann", "term"),
) -> PremiumFit:
    """Eq. 13: R_{m,t+1} − R_{f,t} on DIV, DEF, Rf, TERM.

    The left-hand side is the *next* month's simple excess return.
    Predictors are observed at t. ``rf_ann`` is the annualized T-bill.
    """
    needed = [market, rf, *predictors]
    missing = [c for c in needed if c not in frame.columns]
    if missing:
        raise ValueError(f"fit_mrp missing columns: {missing}")

    work = frame.select(["date", *needed]).sort("date")
    # Paper eq. 13: R_{m,t+1} − R_{f,t} on time-t predictors.
    y = (work[market].shift(-1) - work[rf]).to_numpy()
    X = work.select(list(predictors)).to_numpy().astype(float)
    ok = np.isfinite(y) & np.all(np.isfinite(X), axis=1)
    y = y[ok]
    X = X[ok]
    if len(y) < X.shape[1] + 2:
        raise ValueError(f"only {len(y)} rows for the premium regression")
    Z = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(Z, y, rcond=None)
    fitted = Z @ beta
    ss_res = float(np.sum((y - fitted) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return PremiumFit(
        intercept=float(beta[0]),
        coef={name: float(b) for name, b in zip(predictors, beta[1:], strict=True)},
        nobs=int(len(y)),
        r2=r2,
    )


def attach_mrp(frame: pl.DataFrame, fit: PremiumFit | None = None) -> pl.DataFrame:
    """Add ``mrp`` using ``fit``, or estimate eq. 13 on ``frame`` first."""
    if fit is None:
        fit = fit_mrp(frame)
    return fit.predict(frame)


def load_paper_macro(
    *,
    ff3: str | Path | None = None,
    path_aaa: str | Path | None = None,
    path_baa: str | Path | None = None,
    treasury_paths: dict[str, str | Path] | None = None,
    div: pl.DataFrame | None = None,
    refresh: bool = False,
    fit: bool = True,
) -> pl.DataFrame:
    """FF3 + DEF + Treasury curve + TERM, and MRP if DIV is available.

    ``div`` is an optional frame with columns ``date`` and ``div``. When
    it is present and ``fit`` is True, eq. 13 is estimated on the join
    and ``mrp`` is attached.
    """
    from varvaluation.data.french import load_ff3
    from varvaluation.data.yields import load_corporate_spread, load_treasury_curve

    frame = load_ff3(path=ff3, refresh=refresh)
    curve = load_treasury_curve(paths=treasury_paths, refresh=refresh)
    frame = frame.join(curve, on="date", how="left")
    spread = load_corporate_spread(path_aaa=path_aaa, path_baa=path_baa, refresh=refresh)
    frame = frame.join(spread.select(["date", "defspr"]), on="date", how="left")
    frame = paper_predictors(frame)
    if div is not None:
        frame = frame.join(div.select(["date", "div"]), on="date", how="left")
        if fit:
            try:
                frame = attach_mrp(frame)
            except ValueError:
                pass
    return frame.sort("date")


def paper_predictors(frame: pl.DataFrame) -> pl.DataFrame:
    """Add ``rf_ann`` and ``term`` if the raw pieces are present."""
    cols = frame.columns
    out = frame
    if "rf" in cols and "rf_ann" not in cols:
        out = out.with_columns(pl.Series("rf_ann", annualize_rf(out["rf"].to_numpy())))
    if "y10" in cols and "y1" in cols and "term" not in cols:
        out = out.with_columns((pl.col("y10") - pl.col("y1")).alias("term"))
    return out
