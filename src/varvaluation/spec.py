"""Named-state specification and expected-return builders."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

from varvaluation.exceptions import StateSpecError


@dataclass(frozen=True)
class StateSpec:
    """Bind state names to positions. The only public name-to-index map."""

    names: tuple[str, ...]
    cashflow: str
    date: str = "date"
    group: str | None = None
    horizon: int = 12
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
class ResidualIncome:
    """Clean-surplus cash flow: C_{t+1} = B_t (exp(ROE_{t+1}) - exp(g_{t+1})).

    ``roe`` is log book return, ``ln(1 + NI / B_lag)``. ``book_growth`` is
    log book growth, ``ln(B_t / B_{t-1})``. These are the first two
    coordinates of Giacotto, Lin, and Zhao (2020).
    """

    roe: str = "roe"
    book_growth: str = "g"

    def bind(self, spec: StateSpec) -> tuple[int, int]:
        return spec.index(self.roe), spec.index(self.book_growth)


@dataclass(frozen=True)
class CCAPMSpec:
    """Conditional CAPM: μ_t = R_{f,t} + β_t × MRP_t.

    ``rate`` is unused in the paper path: the Treasury curve sits
    outside the VAR and is supplied later as ``y(τ)``. The quadratic
    form Θ is zero except the symmetric β–MRP cell of 1/2, so
    ``X' Θ X = β × MRP``.
    """

    beta: str = "beta"
    premium: str = "mrp"
    rate: str | None = None

    def theta(self, spec: StateSpec) -> np.ndarray:
        if self.rate is not None:
            spec.index(self.rate)
        theta = np.zeros((spec.K, spec.K))
        i_beta = spec.index(self.beta)
        i_prem = spec.index(self.premium)
        theta[i_beta, i_prem] = theta[i_prem, i_beta] = 0.5
        return theta


def paper_state_spec(*, horizon: int = 4, nw_lags: int = 4) -> StateSpec:
    """Giacotto–Lin–Zhao industry state: (ROE, g, β, MRP).

    Quarterly observations of annualized variables; ``horizon=4`` makes
    each VAR step one year, so a 30-step curve is a 30-year curve.
    """
    return StateSpec(
        names=("roe", "g", "beta", "mrp"),
        cashflow="g",
        horizon=horizon,
        nw_lags=nw_lags,
    )


@dataclass(frozen=True)
class ExpectedReturnSpec:
    """Build xi and Lambda for mu_t = alpha + r_t + beta_t * lambda_t.

    lambda_t = b0 + br * rate_t + sum_z b{z} * z_t
    """

    rate: str = "r"
    beta: str = "beta"
    premium: tuple[str, ...] = ("cay",)

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
