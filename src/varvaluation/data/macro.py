"""FRED and Lettau–Ludvigson cay loaders."""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import polars as pl

from varvaluation.data.cache import cached_download
from varvaluation.data.french import load_ff3
from varvaluation.data.schemas import (
    _validate,
    cay_schema,
    inflation_schema,
    treasury_schema,
)

FRED_GS1_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GS1"
FRED_CPI_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL"
FRED_PCEC_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=PCEC"
# TNWBSHNO starts in 1945; BOGZ1FL192090005Q only in 1987.
FRED_NW_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=TNWBSHNO"
FRED_WAGES_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=A061RC1"
CAY_URLS = (
    "https://www.sydneyludvigson.com/s/cay_current.csv",
    "https://sites.google.com/site/martinlettau/cay_current.csv",
)


def _read_csv(path: str | Path | None, url: str, cache_name: str, refresh: bool) -> pl.DataFrame:
    if path is None:
        path = cached_download(url, cache_name, refresh=refresh)
    return pl.read_csv(path, try_parse_dates=True)


def _month_end(df: pl.DataFrame, date_col: str = "date") -> pl.DataFrame:
    return df.with_columns(pl.col(date_col).cast(pl.Date).dt.month_end())


def load_gs1(*, path: str | Path | None = None, refresh: bool = False) -> pl.DataFrame:
    """One-year Treasury yield (GS1), continuously compounded, monthly."""
    raw = _read_csv(path, FRED_GS1_URL, "gs1.csv", refresh)
    date_col = "observation_date" if "observation_date" in raw.columns else raw.columns[0]
    value_col = "GS1" if "GS1" in raw.columns else raw.columns[1]
    df = raw.rename({date_col: "date", value_col: "GS1"})
    df = df.with_columns(pl.col("GS1").cast(float, strict=False))
    df = df.filter(pl.col("GS1").is_not_null())
    df = df.with_columns((np.log(1 + pl.col("GS1") / 100.0)).alias("r"))
    df = _month_end(df.select(["date", "r"]))
    df = df.unique(subset=["date"], keep="last").sort("date")
    return _validate(treasury_schema, df, "gs1")


def load_cpi(*, path: str | Path | None = None, refresh: bool = False) -> pl.DataFrame:
    """Twelve-month log CPI inflation, monthly."""
    raw = _read_csv(path, FRED_CPI_URL, "cpi.csv", refresh)
    date_col = "observation_date" if "observation_date" in raw.columns else raw.columns[0]
    value_col = "CPIAUCSL" if "CPIAUCSL" in raw.columns else raw.columns[1]
    df = raw.rename({date_col: "date", value_col: "CPIAUCSL"})
    df = df.with_columns(pl.col("CPIAUCSL").cast(float, strict=False)).sort("date")
    df = df.with_columns(
        (pl.col("CPIAUCSL").log() - pl.col("CPIAUCSL").shift(12).log()).alias("pi")
    )
    df = _month_end(df)
    df = df.unique(subset=["date"], keep="last").sort("date")
    df = df.select(["date", "pi"]).drop_nulls(subset=["pi"])
    return _validate(inflation_schema, df, "cpi")


def _quarterly_to_monthly(df: pl.DataFrame) -> pl.DataFrame:
    df = _month_end(df).sort("date")
    start, end = df["date"].min(), df["date"].max()
    monthly = pl.DataFrame(
        {
            "date": pl.datetime_range(start, end, interval="1mo", eager=True)
            .dt.month_end()
            .cast(pl.Date)
        }
    )
    return monthly.join(df, on="date", how="left").with_columns(pl.col("cay").forward_fill())


def _parse_published_cay(raw: pl.DataFrame) -> pl.DataFrame:
    date_col = "date" if "date" in raw.columns else raw.columns[0]
    matches = [c for c in raw.columns if str(c).strip().lower().startswith("cay")]
    if not matches:
        raise ValueError(f"no cay column in file; columns are {raw.columns}")
    df = raw.rename({date_col: "date", matches[0]: "cay"}).select(["date", "cay"])
    return _validate(cay_schema, _quarterly_to_monthly(df), "cay")


def load_cay_from_fred(*, refresh: bool = False) -> pl.DataFrame:
    """Lettau–Ludvigson cay reconstructed from FRED (PCEC, household net worth, wages).

    Estimates the cointegrating vector on 1952–2019Q3 (the published sample)
    and applies it through the latest FRED quarter.
    """
    c = _read_csv(None, FRED_PCEC_URL, "fred_pcec.csv", refresh)
    a = _read_csv(None, FRED_NW_URL, "fred_tnwbshno.csv", refresh)
    y = _read_csv(None, FRED_WAGES_URL, "fred_wages.csv", refresh)

    def _one(raw: pl.DataFrame, name: str) -> pl.DataFrame:
        date_col = "observation_date" if "observation_date" in raw.columns else raw.columns[0]
        val_col = [c for c in raw.columns if c != date_col][0]
        return raw.rename({date_col: "date", val_col: name}).select(["date", name])

    c, a, y = _one(c, "c"), _one(a, "a"), _one(y, "y")
    y = y.filter(pl.col("date").dt.month().is_in([1, 4, 7, 10]))
    df = c.join(a, on="date", how="inner").join(y, on="date", how="inner").sort("date")
    df = df.with_columns(
        pl.col("c").cast(float).log().alias("log_c"),
        pl.col("a").cast(float).log().alias("log_a"),
        pl.col("y").cast(float).log().alias("log_y"),
    ).drop_nulls(subset=["log_c", "log_a", "log_y"])

    est = df.filter(pl.col("date") <= pl.date(2019, 9, 30))
    X = np.column_stack(
        [np.ones(est.height), est.select(["log_a", "log_y"]).to_numpy()]
    )
    coeffs, *_ = np.linalg.lstsq(X, est["log_c"].to_numpy(), rcond=None)
    full_X = np.column_stack(
        [np.ones(df.height), df.select(["log_a", "log_y"]).to_numpy()]
    )
    df = df.with_columns(pl.Series("cay", df["log_c"].to_numpy() - full_X @ coeffs))
    return _validate(cay_schema, _quarterly_to_monthly(df.select(["date", "cay"])), "cay")


def load_cay(*, path: str | Path | None = None, refresh: bool = False) -> pl.DataFrame:
    """Lettau–Ludvigson cay, quarterly, forward-filled to monthly.

    Tries a local path, then the published CSV URLs, then a FRED
    reconstruction (consumption, household net worth, labor income).
    """
    if path is not None:
        return _parse_published_cay(pl.read_csv(path, try_parse_dates=True))

    last_err: Exception | None = None
    for i, url in enumerate(CAY_URLS):
        try:
            raw = _read_csv(None, url, f"cay_current_{i}.csv", refresh)
            return _parse_published_cay(raw)
        except Exception as exc:
            last_err = exc
    try:
        return load_cay_from_fred(refresh=refresh)
    except Exception as exc:
        raise RuntimeError(
            f"could not load published cay ({last_err}) or reconstruct from FRED ({exc})"
        ) from exc


def load_macro(
    *,
    ff3: str | Path | None = None,
    gs1: str | Path | None = None,
    cpi: str | Path | None = None,
    cay: str | Path | None = None,
    refresh: bool = False,
    require_cay: bool = False,
) -> pl.DataFrame:
    """Join FF3, the one-year rate, inflation, and (if available) cay.

    FF3 / GS1 / CPI are required. cay is optional unless ``require_cay``
    is True: a failed cay download does not abort the rest of the frame.
    """
    frame = load_ff3(path=ff3, refresh=refresh)
    frame = frame.join(load_gs1(path=gs1, refresh=refresh), on="date", how="left")
    frame = frame.join(load_cpi(path=cpi, refresh=refresh), on="date", how="left")
    try:
        frame = frame.join(load_cay(path=cay, refresh=refresh), on="date", how="left")
    except Exception as exc:
        if require_cay:
            raise
        warnings.warn(f"cay not joined; continuing without it ({exc})", stacklevel=2)
    return frame.sort("date")
