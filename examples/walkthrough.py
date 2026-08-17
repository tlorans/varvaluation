"""Step-by-step walkthrough on Ken French / FRED / WRDS. No fiction.

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
    StateSpec,
    ValuationModel,
    estimate_var,
    estimate_var_panel,
    news_decomposition,
)
from varvaluation.data import load_bm_deciles, load_macro, prepare_portfolio_state

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
    end = pl.date(int(END[:4]), int(END[5:7]), 1).dt.month_end()
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


def capm_alpha(total: pl.DataFrame, macro: pl.DataFrame, col: str) -> float:
    frame = (
        total.select(["date", col])
        .join(macro.select(["date", "rf", "mkt"]), on="date", how="inner")
        .drop_nulls()
    )
    y = np.log(1 + frame[col].to_numpy()) - np.log(1 + frame["rf"].to_numpy())
    x = np.log(1 + frame["mkt"].to_numpy()) - np.log(1 + frame["rf"].to_numpy())
    ok = np.isfinite(y) & np.isfinite(x)
    X = np.column_stack([np.ones(ok.sum()), x[ok]])
    coeffs, *_ = np.linalg.lstsq(X, y[ok], rcond=None)
    return float(coeffs[0] * 12)


def annual_returns(total: pl.DataFrame, col: str) -> pl.DataFrame:
    frame = total.select(["date", col]).sort("date")
    lr = np.log(1 + frame[col].to_numpy())
    return (
        pl.DataFrame({"date": frame["date"], "lr": lr})
        .with_columns((pl.col("lr").rolling_sum(12).exp() - 1).alias("ret"))
        .select(["date", "ret"])
        .drop_nulls()
    )


def main() -> int:
    _print("Step 1 — public data")
    total, capgains = load_bm_deciles()
    macro = load_macro()
    print(f"BE/ME deciles  {total['date'][0]} → {total['date'][-1]}  n={total.height}")
    print(f"macro          {macro['date'][0]} → {macro['date'][-1]}  n={macro.height}")
    print("macro columns:", list(macro.columns))
    cay = macro.filter(pl.col("cay").is_not_null()) if "cay" in macro.columns else None
    if cay is not None:
        print(f"cay            {cay['date'][0]} → {cay['date'][-1]}")

    _print("Step 2 — portfolio state (D1 growth, D10 value)")
    spec = StateSpec(names=("g", "beta", "dpo", "r", "cay", "pi"), cashflow="g")
    states = {}
    for name in ("D1", "D10"):
        state = prepare_portfolio_state(
            total, capgains, macro, spec, portfolio=name, start=START, end=END
        )
        states[name] = state
        last = state.row(-1, named=True)
        print(
            f"{name}  {state['date'][0]} → {state['date'][-1]}  "
            f"months={state.height}"
        )
        print(
            "  last X: "
            + ", ".join(f"{k}={last[k]:+.3f}" for k in spec.names)
        )

    _print("Step 3 — risk premium")
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

    _print("Step 4 — VAR")
    fits = {}
    for name, state in states.items():
        fit = estimate_var(state, spec)
        fits[name] = fit
        g_i = spec.cashflow_index()
        print(
            f"{name}  nobs={fit.nobs}  spectral radius={fit.spectral_radius:.3f}  "
            f"Phi[g,g]={fit.Phi[g_i, g_i]:+.3f}"
        )
        print(
            "  Phi[g, ·]  "
            + "  ".join(
                f"{n}={fit.Phi[g_i, spec.index(n)]:+.3f}" for n in spec.names
            )
        )

    _print("Step 5 — both sides from X")
    for name, state in states.items():
        fit = fits[name]
        alpha = capm_alpha(total, macro, name)
        model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=alpha)
        X = state.select(list(spec.names)).to_numpy()[-1]
        rates = model.spot_rates(X, n=30)
        cf = model.cashflow_expectation(X, n=30)
        perp = model.perpetuity(X, n=80)
        val = model.value(X, C=1.0, n=80)
        print(f"{name}  alpha={alpha:.3f}")
        print(
            "  spot mu(n) %   n=1, 5, 10, 30: "
            + ", ".join(f"{100 * rates[k]:.2f}" for k in (0, 4, 9, 29))
        )
        print(
            "  E[C]/C         n=1, 5, 10, 30: "
            + ", ".join(f"{cf[k]:.3f}" for k in (0, 4, 9, 29))
        )
        print(
            f"  value={val.pv:.2f}  perpetuity={perp.pv:.2f}  "
            f"n_used={val.n_used}"
        )

    _print("Step 6 — news (same VAR)")
    for name in ("D1", "D10"):
        news = news_decomposition(
            fits[name],
            annual_returns(total, name),
            return_col="ret",
            xi=xi,
            Lambda=Lambda,
        )
        s = news.shares
        print(
            f"{name}  var(cf)={s.var_cf:.4f}  var(dr)={s.var_dr:.4f}  "
            f"residual_share={s.residual_share:.2f}"
        )

    _print("Step 7 — firms from WRDS")
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        from varvaluation.wrds import merge_firm_panel, prepare_firm_state
        from varvaluation.wrds.load import load_ccm_link, load_compustat_annual, load_crsp_monthly

        crsp = load_crsp_monthly(start="2014-01", end="2019-12-31", use_cache=True)
        comp = load_compustat_annual(start="2012-01", end="2019-12-31", use_cache=True)
        link = load_ccm_link(use_cache=True)
        panel = merge_firm_panel(crsp, comp, link)
        spec_f = StateSpec(
            names=("roe", "beta", "bm", "r", "cay", "pi"),
            cashflow="roe",
            group="permno",
        )
        state_f = prepare_firm_state(
            panel, macro, spec_f, start="2015-01", end="2019-09", beta_window=12
        )
        print(
            f"panel  {state_f.height} firm-months  "
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
        roe_i = spec_f.cashflow_index()
        print(
            f"VAR on 80 longest firms  nobs={fit_f.nobs}  "
            f"spectral radius={fit_f.spectral_radius:.3f}  "
            f"Phi[roe,roe]={fit_f.Phi[roe_i, roe_i]:+.3f}"
        )
        print(
            "  Phi[roe, ·]  "
            + "  ".join(
                f"{n}={fit_f.Phi[roe_i, spec_f.index(n)]:+.3f}"
                for n in spec_f.names
            )
        )
        last_date = state_f["date"].max()
        one = (
            slim.filter(pl.col("date") == last_date)
            .sort("permno")
            .head(1)
        )
        if one.height:
            Xf = one.select(list(spec_f.names)).to_numpy()[0]
            xi_f, Lambda_f = ExpectedReturnSpec(premium=("cay",)).xi_lambda(
                spec_f, {"b0": rp["b0"], "br": rp["br"], "bcay": rp["bcay"]}
            )
            model_f = ValuationModel.from_var(
                fit_f, xi=xi_f, Lambda=Lambda_f, alpha=0.02
            )
            rates_f = model_f.spot_rates(Xf, n=10)
            roe = float(one["roe"][0])
            print(
                f"one firm at {last_date}  permno={one['permno'][0]}  "
                f"roe={roe:+.3f}  NI/BE={np.exp(roe):.3f}  "
                f"bm={one['bm'][0]:+.3f}"
            )
            print(
                "  spot mu(n) %   n=1, 5, 10: "
                + ", ".join(f"{100 * rates_f[k]:.2f}" for k in (0, 4, 9))
            )
    except Exception as exc:
        print(f"skipped: {type(exc).__name__}: {exc}")

    print()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
