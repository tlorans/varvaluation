"""CRSP–Compustat firm panel from WRDS."""

from __future__ import annotations

import polars as pl

from varvaluation.wrds.connect import get_wrds_connection, load_or_cache

_CRSP_SQL = """
    SELECT permno, date, ret, retx, prc, shrout, hsiccd AS siccd
    FROM crsp.msf
    WHERE date >= '{start}'
      AND date <= '{end}'
"""

_COMPUSTAT_SQL = """
    SELECT gvkey, datadate, fyear, sich AS sic,
           seq, ceq, at, ni, dvt, csho
    FROM comp.funda
    WHERE indfmt = 'INDL'
      AND datafmt = 'STD' AND popsrc = 'D' AND consol = 'C'
      AND datadate >= '{start}'
      AND datadate <= '{end}'
"""

_CCM_SQL = """
    SELECT gvkey, lpermno, linktype, linkprim, linkdt, linkenddt
    FROM crsp.ccmxpf_lnkhist
    WHERE linktype IN ('LU', 'LC')
      AND substr(linkprim, 1, 1) = 'P'
"""


def _bound(value: str | None, *, default: str) -> str:
    if value is None:
        return default
    if len(value) == 7:
        return f"{value}-01"
    return value


def _fetch(sql: str) -> pl.DataFrame:
    conn = get_wrds_connection()
    try:
        pdf = conn.raw_sql(sql)
    finally:
        conn.close()
    return pl.from_pandas(pdf)


def load_crsp_monthly(
    start: str = "1960-01",
    end: str = "2026-12-31",
    *,
    use_cache: bool = True,
) -> pl.DataFrame:
    start_s, end_s = _bound(start, default="1960-01-01"), _bound(end, default="2026-12-31")

    def _build():
        df = _fetch(_CRSP_SQL.format(start=start_s, end=end_s))
        return df.with_columns(
            pl.col("date").cast(pl.Date),
            pl.col("permno").cast(pl.Int64),
            pl.col("ret").cast(pl.Float64),
            pl.col("retx").cast(pl.Float64),
            pl.col("prc").cast(pl.Float64),
            pl.col("shrout").cast(pl.Float64),
            pl.col("siccd").cast(pl.Int64),
        )

    return load_or_cache(f"crsp_retx_{start_s}_{end_s}", _build, use_cache=use_cache)


def load_compustat_annual(
    start: str = "1950-01",
    end: str = "2026-12-31",
    *,
    use_cache: bool = True,
) -> pl.DataFrame:
    start_s, end_s = _bound(start, default="1950-01-01"), _bound(end, default="2026-12-31")

    def _build():
        df = _fetch(_COMPUSTAT_SQL.format(start=start_s, end=end_s))
        return df.with_columns(
            pl.col("datadate").cast(pl.Date),
            pl.col("fyear").cast(pl.Int64),
            pl.col("sic").cast(pl.Int64),
            pl.col("seq").cast(pl.Float64),
            pl.col("ceq").cast(pl.Float64),
            pl.col("at").cast(pl.Float64),
            pl.col("ni").cast(pl.Float64),
            pl.col("dvt").cast(pl.Float64),
            pl.col("csho").cast(pl.Float64),
        )

    return load_or_cache(f"comp_{start_s}_{end_s}", _build, use_cache=use_cache)


def load_ccm_link(*, use_cache: bool = True) -> pl.DataFrame:
    def _build():
        df = _fetch(_CCM_SQL)
        return df.with_columns(
            pl.col("linkdt").cast(pl.Date),
            pl.col("linkenddt").cast(pl.Date),
            pl.col("lpermno").cast(pl.Int64),
        )

    return load_or_cache("ccm_link", _build, use_cache=use_cache)


def merge_firm_panel(crsp: pl.DataFrame, comp: pl.DataFrame, link: pl.DataFrame) -> pl.DataFrame:
    """Asof-merge Compustat onto CRSP through the CCM link (no WRDS needed)."""
    linked = comp.join(link, on="gvkey", how="inner")
    linked = linked.rename({"lpermno": "permno", "datadate": "date"})
    linked = linked.with_columns(pl.col("linkenddt").fill_null(pl.date(2099, 12, 31)))
    crsp = crsp.sort(["permno", "date"])
    linked = linked.sort(["permno", "date"])
    merged = crsp.join_asof(linked, by="permno", on="date", strategy="backward")
    merged = merged.filter(
        (pl.col("date") >= pl.col("linkdt")) & (pl.col("date") <= pl.col("linkenddt"))
    )
    drop = [c for c in ("linkdt", "linkenddt", "linktype", "linkprim") if c in merged.columns]
    return merged.drop(drop)


_COMPUSTAT_Q_SQL = """
    SELECT gvkey, datadate, fyearq, fqtr, sich AS sic,
           ibq, ceqq, cshoq, prccq
    FROM comp.fundq
    WHERE indfmt = 'INDL'
      AND datafmt = 'STD' AND popsrc = 'D' AND consol = 'C'
      AND datadate >= '{start}'
      AND datadate <= '{end}'
"""

_CRSP_DAILY_SQL = """
    SELECT permno, date, ret, prc, shrout
    FROM crsp.dsf
    WHERE date >= '{start}'
      AND date <= '{end}'
      {permno_clause}
"""

_CRSP_DSI_SQL = """
    SELECT date, vwretd
    FROM crsp.dsi
    WHERE date >= '{start}'
      AND date <= '{end}'
"""

_CRSP_MSI_SQL = """
    SELECT date, vwretd, vwretx
    FROM crsp.msi
    WHERE date >= '{start}'
      AND date <= '{end}'
"""


def load_compustat_quarterly(
    start: str = "1971-01",
    end: str = "2018-12-31",
    *,
    use_cache: bool = True,
) -> pl.DataFrame:
    """Compustat quarterly: ibq (item #8) and ceqq (item #59)."""
    start_s, end_s = _bound(start, default="1971-01-01"), _bound(end, default="2018-12-31")

    def _build():
        df = _fetch(_COMPUSTAT_Q_SQL.format(start=start_s, end=end_s))
        return df.with_columns(
            pl.col("datadate").cast(pl.Date),
            pl.col("fyearq").cast(pl.Int64),
            pl.col("fqtr").cast(pl.Int64),
            pl.col("sic").cast(pl.Int64),
            pl.col("ibq").cast(pl.Float64),
            pl.col("ceqq").cast(pl.Float64),
            pl.col("cshoq").cast(pl.Float64),
            pl.col("prccq").cast(pl.Float64),
        )

    return load_or_cache(f"compq_{start_s}_{end_s}", _build, use_cache=use_cache)


def load_crsp_daily(
    start: str = "1971-01",
    end: str = "2018-12-31",
    *,
    permnos: list[int] | None = None,
    use_cache: bool = True,
) -> pl.DataFrame:
    """CRSP daily stock file, optionally restricted to ``permnos``."""
    start_s, end_s = _bound(start, default="1971-01-01"), _bound(end, default="2018-12-31")
    tag = "all" if not permnos else f"n{len(permnos)}"
    clause = ""
    if permnos:
        chunk = ",".join(str(int(p)) for p in permnos)
        clause = f"AND permno IN ({chunk})"

    def _build():
        df = _fetch(
            _CRSP_DAILY_SQL.format(start=start_s, end=end_s, permno_clause=clause)
        )
        return df.with_columns(
            pl.col("date").cast(pl.Date),
            pl.col("permno").cast(pl.Int64),
            pl.col("ret").cast(pl.Float64),
            pl.col("prc").cast(pl.Float64),
            pl.col("shrout").cast(pl.Float64),
        )

    return load_or_cache(f"crsp_dsf_{start_s}_{end_s}_{tag}", _build, use_cache=use_cache)


def load_crsp_dsi(
    start: str = "1971-01",
    end: str = "2018-12-31",
    *,
    use_cache: bool = True,
) -> pl.DataFrame:
    """CRSP value-weighted market daily return."""
    start_s, end_s = _bound(start, default="1971-01-01"), _bound(end, default="2018-12-31")

    def _build():
        df = _fetch(_CRSP_DSI_SQL.format(start=start_s, end=end_s))
        return df.with_columns(
            pl.col("date").cast(pl.Date),
            pl.col("vwretd").cast(pl.Float64),
        )

    return load_or_cache(f"crsp_dsi_{start_s}_{end_s}", _build, use_cache=use_cache)


def merge_quarterly_panel(
    crsp_m: pl.DataFrame,
    compq: pl.DataFrame,
    link: pl.DataFrame,
) -> pl.DataFrame:
    """Asof-merge quarterly Compustat onto monthly CRSP through CCM."""
    linked = compq.join(link, on="gvkey", how="inner")
    linked = linked.rename({"lpermno": "permno", "datadate": "date"})
    linked = linked.with_columns(pl.col("linkenddt").fill_null(pl.date(2099, 12, 31)))
    crsp_m = crsp_m.sort(["permno", "date"])
    linked = linked.sort(["permno", "date"])
    merged = crsp_m.join_asof(linked, by="permno", on="date", strategy="backward")
    merged = merged.filter(
        (pl.col("date") >= pl.col("linkdt")) & (pl.col("date") <= pl.col("linkenddt"))
    )
    drop = [c for c in ("linkdt", "linkenddt", "linktype", "linkprim") if c in merged.columns]
    return merged.drop(drop)


def load_crsp_msi(
    start: str = "1960-01",
    end: str = "2026-12-31",
    *,
    use_cache: bool = True,
) -> pl.DataFrame:
    """CRSP monthly value-weighted market, with and without dividends."""
    start_s, end_s = _bound(start, default="1960-01-01"), _bound(end, default="2026-12-31")

    def _build():
        df = _fetch(_CRSP_MSI_SQL.format(start=start_s, end=end_s))
        return df.with_columns(
            pl.col("date").cast(pl.Date),
            pl.col("vwretd").cast(pl.Float64),
            pl.col("vwretx").cast(pl.Float64),
        )

    return load_or_cache(f"crsp_msi_{start_s}_{end_s}", _build, use_cache=use_cache)


def load_firm_panel(
    start: str = "1965-07",
    end: str | None = None,
    *,
    use_cache: bool = True,
) -> pl.DataFrame:
    """CRSP monthly returns with Compustat annuals forward-filled via CCM."""
    end_s = end or "2026-12"

    def _build():
        crsp = load_crsp_monthly(start="1960-01", end=end_s, use_cache=use_cache)
        comp = load_compustat_annual(start="1950-01", end=end_s, use_cache=use_cache)
        link = load_ccm_link(use_cache=use_cache)
        return merge_firm_panel(crsp, comp, link)

    return load_or_cache(f"firm_panel_retx_{start}_{end_s}", _build, use_cache=use_cache)
