"""Ang and Liu (2004) — reproduction and sample extension.

Default path uses Ken French / FRED / cay (no WRDS)::

    uv add "varvaluation[data]"
    uv run python examples/reproduce_angliu2004.py

Paper sample is July 1965–December 2000 (BM) and January 1964–December 2000
(industries). The same objects are then re-estimated through the latest cay
month. Compustat Δp and the CRSP VW market require credentials::

    uv add "varvaluation[data,wrds]"
    uv run python examples/reproduce_angliu2004.py --wrds

Offline (no downloads)::

    uv run python examples/reproduce_angliu2004.py --synthetic
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import numpy as np
import polars as pl

from varvaluation.angliu import (
    BM_LABELS,
    BM_START,
    FOCUS_BM,
    FOCUS_INDUSTRIES,
    IND_START,
    PAPER_END,
    VALUATION_DATE,
    capm_alpha,
    check_shape,
    constant_capm_rate,
    curve_snapshot,
    expected_return_loadings,
    fit_portfolio,
    fit_premium,
    lambda_series,
    paper_spec,
    simulate_paper_state,
    var_table,
)


def _label(name: str) -> str:
    return BM_LABELS.get(name, name)


def _print_premium(rp) -> None:
    print()
    print("# Risk premium   y^m_{t+1} − r_t  =  b0 + br r + bcay cay")
    print(
        f"  market {rp.market}   sample {rp.sample[0]} → {rp.sample[1]}   "
        f"n={rp.nobs}   R²={rp.r_squared:.3f}"
    )
    for key in ("b0", "br", "bcay"):
        print(
            f"  {key:>5} = {rp.coeffs[key]:+.4f}   "
            f"(se {rp.stderrs[key]:.4f},  t={rp.tstats[key]:+.2f})"
        )


def _print_moments(result) -> None:
    m = result.moments
    print()
    print(
        f"# Table I  {_label(result.name)}   "
        f"n={int(m['nobs'])}   ρ(Φ)={m['spectral_radius']:.3f}"
    )
    print(f"  {'':<6} {'mean':>8} {'sd':>8} {'ρ_12':>8}")
    for name in ("g", "beta", "dpo", "r", "cay", "pi"):
        print(
            f"  {name:<6} {100 * m[f'{name}_mean']:8.2f} "
            f"{100 * m[f'{name}_sd']:8.2f} {m[f'{name}_auto']:8.3f}"
        )
    print(f"  α_CAPM {100 * result.alpha:7.2f}%    β_CAPM {result.beta_capm:5.2f}")


def _print_var(result) -> None:
    tbl = var_table(result.fit)
    names = list(result.fit.spec.names)
    print()
    print(f"# Table II  Φ   {_label(result.name)}")
    header = f"  {'eq':<6}" + "".join(f"{n:>8}" for n in names)
    print(header)
    for row in tbl.iter_rows(named=True):
        coefs = "".join(f"{row[f'lag_{n}']:+8.3f}" for n in names)
        print(f"  {row['equation']:<6}{coefs}")
        ses = "".join(f"({row[f'se_{n}']:.3f})".rjust(8) for n in names)
        print(f"  {'':<6}{ses}")


def _print_curve(result) -> None:
    snap = curve_snapshot(result.rates)
    print()
    print(f"# Spot curve μ_t(n)  {_label(result.name)}  as of {result.asof}")
    print(f"  identity μ(1)−(α+ξ'X+X'ΛX) = {result.moments['identity_err']:+.2e}")
    print(f"  {'n':>4}  {'μ(n) %':>8}")
    for n in (1, 5, 10, 15, 20, 30):
        key = f"mu_{n}"
        if key in snap:
            print(f"  {n:4d}  {100 * snap[key]:8.2f}")
    print(f"  slope 30−1   {100 * snap['slope_30_1']:+.2f} pp")
    p = result.perp
    print(
        f"  unit perp   TS={p['v_ts']:.2f}   "
        f"flat uncond={p['v_uncond']:.2f} ({p['gap_uncond_pct']:+.1f}%)   "
        f"flat CAPM={p['v_capm']:.2f} ({p['gap_capm_pct']:+.1f}%)"
    )
    print(
        f"  μ_uncond={100 * p['mu_uncond']:.2f}%   "
        f"μ_CAPM={100 * p['mu_capm']:.2f}%   tail={100 * p.get('tail_rate', float('nan')):.2f}%"
    )


def _print_shares(result, n: int = 10) -> None:
    row = result.var_shares.filter(pl.col("maturity") == n)
    if row.is_empty():
        return
    rec = row.row(0, named=True)
    bits = "  ".join(f"{k}={100 * rec[k]:4.1f}%" for k in ("g", "beta", "dpo", "r", "cay", "pi"))
    print(f"  var share n={n}:  {bits}")


def _print_shape(report) -> None:
    flags = []
    flags.append("identity" if report.identity_ok else "IDENTITY FAIL")
    flags.append("stationary" if report.stationary else "UNIT ROOT")
    flags.append("upward" if report.upward else "NOT UPWARD")
    flags.append("below CAPM" if report.below_capm else "NOT BELOW CAPM")
    flags.append(f"|gap|={abs(report.gap_capm_pct):.1f}%")
    print(f"  shape  [{', '.join(flags)}]")


def _news_line(result, total: pl.DataFrame | None, xi, Lambda) -> None:
    if total is None or result.name not in total.columns:
        return
    try:
        from varvaluation.news import news_decomposition

        frame = total.select(["date", result.name]).sort("date")
        log_r = np.log(1.0 + frame[result.name].to_numpy())
        rets = (
            pl.DataFrame({"date": frame["date"], "lr": log_r})
            .with_columns((pl.col("lr").rolling_sum(12).exp() - 1).alias("ret"))
            .select(["date", "ret"])
            .drop_nulls()
        )
        news = news_decomposition(
            result.fit, rets, return_col="ret", xi=xi, Lambda=Lambda
        )
        s = news.shares
        print(
            f"  news   var(cf)={s.var_cf:.5f}  var(dr)={s.var_dr:.5f}  "
            f"residual_share={s.residual_share:.3f}  (not a 2004 table)"
        )
    except Exception as exc:
        print(f"  news   skipped ({type(exc).__name__}: {exc})")


def run_one(
    name: str,
    state: pl.DataFrame,
    spec,
    xi,
    Lambda,
    alpha: float,
    beta_capm: float,
    capm_rate: float,
    when: date,
    *,
    total: pl.DataFrame | None = None,
) -> object | None:
    try:
        result = fit_portfolio(
            name, state, spec, xi, Lambda, alpha, beta_capm, when=when, capm_rate=capm_rate
        )
    except Exception as exc:
        print()
        print(f"# {name}  FAILED  {type(exc).__name__}: {exc}")
        return None
    _print_moments(result)
    _print_var(result)
    _print_curve(result)
    _print_shares(result, n=1)
    _print_shares(result, n=10)
    _print_shares(result, n=30)
    report = check_shape(
        name,
        asof=result.asof,
        rates=result.rates,
        mu_capm=result.perp["mu_capm"],
        gap_capm_pct=result.perp["gap_capm_pct"],
        identity_err=result.moments["identity_err"],
        spectral_radius=result.moments["spectral_radius"],
    )
    _print_shape(report)
    _news_line(result, total, xi, Lambda)
    return result


def run_synthetic() -> int:
    print("Synthetic six-state system (offline). Same objects as Ang and Liu (2004).")
    spec = paper_spec(horizon=1, nw_lags=4)
    from varvaluation.angliu.premium import PremiumResult
    from varvaluation.spec import ExpectedReturnSpec

    # Designed premium: λ = 0.06 − 0.4 r + 1.0 cay
    rp = PremiumResult(
        coeffs={"b0": 0.06, "br": -0.40, "bcay": 1.0},
        stderrs={"b0": 0.01, "br": 0.20, "bcay": 0.30},
        tstats={"b0": 6.0, "br": -2.0, "bcay": 3.3},
        nobs=400,
        r_squared=0.08,
        sample=("1965-07-31", "2000-12-31"),
        market="synthetic",
    )
    _print_premium(rp)
    xi, Lambda = ExpectedReturnSpec(premium=("cay",)).xi_lambda(spec, rp.coeffs)
    for name, beta in (("D1", 0.85), ("D6", 1.00), ("D10", 1.20)):
        state, _ = simulate_paper_state(nobs=426, seed=2000 + hash(name) % 50, beta_mean=beta)
        alpha = 0.01
        capm = alpha + float(state["r"].mean()) + beta * (
            rp.coeffs["b0"] + rp.coeffs["br"] * float(state["r"].mean())
            + rp.coeffs["bcay"] * float(state["cay"].mean())
        )
        run_one(name, state, spec, xi, Lambda, alpha, beta, capm, state["date"][-1])
    return 0


def _match_industries(columns: list[str]) -> list[str]:
    lower = {c.lower().strip(): c for c in columns if c != "date"}
    found = []
    for name in FOCUS_INDUSTRIES:
        key = name.lower()
        if key in lower:
            found.append(lower[key])
            continue
        for cand, orig in lower.items():
            if cand.startswith(key) or key.startswith(cand):
                found.append(orig)
                break
    return found


def run_public(*, do_extension: bool, do_industries: bool) -> dict:
    from varvaluation.data import (
        load_bm_deciles,
        load_industry49,
        load_macro,
        prepare_portfolio_state,
    )

    print("Loading Ken French / FRED / cay (cached).")
    total_bm, cap_bm = load_bm_deciles()
    macro = load_macro()
    print(
        f"  BM deciles {total_bm['date'][0]} → {total_bm['date'][-1]}   "
        f"macro {macro['date'][0]} → {macro['date'][-1]}"
    )
    if "cay" in macro.columns:
        cay = macro.filter(pl.col("cay").is_not_null())
        print(f"  cay {cay['date'][0]} → {cay['date'][-1]}")

    spec = paper_spec()
    rp = fit_premium(macro, BM_START, PAPER_END)
    _print_premium(rp)
    xi, Lambda = expected_return_loadings(spec, rp)
    lam = lambda_series(macro, rp)

    print()
    print("=" * 72)
    print(f"PAPER SAMPLE  {BM_START} → {PAPER_END}   valuation {VALUATION_DATE}")
    print("=" * 72)

    results = {"paper": {}, "extended": {}}
    for name in FOCUS_BM:
        state = prepare_portfolio_state(
            total_bm, cap_bm, macro, spec, portfolio=name, start=BM_START, end=PAPER_END
        )
        alpha, beta = capm_alpha(total_bm, macro, name, start=BM_START, end=PAPER_END)
        capm = constant_capm_rate(state, lam, alpha=alpha, beta_capm=beta)
        results["paper"][name] = run_one(
            name, state, spec, xi, Lambda, alpha, beta, capm, VALUATION_DATE, total=total_bm
        )

    if do_industries:
        try:
            total_ind, names, cap_ind = load_industry49()
        except Exception as exc:
            print(f"\nIndustries skipped ({type(exc).__name__}: {exc})")
            total_ind = cap_ind = None
        else:
            focus = _match_industries(list(total_ind.columns))
            print()
            print(f"Industry focus: {focus}")
            for name in focus:
                state = prepare_portfolio_state(
                    total_ind,
                    cap_ind,
                    macro,
                    spec,
                    portfolio=name,
                    start=IND_START,
                    end=PAPER_END,
                )
                alpha, beta = capm_alpha(
                    total_ind, macro, name, start=IND_START, end=PAPER_END
                )
                capm = constant_capm_rate(state, lam, alpha=alpha, beta_capm=beta)
                results["paper"][name] = run_one(
                    name,
                    state,
                    spec,
                    xi,
                    Lambda,
                    alpha,
                    beta,
                    capm,
                    VALUATION_DATE,
                    total=total_ind,
                )

    if not do_extension:
        return results

    cay_end = None
    if "cay" in macro.columns:
        cay_nn = macro.filter(pl.col("cay").is_not_null())
        if cay_nn.height:
            cay_end = cay_nn["date"][-1]
    end_s = f"{cay_end.year}-{cay_end.month:02d}" if cay_end else None
    print()
    print("=" * 72)
    print(f"EXTENSION  {BM_START} → {end_s or 'latest'}   (not in the 2004 paper)")
    print("=" * 72)

    rp_x = fit_premium(macro, BM_START, end_s or PAPER_END)
    _print_premium(rp_x)
    xi_x, Lam_x = expected_return_loadings(spec, rp_x)
    lam_x = lambda_series(macro, rp_x)
    when = cay_end or date(2019, 9, 30)

    for name in FOCUS_BM:
        state = prepare_portfolio_state(
            total_bm, cap_bm, macro, spec, portfolio=name, start=BM_START, end=end_s
        )
        alpha, beta = capm_alpha(total_bm, macro, name, start=BM_START, end=end_s)
        capm = constant_capm_rate(state, lam_x, alpha=alpha, beta_capm=beta)
        print()
        print(f"--- {name} on the long sample, valued at {when} ---")
        results["extended"][name] = run_one(
            name, state, spec, xi_x, Lam_x, alpha, beta, capm, when, total=total_bm
        )
        # Same long-sample system, paper date (look-ahead in Φ).
        print(f"--- {name} on the long sample, valued at {VALUATION_DATE} (look-ahead) ---")
        run_one(
            name, state, spec, xi_x, Lam_x, alpha, beta, capm, VALUATION_DATE, total=total_bm
        )

    return results


def run_wrds(_public_results: dict | None = None) -> None:
    from varvaluation.angliu.payout import (
        attach_compustat_dpo,
        crsp_vw_returns,
        market_compustat_dpo,
        proxy_vs_compustat,
    )
    from varvaluation.data import load_macro, prepare_portfolio_state

    print()
    print("=" * 72)
    print("WRDS  Compustat Δp on the CRSP value-weighted market")
    print("=" * 72)
    total, cap = crsp_vw_returns(start="1960-01", end="2000-12-31")
    dpo = market_compustat_dpo(start="1960-01", end="2000-12-31")
    cmp = proxy_vs_compustat(total, cap, dpo, portfolio="MKT")
    print(
        f"  proxy vs Compustat Δp   n={int(cmp['nobs'])}   "
        f"corr={cmp.get('corr', float('nan')):.3f}   "
        f"sd proxy={cmp.get('proxy_sd', float('nan')):.3f}   "
        f"sd Compustat={cmp.get('compustat_sd', float('nan')):.3f}"
    )

    macro = load_macro()
    spec = paper_spec()
    # Join CRSP VW as a one-column portfolio named MKT.
    state_proxy = prepare_portfolio_state(
        total, cap, macro, spec, portfolio="MKT", start=BM_START, end=PAPER_END
    )
    state_cs = attach_compustat_dpo(state_proxy, dpo)
    rp = fit_premium(macro, BM_START, PAPER_END)
    xi, Lambda = expected_return_loadings(spec, rp)
    lam = lambda_series(macro, rp)
    # Build a fake total frame so capm_alpha can see MKT — use CRSP VW vs FF market.
    alpha, beta = capm_alpha(total, macro, "MKT", start=BM_START, end=PAPER_END)
    for label, state in (("proxy Δp", state_proxy), ("Compustat Δp", state_cs)):
        capm = constant_capm_rate(state, lam, alpha=alpha, beta_capm=beta)
        print()
        print(f"--- CRSP VW market, {label} ---")
        run_one("MKT", state, spec, xi, Lambda, alpha, beta, capm, VALUATION_DATE, total=total)

    # Alternative premium using CRSP VW instead of FF market.
    mkt = total.rename({"MKT": "mkt_crsp"}).select(["date", "mkt_crsp"])
    macro_c = macro.join(mkt, on="date", how="left")
    try:
        rp_c = fit_premium(macro_c, BM_START, PAPER_END, market="mkt_crsp")
        print()
        print("Premium on CRSP vwretd (instead of Ken French Mkt):")
        _print_premium(rp_c)
    except Exception as exc:
        print(f"  CRSP premium skipped ({type(exc).__name__}: {exc})")


def _maybe_figures(results: dict) -> None:
    paper = results.get("paper") or {}
    usable = {k: v for k, v in paper.items() if v is not None and k in FOCUS_BM}
    if len(usable) < 2:
        return
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return
    out = Path("docs/assets/figures")
    out.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    mat = np.arange(1, 31)
    for name, res in usable.items():
        ax.plot(mat, 100 * res.rates, label=_label(name), linewidth=1.6)
        ax.axhline(100 * res.perp["mu_capm"], color="0.5", linestyle="--", linewidth=0.8)
    ax.set_xlabel("Maturity (years)")
    ax.set_ylabel("Spot discount rate μ_t(n) (%)")
    ax.set_title("Ang–Liu spot curves at December 2000")
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / "angliu_dec2000_curves.svg")
    fig.savefig(out / "angliu_dec2000_curves.png", dpi=140)
    plt.close(fig)

    fig, axes = plt.subplots(1, len(usable), figsize=(4.2 * len(usable), 3.6), sharey=True)
    if len(usable) == 1:
        axes = [axes]
    names = list(usable)
    for ax, name in zip(axes, names, strict=True):
        res = usable[name]
        share = res.var_shares
        cols = ["g", "beta", "dpo", "r", "cay", "pi"]
        ax.stackplot(
            share["maturity"].to_numpy(),
            *[np.clip(share[c].to_numpy(), 0, None) for c in cols],
            labels=cols,
        )
        ax.set_title(_label(name))
        ax.set_xlabel("Maturity")
        ax.set_ylim(0, 1)
    axes[0].set_ylabel("Share of var(μ_t(n))")
    axes[-1].legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(out / "angliu_varshare.svg")
    fig.savefig(out / "angliu_varshare.png", dpi=140)
    plt.close(fig)
    print(f"\nWrote figures under {out}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic", action="store_true", help="offline six-state draw")
    parser.add_argument("--wrds", action="store_true", help="Compustat Δp + CRSP VW market")
    parser.add_argument("--paper-only", action="store_true", help="skip the post-2000 extension")
    parser.add_argument("--no-industries", action="store_true", help="skip the 49-industry file")
    args = parser.parse_args(argv)

    if args.synthetic:
        return run_synthetic()

    results = run_public(do_extension=not args.paper_only, do_industries=not args.no_industries)
    _maybe_figures(results)
    if args.wrds:
        run_wrds(results)
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
