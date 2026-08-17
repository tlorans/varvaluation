import math
from pathlib import Path

import numpy as np
import polars as pl
import pytest

pytest.importorskip("pandas_datareader")

from varvaluation.data import (
    annualize_rf,
    dividend_yield_from_returns,
    fit_mrp,
    interpolate_yields,
    load_corporate_spread,
    load_paper_macro,
    load_treasury_curve,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_corporate_spread_is_baa_minus_aaa():
    df = load_corporate_spread(
        path_aaa=FIXTURES / "aaa_sample.csv",
        path_baa=FIXTURES / "baa_sample.csv",
    )
    assert df.height == 3
    expected = math.log(1 + 0.038) - math.log(1 + 0.032)
    assert df["defspr"][0] == pytest.approx(expected)


def test_treasury_curve_and_interpolation():
    curve = load_treasury_curve(
        paths={
            "GS1": FIXTURES / "gs1_sample.csv",
            "GS10": FIXTURES / "gs10_sample.csv",
        },
        tenors=(1, 10),
    )
    assert {"y1", "y10"}.issubset(curve.columns)
    y = interpolate_yields(curve.row(0, named=True), n=10)
    assert y.shape == (10,)
    assert y[0] == pytest.approx(math.log(1 + 0.0236))
    assert y[9] == pytest.approx(math.log(1 + 0.0280))
    assert y[0] < y[4] < y[9]


def test_dividend_yield_from_returns():
    n = 24
    total = np.full(n, 0.01)
    capgains = np.full(n, 0.006)
    dates = [f"1953-{m:02d}-28" for m in range(1, 13)] + [
        f"1954-{m:02d}-28" for m in range(1, 13)
    ]
    df = dividend_yield_from_returns(total, capgains, dates)
    assert df["div"][:12].null_count() == 12 or np.all(np.isnan(df["div"].to_numpy()[:12]))
    last = df["div"][-1]
    assert last is not None and last > 0


def test_fit_mrp_recovers_known_coefficients():
    rng = np.random.default_rng(1)
    n = 80
    div = 0.03 + 0.002 * rng.normal(size=n)
    defspr = 0.01 + 0.001 * rng.normal(size=n)
    rf_ann = 0.04 + 0.002 * rng.normal(size=n)
    term = 0.01 + 0.002 * rng.normal(size=n)
    rf = np.full(n, 0.003)
    # mkt_{t+1} − rf_t = 0.005 + 0.4 DIV_t − 0.2 DEF_t
    signal = 0.005 + 0.4 * div - 0.2 * defspr
    mkt = np.zeros(n)
    mkt[1:] = rf[:-1] + signal[:-1] + 0.0001 * rng.normal(size=n - 1)
    dates = pl.date_range(pl.date(1960, 1, 31), pl.date(1966, 8, 31), "1mo", eager=True)[:n]
    frame = pl.DataFrame(
        {
            "date": dates,
            "mkt": mkt,
            "rf": rf,
            "div": div,
            "defspr": defspr,
            "rf_ann": rf_ann,
            "term": term,
        }
    )
    fit = fit_mrp(frame)
    assert fit.nobs == n - 1
    assert fit.coef["div"] == pytest.approx(0.4, abs=0.05)
    assert fit.coef["defspr"] == pytest.approx(-0.2, abs=0.05)
    predicted = fit.predict(frame)
    assert "mrp" in predicted.columns


def test_annualize_rf():
    assert annualize_rf(np.array([0.002]))[0] == pytest.approx(12 * math.log(1.002))


def test_load_paper_macro_joins_without_div():
    df = load_paper_macro(
        ff3=FIXTURES / "ff3_sample.csv",
        path_aaa=FIXTURES / "aaa_sample.csv",
        path_baa=FIXTURES / "baa_sample.csv",
        treasury_paths={
            "GS1": FIXTURES / "gs1_sample.csv",
            "GS10": FIXTURES / "gs10_sample.csv",
        },
        fit=False,
    )
    assert {"date", "mkt", "rf", "defspr", "y1", "term", "rf_ann"}.issubset(df.columns)
    assert "mrp" not in df.columns
