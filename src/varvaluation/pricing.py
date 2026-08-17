"""How well model present values line up with market equity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import polars as pl

from varvaluation.exceptions import NonStationaryVARError, PerpetuityDivergesError
from varvaluation.model import AngLiuModel
from varvaluation.spec import StateSpec


@dataclass(frozen=True)
class PricingFit:
    """Cross-section of model PV against market equity."""

    n: int
    n_failed: int
    median_pv_me: float
    mean_log_pv_me: float
    rmse_log_pv_me: float
    corr_log: float
    share_within_2x: float
    frame: pl.DataFrame


def pricing_errors(
    model: AngLiuModel,
    state: pl.DataFrame,
    *,
    me: str = "me",
    cash: str = "div",
    n: int = 40,
) -> PricingFit:
    """Value every row and compare to ``me``.

    ``state`` must contain the model's named states, ``cash`` (current
    cash-flow level), and ``me`` (market equity in the same units).
    """
    spec: StateSpec = model.spec
    pvs: list[float | None] = []
    for row in state.iter_rows(named=True):
        X = np.array([row[name] for name in spec.names], dtype=float)
        C = float(row[cash])
        try:
            pvs.append(float(model.value(X, C=C, n=n).pv))
        except (PerpetuityDivergesError, FloatingPointError, ValueError):
            pvs.append(None)
    frame = state.with_columns(pl.Series("pv", pvs))
    ok = frame.filter(
        pl.col("pv").is_not_null()
        & pl.col(me).is_not_null()
        & (pl.col(me) > 0)
        & (pl.col("pv") > 0)
    )
    if ok.height < 2:
        return PricingFit(
            n=0,
            n_failed=state.height,
            median_pv_me=float("nan"),
            mean_log_pv_me=float("nan"),
            rmse_log_pv_me=float("nan"),
            corr_log=float("nan"),
            share_within_2x=float("nan"),
            frame=frame,
        )
    ratio = ok["pv"].to_numpy() / ok[me].to_numpy()
    log_r = np.log(ratio)
    log_pv = np.log(ok["pv"].to_numpy())
    log_me = np.log(ok[me].to_numpy())
    if np.std(log_pv) < 1e-15 or np.std(log_me) < 1e-15:
        corr = 1.0 if np.allclose(log_pv, log_me) else float("nan")
    else:
        corr = float(np.corrcoef(log_pv, log_me)[0, 1])
    return PricingFit(
        n=ok.height,
        n_failed=state.height - ok.height,
        median_pv_me=float(np.median(ratio)),
        mean_log_pv_me=float(np.mean(log_r)),
        rmse_log_pv_me=float(np.sqrt(np.mean(log_r**2))),
        corr_log=corr,
        share_within_2x=float(np.mean(np.abs(log_r) < np.log(2.0))),
        frame=frame,
    )


def calibrate_alpha(
    fit,
    xi,
    Lambda,
    state: pl.DataFrame,
    *,
    n: int = 40,
    alpha0: float = 0.04,
    lo: float = 0.0,
    hi: float = 0.25,
    steps: int = 16,
    me: str = "me",
    cash: str = "div",
) -> tuple[float, PricingFit]:
    """Grid-search the discount intercept so median PV/ME is nearest 1."""

    def _eval(alpha: float) -> PricingFit | None:
        try:
            model = AngLiuModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=alpha)
        except NonStationaryVARError:
            return None
        return pricing_errors(model, state, me=me, cash=cash, n=n)

    best_a, best = alpha0, _eval(alpha0)
    for alpha in np.linspace(lo, hi, steps):
        err = _eval(float(alpha))
        if err is None or err.n < 2 or not np.isfinite(err.median_pv_me):
            continue
        if best is None or abs(np.log(err.median_pv_me)) < abs(np.log(best.median_pv_me)):
            best_a, best = float(alpha), err
    if best is None:
        raise NonStationaryVARError("no stationary alpha on the grid produced prices")
    return float(best_a), best


def as_of(
    state: pl.DataFrame,
    panel: pl.DataFrame,
    on: date,
    *,
    group: str = "permno",
) -> pl.DataFrame:
    """State rows on ``on``, with market equity from ``panel`` (prc × shrout)."""
    last = state.filter(pl.col("date") == on)
    me = (
        panel.filter(pl.col("date") == on)
        .select([group, "prc", "shrout"])
        .with_columns((pl.col("prc").abs() * pl.col("shrout")).alias("me"))
        .select([group, "me"])
    )
    return last.join(me, on=group, how="left")
