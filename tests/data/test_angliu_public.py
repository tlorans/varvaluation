"""Public-data helpers for the Ang–Liu recipe, offline against fixtures."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

pytest.importorskip("pandas_datareader")

from varvaluation.angliu import paper_spec
from varvaluation.angliu.premium import fit_premium
from varvaluation.data.french import parse_ff3
from varvaluation.data.portfolio import compute_dividend_growth, compute_payout_ratio_change

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_paper_spec_and_portfolio_constructors_on_fixture():
    assert paper_spec().cashflow == "g"
    ff3 = parse_ff3((FIXTURES / "ff3_sample.csv").read_text(encoding="latin-1"))
    assert "mkt" in ff3.columns
    n = ff3.height
    tot = ff3.select(["date", pl.col("mkt").alias("D10")])
    cap = ff3.select(["date", (pl.col("mkt") - 0.002).alias("D10")])
    g = compute_dividend_growth(tot["D10"].to_numpy(), cap["D10"].to_numpy())
    dpo = compute_payout_ratio_change(tot["D10"].to_numpy(), cap["D10"].to_numpy())
    assert g.shape == (n,)
    assert dpo.shape == (n,)
    # Four fixture months are too short for trailing-year g; constructors
    # must still return a finite-or-null array of the same length.
    assert n == 4


def test_fit_premium_on_constructed_macro():
    dates = pl.date_range(pl.date(1965, 7, 31), pl.date(2000, 12, 31), "1mo", eager=True)
    dates = dates.dt.month_end()
    n = dates.len()
    import numpy as np

    rng = np.random.default_rng(0)
    macro = pl.DataFrame(
        {
            "date": dates,
            "mkt": 0.01 + 0.04 * rng.standard_normal(n),
            "r": 0.05 + 0.01 * rng.standard_normal(n),
            "cay": 0.02 * rng.standard_normal(n),
        }
    )
    rp = fit_premium(macro, "1965-07", "2000-12")
    assert set(rp.coeffs) == {"b0", "br", "bcay"}
    assert rp.nobs > 100
    assert np.isfinite(rp.r_squared)
