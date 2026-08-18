"""Offline Ang and Liu (2004) table objects on a designed six-state draw."""

from __future__ import annotations

import numpy as np
import pytest

from varvaluation.angliu import (
    FOCUS_BM,
    VALUATION_DATE,
    check_shape,
    curve_snapshot,
    expected_return_loadings,
    fit_portfolio,
    identity_error,
    paper_spec,
    perpetuity_comparison,
    sample_moments,
    simulate_paper_state,
    var_table,
)
from varvaluation.angliu.premium import PremiumResult
from varvaluation.angliu.targets import PAPER_CURVE_BAND


def _premium() -> PremiumResult:
    return PremiumResult(
        coeffs={"b0": 0.06, "br": -0.40, "bcay": 1.0},
        stderrs={"b0": 0.01, "br": 0.20, "bcay": 0.30},
        tstats={"b0": 6.0, "br": -2.0, "bcay": 3.3},
        nobs=400,
        r_squared=0.08,
        sample=("1965-07-31", "2000-12-31"),
        market="synthetic",
    )


def test_paper_spec_layout():
    spec = paper_spec()
    assert spec.names == ("g", "beta", "dpo", "r", "cay", "pi")
    assert spec.cashflow == "g"
    assert spec.horizon == 12
    assert spec.nw_lags == 12
    assert VALUATION_DATE.year == 2000
    assert VALUATION_DATE.month == 12
    assert FOCUS_BM == ("D1", "D6", "D10")


def test_simulate_and_identity():
    state, spec = simulate_paper_state(nobs=240, seed=7, beta_mean=1.0)
    assert set(spec.names).issubset(state.columns)
    assert state.height == 240
    rp = _premium()
    xi, Lambda = expected_return_loadings(spec, rp)
    result = fit_portfolio(
        "D6",
        state,
        spec,
        xi,
        Lambda,
        alpha=0.01,
        beta_capm=1.0,
        when=state["date"][-1],
        capm_rate=0.10,
    )
    assert result.fit.spectral_radius < 1.0
    assert identity_error(result.model, result.X) == pytest.approx(0.0, abs=1e-10)
    assert result.moments["identity_err"] == pytest.approx(0.0, abs=1e-10)


def test_dec2000_shape_on_designed_draw():
    state, spec = simulate_paper_state(nobs=426, seed=2000, beta_mean=1.0)
    rp = _premium()
    xi, Lambda = expected_return_loadings(spec, rp)
    result = fit_portfolio(
        "D6",
        state,
        spec,
        xi,
        Lambda,
        alpha=0.01,
        beta_capm=1.0,
        when=state["date"][-1],
        capm_rate=0.12,
    )
    snap = curve_snapshot(result.rates)
    assert snap["slope_30_1"] > 0.0
    assert result.rates[0] < 0.12
    assert PAPER_CURVE_BAND["mu_1_min"] < result.rates[0] < PAPER_CURVE_BAND["mu_1_max"]
    report = check_shape(
        "D6",
        asof=result.asof,
        rates=result.rates,
        mu_capm=0.12,
        gap_capm_pct=result.perp["gap_capm_pct"],
        identity_err=result.moments["identity_err"],
        spectral_radius=result.moments["spectral_radius"],
    )
    assert report.ok
    assert report.upward
    assert report.below_capm
    # Low Dec-2000 rates ⇒ term-structure PV above the flat CAPM PV.
    assert result.perp["v_ts"] > result.perp["v_capm"]
    assert result.perp["gap_capm_pct"] < 0.0


def test_table_schemas():
    state, spec = simulate_paper_state(nobs=180, seed=3)
    rp = _premium()
    xi, Lambda = expected_return_loadings(spec, rp)
    result = fit_portfolio(
        "D1",
        state,
        spec,
        xi,
        Lambda,
        alpha=0.005,
        beta_capm=0.85,
        when=state["date"][-1],
        capm_rate=0.10,
    )
    moments = sample_moments(state, spec)
    assert moments["nobs"] == 180
    assert np.isfinite(moments["g_mean"])
    tbl = var_table(result.fit)
    assert tbl.height == spec.K
    assert "lag_g" in tbl.columns and "se_g" in tbl.columns
    assert result.var_shares.height == 30
    assert set(["g", "beta", "dpo", "r", "cay", "pi", "maturity"]).issubset(
        result.var_shares.columns
    )
    perp = perpetuity_comparison(result.model, result.X, capm_rate=0.10)
    assert np.isfinite(perp["v_ts"])


def test_synthetic_driver_exits_zero():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "examples" / "reproduce_angliu2004.py"
    spec = importlib.util.spec_from_file_location("reproduce_angliu2004", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.run_synthetic() == 0
