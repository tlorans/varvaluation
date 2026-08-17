"""Chen-aware cash-flow and discount-rate news."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import polars as pl

from varvaluation.estimate import VARFit, estimate_var
from varvaluation.exceptions import NonStationaryVARError, StateSpecError
from varvaluation.schemas import validate_returns
from varvaluation.spec import StateSpec


DEFAULT_RHO = 0.96


@dataclass(frozen=True)
class NewsShares:
    var_cf: float
    var_dr: float
    cov: float
    var_unexpected: float
    residual_share: float


@dataclass(frozen=True)
class NewsResult:
    frame: pl.DataFrame
    shares: NewsShares
    rho: float
    return_state: str | None


def _news_mapping(
    fit: VARFit,
    *,
    return_state: str | None,
    xi: np.ndarray | None,
    Lambda: np.ndarray | None,
    rho: float,
) -> np.ndarray:
    """Return lambda such that N_DR = lambda' rho Phi (I - rho Phi)^{-1} u."""
    has_named = return_state is not None
    has_grad = xi is not None or Lambda is not None
    if has_named and has_grad:
        raise StateSpecError("pass either return_state or (xi, Lambda), not both")
    if not has_named and not has_grad:
        raise StateSpecError("pass return_state or (xi, Lambda)")

    Phi = fit.Phi
    K = fit.spec.K
    eye = np.eye(K)
    try:
        resolvent = np.linalg.inv(eye - rho * Phi)
    except np.linalg.LinAlgError as exc:
        raise NonStationaryVARError(
            "I - rho*Phi is singular; cannot form news mappings"
        ) from exc

    if return_state is not None:
        lam = fit.spec.e_vec(return_state)
    else:
        if xi is None or Lambda is None:
            raise StateSpecError("gradient path requires both xi and Lambda")
        xi_arr = np.asarray(xi, dtype=float)
        Lam = np.asarray(Lambda, dtype=float)
        X_bar = np.linalg.solve(eye - Phi, fit.c)
        lam = xi_arr + 2.0 * Lam @ X_bar

    return rho * Phi.T @ resolvent.T @ lam, resolvent.T @ fit.spec.e_vec(fit.spec.cashflow)


def news_decomposition(
    fit: VARFit,
    returns: pl.DataFrame,
    *,
    return_col: str = "ret",
    return_state: str | None = None,
    xi: np.ndarray | None = None,
    Lambda: np.ndarray | None = None,
    alpha: float = 0.0,
    rho: float | None = None,
    valuation_ratio: str | None = None,
) -> NewsResult:
    """Direct cash-flow news and discount-rate news from a fitted VAR.

    Cash-flow news is the cash-flow-equation revision, never the residual.
    """
    del alpha  # reserved for a future higher-order expansion of mu
    date_col = fit.spec.date
    ret = validate_returns(returns, date=date_col, return_col=return_col)

    if rho is None:
        if valuation_ratio is not None and valuation_ratio in ret.columns:
            level = ret[valuation_ratio].drop_nulls().to_numpy()
            mean_level = float(np.mean(level))
            rho = mean_level / (1.0 + mean_level) if mean_level > 0 else DEFAULT_RHO
        else:
            rho = DEFAULT_RHO
    if not 0.0 < rho < 1.0:
        raise StateSpecError(f"rho must be in (0, 1); got {rho}")

    lam_dr, lam_cf = _news_mapping(
        fit, return_state=return_state, xi=xi, Lambda=Lambda, rho=rho
    )

    u = fit.residuals
    cf = u @ lam_cf
    dr = u @ lam_dr

    ret_dates = ret.select([date_col, return_col])
    fit_dates = pl.DataFrame(
        {date_col: list(fit.residual_dates), "_i": np.arange(len(fit.residual_dates))}
    )
    aligned = fit_dates.join(ret_dates, on=date_col, how="inner").sort("_i")
    if aligned.is_empty():
        raise StateSpecError(
            "no overlapping dates between VAR residuals and the returns frame"
        )

    idx = aligned["_i"].to_numpy()
    cf = cf[idx]
    dr = dr[idx]
    r = aligned[return_col].to_numpy().astype(float)

    if return_state is not None and return_col == return_state:
        unexpected = u[idx, fit.spec.index(return_state)]
    else:
        unexpected = r - float(np.mean(r))

    residual = unexpected - (cf - dr)

    frame = pl.DataFrame(
        {
            "date": aligned[date_col],
            "cf": cf,
            "dr": dr,
            "unexpected": unexpected,
            "residual": residual,
        }
    )

    var_cf = float(np.var(cf, ddof=0))
    var_dr = float(np.var(dr, ddof=0))
    cov = float(np.cov(cf, dr, ddof=0)[0, 1]) if len(cf) > 1 else 0.0
    var_un = float(np.var(unexpected, ddof=0))
    var_res = float(np.var(residual, ddof=0))
    shares = NewsShares(
        var_cf=var_cf,
        var_dr=var_dr,
        cov=cov,
        var_unexpected=var_un,
        residual_share=(var_res / var_un) if var_un > 0 else 0.0,
    )
    return NewsResult(frame=frame, shares=shares, rho=rho, return_state=return_state)


def _month_ends(n: int, start: date = date(1960, 1, 1)) -> list[date]:
    dates: list[date] = []
    y, m = start.year, start.month
    for _ in range(n):
        if m == 12:
            nxt = date(y + 1, 1, 1)
        else:
            nxt = date(y, m + 1, 1)
        dates.append(nxt.fromordinal(nxt.toordinal() - 1))
        y, m = nxt.year, nxt.month
    return dates


def simulate_return_var(
    nobs: int = 600,
    *,
    seed: int = 0,
    cashflow_zero: bool = False,
) -> tuple[pl.DataFrame, StateSpec]:
    """Simulate a two-state (ret, g) VAR used by tests and treasury_test."""
    rng = np.random.default_rng(seed)
    spec = StateSpec(names=("ret", "g"), cashflow="g", horizon=1, nw_lags=2)
    Phi = np.array([[0.3, 0.05], [0.0, 0.4]])
    c = np.array([0.006, 0.002])
    if cashflow_zero:
        Phi[1, :] = 0.0
        c[1] = 0.0
    X = np.zeros((nobs, 2))
    for t in range(1, nobs):
        shock_g = 0.0 if cashflow_zero else rng.normal(scale=0.01)
        shock = np.array([rng.normal(scale=0.02), shock_g])
        X[t] = c + Phi @ X[t - 1] + shock
    df = pl.DataFrame(
        {
            "date": _month_ends(nobs),
            "ret": X[:, 0],
            "g": X[:, 1],
        }
    )
    return df, spec


def treasury_test(nobs: int = 600, *, seed: int = 0) -> NewsResult:
    """Chen Treasury check: known cash flows ⇒ direct CF news ≈ 0."""
    df, spec = simulate_return_var(nobs, seed=seed, cashflow_zero=True)
    fit = estimate_var(df, spec)
    returns = df.select(["date", "ret"])
    return news_decomposition(fit, returns, return_col="ret", return_state="ret")
