import numpy as np
import pytest

from varvaluation import (
    StateSpecError,
    estimate_var,
    news_decomposition,
    treasury_test,
)
from varvaluation.news import simulate_return_var


def test_treasury_cf_near_zero():
    news = treasury_test(nobs=800, seed=1)
    assert news.shares.var_cf == pytest.approx(0.0, abs=1e-6)


def test_identity_residual():
    news = treasury_test(nobs=400, seed=2)
    f = news.frame
    got = f["unexpected"] - (f["cf"] - f["dr"])
    np.testing.assert_allclose(got.to_numpy(), f["residual"].to_numpy(), atol=1e-10)


def test_cf_ignores_return_residual_scramble():
    df, spec = simulate_return_var(nobs=400, seed=3, cashflow_zero=False)
    fit = estimate_var(df, spec)
    xi = np.array([1.0, 0.0])
    Lambda = np.zeros((2, 2))
    news0 = news_decomposition(
        fit, df.select(["date", "ret"]), return_col="ret", xi=xi, Lambda=Lambda
    )
    cf0 = news0.frame["cf"].to_numpy()

    rng = np.random.default_rng(99)
    scrambled = df.with_columns(ret=rng.permutation(df["ret"].to_numpy()))
    news1 = news_decomposition(
        fit,
        scrambled.select(["date", "ret"]),
        return_col="ret",
        xi=xi,
        Lambda=Lambda,
    )
    np.testing.assert_allclose(news1.frame["cf"].to_numpy(), cf0, atol=1e-12)
    assert not np.allclose(
        news1.frame["unexpected"].to_numpy(),
        news0.frame["unexpected"].to_numpy(),
    )


def test_rejects_both_or_neither_mapping():
    df, spec = simulate_return_var(nobs=80, seed=4)
    fit = estimate_var(df, spec)
    returns = df.select(["date", "ret"])
    with pytest.raises(StateSpecError, match="either return_state"):
        news_decomposition(
            fit,
            returns,
            return_state="ret",
            xi=np.zeros(2),
            Lambda=np.zeros((2, 2)),
        )
    with pytest.raises(StateSpecError, match="return_state or"):
        news_decomposition(fit, returns)
