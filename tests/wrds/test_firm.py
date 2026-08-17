import datetime as dt

import numpy as np
import polars as pl
import pytest

pytest.importorskip("wrds")

from varvaluation import StateSpec
from varvaluation.wrds import filter_firms, merge_firm_panel, prepare_firm_state


def _months(n: int, start: dt.date = dt.date(2000, 1, 1)) -> list[dt.date]:
    dates = []
    y, m = start.year, start.month
    for _ in range(n):
        nxt = dt.date(y + 1, 1, 1) if m == 12 else dt.date(y, m + 1, 1)
        dates.append(dt.date.fromordinal(nxt.toordinal() - 1))
        y, m = nxt.year, nxt.month
    return dates


def _synthetic_panel(n_months: int = 48) -> pl.DataFrame:
    dates = _months(n_months)
    rows = []
    for permno, sic, be0, ni_scale in ((101, 3571, 100.0, 12.0), (202, 7372, 80.0, 10.0)):
        for i, d in enumerate(dates):
            fyear = d.year if d.month >= 6 else d.year - 1
            years = fyear - 1999
            rows.append(
                {
                    "permno": permno,
                    "date": d,
                    "ret": 0.01 + 0.001 * permno / 100,
                    "prc": 20.0 + 0.1 * i,
                    "shrout": 5000.0,
                    "siccd": sic,
                    "sic": sic,
                    "gvkey": str(permno),
                    "fyear": fyear,
                    "seq": be0 + 5.0 * years,
                    "ceq": be0 + 5.0 * years,
                    "at": 400.0,
                    "ni": ni_scale + years,
                    "dvt": 1.0,
                    "csho": 5.0,
                }
            )
    return pl.DataFrame(rows)


def test_filter_drops_financials():
    panel = _synthetic_panel(12).with_columns(sic=pl.lit(6021), siccd=pl.lit(6021))
    out = filter_firms(panel)
    assert out.height == 0


def test_merge_firm_panel_asof():
    dates = _months(6)
    crsp = pl.DataFrame(
        {
            "permno": [1] * 6,
            "date": dates,
            "ret": [0.01] * 6,
            "prc": [10.0] * 6,
            "shrout": [1000.0] * 6,
            "siccd": [3571] * 6,
        }
    )
    comp = pl.DataFrame(
        {
            "gvkey": ["a"],
            "datadate": [dates[1]],
            "fyear": [2000],
            "sic": [3571],
            "seq": [50.0],
            "ceq": [50.0],
            "at": [200.0],
            "ni": [5.0],
            "dvt": [1.0],
            "csho": [10.0],
        }
    )
    link = pl.DataFrame(
        {
            "gvkey": ["a"],
            "lpermno": [1],
            "linktype": ["LU"],
            "linkprim": ["P"],
            "linkdt": [dates[0]],
            "linkenddt": [dates[-1]],
        }
    )
    merged = merge_firm_panel(crsp, comp, link)
    # asof backward: first month has no prior fiscal year-end
    assert merged.height >= 4
    assert "seq" in merged.columns


def test_prepare_firm_state_named_columns():
    panel = _synthetic_panel(48)
    dates = panel["date"].unique().sort()
    n = dates.len()
    rng = np.random.default_rng(0)
    macro = pl.DataFrame(
        {
            "date": dates,
            "rf": np.full(n, 0.003),
            "mkt": 0.008 + rng.normal(scale=0.03, size=n),
            "r": np.full(n, 0.04),
            "cay": rng.normal(scale=0.01, size=n),
            "pi": rng.normal(scale=0.002, size=n),
        }
    )
    spec = StateSpec(
        names=("roe", "beta", "bm", "r", "cay", "pi"),
        cashflow="roe",
        group="permno",
    )
    state = prepare_firm_state(panel, macro, spec, beta_window=12)
    assert set(spec.names).issubset(state.columns)
    assert "permno" in state.columns
    assert state.height > 5
    assert state["roe"].to_numpy().min() == pytest.approx(
        state["roe"].to_numpy().min()
    )  # finite
    assert np.isfinite(state["roe"].to_numpy()).all()
    assert np.isfinite(state["bm"].to_numpy()).all()


def _dividend_panel(n_months: int = 48) -> pl.DataFrame:
    """Two payers: constant price and constant monthly yield, so g is near zero after burn-in."""
    panel = _synthetic_panel(n_months)
    return panel.with_columns(retx=pl.col("ret") - 0.002, prc=pl.lit(20.0))


def test_firm_dividend_growth_constant_yield_is_flat():
    from varvaluation.wrds.firm import compute_firm_dividend_growth

    panel = _dividend_panel(48)
    out = compute_firm_dividend_growth(panel)
    assert "g" in out.columns
    assert "div" in out.columns
    g = out["g"].to_numpy()
    g = g[np.isfinite(g)]
    assert g.size > 0
    assert np.abs(g).max() < 0.05
    div = out["div"].to_numpy()
    div = div[np.isfinite(div)]
    assert div.size > 0
    assert div.min() > 0


def test_prepare_firm_state_builds_g_and_div():
    panel = _dividend_panel(48)
    dates = panel["date"].unique().sort()
    n = dates.len()
    rng = np.random.default_rng(1)
    macro = pl.DataFrame(
        {
            "date": dates,
            "rf": np.full(n, 0.003),
            "mkt": 0.008 + rng.normal(scale=0.03, size=n),
            "r": np.full(n, 0.04),
            "cay": rng.normal(scale=0.01, size=n),
            "pi": rng.normal(scale=0.002, size=n),
        }
    )
    spec = StateSpec(
        names=("g", "beta", "bm", "r", "cay", "pi"),
        cashflow="g",
        group="permno",
    )
    state = prepare_firm_state(panel, macro, spec, beta_window=12)
    assert "g" in state.columns
    assert "div" in state.columns
    assert spec.cashflow == "g"
    assert state.height > 0
    assert np.isfinite(state["g"].to_numpy()).all()
    assert (state["div"].to_numpy() > 0).all()


def test_compute_g_requires_retx():
    from varvaluation.wrds.firm import compute_firm_dividend_growth

    with pytest.raises(ValueError, match="retx"):
        compute_firm_dividend_growth(_synthetic_panel(24))
