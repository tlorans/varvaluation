"""Giacotto, Lin, and Zhao (2020) — term structure for insurance industries.

Default path is synthetic (no downloads). It prints the same objects as
the paper — an unconditional curve, CAPM / slope tests, a 30-year
annuity — so the API is visible without WRDS.

Live reproduction (Compustat quarterly + CRSP daily)::

    uv add "varvaluation[data,wrds]"
    uv run python examples/reproduce_glz2020.py --wrds

Compare the printed Table 2 means to IME 95 (2020), p. 156.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

from varvaluation import (
    CCAPMSpec,
    INSURANCE,
    ResidualIncome,
    TermStructureModel,
    capm_tests,
    estimate_var,
    flat_annuity_value,
    paper_state_spec,
    simulate_paper_state,
    slope_tests,
    valuation_discrepancy,
)
from varvaluation.industry import curve_panel


def _print_curve(title: str, rho: np.ndarray, y: float, capm: float) -> None:
    print()
    print(f"# {title}")
    print(f"{'τ':>4}  {'ρ(τ)':>8}  {'y(τ)':>8}  {'CCAPM':>8}  {'CAPM':>8}")
    for tau in (1, 5, 10, 15, 20, 25, 30):
        print(
            f"{tau:4d}  {100 * rho[tau - 1]:8.2f}  {100 * y:8.2f}  "
            f"{100 * rho[0]:8.2f}  {100 * capm:8.2f}"
        )


def _print_tests(rho_ts: np.ndarray, capm: np.ndarray) -> None:
    print()
    print("# Table 2  H0: mean ρ(τ) = mean CAPM")
    print(f"{'τ':>4}  {'mean':>8}  {'t':>8}  {'p':>8}")
    for row in capm_tests(rho_ts, capm):
        print(f"{row.tau:4d}  {100 * row.mean:8.2f}  {row.tstat:8.2f}  {row.pvalue:8.3f}")
    print()
    print("# Table 3  H0: mean ρ(τ) = mean ρ(1)")
    print(f"{'τ':>4}  {'slope':>8}  {'t':>8}  {'p':>8}")
    for row in slope_tests(rho_ts):
        print(f"{row.tau:4d}  {100 * row.mean:8.2f}  {row.tstat:8.2f}  {row.pvalue:8.3f}")


def run_synthetic() -> None:
    print("Synthetic industry state (offline). Same API as the paper.")
    portfolios = {
        "All insurers": 0.65,
        "P/C": 0.62,
        "Life": 0.78,
        "Health": 0.64,
        "All stocks excl. insurers": 0.97,
    }
    y_bar = 0.055
    for name, beta in portfolios.items():
        state, spec = simulate_paper_state(nobs=160, seed=11, beta_mean=beta)
        spec = paper_state_spec(horizon=1)
        fit = estimate_var(state, spec)
        model = TermStructureModel.from_var(fit, ResidualIncome(), CCAPMSpec())
        rho_bar = model.unconditional_curve(y_bar, n=30)
        xbar = model.unconditional_mean()
        capm_flat = y_bar + float(np.mean(state["beta"].to_numpy()) * np.mean(state["mrp"].to_numpy()))
        _print_curve(name, rho_bar, y_bar, capm_flat)
        rho_ts = curve_panel(model, state, y_bar, n=30)
        capm_ts = y_bar + state["beta"].to_numpy() * state["mrp"].to_numpy()
        _print_tests(rho_ts, capm_ts)
        v_ts = model.annuity_value(xbar, y_bar, n=30)
        v_ccapm = flat_annuity_value(model.flat_ccapm_rate(xbar, y_bar), n=30)
        v_capm = flat_annuity_value(capm_flat, n=30)
        print()
        print("# Table 4  30-year $1 annuity at the long-run mean")
        print(f"  term structure {v_ts:.2f}")
        print(f"  CCAPM          {v_ccapm:.2f}  discrepancy {100 * valuation_discrepancy(v_ts, v_ccapm):+.2f}%")
        print(f"  CAPM           {v_capm:.2f}  discrepancy {100 * valuation_discrepancy(v_ts, v_capm):+.2f}%")


def run_wrds() -> None:
    from varvaluation.data import load_paper_macro
    from varvaluation.industry import prepare_industry_state
    from varvaluation.wrds import (
        attach_posterior_beta,
        load_ccm_link,
        load_compustat_quarterly,
        load_crsp_daily,
        load_crsp_dsi,
        load_crsp_monthly,
        merge_quarterly_panel,
        quarter_end_betas,
    )

    import polars as pl

    print("Loading WRDS quarterly Compustat + CRSP daily (cached).")
    start, end = "1971-01", "2018-12-31"
    macro = load_paper_macro()
    compq = load_compustat_quarterly(start=start, end=end)
    link = load_ccm_link()
    crsp_m = load_crsp_monthly(start=start, end=end)
    panel = merge_quarterly_panel(crsp_m, compq, link)
    permnos = panel["permno"].unique().to_list()
    daily = load_crsp_daily(start=start, end=end, permnos=permnos)
    dsi = load_crsp_dsi(start=start, end=end)
    daily_mkt = dsi.rename({"vwretd": "mkt"}).join(
        macro.select(["date", "rf"]).unique(), on="date", how="left"
    )
    daily_mkt = daily_mkt.with_columns(pl.col("rf").forward_fill())

    qe = quarter_end_betas(daily, daily_mkt)
    panel = attach_posterior_beta(panel, qe, method="rolling")
    spec = paper_state_spec(horizon=4)
    y_bar = float(macro["y1"].drop_nulls().mean()) if "y1" in macro.columns else 0.05
    labels = {
        "All insurers": INSURANCE["all"],
        "P/C": INSURANCE["pc"],
        "Life": INSURANCE["life"],
        "Health": INSURANCE["health"],
        "All stocks excl. insurers": "ex",
    }
    for name, sic in labels.items():
        state = prepare_industry_state(panel, macro, spec, sic=sic)
        fit = estimate_var(state, spec)
        model = TermStructureModel.from_var(fit, ResidualIncome(), CCAPMSpec())
        rho_bar = model.unconditional_curve(y_bar, n=30)
        capm_flat = y_bar + float(state["beta"].mean() * state["mrp"].mean())
        _print_curve(name, rho_bar, y_bar, capm_flat)
        rho_ts = curve_panel(model, state, y_bar, n=30)
        capm_ts = y_bar + state["beta"].to_numpy() * state["mrp"].to_numpy()
        _print_tests(rho_ts, capm_ts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--wrds",
        action="store_true",
        help="load Compustat quarterly + CRSP daily and rebuild the paper sample",
    )
    args = parser.parse_args(argv)
    if args.wrds:
        run_wrds()
    else:
        run_synthetic()
    return 0


if __name__ == "__main__":
    sys.exit(main())
