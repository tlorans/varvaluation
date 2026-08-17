import datetime as dt

import numpy as np
import polars as pl
import pytest

pytest.importorskip("pandas_datareader")

from varvaluation import StateSpec
from varvaluation.data import prepare_portfolio_state


def _month_ends(n: int, start: dt.date = dt.date(1990, 1, 1)) -> list[dt.date]:
    dates = []
    y, m = start.year, start.month
    for _ in range(n):
        if m == 12:
            nxt = dt.date(y + 1, 1, 1)
        else:
            nxt = dt.date(y, m + 1, 1)
        dates.append(nxt.fromordinal(nxt.toordinal() - 1))
        y, m = nxt.year, nxt.month
    return dates


def test_prepare_portfolio_state_builds_named_columns():
    n = 80
    rng = np.random.default_rng(0)
    dates = _month_ends(n)
    total_ret = 0.01 + rng.normal(scale=0.03, size=n)
    cap_ret = total_ret - 0.002
    mkt = 0.008 + rng.normal(scale=0.04, size=n)
    rf = np.full(n, 0.003)
    total = pl.DataFrame({"date": dates, "D1": total_ret, "D10": total_ret + 0.001})
    capgains = pl.DataFrame({"date": dates, "D1": cap_ret, "D10": cap_ret})
    macro = pl.DataFrame(
        {
            "date": dates,
            "rf": rf,
            "mkt": mkt,
            "r": np.full(n, 0.04),
            "cay": rng.normal(scale=0.01, size=n),
            "pi": rng.normal(scale=0.002, size=n),
        }
    )
    spec = StateSpec(names=("g", "beta", "dpo", "r", "cay", "pi"), cashflow="g")
    state = prepare_portfolio_state(
        total, capgains, macro, spec, portfolio="D1", beta_window=12
    )
    assert set(spec.names).issubset(state.columns)
    assert "date" in state.columns
    assert state.height > 10
    assert np.isfinite(state["g"].to_numpy()).all()
    assert np.isfinite(state["beta"].to_numpy()).all()


def test_prepare_portfolio_state_missing_macro_column():
    dates = _month_ends(20)
    total = pl.DataFrame({"date": dates, "D1": [0.01] * 20})
    capgains = pl.DataFrame({"date": dates, "D1": [0.008] * 20})
    macro = pl.DataFrame({"date": dates, "rf": [0.001] * 20, "mkt": [0.01] * 20})
    spec = StateSpec(names=("g", "r"), cashflow="g")
    with pytest.raises(ValueError, match="missing columns"):
        prepare_portfolio_state(total, capgains, macro, spec, portfolio="D1", beta_window=5)
