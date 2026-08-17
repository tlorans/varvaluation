"""Scenario AR(1) dynamics for a named climate state."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import numpy as np
import polars as pl

from varvaluation.climate.state import Y_PERSISTENCE

T0 = 1.25
SIGMA_W = 0.005
SIGMA_IOTA = 0.045
MONTHS_PER_YEAR = 12
DEFAULT_HORIZON_YEARS = 76


@dataclass(frozen=True)
class AR1Dynamics:
    """AR(1) moments used by ``override_var``: x_{t+1} = c + phi x_t + eps."""

    intercept: float
    phi: float
    sigma: float
    mean: float
    scenario: str | None = None
    T_final: float | None = None

    @property
    def c_Y(self) -> float:
        return self.intercept

    @property
    def phi_Y(self) -> float:
        return self.phi

    @property
    def sigma_Y(self) -> float:
        return self.sigma

    @property
    def mean_Y(self) -> float:
        return self.mean


def load_scenario_parameters(path: str | Path | None = None) -> pl.DataFrame:
    """NGFS / Melin–Zhang scenario table (nu, alpha, barp, sigma_zeta)."""
    if path is None:
        csv = resources.files("varvaluation.climate").joinpath("scenario_parameters.csv")
        df = pl.read_csv(csv)
    else:
        df = pl.read_csv(path)
    rename = {c: c.strip().lower() for c in df.columns}
    return df.rename(rename)


def simulate_climate_block(
    nu: float,
    bar_p: float,
    sigma_zeta: float,
    alpha: float = 0.9999,
    beta: float = Y_PERSISTENCE,
    sigma_w: float = SIGMA_W,
    sigma_iota: float = SIGMA_IOTA,
    T_init: float = T0,
    horizon_years: int = DEFAULT_HORIZON_YEARS,
    n_paths: int = 2000,
    seed: int = 12345,
    include_policy_noise: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Simulate (T, Y, P) monthly. Arrays are (n_steps, n_paths)."""
    rng = np.random.default_rng(seed)
    n_steps = horizon_years * MONTHS_PER_YEAR + 1
    T = np.zeros((n_steps, n_paths))
    Y = np.zeros((n_steps, n_paths))
    P = np.zeros((n_steps, n_paths))
    T[0] = T_init
    P[0] = bar_p
    for i in range(n_steps - 1):
        iota = rng.standard_normal(n_paths) if include_policy_noise else 0.0
        P[i + 1] = alpha * P[i] + (1 - alpha) * bar_p + sigma_iota * iota
        zeta = rng.standard_normal(n_paths)
        T[i + 1] = nu * T[i] + (1 - nu) * P[i] + sigma_zeta * zeta
        w = rng.standard_normal(n_paths)
        Y[i + 1] = beta * Y[i] + (T[i + 1] - T[i]) + sigma_w * w
    return T, Y, P


def fit_ar1(Y: np.ndarray, burn_in: int = 0) -> tuple[float, float, float]:
    """Pooled OLS: Y_{t+1} = c + phi Y_t + eps."""
    Y = np.asarray(Y)[burn_in:]
    y_lag = Y[:-1].ravel()
    y_now = Y[1:].ravel()
    Z = np.column_stack([np.ones(y_lag.size), y_lag])
    coeffs, *_ = np.linalg.lstsq(Z, y_now, rcond=None)
    resid = y_now - Z @ coeffs
    return float(coeffs[0]), float(coeffs[1]), float(resid.std(ddof=2))


def scenario_dynamics(
    scenario: str,
    *,
    params: pl.DataFrame | None = None,
    annualise: bool = True,
    n_paths: int = 400,
    horizon_years: int = DEFAULT_HORIZON_YEARS,
    seed: int = 12345,
) -> AR1Dynamics:
    """Fit an AR(1) to the climate state under one named scenario."""
    if params is None:
        params = load_scenario_parameters()
    name_col = "scenario" if "scenario" in params.columns else params.columns[0]
    names = params[name_col].to_list()
    if scenario not in names:
        raise KeyError(f"unknown scenario {scenario!r}; have {names}")
    row = params.filter(pl.col(name_col) == scenario).row(0, named=True)
    T, Y, _ = simulate_climate_block(
        nu=float(row["nu"]),
        bar_p=float(row["barp"]),
        sigma_zeta=float(row["sigma_zeta"]),
        alpha=float(row["alpha"]),
        n_paths=n_paths,
        horizon_years=horizon_years,
        seed=seed,
    )
    c_m, phi_m, sigma_m = fit_ar1(Y)
    if annualise:
        h = MONTHS_PER_YEAR
        phi = phi_m**h
        c = c_m * (1 - phi) / (1 - phi_m) if abs(1 - phi_m) > 1e-12 else c_m * h
        var = sigma_m**2 * (1 - phi_m ** (2 * h)) / (1 - phi_m**2)
        sigma = float(np.sqrt(var))
    else:
        c, phi, sigma = c_m, phi_m, sigma_m
    mean = c / (1 - phi) if abs(1 - phi) > 1e-12 else float("nan")
    return AR1Dynamics(
        intercept=float(c),
        phi=float(phi),
        sigma=float(sigma),
        mean=float(mean),
        scenario=scenario,
        T_final=float(T[-1].mean()),
    )


def all_scenario_dynamics(**kwargs) -> pl.DataFrame:
    params = kwargs.pop("params", None)
    if params is None:
        params = load_scenario_parameters()
    name_col = "scenario" if "scenario" in params.columns else params.columns[0]
    rows = []
    for name in params[name_col].to_list():
        dyn = scenario_dynamics(name, params=params, **kwargs)
        rows.append(
            {
                "scenario": dyn.scenario,
                "c_Y": dyn.intercept,
                "phi_Y": dyn.phi,
                "sigma_Y": dyn.sigma,
                "mean_Y": dyn.mean,
                "T_final": dyn.T_final,
            }
        )
    return pl.DataFrame(rows)
