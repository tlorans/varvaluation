"""Live Compustat Δp vs capital-gains proxy. Skipped without WRDS credentials."""

from __future__ import annotations

import os
from pathlib import Path

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


def test_market_compustat_dpo_finite():
    from varvaluation.angliu.payout import (
        crsp_vw_returns,
        market_compustat_dpo,
        proxy_vs_compustat,
    )

    total, cap = crsp_vw_returns(start="1995-01", end="2000-12-31")
    assert total.height > 50
    assert {"date", "MKT"}.issubset(total.columns)
    dpo = market_compustat_dpo(start="1995-01", end="2000-12-31")
    assert dpo.height > 12
    assert dpo["dpo"].is_finite().all()
    cmp = proxy_vs_compustat(total, cap, dpo, portfolio="MKT")
    assert cmp["nobs"] >= 12
    # Same economic object, different earnings measure — should move together.
    if cmp["nobs"] >= 24:
        assert cmp["corr"] > 0.0
