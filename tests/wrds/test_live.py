"""Live WRDS smoke test. Skipped unless credentials are in the environment."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import polars as pl
import pytest
from dotenv import load_dotenv

pytest.importorskip("wrds")

_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV)

_HAS_CREDS = bool(
    (os.environ.get("WRDS_USERNAME") or os.environ.get("WRDS_USER"))
    and os.environ.get("WRDS_PASSWORD")
)


pytestmark = [
    pytest.mark.wrds,
    pytest.mark.skipif(not _HAS_CREDS, reason="no WRDS credentials"),
]


def test_wrds_connection():
    from varvaluation.wrds.connect import get_wrds_connection

    conn = get_wrds_connection()
    try:
        one = conn.raw_sql("SELECT 1 AS x")
    finally:
        conn.close()
    assert int(one["x"].iloc[0]) == 1


def test_live_panel_and_firm_state():
    from varvaluation import StateSpec, estimate_var_panel
    from varvaluation.wrds import merge_firm_panel, prepare_firm_state
    from varvaluation.wrds.load import load_ccm_link, load_compustat_annual, load_crsp_monthly

    crsp = load_crsp_monthly(start="2019-01", end="2021-12-31", use_cache=True)
    comp = load_compustat_annual(start="2018-01", end="2021-12-31", use_cache=True)
    link = load_ccm_link(use_cache=True)
    assert crsp.height > 1000
    assert {"permno", "date", "ret"}.issubset(crsp.columns)
    assert comp.height > 100
    assert link.height > 100

    panel = merge_firm_panel(crsp, comp, link)
    assert panel.height > 100
    assert {"permno", "date", "seq", "ni"}.issubset(panel.columns)

    dates = panel["date"].unique().sort()
    n = dates.len()
    macro = pl.DataFrame(
        {
            "date": dates,
            "rf": np.full(n, 0.001),
            "mkt": np.full(n, 0.01),
            "r": np.full(n, 0.03),
            "cay": np.zeros(n),
            "pi": np.zeros(n),
        }
    )
    spec = StateSpec(
        names=("roe", "beta", "bm", "r", "cay", "pi"),
        cashflow="roe",
        group="permno",
        horizon=12,
        nw_lags=3,
    )
    state = prepare_firm_state(panel, macro, spec, beta_window=12)
    assert state.height > 50
    assert set(spec.names).issubset(state.columns)
    assert state["permno"].n_unique() >= 5

    # Keep the VAR small: most-observed firms only.
    top = (
        state.group_by("permno")
        .len()
        .sort("len", descending=True)
        .head(40)["permno"]
        .to_list()
    )
    slim = state.filter(pl.col("permno").is_in(top))
    fit = estimate_var_panel(slim, spec)
    assert fit.nobs > spec.K + 1
    assert fit.Phi.shape == (spec.K, spec.K)
    assert np.isfinite(fit.spectral_radius)
