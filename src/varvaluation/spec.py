"""Named-state specification and expected-return builders."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

from varvaluation.exceptions import StateSpecError


@dataclass(frozen=True)
class StateSpec:
    """Bind state names to positions in a Polars frame.

    Parameters
    ----------
    names :
        Column names of the state variables, in order.
    cashflow :
        Which of ``names`` is cash-flow growth.
    date :
        Date column name (required for lag pairing).
    group :
        Optional firm / portfolio id column for ``estimate_var_panel``.
    horizon :
        Lag in observation steps between ``X_t`` and ``X_{t+h}``.
    nw_lags :
        Newey–West lag length for standard errors.
    """

    names: tuple[str, ...]
    cashflow: str
    date: str = "date"
    group: str | None = None
    horizon: int = 1
    nw_lags: int = 12

    def __post_init__(self) -> None:
        if not self.names:
            raise StateSpecError("names must be a non-empty tuple")
        if any(not n or not isinstance(n, str) for n in self.names):
            raise StateSpecError("every state name must be a non-empty string")
        if len(set(self.names)) != len(self.names):
            raise StateSpecError(f"duplicate state names: {self.names}")
        if self.cashflow not in self.names:
            raise StateSpecError(
                f"cashflow {self.cashflow!r} is not in names {self.names}"
            )
        if self.horizon < 1:
            raise StateSpecError(f"horizon must be >= 1, got {self.horizon}")
        if self.nw_lags < 0:
            raise StateSpecError(f"nw_lags must be >= 0, got {self.nw_lags}")
        if not self.date:
            raise StateSpecError("date column name must be a non-empty string")

    @property
    def K(self) -> int:
        return len(self.names)

    def index(self, name: str) -> int:
        try:
            return self.names.index(name)
        except ValueError:
            raise StateSpecError(
                f"unknown state name {name!r}; known names are {self.names}"
            ) from None

    def cashflow_index(self) -> int:
        return self.index(self.cashflow)

    def e_vec(self, name: str) -> np.ndarray:
        v = np.zeros(self.K)
        v[self.index(name)] = 1.0
        return v


@dataclass(frozen=True)
class ExpectedReturnSpec:
    """Build xi and Lambda for mu_t = alpha + r_t + beta_t * lambda_t.

    lambda_t = b0 + br * rate_t + sum_z b{z} * z_t
    """

    rate: str = "r"
    beta: str = "beta"
    premium: tuple[str, ...] = ()

    def xi_lambda(
        self,
        spec: StateSpec,
        coeffs: Mapping[str, float],
    ) -> tuple[np.ndarray, np.ndarray]:
        for required in (self.rate, self.beta, *self.premium):
            spec.index(required)

        xi = np.zeros(spec.K)
        xi[spec.index(self.rate)] = 1.0
        xi[spec.index(self.beta)] = float(coeffs.get("b0", 0.0))

        Lambda = np.zeros((spec.K, spec.K))
        i_beta = spec.index(self.beta)
        i_rate = spec.index(self.rate)
        br = float(coeffs.get("br", 0.0))
        Lambda[i_beta, i_rate] = Lambda[i_rate, i_beta] = br / 2.0

        for z in self.premium:
            key = f"b{z}"
            i_z = spec.index(z)
            bz = float(coeffs.get(key, 0.0))
            Lambda[i_beta, i_z] = Lambda[i_z, i_beta] = bz / 2.0

        return xi, Lambda
