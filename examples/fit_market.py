"""Does the joint model line up with market equity? Try restrictions and alpha.

Run from the package root::

    uv run python examples/fit_market.py
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import polars as pl
import statsmodels.api as sm
from dotenv import load_dotenv

from varvaluation import (
    ExpectedReturnSpec,
    NonStationaryVARError,
    StateSpec,
    ValuationModel,
    calibrate_alpha,
    estimate_var_panel,
    pricing_errors,
)
from varvaluation.data import load_macro
from varvaluation.pricing import as_of
from varvaluation.wrds import merge_firm_panel, prepare_firm_state
from varvaluation.wrds.load import load_ccm_link, load_compustat_annual, load_crsp_monthly

warnings.filterwarnings("ignore")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

CANDIDATES: list[tuple[str, tuple[tuple[str, str], ...] | None]] = [
    ("unrestricted", None),
    ("g: no r, pi", (("g", "r"), ("g", "pi"))),
    ("g: no r, pi, cay", (("g", "r"), ("g", "pi"), ("g", "cay"))),
    (
        "g: own lag only",
        (("g", "beta"), ("g", "bm"), ("g", "r"), ("g", "cay"), ("g", "pi")),
    ),
]


def premium(macro: pl.DataFrame, spec: StateSpec):
    log_mkt = np.log(1 + macro["mkt"].to_numpy())
    frame = macro.with_columns(pl.Series("log_mkt", log_mkt))
    frame = frame.with_columns(pl.col("log_mkt").rolling_sum(12).shift(-12).alias("y_fwd"))
    frame = frame.with_columns((pl.col("y_fwd") - pl.col("r")).alias("y"))
    frame = (
        frame.filter(
            pl.col("date").ge(pl.date(1965, 7, 1)) & pl.col("date").le(pl.date(2019, 9, 30))
        )
        .select(["date", "y", "r", "cay"])
        .drop_nulls()
    )
    y = frame["y"].to_numpy()
    X = np.column_stack([np.ones(len(y)), frame.select(["r", "cay"]).to_numpy()])
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
    return ExpectedReturnSpec(premium=("cay",)).xi_lambda(
        spec, {"b0": float(fit.params[0]), "br": float(fit.params[1]), "bcay": float(fit.params[2])}
    )


def _print(err, *, label: str, extra: str = "") -> None:
    print(
        f"{label:22} n={err.n:4d}  fail={err.n_failed:3d}  "
        f"med PV/ME={err.median_pv_me:7.3f}  "
        f"rmse log={err.rmse_log_pv_me:6.3f}  "
        f"corr={err.corr_log:5.3f}  "
        f"within 2x={100 * err.share_within_2x:5.1f}%{extra}"
    )


def main() -> int:
    macro = load_macro()
    print("loading firm panel 2000-2019...")
    crsp = load_crsp_monthly(start="2000-01", end="2019-12-31", use_cache=True)
    comp = load_compustat_annual(start="1998-01", end="2019-12-31", use_cache=True)
    panel = merge_firm_panel(crsp, comp, load_ccm_link(use_cache=True))
    spec = StateSpec(
        names=("g", "beta", "bm", "r", "cay", "pi"),
        cashflow="g",
        group="permno",
        horizon=12,
        nw_lags=12,
    )
    state = prepare_firm_state(
        panel, macro, spec, start="2001-01", end="2019-09", beta_window=60
    )
    top = (
        state.group_by("permno").len().sort("len", descending=True).head(80)["permno"].to_list()
    )
    slim = state.filter(pl.col("permno").is_in(top))
    last_date = slim["date"].max()
    cross = as_of(slim, panel, last_date)
    print(f"cross-section {last_date}  firms={cross.height}")
    xi, Lambda = premium(macro, spec)

    # Profitability as a predictor of dividend growth (cash-flow slot stays g).
    spec_roe = StateSpec(
        names=("g", "roe", "beta", "bm", "r", "cay", "pi"),
        cashflow="g",
        group="permno",
        horizon=12,
        nw_lags=12,
    )
    state_roe = prepare_firm_state(
        panel, macro, spec_roe, start="2001-01", end="2019-09", beta_window=60
    )
    top_roe = (
        state_roe.group_by("permno")
        .len()
        .sort("len", descending=True)
        .head(80)["permno"]
        .to_list()
    )
    slim_roe = state_roe.filter(pl.col("permno").is_in(top_roe))
    cross_roe = as_of(slim_roe, panel, last_date)
    xi_roe, lam_roe = premium(macro, spec_roe)

    print()
    print("Raw alpha=0.02")
    best = None
    for label, zeros in CANDIDATES:
        fit = estimate_var_panel(slim, spec, phi_zeros=zeros)
        try:
            model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.02)
        except NonStationaryVARError as exc:
            print(f"{label:22} refused ({exc})")
            continue
        err = pricing_errors(model, cross)
        extra = f"  rho={fit.spectral_radius:.3f}"
        _print(err, label=label, extra=extra)
        score = err.rmse_log_pv_me
        if best is None or (np.isfinite(score) and score < best[0]):
            best = (score, label, zeros, fit)

    print()
    print("With roe in the state (cash-flow slot still g)")
    fit_roe = estimate_var_panel(slim_roe, spec_roe, phi_zeros=(("g", "r"), ("g", "pi")))
    try:
        a_roe, err_roe = calibrate_alpha(
            fit_roe, xi_roe, lam_roe, cross_roe, alpha0=0.02, n=40
        )
        _print(err_roe, label="g + roe", extra=f"  alpha={a_roe:.3f}  rho={fit_roe.spectral_radius:.3f}")
        extra_best = (err_roe.rmse_log_pv_me, "g + roe", (("g", "r"), ("g", "pi")), a_roe, err_roe)
    except NonStationaryVARError as exc:
        print(f"g + roe refused ({exc})")
        extra_best = None

    print()
    print("Alpha calibrated so median PV/ME ~ 1")
    best_cal = extra_best
    for label, zeros in CANDIDATES:
        fit = estimate_var_panel(slim, spec, phi_zeros=zeros)
        try:
            a_star, err = calibrate_alpha(fit, xi, Lambda, cross, alpha0=0.02, n=40)
        except NonStationaryVARError as exc:
            print(f"{label:22} refused ({exc})")
            continue
        _print(err, label=label, extra=f"  alpha={a_star:.3f}")
        score = err.rmse_log_pv_me
        if best_cal is None or (np.isfinite(score) and score < best_cal[0]):
            best_cal = (score, label, zeros, a_star, err)

    if best_cal:
        print()
        print(
            f"Best cross-section after calibration: {best_cal[1]}  "
            f"alpha={best_cal[3]:.3f}  rmse log={best_cal[0]:.3f}  "
            f"corr={best_cal[4].corr_log:.3f}  within 2x={100 * best_cal[4].share_within_2x:.1f}%"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
