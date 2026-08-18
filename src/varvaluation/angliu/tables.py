"""Table objects for the Ang and Liu (2004) reproduction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import polars as pl

from varvaluation.estimate import VARFit, estimate_var
from varvaluation.exceptions import NonStationaryVARError, PerpetuityDivergesError
from varvaluation.model import ValuationModel
from varvaluation.spec import StateSpec
from varvaluation.valuation import perpetuity_value


@dataclass(frozen=True)
class PortfolioResult:
    name: str
    state: pl.DataFrame
    fit: VARFit
    model: ValuationModel
    alpha: float
    beta_capm: float
    X: np.ndarray
    asof: date
    rates: np.ndarray
    moments: dict[str, float]
    perp: dict[str, float]
    var_shares: pl.DataFrame


def as_of_row(state: pl.DataFrame, when: date, spec: StateSpec) -> tuple[np.ndarray, date]:
    """State vector at ``when``, or the last row on or before that date."""
    work = state.filter(pl.col(spec.date) <= when)
    if work.is_empty():
        work = state
    row = work.row(-1, named=True)
    X = np.array([float(row[n]) for n in spec.names], dtype=float)
    return X, row[spec.date]


def sample_moments(state: pl.DataFrame, spec: StateSpec, *, lag: int = 12) -> dict[str, float]:
    """Means, s.d., and annual-lag autocorrelations of the named state."""
    out: dict[str, float] = {"nobs": float(state.height)}
    for name in spec.names:
        x = state[name].to_numpy().astype(float)
        out[f"{name}_mean"] = float(np.nanmean(x))
        out[f"{name}_sd"] = float(np.nanstd(x, ddof=1)) if len(x) > 1 else float("nan")
        if len(x) > lag:
            a = x[lag:]
            b = x[:-lag]
            ok = np.isfinite(a) & np.isfinite(b)
            if ok.sum() > 2:
                out[f"{name}_auto"] = float(np.corrcoef(a[ok], b[ok])[0, 1])
            else:
                out[f"{name}_auto"] = float("nan")
        else:
            out[f"{name}_auto"] = float("nan")
    return out


def var_table(fit: VARFit) -> pl.DataFrame:
    """Companion Φ with Newey–West standard errors (one row per equation)."""
    names = list(fit.spec.names)
    rows = []
    for i, eq in enumerate(names):
        rec: dict[str, float | str] = {"equation": eq, "c": float(fit.c[i])}
        rec["se_c"] = float(fit.se[0, i])
        for j, lag in enumerate(names):
            rec[f"lag_{lag}"] = float(fit.Phi[i, j])
            rec[f"se_{lag}"] = float(fit.se[j + 1, i])
        rows.append(rec)
    return pl.DataFrame(rows)


def curve_snapshot(
    rates: np.ndarray,
    maturities: tuple[int, ...] = (1, 5, 10, 15, 20, 30),
) -> dict[str, float]:
    out: dict[str, float] = {}
    for n in maturities:
        if n <= len(rates):
            out[f"mu_{n}"] = float(rates[n - 1])
    out["slope_30_1"] = float(rates[min(29, len(rates) - 1)] - rates[0])
    return out


def _flat_perpetuity(rate: float) -> float:
    if not np.isfinite(rate) or rate <= 1e-4:
        return float("nan")
    return float(np.exp(-rate) / (1.0 - np.exp(-rate)))


def perpetuity_comparison(
    model: ValuationModel,
    X: np.ndarray,
    *,
    capm_rate: float,
    n: int = 100,
) -> dict[str, float]:
    """Unit perpetuity: term structure vs flat unconditional vs flat CAPM."""
    try:
        ts = perpetuity_value(model, X, n=n)
        v_ts = float(ts.pv)
        tail = float(ts.tail_rate)
    except (PerpetuityDivergesError, NonStationaryVARError) as exc:
        return {
            "v_ts": float("nan"),
            "v_uncond": float("nan"),
            "v_capm": float("nan"),
            "gap_uncond_pct": float("nan"),
            "gap_capm_pct": float("nan"),
            "mu_uncond": float("nan"),
            "mu_capm": float(capm_rate),
            "tail_rate": float("nan"),
            "error": str(exc),
        }

    xbar = model.unconditional_mean()
    mu_uncond = float(model.spot_rates(xbar, 1)[0])
    v_uncond = _flat_perpetuity(mu_uncond)
    v_capm = _flat_perpetuity(capm_rate)

    def _gap(flat: float, curve: float) -> float:
        if not np.isfinite(flat) or not np.isfinite(curve) or curve == 0.0:
            return float("nan")
        return 100.0 * (flat - curve) / curve

    return {
        "v_ts": v_ts,
        "v_uncond": v_uncond,
        "v_capm": v_capm,
        "gap_uncond_pct": _gap(v_uncond, v_ts),
        "gap_capm_pct": _gap(v_capm, v_ts),
        "mu_uncond": mu_uncond,
        "mu_capm": float(capm_rate),
        "tail_rate": tail,
    }


def variance_share_table(model: ValuationModel, n: int = 30) -> pl.DataFrame:
    decomp, total = model.variance_decomposition(n)
    names = list(model.spec.names)
    share = decomp / np.maximum(total[:, None], 1e-16)
    rec: dict[str, list] = {"maturity": list(range(1, n + 1))}
    for i, name in enumerate(names):
        rec[name] = share[:, i].tolist()
    rec["total_var"] = total.tolist()
    return pl.DataFrame(rec)


def identity_error(model: ValuationModel, X: np.ndarray) -> float:
    """μ_t(1) − (α + ξ'X + X'ΛX). Should be ~0."""
    mu1 = float(model.spot_rates(X, 1)[0])
    mu = float(model.alpha + model.xi @ X + X @ model.Lambda @ X)
    return mu1 - mu


def fit_portfolio(
    name: str,
    state: pl.DataFrame,
    spec: StateSpec,
    xi: np.ndarray,
    Lambda: np.ndarray,
    alpha: float,
    beta_capm: float,
    *,
    when: date,
    capm_rate: float,
    n_curve: int = 30,
) -> PortfolioResult:
    fit = estimate_var(state, spec)
    model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=alpha)
    X, asof = as_of_row(state, when, spec)
    rates = model.spot_rates(X, n_curve)
    moments = sample_moments(state, spec)
    moments["alpha"] = float(alpha)
    moments["beta_capm"] = float(beta_capm)
    moments["spectral_radius"] = float(fit.spectral_radius)
    moments["identity_err"] = identity_error(model, X)
    perp = perpetuity_comparison(model, X, capm_rate=capm_rate)
    shares = variance_share_table(model, n=n_curve)
    return PortfolioResult(
        name=name,
        state=state,
        fit=fit,
        model=model,
        alpha=float(alpha),
        beta_capm=float(beta_capm),
        X=X,
        asof=asof,
        rates=rates,
        moments=moments,
        perp=perp,
        var_shares=shares,
    )


def constant_capm_rate(
    state: pl.DataFrame,
    premium_lam: pl.DataFrame,
    *,
    alpha: float,
    beta_capm: float | None = None,
) -> float:
    """α + mean(r) + mean(β) mean(λ), the constant-CAPM rate at sample means."""
    joined = state.select(["date", "r", "beta"]).join(
        premium_lam.select(["date", "lam"]), on="date", how="inner"
    )
    if joined.is_empty():
        return float("nan")
    r_bar = float(joined["r"].mean())
    b_bar = float(beta_capm) if beta_capm is not None else float(joined["beta"].mean())
    lam_bar = float(joined["lam"].mean())
    return float(alpha + r_bar + b_bar * lam_bar)
