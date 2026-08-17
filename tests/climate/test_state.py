import datetime as dt

import numpy as np
import polars as pl
import pytest

from varvaluation.climate import build_climate_state


def _months(n: int, start: dt.date = dt.date(2000, 1, 1)) -> list[dt.date]:
    dates = []
    y, m = start.year, start.month
    for _ in range(n):
        nxt = dt.date(y + 1, 1, 1) if m == 12 else dt.date(y, m + 1, 1)
        dates.append(dt.date.fromordinal(nxt.toordinal() - 1))
        y, m = nxt.year, nxt.month
    return dates


def test_build_climate_state_persistence():
    n = 20
    temps = np.linspace(0.0, 1.0, n)
    temp = pl.DataFrame({"date": _months(n), "temp": temps})
    out = build_climate_state(temp, persistence=0.5, burn_in=0)
    assert out.height == n
    assert out["Y"][0] == pytest.approx(0.0)
    dT = np.diff(temps, prepend=temps[0])
    assert out["Y"][1] == pytest.approx(0.5 * 0.0 + dT[1])


def test_burn_in_drops_prefix():
    temp = pl.DataFrame({"date": _months(10), "temp": list(range(10))})
    out = build_climate_state(temp, burn_in=3)
    assert out.height == 7
