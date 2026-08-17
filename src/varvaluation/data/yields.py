"""Treasury yield curve from FRED (GS1 … GS30)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl

from varvaluation.data.macro import _month_end, _read_csv

FRED_GRAPH = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

# Tenors the paper needs for y(τ) and for TERM = GS10 − GS1.
TREASURY_TENORS: tuple[int, ...] = (1, 2, 3, 5, 7, 10, 20, 30)
TREASURY_IDS = {n: f"GS{n}" for n in TREASURY_TENORS}


def _load_fred_percent(
    series_id: str,
    *,
    path: str | Path | None,
    refresh: bool,
    out_name: str,
) -> pl.DataFrame:
    url = FRED_GRAPH + series_id
    raw = _read_csv(path, url, f"{series_id.lower()}.csv", refresh)
    date_col = "observation_date" if "observation_date" in raw.columns else raw.columns[0]
    value_col = series_id if series_id in raw.columns else raw.columns[1]
    df = raw.rename({date_col: "date", value_col: series_id})
    df = df.with_columns(pl.col(series_id).cast(float, strict=False))
    df = df.filter(pl.col(series_id).is_not_null())
    df = df.with_columns((np.log(1 + pl.col(series_id) / 100.0)).alias(out_name))
    df = _month_end(df.select(["date", out_name]))
    return df.unique(subset=["date"], keep="last").sort("date")


def load_corporate_spread(
    *,
    path_aaa: str | Path | None = None,
    path_baa: str | Path | None = None,
    refresh: bool = False,
) -> pl.DataFrame:
    """Moody's Baa minus Aaa, continuously compounded. Column ``defspr``."""
    aaa = _load_fred_percent("AAA", path=path_aaa, refresh=refresh, out_name="aaa")
    baa = _load_fred_percent("BAA", path=path_baa, refresh=refresh, out_name="baa")
    df = aaa.join(baa, on="date", how="inner")
    return df.with_columns((pl.col("baa") - pl.col("aaa")).alias("defspr")).sort("date")


def _tenors_from_paths(paths: dict[str, str | Path]) -> tuple[int, ...]:
    found: list[int] = []
    for n, series_id in TREASURY_IDS.items():
        if series_id in paths or f"y{n}" in paths:
            found.append(n)
    return tuple(found) if found else TREASURY_TENORS


def load_treasury_curve(
    *,
    paths: dict[str, str | Path] | None = None,
    refresh: bool = False,
    tenors: tuple[int, ...] | None = None,
) -> pl.DataFrame:
    """Continuously compounded Treasury yields, one column ``y{n}`` per tenor.

    If ``paths`` is given and ``tenors`` is not, only those series that
    have a path are loaded (so tests never hit the network).
    """
    paths = paths or {}
    if tenors is None:
        tenors = _tenors_from_paths(paths) if paths else TREASURY_TENORS
    frame: pl.DataFrame | None = None
    for n in tenors:
        series_id = TREASURY_IDS[n]
        col = f"y{n}"
        path = paths.get(series_id) or paths.get(col)
        one = _load_fred_percent(series_id, path=path, refresh=refresh, out_name=col)
        frame = one if frame is None else frame.join(one, on="date", how="full")
    assert frame is not None
    return frame.sort("date")


def interpolate_yields(row: dict[str, float] | pl.Series, n: int = 30) -> np.ndarray:
    """Integer-year curve from the available ``y{k}`` tenors.

    Linear in maturity. Flat extrapolation beyond the last observed tenor.
    Missing interior tenors are skipped. Raises if no tenor is present.
    """
    if isinstance(row, pl.Series):
        data = {k: row[k] for k in row.to_dict()}
    else:
        data = row
    knots: list[tuple[int, float]] = []
    for k in TREASURY_TENORS:
        val = data.get(f"y{k}")
        if val is None:
            continue
        try:
            fval = float(val)
        except (TypeError, ValueError):
            continue
        if np.isfinite(fval):
            knots.append((k, fval))
    if not knots:
        raise ValueError("no Treasury tenors available to interpolate")
    knots.sort()
    xs = np.array([k for k, _ in knots], dtype=float)
    ys = np.array([v for _, v in knots], dtype=float)
    maturities = np.arange(1, n + 1, dtype=float)
    out = np.interp(maturities, xs, ys)
    out[maturities < xs[0]] = ys[0]
    out[maturities > xs[-1]] = ys[-1]
    return out


def yield_curve_frame(curve: pl.DataFrame, n: int = 30) -> pl.DataFrame:
    """Add ``y`` as a list-column of length ``n`` on every date."""
    rows = []
    for rec in curve.iter_rows(named=True):
        try:
            rows.append(interpolate_yields(rec, n=n).tolist())
        except ValueError:
            rows.append(None)
    return curve.with_columns(pl.Series("y", rows))
