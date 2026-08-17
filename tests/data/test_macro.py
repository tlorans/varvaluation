from pathlib import Path

import pytest

pytest.importorskip("pandas_datareader")

from varvaluation.data import load_cay, load_cpi, load_gs1, load_temperature

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_load_gs1_continuously_compounded():
    df = load_gs1(path=FIXTURES / "gs1_sample.csv")
    import math

    assert df.height == 3
    assert df["r"][0] == pytest.approx(math.log(1 + 0.0236))
    assert df["date"][0].day >= 28


def test_load_cpi_twelve_month_log():
    df = load_cpi(path=FIXTURES / "cpi_sample.csv")
    import math

    # Jan 1948 vs Jan 1947
    assert df.height == 1
    expected = math.log(23.680) - math.log(21.480)
    assert df["pi"][0] == pytest.approx(expected)
    assert df["date"][0].year == 1948


def test_load_cay_forward_fills_quarterly():
    df = load_cay(path=FIXTURES / "cay_sample.csv")
    assert "cay" in df.columns
    assert df.height >= 7  # Mar through Sep 1952 monthly
    # April should carry March's value
    import polars as pl

    april = df.filter(pl.col("date").dt.month() == 4)
    march = df.filter(pl.col("date").dt.month() == 3)
    assert april["cay"][0] == pytest.approx(march["cay"][0])


def test_load_temperature_monthly():
    df = load_temperature(path=FIXTURES / "gistemp_sample.csv")
    assert df.height == 24
    assert df["temp"][0] == pytest.approx(0.24)
    assert df["date"][0].month == 1
