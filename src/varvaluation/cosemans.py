"""Cosemans et al. (2016) posterior market beta.

Giacotto, Lin, and Zhao (2020) §3.1–3.2: a 125-day rolling-window
beta, a firm-characteristic beta, and a precision-weighted shrink.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from varvaluation.betas import compute_rolling_betas

RW_WINDOW = 125
VOL_WINDOW = 126


def market_volatility(mkt: np.ndarray, dates, window: int = VOL_WINDOW) -> pl.DataFrame:
    """Trailing-window standard deviation of daily market returns."""
    mkt = np.asarray(mkt, dtype=float)
    n = len(mkt)
    vol = np.full(n, np.nan)
    for t in range(window, n):
        w = mkt[t - window : t]
        w = w[np.isfinite(w)]
        if len(w) >= window // 2:
            vol[t] = float(np.std(w, ddof=1))
    return pl.DataFrame({"date": list(dates), "mktvol": vol})


def rolling_window_beta(
    ret: np.ndarray,
    rf: np.ndarray,
    mkt: np.ndarray,
    window: int = RW_WINDOW,
) -> tuple[np.ndarray, np.ndarray]:
    """Daily rolling beta and its OLS variance, window ending at t-1.

    Variance is σ²_ε (Σ_s r_{m,s}²)^{-1} as in the paper's §3.1, using
    the demeaned market in the window (the usual OLS slope variance).
    """
    beta = compute_rolling_betas(ret, rf, mkt, window=window)
    log_ex_p = np.log1p(ret) - np.log1p(rf)
    log_ex_m = np.log1p(mkt) - np.log1p(rf)
    n = len(ret)
    var = np.full(n, np.nan)
    for t in range(window, n):
        y = log_ex_p[t - window : t]
        x = log_ex_m[t - window : t]
        ok = np.isfinite(y) & np.isfinite(x)
        if ok.sum() < window // 2:
            continue
        x_ok = x[ok]
        y_ok = y[ok]
        x_d = x_ok - x_ok.mean()
        sxx = float(np.dot(x_d, x_d))
        if sxx <= 0:
            continue
        resid = y_ok - (y_ok.mean() + beta[t] * x_d)
        # residual variance with 2 degrees of freedom (intercept + slope)
        dof = max(int(ok.sum()) - 2, 1)
        sigma2 = float(np.dot(resid, resid) / dof)
        var[t] = sigma2 / sxx
    return beta, var


@dataclass(frozen=True)
class CharacteristicBeta:
    """Pooled γ and firm-specific (δ0, δ_macro) from the paper's eq. 11."""

    gamma: np.ndarray
    intercept: dict
    macro_delta: dict
    z_names: tuple[str, ...]
    m_names: tuple[str, ...]


def _firm_residualize(y, Z, M):
    """Residualize y and Z on [1, M]. Returns (y_res, Z_res) or None."""
    n = len(y)
    X = np.column_stack([np.ones(n), M])
    try:
        coef_y, *_ = np.linalg.lstsq(X, y, rcond=None)
        coef_z, *_ = np.linalg.lstsq(X, Z, rcond=None)
    except np.linalg.LinAlgError:
        return None
    return y - X @ coef_y, Z - X @ coef_z


def fit_characteristic_beta(
    panel: pl.DataFrame,
    *,
    group: str = "permno",
    beta: str = "beta_rw",
    macro: tuple[str, ...] = ("defspr", "div", "rf_ann", "term", "mktvol"),
    chars: tuple[str, ...] = ("size", "bm", "beta_lag"),
) -> CharacteristicBeta:
    """Eq. 11: firm-specific macro slopes, pooled size / BM / lag-β.

    Frisch–Waugh–Lovell: residualize within firm on [1, macro], pool
    to get γ, then recover each firm's (δ0, δ).
    """
    needed = [group, beta, *macro, *chars]
    missing = [c for c in needed if c not in panel.columns]
    if missing:
        raise ValueError(f"characteristic beta missing columns: {missing}")

    y_res_all: list[np.ndarray] = []
    z_res_all: list[np.ndarray] = []
    groups = []
    for key, sub in panel.group_by(group, maintain_order=True):
        gid = key[0] if isinstance(key, tuple) else key
        work = sub.select([beta, *macro, *chars]).drop_nulls()
        if work.height < len(macro) + len(chars) + 2:
            continue
        y = work[beta].to_numpy().astype(float)
        M = work.select(list(macro)).to_numpy().astype(float)
        Z = work.select(list(chars)).to_numpy().astype(float)
        res = _firm_residualize(y, Z, M)
        if res is None:
            continue
        y_res, z_res = res
        y_res_all.append(y_res)
        z_res_all.append(z_res)
        groups.append(gid)

    if not y_res_all:
        raise ValueError("no firm has enough rows for the characteristic beta")

    y_stack = np.concatenate(y_res_all)
    z_stack = np.vstack(z_res_all)
    gamma, *_ = np.linalg.lstsq(z_stack, y_stack, rcond=None)

    intercept: dict = {}
    macro_delta: dict = {}
    for key, sub in panel.group_by(group, maintain_order=True):
        gid = key[0] if isinstance(key, tuple) else key
        work = sub.select([beta, *macro, *chars]).drop_nulls()
        if work.height < len(macro) + 2:
            continue
        y = work[beta].to_numpy().astype(float)
        M = work.select(list(macro)).to_numpy().astype(float)
        Z = work.select(list(chars)).to_numpy().astype(float)
        y_star = y - Z @ gamma
        X = np.column_stack([np.ones(len(y_star)), M])
        coef, *_ = np.linalg.lstsq(X, y_star, rcond=None)
        intercept[gid] = float(coef[0])
        macro_delta[gid] = coef[1:].astype(float)

    return CharacteristicBeta(
        gamma=np.asarray(gamma, dtype=float),
        intercept=intercept,
        macro_delta=macro_delta,
        z_names=chars,
        m_names=macro,
    )


def fitted_characteristic_beta(
    panel: pl.DataFrame,
    fit: CharacteristicBeta,
    *,
    group: str = "permno",
) -> pl.DataFrame:
    """β_FC on each row from eq. 11."""
    values = np.full(panel.height, np.nan)
    keys = panel[group].to_list()
    M = panel.select(list(fit.m_names)).to_numpy().astype(float)
    Z = panel.select(list(fit.z_names)).to_numpy().astype(float)
    for i, gid in enumerate(keys):
        if gid not in fit.intercept:
            continue
        if not np.all(np.isfinite(M[i])) or not np.all(np.isfinite(Z[i])):
            continue
        values[i] = fit.intercept[gid] + float(fit.macro_delta[gid] @ M[i]) + float(
            fit.gamma @ Z[i]
        )
    return panel.with_columns(pl.Series("beta_fc", values))


def posterior_beta(
    beta_fc: np.ndarray,
    var_fc: np.ndarray,
    beta_rw: np.ndarray,
    var_rw: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Eq. 12: w = V_RW / (V_FC + V_RW), posterior = w FC + (1-w) RW."""
    beta_fc = np.asarray(beta_fc, dtype=float)
    var_fc = np.asarray(var_fc, dtype=float)
    beta_rw = np.asarray(beta_rw, dtype=float)
    var_rw = np.asarray(var_rw, dtype=float)
    post = np.full(beta_rw.shape, np.nan)
    weight = np.full(beta_rw.shape, np.nan)
    ok = (
        np.isfinite(beta_fc)
        & np.isfinite(beta_rw)
        & np.isfinite(var_fc)
        & np.isfinite(var_rw)
        & (var_fc > 0)
        & (var_rw > 0)
    )
    w = var_rw[ok] / (var_fc[ok] + var_rw[ok])
    weight[ok] = w
    post[ok] = w * beta_fc[ok] + (1.0 - w) * beta_rw[ok]
    return post, weight


def characteristic_variance(
    panel: pl.DataFrame,
    fit: CharacteristicBeta,
    *,
    group: str = "permno",
    beta: str = "beta_rw",
) -> np.ndarray:
    """Rough V[β_FC]: firm residual variance times the leverage of the row.

    Not the paper's Appendix B in full; enough to shrink noisy firms
    toward the rolling window. Rows that cannot be scored stay NaN.
    """
    out = np.full(panel.height, np.nan)
    keys = panel[group].to_list()
    # map group -> residual variance from the characteristic fit
    var_e: dict = {}
    for key, sub in panel.group_by(group, maintain_order=True):
        gid = key[0] if isinstance(key, tuple) else key
        if gid not in fit.intercept:
            continue
        work = sub.select([beta, *fit.m_names, *fit.z_names]).drop_nulls()
        if work.height < 4:
            continue
        y = work[beta].to_numpy().astype(float)
        M = work.select(list(fit.m_names)).to_numpy().astype(float)
        Z = work.select(list(fit.z_names)).to_numpy().astype(float)
        yhat = fit.intercept[gid] + M @ fit.macro_delta[gid] + Z @ fit.gamma
        resid = y - yhat
        var_e[gid] = float(np.dot(resid, resid) / max(len(resid) - 2, 1))

    M_all = panel.select(list(fit.m_names)).to_numpy().astype(float)
    Z_all = panel.select(list(fit.z_names)).to_numpy().astype(float)
    for i, gid in enumerate(keys):
        if gid not in var_e:
            continue
        if not np.all(np.isfinite(M_all[i])) or not np.all(np.isfinite(Z_all[i])):
            continue
        # leverage proxy: 1 + ||z||^2 / n_typical — keep it simple and positive
        out[i] = var_e[gid] * (1.0 + float(np.dot(Z_all[i], Z_all[i])))
    return out
