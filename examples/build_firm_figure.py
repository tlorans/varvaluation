"""Spot curves at three firms. Run after walkthrough data are cached."""

from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from varvaluation import ExpectedReturnSpec, StateSpec, ValuationModel, estimate_var_panel
from varvaluation.data import load_macro
from varvaluation.wrds import merge_firm_panel, prepare_firm_state
from varvaluation.wrds.load import load_ccm_link, load_compustat_annual, load_crsp_monthly

OUT = Path(__file__).resolve().parents[1] / "docs" / "assets" / "figures"
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white",
        "savefig.bbox": "tight",
        "savefig.dpi": 160,
    }
)


def main() -> None:
    macro = load_macro()
    panel = merge_firm_panel(
        load_crsp_monthly(start="2014-01", end="2019-12-31", use_cache=True),
        load_compustat_annual(start="2012-01", end="2019-12-31", use_cache=True),
        load_ccm_link(use_cache=True),
    )
    spec = StateSpec(
        names=("roe", "beta", "bm", "r", "cay", "pi"),
        cashflow="roe",
        group="permno",
    )
    state = prepare_firm_state(
        panel, macro, spec, start="2015-01", end="2019-09", beta_window=12
    )
    top = (
        state.group_by("permno")
        .len()
        .sort("len", descending=True)
        .head(80)["permno"]
        .to_list()
    )
    slim = state.filter(pl.col("permno").is_in(top))
    fit = estimate_var_panel(slim, spec)
    xi, lam = ExpectedReturnSpec(premium=("cay",)).xi_lambda(
        spec, {"b0": 0.095, "br": -0.737, "bcay": 0.708}
    )
    model = ValuationModel.from_var(fit, xi, lam, 0.02)
    last = slim.filter(pl.col("date") == slim["date"].max()).sort("permno")
    picks = [last.row(0, named=True), last.row(last.height // 2, named=True), last.row(-1, named=True)]
    colors = ["#1d4e89", "#2f6f4e", "#b04a3a"]
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    n = np.arange(1, 11)
    for row, col in zip(picks, colors, strict=True):
        x = np.array([row[k] for k in spec.names])
        ax.plot(
            n,
            100 * model.spot_rates(x, 10),
            color=col,
            label=f"permno {row['permno']}  β={row['beta']:.2f}",
        )
    ax.set_xlabel("horizon $n$ (years)")
    ax.set_ylabel(r"spot rate $\mu_t(n)$ (%)")
    ax.legend(frameon=False)
    ax.set_xlim(1, 10)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "firm_spot_curves.png"
    fig.savefig(path)
    print("wrote", path)


if __name__ == "__main__":
    main()
