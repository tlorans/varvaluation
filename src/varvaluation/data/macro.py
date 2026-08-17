"""FRED, Lettau–Ludvigson cay, and NASA GISTEMP loaders."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl

from varvaluation.data.cache import cached_download
from varvaluation.data.french import load_ff3
from varvaluation.data.schemas import (
    _validate,
    cay_schema,
    inflation_schema,
    temperature_schema,
    treasury_schema,
)

FRED_GS1_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GS1"
FRED_CPI_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL"
CAY_URL = "https://www.sydneyludvigson.com/s/cay_current.csv"
GISTEMP_URL = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"

_MONTH_COLS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


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


def load_cay(*, path: str | Path | None = None, refresh: bool = False) -> pl.DataFrame:
    """Lettau–Ludvigson cay, quarterly, forward-filled to monthly."""
    raw = _read_csv(path, CAY_URL, "cay_current.csv", refresh)
    date_col = "date" if "date" in raw.columns else raw.columns[0]
    matches = [c for c in raw.columns if str(c).strip().lower().startswith("cay")]
    if not matches:
        raise ValueError(f"no cay column in file; columns are {raw.columns}")
    df = raw.rename({date_col: "date", matches[0]: "cay"}).select(["date", "cay"])
    df = _month_end(df).sort("date")
    start, end = df["date"].min(), df["date"].max()
    monthly = pl.DataFrame(
        {
            "date": pl.datetime_range(start, end, interval="1mo", eager=True)
            .dt.month_end()
            .cast(pl.Date)
        }
    )
    df = monthly.join(df, on="date", how="left").with_columns(pl.col("cay").forward_fill())
    return _validate(cay_schema, df, "cay")


def parse_gistemp(text: str) -> pl.DataFrame:
    lines = text.splitlines()
    header_idx = next(
        (i for i, line in enumerate(lines) if line.strip().startswith("Year")),
        None,
    )
    if header_idx is None:
        raise ValueError("no 'Year' header row in GISTEMP file")
    headers = [h.strip() for h in lines[header_idx].split(",")]
    month_pos = {m: headers.index(m) for m in _MONTH_COLS if m in headers}
    if len(month_pos) != 12:
        raise ValueError(f"expected 12 monthly columns, found {list(month_pos)}")

    dates: list[int] = []
    values: list[float] = []
    for line in lines[header_idx + 1 :]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 13:
            continue
        try:
            year = int(parts[0])
        except (ValueError, IndexError):
            continue
        for m_num, month in enumerate(_MONTH_COLS, start=1):
            token = parts[month_pos[month]]
            if not token or token.startswith("*"):
                continue
            try:
                values.append(float(token))
            except ValueError:
                continue
            dates.append(year * 100 + m_num)

    from varvaluation.data.french import _yyyymm_to_date

    df = pl.DataFrame({"date": _yyyymm_to_date(dates), "temp": values}).sort("date")
    return _validate(temperature_schema, df, "gistemp")


def load_temperature(*, path: str | Path | None = None, refresh: bool = False) -> pl.DataFrame:
    """NASA GISTEMP v4 global land-ocean temperature anomaly, monthly, °C."""
    if path is None:
        path = cached_download(GISTEMP_URL, "gistemp_glb.csv", refresh=refresh)
    return parse_gistemp(Path(path).read_text(encoding="utf-8", errors="replace"))


def load_macro(
    *,
    ff3: str | Path | None = None,
    gs1: str | Path | None = None,
    cpi: str | Path | None = None,
    cay: str | Path | None = None,
    refresh: bool = False,
) -> pl.DataFrame:
    """Join FF3, the one-year rate, inflation, and cay on month-end dates."""
    frame = load_ff3(path=ff3, refresh=refresh)
    frame = frame.join(load_gs1(path=gs1, refresh=refresh), on="date", how="left")
    frame = frame.join(load_cpi(path=cpi, refresh=refresh), on="date", how="left")
    frame = frame.join(load_cay(path=cay, refresh=refresh), on="date", how="left")
    return frame.sort("date")
