"""Attach Cosemans / rolling daily betas to a firm-quarter panel."""

from __future__ import annotations

import numpy as np
import polars as pl

from varvaluation.cosemans import (
    RW_WINDOW,
    characteristic_variance,
    fit_characteristic_beta,
    fitted_characteristic_beta,
    posterior_beta,
    rolling_window_beta,
)


def quarter_end_betas(
    daily: pl.DataFrame,
    market: pl.DataFrame,
    *,
    group: str = "permno",
    rf: str = "rf",
    mkt: str = "mkt",
    window: int = RW_WINDOW,
) -> pl.DataFrame:
    """One rolling-window beta per permno-day, then keep quarter-ends.

    ``market`` must have ``date``, ``rf``, and ``mkt`` (daily).
    """
    joined = daily.join(market.select(["date", rf, mkt]), on="date", how="left")
    parts: list[pl.DataFrame] = []
    for key, sub in joined.group_by(group, maintain_order=True):
        gid = key[0] if isinstance(key, tuple) else key
        sub = sub.sort("date")
        beta, var = rolling_window_beta(
            sub["ret"].to_numpy().astype(float),
            sub[rf].to_numpy().astype(float),
            sub[mkt].to_numpy().astype(float),
            window=window,
        )
        parts.append(
            pl.DataFrame(
                {
                    group: [gid] * sub.height,
                    "date": sub["date"].to_list(),
                    "beta_rw": beta,
                    "var_rw": var,
                }
            )
        )
    if not parts:
        return pl.DataFrame(
            schema={group: pl.Int64, "date": pl.Date, "beta_rw": pl.Float64, "var_rw": pl.Float64}
        )
    frame = pl.concat(parts)
    # last trading day of each calendar quarter
    frame = frame.with_columns(pl.col("date").dt.quarter().alias("_q"))
    frame = frame.with_columns(pl.col("date").dt.year().alias("_y"))
    qe = (
        frame.group_by([group, "_y", "_q"])
        .agg(pl.col("date").max().alias("date"))
        .join(frame, on=[group, "date"], how="left")
        .drop(["_y", "_q"])
    )
    return qe


def attach_posterior_beta(
    quarters: pl.DataFrame,
    daily_betas: pl.DataFrame,
    *,
    group: str = "permno",
    method: str = "cosemans",
) -> pl.DataFrame:
    """Add ``beta`` to the firm-quarter panel.

    ``method="rolling"`` copies the 125-day beta. ``method="cosemans"``
    shrinks it toward the characteristic model when the columns exist.
    """
    q = quarters.sort([group, "date"])
    b = daily_betas.sort([group, "date"])
    q = q.join_asof(b, by=group, on="date", strategy="backward")
    if method == "rolling":
        return q.with_columns(pl.col("beta_rw").alias("beta"))

    if "beta_lag" not in q.columns:
        q = q.with_columns(pl.col("beta_rw").shift(1).over(group).alias("beta_lag"))
    need = ("defspr", "div", "rf_ann", "term", "mktvol", "size", "bm", "beta_lag")
    if any(c not in q.columns for c in need):
        return q.with_columns(pl.col("beta_rw").alias("beta"))

    fit = fit_characteristic_beta(q)
    q = fitted_characteristic_beta(q, fit, group=group)
    var_fc = characteristic_variance(q, fit, group=group)
    post, _ = posterior_beta(
        q["beta_fc"].to_numpy(),
        var_fc,
        q["beta_rw"].to_numpy(),
        q["var_rw"].to_numpy() if "var_rw" in q.columns else np.full(q.height, 0.05),
    )
    return q.with_columns(pl.Series("beta", post))
