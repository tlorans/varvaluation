"""Rolling market beta from log excess returns."""

from __future__ import annotations

import numpy as np

BETA_WINDOW = 60


def compute_rolling_betas(
    total_ret: np.ndarray,
    rf: np.ndarray,
    mkt_ret: np.ndarray,
    window: int = BETA_WINDOW,
) -> np.ndarray:
    """Rolling market beta. The window ends at t-1 (no contemporaneous data)."""
    log_ex_p = np.log(1 + total_ret) - np.log(1 + rf)
    log_ex_m = np.log(1 + mkt_ret) - np.log(1 + rf)
    n = len(total_ret)
    betas = np.full(n, np.nan)
    for t in range(window, n):
        y = log_ex_p[t - window : t]
        x = log_ex_m[t - window : t]
        ok = np.isfinite(y) & np.isfinite(x)
        if ok.sum() < window // 2:
            continue
        x_mat = np.column_stack([np.ones(int(ok.sum())), x[ok]])
        coeffs, *_ = np.linalg.lstsq(x_mat, y[ok], rcond=None)
        betas[t] = coeffs[1]
    return betas
