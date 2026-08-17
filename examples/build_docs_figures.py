"""Build the figures embedded in the MkDocs site.

Run from the package root after `uv sync --extra data --extra docs`:

    uv run python examples/build_docs_figures.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import statsmodels.api as sm

from varvaluation import (
    ExpectedReturnSpec,
    StateSpec,
    ValuationModel,
    estimate_var,
    news_decomposition,
)
from varvaluation.data import (
    load_bm_deciles,
    load_cay,
    load_macro,
    prepare_portfolio_state,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "figures"
PAPER = Path(r"C:\DBD\corpo_research_papers\papers\01-discounting\code\data")
START, END = "1965-07", "2024-12"
FOCUS = ("D1", "D6", "D10")
LABEL = {"D1": "D1 growth", "D6": "D6", "D10": "D10 value"}
COLORS = {"D1": "#1d4e89", "D6": "#5b7c99", "D10": "#b04a3a"}
STATE_COLORS = ["#1d4e89", "#b04a3a", "#c48a2a", "#2f6f4e", "#6b4c9a", "#7a6a53"]

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.7,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.bbox": "tight",
        "savefig.dpi": 160,
    }
)


def _load():
    try:
        total, cap = load_bm_deciles()
    except Exception:
        total, cap = load_bm_deciles(
            path_total=PAPER / "bm10_portfolios" / "Portfolios_Formed_on_BE-ME.csv",
            path_exdiv=PAPER / "bm10_exdiv" / "Portfolios_Formed_on_BE-ME_Wout_Div.csv",
        )
    macro = load_macro()
    if PAPER.exists() and (PAPER / "cay_current.csv").exists():
        published = load_cay(path=PAPER / "cay_current.csv")
        live = macro["cay"] if "cay" in macro.columns else None
        if "cay" in macro.columns:
            macro = macro.drop("cay")
        macro = macro.join(published, on="date", how="left")
        if live is not None:
            macro = macro.with_columns(pl.coalesce(pl.col("cay"), live).alias("cay"))
    return total, cap, macro


def _rp(macro: pl.DataFrame) -> dict:
    log_mkt = np.log(1 + macro["mkt"].to_numpy())
    frame = macro.with_columns(pl.Series("log_mkt", log_mkt))
    frame = frame.with_columns(pl.col("log_mkt").rolling_sum(12).shift(-12).alias("y_fwd"))
    frame = frame.with_columns((pl.col("y_fwd") - pl.col("r")).alias("y"))
    start = pl.date(int(START[:4]), int(START[5:7]), 1)
    end = pl.date(int(END[:4]), int(END[5:7]), 1).dt.month_end()
    frame = frame.filter(pl.col("date").ge(start) & pl.col("date").le(end))
    frame = frame.select(["y", "r", "cay"]).drop_nulls()
    y = frame["y"].to_numpy()
    X = np.column_stack([np.ones(len(y)), frame.select(["r", "cay"]).to_numpy()])
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
    return {"b0": float(fit.params[0]), "br": float(fit.params[1]), "bcay": float(fit.params[2])}


def _alpha(total, macro, col):
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


def _ann_ret(total, col):
    frame = total.select(["date", col]).sort("date")
    lr = np.log(1 + frame[col].to_numpy())
    return (
        pl.DataFrame({"date": frame["date"], "lr": lr})
        .with_columns((pl.col("lr").rolling_sum(12).exp() - 1).alias("ret"))
        .select(["date", "ret"])
        .drop_nulls()
    )


def _save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    fig.savefig(path)
    plt.close(fig)
    print("wrote", path)


def main():
    total, cap, macro = _load()
    spec = StateSpec(names=("g", "beta", "dpo", "r", "cay", "pi"), cashflow="g")
    coeffs = _rp(macro)
    xi, Lambda = ExpectedReturnSpec().xi_lambda(spec, coeffs)

    models = {}
    for name in FOCUS:
        state = prepare_portfolio_state(
            total, cap, macro, spec, portfolio=name, start=START, end=END
        )
        fit = estimate_var(state, spec)
        model = ValuationModel.from_var(fit, xi, Lambda, _alpha(total, macro, name))
        X = state.select(list(spec.names)).to_numpy()[-1]
        models[name] = dict(state=state, fit=fit, model=model, X=X)

    maturities = np.arange(1, 31)
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    for name in FOCUS:
        rates = 100 * models[name]["model"].spot_rates(models[name]["X"], 30)
        ax.plot(maturities, rates, color=COLORS[name], lw=1.8, label=LABEL[name])
    ax.set_xlabel("Maturity (years)")
    ax.set_ylabel("Spot discount rate (%)")
    ax.legend(frameon=False)
    _save(fig, "spot_curves.png")

    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    decomp, tot = models["D10"]["model"].variance_decomposition(30)
    share = np.clip(decomp / np.maximum(tot[:, None], 1e-16), 0, None)
    ax.stackplot(maturities, share.T, labels=list(spec.names), colors=STATE_COLORS, alpha=0.9)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Maturity (years)")
    ax.set_ylabel("Share of spot-rate variance")
    ax.legend(frameon=False, ncol=3, fontsize=8, loc="upper right")
    _save(fig, "variance_decomp_d10.png")

    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    xs = np.arange(len(FOCUS))
    cf_s, dr_s = [], []
    for name in FOCUS:
        news = news_decomposition(
            models[name]["fit"],
            _ann_ret(total, name),
            return_col="ret",
            xi=xi,
            Lambda=Lambda,
        )
        cf_s.append(news.shares.var_cf)
        dr_s.append(news.shares.var_dr)
    ax.bar(xs - 0.18, cf_s, 0.36, color="#1d4e89", label="Cash-flow news")
    ax.bar(xs + 0.18, dr_s, 0.36, color="#b04a3a", label="Discount-rate news")
    ax.set_xticks(xs, [LABEL[n] for n in FOCUS])
    ax.set_ylabel("Variance")
    ax.legend(frameon=False)
    _save(fig, "news_shares.png")
    print("done")


if __name__ == "__main__":
    main()
