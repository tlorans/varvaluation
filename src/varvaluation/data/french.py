"""Ken French Data Library loaders."""

from __future__ import annotations

import zipfile
from pathlib import Path

import polars as pl

from varvaluation.data.cache import cached_download
from varvaluation.data.schemas import _validate, ff3_schema

FRENCH_BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"

FRENCH_FILES = {
    "ff3": "F-F_Research_Data_Factors_CSV.zip",
    "bm": "Portfolios_Formed_on_BE-ME_CSV.zip",
    "bm_exdiv": "Portfolios_Formed_on_BE-ME_Wout_Div_CSV.zip",
    "ind49": "49_Industry_Portfolios_CSV.zip",
    "ind49_exdiv": "49_Industry_Portfolios_Wout_Div_CSV.zip",
}

_STOP_MARKERS = (
    "Equal Weight Returns",
    "Annual from",
    "Average Equal Weighted",
    "Average Value Weighted Returns -- Annual",
    "Number of Firms",
    "Average Market Cap",
    "Percentile Portfolio",
    "Annual Factors",
)

DECILE_NAMES = [
    "Lo 10",
    "2-Dec",
    "3-Dec",
    "4-Dec",
    "5-Dec",
    "6-Dec",
    "7-Dec",
    "8-Dec",
    "9-Dec",
    "Hi 10",
]
DECILE_LABELS = [f"D{i}" for i in range(1, 11)]

MISSING_CODES = {"-99.99", "-999", "-99.99 "}


def _yyyymm_to_date(dates: list[int]) -> list:
    df = pl.DataFrame(
        {
            "year": [d // 100 for d in dates],
            "month": [d % 100 for d in dates],
            "day": [1] * len(dates),
        }
    )
    return df.select(
        pl.datetime("year", "month", "day").dt.month_end().cast(pl.Date)
    )["datetime"].to_list()


def _to_return(token: str) -> float | None:
    token = token.strip()
    if token in MISSING_CODES or token == "":
        return None
    return float(token) / 100.0


def read_text(path: str | Path) -> str:
    """Read a Ken French CSV, unzipping if ``path`` is a zip archive."""
    path = Path(path)
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith((".csv", ".txt"))]
            if not names:
                raise ValueError(f"no CSV/TXT member in {path}")
            with zf.open(names[0]) as fh:
                return fh.read().decode("latin-1")
    return path.read_text(encoding="latin-1")


def _resolve(key: str, path: str | Path | None, refresh: bool) -> str:
    if path is not None:
        return read_text(path)
    zip_name = FRENCH_FILES[key]
    dest = cached_download(FRENCH_BASE + zip_name, zip_name, refresh=refresh)
    return read_text(dest)


def parse_french_section(
    text: str,
    section_name: str,
    *,
    decile_only: bool = False,
) -> pl.DataFrame:
    """Parse one named monthly section of a Ken French multi-section file."""
    idx = text.find(section_name)
    if idx < 0:
        raise ValueError(f"could not find section {section_name!r}")

    rest = text[idx + len(section_name) :]
    for marker in _STOP_MARKERS:
        if marker == section_name:
            continue
        stop = rest.find(marker)
        if stop > 0:
            rest = rest[:stop]
            break

    lines = [ln for ln in rest.splitlines() if ln.strip()]
    header_i = 0
    while header_i < len(lines) and "," not in lines[header_i]:
        header_i += 1
    if header_i >= len(lines):
        raise ValueError(f"no header row in section {section_name!r}")

    headers = [h.strip() for h in lines[header_i].split(",")]

    if decile_only:
        col_map = {name: headers.index(name) for name in DECILE_NAMES if name in headers}
        if len(col_map) != 10:
            raise ValueError(f"expected 10 BE/ME decile columns, found {list(col_map)}")
        src_names = DECILE_NAMES
        out_names = DECILE_LABELS
    else:
        col_map = {h: j for j, h in enumerate(headers) if j > 0 and h}
        src_names = list(col_map)
        out_names = [n.strip() for n in src_names]

    dates: list[int] = []
    rows: list[dict] = []
    for line in lines[header_i + 1 :]:
        parts = line.split(",")
        if len(parts) < 2:
            continue
        try:
            date_val = int(float(parts[0].strip()))
        except (ValueError, IndexError):
            continue
        if not (190100 <= date_val <= 210000):
            continue
        row = {}
        for name, col in col_map.items():
            if col < len(parts):
                row[name] = _to_return(parts[col])
        dates.append(date_val)
        rows.append(row)

    df = pl.DataFrame(rows)
    df = df.with_columns(pl.Series("date", _yyyymm_to_date(dates)))
    rename = {src: out for src, out in zip(src_names, out_names, strict=False) if src != out}
    if rename:
        df = df.rename(rename)
    return df.select(["date", *out_names])


def parse_ff3(text: str) -> pl.DataFrame:
    dates: list[int] = []
    rows: list[dict] = []
    in_data = False
    for line in text.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            continue
        try:
            date_val = int(float(parts[0]))
        except (ValueError, IndexError):
            continue
        if 190000 < date_val < 210000:
            in_data = True
            rows.append(
                {
                    "mkt_rf": float(parts[1]) / 100.0,
                    "smb": float(parts[2]) / 100.0,
                    "hml": float(parts[3]) / 100.0,
                    "rf": float(parts[4]) / 100.0,
                }
            )
            dates.append(date_val)
        elif in_data and 1800 < date_val < 1900:
            break
    df = pl.DataFrame(rows)
    df = df.with_columns(pl.Series("date", _yyyymm_to_date(dates)))
    df = df.with_columns((pl.col("mkt_rf") + pl.col("rf")).alias("mkt"))
    return _validate(ff3_schema, df, "ff3")


def load_ff3(*, path: str | Path | None = None, refresh: bool = False) -> pl.DataFrame:
    """Fama–French three factors plus the riskless rate and market return."""
    return parse_ff3(_resolve("ff3", path, refresh))


def load_bm_deciles(
    *,
    path_total: str | Path | None = None,
    path_exdiv: str | Path | None = None,
    refresh: bool = False,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """10 book-to-market deciles: (total returns, capital-gains returns)."""
    total = parse_french_section(
        _resolve("bm", path_total, refresh),
        "Value Weight Returns -- Monthly",
        decile_only=True,
    )
    capgains = parse_french_section(
        _resolve("bm_exdiv", path_exdiv, refresh),
        "Value Weight Returns -- Monthly",
        decile_only=True,
    )
    return total, capgains


def load_industry49(
    *,
    path_total: str | Path | None = None,
    path_exdiv: str | Path | None = None,
    refresh: bool = False,
) -> tuple[pl.DataFrame, list[str], pl.DataFrame]:
    """49 industry portfolios: (total, names, capital-gains)."""
    total = parse_french_section(
        _resolve("ind49", path_total, refresh),
        "Average Value Weighted Returns -- Monthly",
        decile_only=False,
    )
    capgains = parse_french_section(
        _resolve("ind49_exdiv", path_exdiv, refresh),
        "Average Value Weighted Returns -- Monthly",
        decile_only=False,
    )
    names = [c for c in total.columns if c != "date"]
    return total, names, capgains
