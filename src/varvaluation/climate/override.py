"""Replace one named state's own AR(1) block in a fitted VAR."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from varvaluation.climate.scenarios import AR1Dynamics
from varvaluation.estimate import VARFit, spectral_radius
from varvaluation.exceptions import StateSpecError


def _moments(dynamics: AR1Dynamics | Mapping) -> tuple[float, float, float]:
    if isinstance(dynamics, AR1Dynamics):
        return dynamics.intercept, dynamics.phi, dynamics.sigma
    if "phi_Y" in dynamics:
        return float(dynamics["c_Y"]), float(dynamics["phi_Y"]), float(dynamics["sigma_Y"])
    return float(dynamics["intercept"]), float(dynamics["phi"]), float(dynamics["sigma"])


def override_var(
    fit: VARFit,
    dynamics: AR1Dynamics | Mapping,
    state: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Replace the named state's own equation with AR(1) moments.

    Row ``state`` of Phi becomes a unit-root-safe own-lag ``phi``; its
    intercept becomes ``c``; its innovation variance becomes ``sigma**2``
    and its covariances with the rest of the system are zeroed. Every
    other equation is left unchanged.
    """
    idx = fit.spec.index(state)
    c_y, phi_y, sigma_y = _moments(dynamics)
    if not np.isfinite(phi_y) or abs(phi_y) >= 1.0:
        raise StateSpecError(f"scenario own-lag phi={phi_y} is not a stationary AR(1)")

    Phi = np.array(fit.Phi, dtype=float, copy=True)
    c = np.array(fit.c, dtype=float, copy=True)
    Sigma = np.array(fit.Sigma, dtype=float, copy=True)

    Phi[idx, :] = 0.0
    Phi[idx, idx] = phi_y
    c[idx] = c_y
    Sigma[idx, :] = 0.0
    Sigma[:, idx] = 0.0
    Sigma[idx, idx] = sigma_y**2
    return Phi, c, Sigma


def override_fit(fit: VARFit, dynamics: AR1Dynamics | Mapping, state: str) -> VARFit:
    """Like ``override_var``, but return a new ``VARFit``."""
    Phi, c, Sigma = override_var(fit, dynamics, state)
    return VARFit(
        spec=fit.spec,
        Phi=Phi,
        c=c,
        Sigma=Sigma,
        se=fit.se,
        nobs=fit.nobs,
        spectral_radius=spectral_radius(Phi),
        residuals=fit.residuals,
        residual_dates=fit.residual_dates,
        X_lag=fit.X_lag,
    )
