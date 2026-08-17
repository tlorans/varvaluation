"""VAR(1) estimation with Newey–West standard errors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import polars as pl

from varvaluation.exceptions import EstimationError
from varvaluation.schemas import validate_state
from varvaluation.spec import StateSpec


def spectral_radius(Phi: np.ndarray) -> float:
    return float(np.max(np.abs(np.linalg.eigvals(np.asarray(Phi, dtype=float)))))


@dataclass(frozen=True)
class VARFit:
    """Estimated companion form X_{t+h} = c + Phi X_t + u."""

    spec: StateSpec
    Phi: np.ndarray
    c: np.ndarray
    Sigma: np.ndarray
    se: np.ndarray
    nobs: int
    spectral_radius: float
    residuals: np.ndarray
    residual_dates: tuple[date, ...]
    X_lag: np.ndarray


def newey_west_se(Z: np.ndarray, Y: np.ndarray, coeffs: np.ndarray, maxlags: int) -> np.ndarray:
    """Equation-by-equation Newey–West standard errors.

    Returns an array shaped like ``coeffs``: (n_regressors, n_equations).
    """
    n, _k = Z.shape
    resid = Y - Z @ coeffs
    ZtZ_inv = np.linalg.pinv(Z.T @ Z / n)

    se = np.zeros_like(coeffs)
    for eq in range(Y.shape[1]):
        u = resid[:, eq]
        S = (Z * u[:, None]).T @ (Z * u[:, None]) / n
        for lag in range(1, maxlags + 1):
            weight = 1 - lag / (maxlags + 1)
            Zu_t = Z[lag:] * u[lag:, None]
            Zu_tl = Z[:-lag] * u[:-lag, None]
            Gamma = Zu_t.T @ Zu_tl / n
            S += weight * (Gamma + Gamma.T)
        cov = ZtZ_inv @ S @ ZtZ_inv / n
        se[:, eq] = np.sqrt(np.maximum(np.diag(cov), 0.0))
    return se


def _fit_from_pairs(
    spec: StateSpec,
    X_lag: np.ndarray,
    X_future: np.ndarray,
    future_dates: tuple[date, ...],
) -> VARFit:
    n, K = X_future.shape
    if n < K + 1:
        raise EstimationError(
            f"only {n} usable pairs after lag/group filtering; need at least {K + 1}"
        )

    Z = np.column_stack([np.ones(n), X_lag])
    coeffs, *_ = np.linalg.lstsq(Z, X_future, rcond=None)
    c = coeffs[0, :].astype(float)
    Phi = coeffs[1:, :].T.astype(float)
    resid = X_future - Z @ coeffs
    Sigma = resid.T @ resid / (n - K - 1)
    se = newey_west_se(Z, X_future, coeffs, maxlags=spec.nw_lags)
    return VARFit(
        spec=spec,
        Phi=Phi,
        c=c,
        Sigma=Sigma,
        se=se,
        nobs=n,
        spectral_radius=spectral_radius(Phi),
        residuals=np.asarray(resid, dtype=float),
        residual_dates=future_dates,
        X_lag=np.asarray(X_lag, dtype=float),
    )


def estimate_var(df: pl.DataFrame, spec: StateSpec) -> VARFit:
    """Estimate X_{t+h} = c + Phi X_t + u on a single series."""
    data = validate_state(df, spec).sort(spec.date)
    X = data.select(list(spec.names)).to_numpy().astype(float)
    dates = data[spec.date].to_list()
    h = spec.horizon

    if len(X) <= h:
        raise EstimationError(
            f"only {len(X)} rows; horizon={h} leaves no pairs"
        )

    X_lag = X[:-h]
    X_future = X[h:]
    future_dates = tuple(dates[h:])

    finite = np.all(np.isfinite(X_lag), axis=1) & np.all(np.isfinite(X_future), axis=1)
    return _fit_from_pairs(
        spec,
        X_lag[finite],
        X_future[finite],
        tuple(d for d, ok in zip(future_dates, finite, strict=True) if ok),
    )


def estimate_var_panel(df: pl.DataFrame, spec: StateSpec) -> VARFit:
    """Pooled VAR; lag pairs are formed only within ``spec.group``."""
    if spec.group is None:
        raise EstimationError("estimate_var_panel requires spec.group")

    data = validate_state(df, spec).sort([spec.group, spec.date])
    X = data.select(list(spec.names)).to_numpy().astype(float)
    groups = data[spec.group].to_numpy()
    dates = data[spec.date].to_list()
    h = spec.horizon

    X_lag_list: list[np.ndarray] = []
    X_future_list: list[np.ndarray] = []
    future_dates: list[date] = []
    for i in range(len(X) - h):
        if groups[i] != groups[i + h]:
            continue
        row_lag = X[i]
        row_future = X[i + h]
        if np.all(np.isfinite(row_lag)) and np.all(np.isfinite(row_future)):
            X_lag_list.append(row_lag)
            X_future_list.append(row_future)
            future_dates.append(dates[i + h])

    if not X_lag_list:
        raise EstimationError("no valid within-group lag pairs")

    return _fit_from_pairs(
        spec,
        np.asarray(X_lag_list, dtype=float),
        np.asarray(X_future_list, dtype=float),
        tuple(future_dates),
    )
