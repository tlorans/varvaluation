import datetime as dt

import numpy as np
import polars as pl
import pytest

from varvaluation import (
    INSURANCE,
    capm_tests,
    paper_state_spec,
    prepare_industry_state,
    select_sic,
    slope_tests,
)
from varvaluation.industry import compute_book_growth, compute_quarterly_roe


def _quarters(n: int) -> list[dt.date]:
    out: list[dt.date] = []
    year, q = 2000, 1
    ends = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
    for _ in range(n):
        month, day = ends[q]
        out.append(dt.date(year, month, day))
        q += 1
        if q == 5:
            q = 1
            year += 1
    return out


def _panel(n_q: int = 10) -> pl.DataFrame:
    dates = _quarters(n_q)
    rows = []
    for permno, sic, book0, earn, me0 in (
        (1, 6330, 100.0, 4.0, 200.0),
        (2, 6311, 80.0, 3.0, 100.0),
        (3, 3571, 50.0, 2.0, 80.0),
    ):
        book = book0
        for i, d in enumerate(dates):
            book = book * 1.02
            rows.append(
                {
                    "permno": permno,
                    "date": d,
                    "sic": sic,
                    "ibq": earn + 0.1 * i,
                    "ceqq": book,
                    "me": me0 * (1.01**i),
                    "beta": 0.6 + 0.05 * permno,
                    "bm": book / (me0 * (1.01**i)),
                }
            )
    return pl.DataFrame(rows)


def test_select_sic_insurance_and_ex():
    panel = _panel()
    all_ins = select_sic(panel, INSURANCE["all"])
    assert set(all_ins["permno"].unique().to_list()) == {1, 2}
    pc = select_sic(panel, INSURANCE["pc"])
    assert set(pc["permno"].unique().to_list()) == {1}
    ex = select_sic(panel, "ex")
    assert set(ex["permno"].unique().to_list()) == {3}


def test_quarterly_roe_and_book_growth():
    panel = _panel()
    one = panel.filter(pl.col("permno") == 1)
    with_roe = compute_quarterly_roe(one)
    with_g = compute_book_growth(with_roe)
    # first three quarters cannot form a four-quarter sum + lag
    assert with_roe["roe"][:3].null_count() >= 3
    later = with_g.filter(pl.col("roe").is_not_null() & pl.col("g").is_not_null())
    assert later.height >= 1
    assert later["g"][0] == pytest.approx(np.log(1.02**4), rel=1e-6)


def test_prepare_industry_state_value_weights():
    panel = _panel()
    dates = panel["date"].unique().sort()
    macro = pl.DataFrame({"date": dates, "mrp": [0.05] * dates.len()})
    spec = paper_state_spec(horizon=1)
    state = prepare_industry_state(panel, macro, spec, sic=INSURANCE["all"])
    assert set(spec.names).issubset(state.columns)
    assert state.height >= 1
    # only insurers 1 and 2; beta is constant within firm
    last = state.tail(1)
    # value-weighted beta of 0.65 and 0.70, firm 1 has more me
    assert 0.65 < last["beta"][0] < 0.70


def test_capm_and_slope_tests():
    rng = np.random.default_rng(0)
    T, N = 80, 30
    # hump: ρ(1)=0.09, ρ(10)=0.105, ρ(30)=0.09, CAPM=0.117
    tau = np.arange(1, N + 1)
    mean_curve = 0.09 + 0.015 * np.exp(-((tau - 10) ** 2) / 80)
    rho = mean_curve + 0.005 * rng.normal(size=(T, N))
    capm = np.full(T, 0.117) + 0.002 * rng.normal(size=T)
    table2 = capm_tests(rho, capm, taus=(1, 10, 30))
    assert table2[0].tau == 1
    assert table2[1].mean > table2[0].mean  # hump vs short end
    assert table2[0].tstat < 0  # curve below CAPM
    table3 = slope_tests(rho, taus=(10, 30))
    assert table3[0].mean > 0  # 10y above 1y
    assert table3[0].pvalue < 0.05
