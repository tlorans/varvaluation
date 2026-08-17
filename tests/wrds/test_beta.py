import datetime as dt

import numpy as np
import polars as pl
import pytest

pytest.importorskip("wrds")

from varvaluation.wrds.beta import attach_posterior_beta, quarter_end_betas


def _business_days(n: int, start: dt.date = dt.date(2000, 1, 3)) -> list[dt.date]:
    out = []
    d = start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d = dt.date.fromordinal(d.toordinal() + 1)
    return out


def test_quarter_end_rolling_beta():
    dates = _business_days(200)
    rng = np.random.default_rng(3)
    rf = np.full(200, 0.0001)
    mkt = 0.0004 + 0.01 * rng.normal(size=200)
    ret = rf + 0.9 * (mkt - rf) + 0.003 * rng.normal(size=200)
    daily = pl.DataFrame({"permno": [11] * 200, "date": dates, "ret": ret})
    market = pl.DataFrame({"date": dates, "rf": rf, "mkt": mkt})
    qe = quarter_end_betas(daily, market)
    assert qe.height >= 1
    assert qe["beta_rw"].drop_nulls().len() >= 1
    quarters = qe.select(["permno", "date"]).with_columns(pl.lit(1.0).alias("dummy"))
    out = attach_posterior_beta(qe, qe, method="rolling")
    assert "beta" in out.columns
