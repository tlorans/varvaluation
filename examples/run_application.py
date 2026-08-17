"""Apply the VAR to public data and print the main valuation / news results.

Tries live Ken French / FRED / cay downloads first. If a source
fails, falls back to the local manuscript data directory when present.

Run from the package root::

    uv run python examples/run_application.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl
import statsmodels.api as sm

from varvaluation import (
    ExpectedReturnSpec,
    StateSpec,
    ValuationModel,
    estimate_var,
    estimate_var_panel,
    news_decomposition,
)
from varvaluation.data import (
    load_bm_deciles,
    load_cay,
    load_cpi,
    load_ff3,
    load_gs1,
    load_macro,
    prepare_portfolio_state,
)

PAPER_DATA = Path(r"C:\DBD\corpo_research_papers\papers\01-discounting\code\data")
START, END = "1965-07", "2024-12"
FOCUS = ("D1", "D6", "D10")


def _ok(label: str, fn):
    try:
        out = fn()
        print(f"  [ok] {label}")
        return out
    except Exception as exc:
        print(f"  [fail] {label}: {type(exc).__name__}: {exc}")
        return None


def load_inputs():
    print("Loading public data (live, then local fallback)")
    total_cap = _ok("Ken French BE/ME deciles", load_bm_deciles)
    if total_cap is None and PAPER_DATA.exists():
        total_cap = _ok(
            "Ken French BE/ME (local paper files)",
            lambda: load_bm_deciles(
                path_total=PAPER_DATA / "bm10_portfolios" / "Portfolios_Formed_on_BE-ME.csv",
                path_exdiv=PAPER_DATA / "bm10_exdiv" / "Portfolios_Formed_on_BE-ME_Wout_Div.csv",
            ),
        )
    if total_cap is None:
        raise SystemExit("could not load book-to-market deciles")
    total, capgains = total_cap

    macro = _ok("macro (live FF3 / FRED / cay)", load_macro)
    if macro is None:
        raise SystemExit("could not load macro state")
    # Overlay the published Lettau–Ludvigson file when present so the
    # 1965–2019 sample is the official cay, not only the FRED reconstruction.
    if PAPER_DATA.exists() and (PAPER_DATA / "cay_current.csv").exists():
        published = _ok(
            "published cay overlay",
            lambda: load_cay(path=PAPER_DATA / "cay_current.csv"),
        )
        if published is not None:
            live = macro["cay"] if "cay" in macro.columns else None
            if "cay" in macro.columns:
                macro = macro.drop("cay")
            macro = macro.join(published, on="date", how="left")
            if live is not None:
                macro = macro.with_columns(
                    pl.coalesce(pl.col("cay"), live).alias("cay")
                )
    print("  macro columns:", list(macro.columns))
    if "cay" in macro.columns:
        cay_nn = macro.filter(pl.col("cay").is_not_null())
        print(f"  cay {cay_nn['date'][0]} → {cay_nn['date'][-1]}")
    return total, capgains, macro


def risk_premium(macro: pl.DataFrame, y_col: str | None = None) -> dict:
    log_mkt = np.log(1 + macro["mkt"].to_numpy())
    frame = macro.with_columns(pl.Series("log_mkt", log_mkt))
    frame = frame.with_columns(
        pl.col("log_mkt").rolling_sum(12).shift(-12).alias("y_fwd")
    )
    frame = frame.with_columns((pl.col("y_fwd") - pl.col("r")).alias("y"))
    start = pl.date(int(START[:4]), int(START[5:7]), 1)
    end = pl.date(int(END[:4]), int(END[5:7]), 1).dt.month_end()
    frame = frame.filter(pl.col("date").ge(start) & pl.col("date").le(end))
    cols = ["r", "cay"]
    if y_col and y_col in frame.columns:
        cols.append(y_col)
    frame = frame.select(["date", "y", *cols]).drop_nulls()
    y = frame["y"].to_numpy()
    X = np.column_stack([np.ones(len(y)), frame.select(cols).to_numpy()])
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
    keys = ["b0", "br", "bcay"] + ([f"b{y_col}"] if y_col in cols else [])
    coeffs = {keys[i]: float(fit.params[i]) for i in range(len(keys))}
    tstats = {keys[i]: float(fit.tvalues[i]) for i in range(len(keys))}
    return {
        "coeffs": coeffs,
        "tstats": tstats,
        "nobs": int(fit.nobs),
        "r_squared": float(fit.rsquared),
        "sample": (str(frame["date"][0]), str(frame["date"][-1])),
    }


def capm_alpha(total: pl.DataFrame, macro: pl.DataFrame, col: str) -> float:
    frame = total.select(["date", col]).join(
        macro.select(["date", "rf", "mkt"]), on="date", how="inner"
    ).drop_nulls()
    y = np.log(1 + frame[col].to_numpy()) - np.log(1 + frame["rf"].to_numpy())
    x = np.log(1 + frame["mkt"].to_numpy()) - np.log(1 + frame["rf"].to_numpy())
    ok = np.isfinite(y) & np.isfinite(x)
    X = np.column_stack([np.ones(ok.sum()), x[ok]])
    coeffs, *_ = np.linalg.lstsq(X, y[ok], rcond=None)
    return float(coeffs[0] * 12)


def annual_returns(total: pl.DataFrame, col: str) -> pl.DataFrame:
    """Trailing twelve-month simple return, for the news returns frame."""
    frame = total.select(["date", col]).sort("date")
    log_r = np.log(1 + frame[col].to_numpy())
    return (
        pl.DataFrame({"date": frame["date"], "lr": log_r})
        .with_columns((pl.col("lr").rolling_sum(12).exp() - 1).alias("ret"))
        .select(["date", "ret"])
        .drop_nulls()
    )


def report_portfolio(name, total, capgains, macro, spec, xi, Lambda):
    print(f"\n=== {name} ===")
    state = prepare_portfolio_state(
        total, capgains, macro, spec, portfolio=name, start=START, end=END
    )
    print(f"  state months: {state.height}  {state['date'][0]} → {state['date'][-1]}")
    fit = estimate_var(state, spec)
    print(f"  VAR nobs={fit.nobs}  spectral radius={fit.spectral_radius:.4f}")
    names = list(spec.names)
    g_i = spec.index("g")
    print("  Phi[g, ·]:", {n: f"{fit.Phi[g_i, spec.index(n)]:+.3f}" for n in names})

    alpha = capm_alpha(total, macro, name)
    try:
        model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=alpha)
    except Exception as exc:
        print(f"  model failed: {type(exc).__name__}: {exc}")
        return None

    X = state.select(list(spec.names)).to_numpy()[-1]
    rates = model.spot_rates(X, 30)
    print(
        "  spot μ(n) %  n=1,5,10,30: "
        + ", ".join(f"{100 * rates[k]:.2f}" for k in (0, 4, 9, 29))
    )
    try:
        perp = model.perpetuity(X, n=80)
        val = model.value(X, n=80)
        print(f"  perpetuity PV={perp.pv:.3f}  full PV={val.pv:.3f}  n_used={val.n_used}")
        Xbar = model.unconditional_mean()
        mu_bar = model.spot_rates(Xbar, 1)[0]
        # constant-rate value at unconditional one-period rate
        if mu_bar > 1e-4:
            v_fixed = 1.0 / (np.exp(mu_bar) - 1.0)
            mis = 100.0 * (v_fixed - perp.pv) / perp.pv
            print(f"  flat-rate PV={v_fixed:.3f}  term-structure gap={mis:+.1f}%")
    except Exception as exc:
        print(f"  valuation failed: {type(exc).__name__}: {exc}")
        perp = val = None

    decomp, total_var = model.variance_decomposition(30)
    share = decomp / np.maximum(total_var[:, None], 1e-16)
    print("  var share at n=10:", {n: f"{100 * share[9, spec.index(n)]:.1f}%" for n in names})

    try:
        rets = annual_returns(total, name)
        news = news_decomposition(fit, rets, return_col="ret", xi=xi, Lambda=Lambda)
        s = news.shares
        print(
            f"  news  var(cf)={s.var_cf:.5f}  var(dr)={s.var_dr:.5f}  "
            f"residual_share={s.residual_share:.3f}  rho={news.rho}"
        )
    except Exception as exc:
        print(f"  news failed: {type(exc).__name__}: {exc}")
        news = None
    return {
        "name": name,
        "fit": fit,
        "model": model,
        "state": state,
        "X": X,
        "rates": rates,
        "news": news,
        "alpha": alpha,
    }


def main():
    total, capgains, macro = load_inputs()
    print(
        f"  deciles {total['date'][0]} → {total['date'][-1]}  "
        f"macro {macro['date'][0]} → {macro['date'][-1]}"
    )

    spec = StateSpec(names=("g", "beta", "dpo", "r", "cay", "pi"), cashflow="g")
    rp = risk_premium(macro)
    print("\nRisk-premium regression  y^m_{t+1}-r_t = b0 + br r + bcay cay")
    print(f"  sample {rp['sample'][0]} → {rp['sample'][1]}  n={rp['nobs']}  R²={rp['r_squared']:.3f}")
    for k, v in rp["coeffs"].items():
        print(f"  {k:>5} = {v:+.3f}  (t={rp['tstats'][k]:+.2f})")

    er = ExpectedReturnSpec(premium=("cay",))
    xi, Lambda = er.xi_lambda(spec, rp["coeffs"])

    results = {}
    for name in FOCUS:
        results[name] = report_portfolio(
            name, total, capgains, macro, spec, xi, Lambda
        )

    print("\n=== Firm-level (cached WRDS window if present) ===")
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        from varvaluation.wrds.load import load_ccm_link, load_compustat_annual, load_crsp_monthly
        from varvaluation.wrds import merge_firm_panel, prepare_firm_state

        crsp = load_crsp_monthly(start="2014-01", end="2019-12-31", use_cache=True)
        comp = load_compustat_annual(start="2012-01", end="2019-12-31", use_cache=True)
        link = load_ccm_link(use_cache=True)
        panel = merge_firm_panel(crsp, comp, link)
        spec_f = StateSpec(
            names=("roe", "beta", "bm", "r", "cay", "pi"),
            cashflow="roe",
            group="permno",
            horizon=12,
            nw_lags=12,
        )
        state_f = prepare_firm_state(
            panel, macro, spec_f, start="2015-01", end="2019-09", beta_window=12
        )
        print(
            f"  state {state_f.height} firm-months  "
            f"{state_f['permno'].n_unique()} firms  "
            f"{state_f['date'].min()} → {state_f['date'].max()}"
        )
        top = (
            state_f.group_by("permno")
            .len()
            .sort("len", descending=True)
            .head(80)["permno"]
            .to_list()
        )
        slim = state_f.filter(pl.col("permno").is_in(top))
        fit_f = estimate_var_panel(slim, spec_f)
        print(
            f"  VAR on top 80  nobs={fit_f.nobs}  ρ(Φ)={fit_f.spectral_radius:.4f}"
        )
        print(
            f"  Φ[roe,roe]={fit_f.Phi[0, 0]:+.3f}  "
            f"Φ[roe,bm]={fit_f.Phi[0, spec_f.index('bm')]:+.3f}  "
            f"Φ[roe,cay]={fit_f.Phi[0, spec_f.index('cay')]:+.3f}"
        )
    except Exception as exc:
        print(f"  skipped: {type(exc).__name__}: {exc}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
