"""Firm illustration of the joint VAR. Ken French is not used.

Run from the package root::

    uv run python examples/walkthrough.py
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import polars as pl
import statsmodels.api as sm

warnings.filterwarnings("ignore", message="divide by zero")
warnings.filterwarnings("ignore", message="invalid value")
warnings.filterwarnings("ignore", message="Sortedness of columns")

from varvaluation import (
    ExpectedReturnSpec,
    NonStationaryVARError,
    PerpetuityDivergesError,
    StateSpec,
    ValuationModel,
    calibrate_alpha,
    estimate_var_panel,
    isolate_channels,
    news_decomposition,
    pricing_errors,
)
from varvaluation.pricing import as_of
from varvaluation.data import load_macro

START, END = "1965-07", "2024-12"


def _print(title: str) -> None:
    print()
    print(f"# {title}")


def risk_premium(macro: pl.DataFrame) -> dict:
    log_mkt = np.log(1 + macro["mkt"].to_numpy())
    frame = macro.with_columns(pl.Series("log_mkt", log_mkt))
    frame = frame.with_columns(
        pl.col("log_mkt").rolling_sum(12).shift(-12).alias("y_fwd")
    )
    frame = frame.with_columns((pl.col("y_fwd") - pl.col("r")).alias("y"))
    start = pl.date(int(START[:4]), int(START[5:7]), 1)
    # Stop the premium at the valuation date (no look-ahead past 2019-09).
    end = pl.date(2019, 9, 30)
    frame = (
        frame.filter(pl.col("date").ge(start) & pl.col("date").le(end))
        .select(["date", "y", "r", "cay"])
        .drop_nulls()
    )
    y = frame["y"].to_numpy()
    X = np.column_stack([np.ones(len(y)), frame.select(["r", "cay"]).to_numpy()])
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
    return {
        "b0": float(fit.params[0]),
        "br": float(fit.params[1]),
        "bcay": float(fit.params[2]),
        "t": [float(t) for t in fit.tvalues],
        "nobs": int(fit.nobs),
        "r2": float(fit.rsquared),
        "start": str(frame["date"][0]),
        "end": str(frame["date"][-1]),
    }


def expected_cashflow_state(fit, X, n: int) -> np.ndarray:
    """E_t[cash-flow name_{t+k}] for k = 1..n from the VAR companion."""
    e = fit.spec.e_vec(fit.spec.cashflow)
    out = np.zeros(n)
    mean = X.copy()
    for k in range(n):
        mean = fit.c + fit.Phi @ mean
        out[k] = float(e @ mean)
    return out


def main() -> int:
    _print("Step 1 — macro and the firm panel")
    macro = load_macro()
    print(f"macro  {macro['date'][0]} → {macro['date'][-1]}  n={macro.height}")
    print("macro columns:", list(macro.columns))

    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        from varvaluation.wrds import merge_firm_panel, prepare_firm_state
        from varvaluation.wrds.load import (
            load_ccm_link,
            load_compustat_annual,
            load_crsp_monthly,
        )
    except Exception as exc:
        print(f"WRDS extra missing: {type(exc).__name__}: {exc}")
        return 1

    crsp = load_crsp_monthly(start="2000-01", end="2019-12-31", use_cache=True)
    comp = load_compustat_annual(start="1998-01", end="2019-12-31", use_cache=True)
    link = load_ccm_link(use_cache=True)
    panel = merge_firm_panel(crsp, comp, link)
    print(
        f"CRSP–Compustat  {panel['date'].min()} → {panel['date'].max()}  "
        f"rows={panel.height}  permno={panel['permno'].n_unique()}"
    )

    _print("Step 2 — StateSpec and prepare_firm_state")
    spec = StateSpec(
        names=("g", "roe", "beta", "bm", "r", "cay", "pi"),
        cashflow="g",
        group="permno",
        horizon=12,
        nw_lags=12,
    )
    print(f"names={spec.names}  cashflow={spec.cashflow}  "
          f"cashflow_index={spec.cashflow_index()}  group={spec.group}")
    state = prepare_firm_state(
        panel, macro, spec, start="2001-01", end="2019-09", beta_window=60
    )
    print(
        f"state  {state.height} firm-months  "
        f"{state['permno'].n_unique()} firms  "
        f"{state['date'].min()} → {state['date'].max()}"
    )

    _print("Step 3 — ExpectedReturnSpec (market premium)")
    rp = risk_premium(macro)
    print(f"sample {rp['start']} → {rp['end']}  n={rp['nobs']}  R2={rp['r2']:.3f}")
    print(
        f"b0={rp['b0']:+.3f} (t={rp['t'][0]:+.2f})  "
        f"br={rp['br']:+.3f} (t={rp['t'][1]:+.2f})  "
        f"bcay={rp['bcay']:+.3f} (t={rp['t'][2]:+.2f})"
    )
    xi, Lambda = ExpectedReturnSpec(premium=("cay",)).xi_lambda(
        spec, {"b0": rp["b0"], "br": rp["br"], "bcay": rp["bcay"]}
    )
    print(f"xi[r]={xi[spec.index('r')]:+.3f}  "
          f"xi[beta]={xi[spec.index('beta')]:+.3f}  "
          f"Lambda[beta,cay]={Lambda[spec.index('beta'), spec.index('cay')]:+.3f}")

    _print("Step 4 — estimate_var_panel")
    top = (
        state.group_by("permno")
        .len()
        .sort("len", descending=True)
        .head(80)["permno"]
        .to_list()
    )
    slim = state.filter(pl.col("permno").is_in(top))
    # r and pi belong in the required-return side of X. They are not
    # free predictors of dividend growth (short-sample artifact).
    fit = estimate_var_panel(slim, spec, phi_zeros=(("g", "r"), ("g", "pi")))
    g_i = spec.cashflow_index()
    print(
        f"nobs={fit.nobs}  spectral_radius={fit.spectral_radius:.3f}  "
        f"Phi[g,g]={fit.Phi[g_i, g_i]:+.3f}"
    )
    print(
        "Phi[g, ·]  "
        + "  ".join(f"{n}={fit.Phi[g_i, spec.index(n)]:+.3f}" for n in spec.names)
    )

    _print("Step 5 — ValuationModel at three firms")
    try:
        model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.02)
    except NonStationaryVARError as exc:
        print(exc)
        print("No present value: the companion is explosive on this window.")
        return 0
    last_date = slim["date"].max()
    last = slim.filter(pl.col("date") == last_date).sort("permno")
    me = (
        panel.filter(pl.col("date") == last_date)
        .select(["permno", "prc", "shrout"])
        .with_columns((pl.col("prc").abs() * pl.col("shrout")).alias("me"))
        .select(["permno", "me"])
    )
    last = last.join(me, on="permno", how="left")
    raw = pricing_errors(model, last)
    print(
        f"pricing  n={raw.n}  med PV/ME={raw.median_pv_me:.3f}  "
        f"rmse log={raw.rmse_log_pv_me:.3f}  corr={raw.corr_log:.3f}  "
        f"within 2x={100 * raw.share_within_2x:.1f}%"
    )
    alpha_star, cal = calibrate_alpha(fit, xi, Lambda, last, alpha0=0.02)
    print(
        f"calibrated alpha={alpha_star:.3f}  n={cal.n}  "
        f"med PV/ME={cal.median_pv_me:.3f}  rmse log={cal.rmse_log_pv_me:.3f}  "
        f"corr={cal.corr_log:.3f}  within 2x={100 * cal.share_within_2x:.1f}%"
    )
    model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=alpha_star)
    picks = [
        last.row(0, named=True),
        last.row(last.height // 2, named=True),
        last.row(last.height - 1, named=True),
    ]
    for row in picks:
        X = np.array([row[n] for n in spec.names], dtype=float)
        g = float(row["g"])
        C = float(row["div"])
        rates = model.spot_rates(X, n=10)
        perp = model.perpetuity(X, n=40)
        eg = expected_cashflow_state(fit, X, 10)
        print(
            f"permno={row['permno']}  {last_date}  "
            f"g={g:+.3f}  TTM_div={C:.2f}  "
            f"beta={row['beta']:+.2f}  bm={row['bm']:+.3f}"
        )
        print(
            "  spot mu(n) %   n=1, 5, 10: "
            + ", ".join(f"{100 * rates[k]:.2f}" for k in (0, 4, 9))
        )
        print(
            "  E[g]           n=1, 5, 10: "
            + ", ".join(f"{eg[k]:+.3f}" for k in (0, 4, 9))
        )
        print(
            f"  unit_curve_pv={perp.pv:.2f}  "
            f"terminal_spot={100 * perp.tail_rate:.2f}%"
        )
        try:
            val = model.value(X, C=C, n=40)
            extra = ""
            if row.get("me") is not None:
                extra = f"  ME={row['me']:.1f}  PV/ME={val.pv / float(row['me']):.3f}"
            print(
                f"  pv={val.pv:.2f} CRSP thousands  "
                f"(${val.pv / 1e3:,.1f} million; C=TTM dividends){extra}"
            )
        except PerpetuityDivergesError as exc:
            print(f"  value  {exc}")

    X0 = np.array([picks[0][n] for n in spec.names], dtype=float)
    decomp, total_var = model.variance_decomposition(10)
    share = decomp / np.maximum(total_var[:, None], 1e-16)
    print(
        "var share of mu(n=10): "
        + "  ".join(f"{n}={100 * share[9, spec.index(n)]:.1f}%" for n in spec.names)
    )
    try:
        iso = isolate_channels(model, X0, shut=("cay",), on="discount", n=40)
        print(f"isolate_channels shut=cay on=discount  pv={iso.pv:.3f}")
    except PerpetuityDivergesError as exc:
        print(f"isolate_channels shut=cay on=discount  {exc}")

    _print("Step 6 — news_decomposition")
    # firm simple returns from the CRSP panel, aligned to residual dates
    rets = (
        panel.select(["permno", "date", "ret"])
        .filter(pl.col("permno").is_in(top))
        .drop_nulls()
    )
    # news_decomposition wants a single returns series; use equal-weight
    # mean of the 80 firms
    ew = (
        rets.group_by("date")
        .agg(pl.col("ret").mean().alias("ret"))
        .sort("date")
    )
    news = news_decomposition(fit, ew, return_col="ret", xi=xi, Lambda=Lambda)
    s = news.shares
    print(
        f"var(cf)={s.var_cf:.4f}  var(dr)={s.var_dr:.4f}  "
        f"residual_share={s.residual_share:.2f}  rho={news.rho}"
    )
    print("news.frame columns:", news.frame.columns)

    print()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
