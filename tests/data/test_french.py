from pathlib import Path

import pytest

pytest.importorskip("pandas_datareader")

from varvaluation.data import load_bm_deciles, load_ff3, load_industry49

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_load_ff3_sample():
    df = load_ff3(path=FIXTURES / "ff3_sample.csv")
    assert df.height == 4
    assert set(df.columns) == {"date", "mkt_rf", "smb", "hml", "rf", "mkt"}
    assert df["mkt"][0] == pytest.approx(0.0289 + 0.0022)
    assert df["date"][0].year == 1926
    assert df["date"][0].month == 7


def test_load_bm_deciles_sample():
    total, cap = load_bm_deciles(
        path_total=FIXTURES / "bm_sample.csv",
        path_exdiv=FIXTURES / "bm_sample.csv",
    )
    assert total.columns == ["date", *[f"D{i}" for i in range(1, 11)]]
    assert total.height == 2
    assert total["D1"][0] == pytest.approx(0.0438)
    assert cap["D10"][1] == pytest.approx(0.1010)


def test_load_industry49_sample():
    total, names, cap = load_industry49(
        path_total=FIXTURES / "industry_sample.csv",
        path_exdiv=FIXTURES / "industry_sample.csv",
    )
    assert names == ["Agric", "Food", "Oil", "Softw"]
    assert total["Softw"][0] is None or total["Softw"].is_null()[0]
    assert total["Oil"][0] == pytest.approx(-0.0135)
    assert cap.height == total.height
