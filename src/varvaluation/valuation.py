"""Present value and named-state channel isolation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from varvaluation.exceptions import PerpetuityDivergesError, StateSpecError
from varvaluation.model import AngLiuModel


@dataclass(frozen=True)
class ValuationResult:
    pv: float
    n_used: int
    tail_rate: float


def _finite_prefix(*arrays: np.ndarray) -> int:
    finite = np.ones(len(arrays[0]), dtype=bool)
    for arr in arrays:
        finite &= np.isfinite(arr)
    if finite.all():
        return len(finite)
    n_used = int(np.argmin(finite))
    if n_used < 1:
        raise PerpetuityDivergesError("no finite spot rate at any maturity")
    return n_used


def perpetuity_value(
    model: AngLiuModel,
    X,
    n: int = 100,
    min_tail_rate: float = 1e-4,
) -> ValuationResult:
    rates = model.spot_rates(X, n)
    n_used = _finite_prefix(rates)
    mu = rates[:n_used]
    mu_tail = float(mu[-1])
    if not np.isfinite(mu_tail) or mu_tail <= min_tail_rate:
        raise PerpetuityDivergesError(
            f"terminal discount rate {mu_tail:.5f} at n={n_used} is non-positive; "
            "the perpetuity does not converge"
        )
    maturities = np.arange(1, n_used + 1)
    pv = float(np.sum(np.exp(-maturities * mu)))
    pv += float(np.exp(-(n_used + 1) * mu_tail) / (1 - np.exp(-mu_tail)))
    return ValuationResult(pv=pv, n_used=n_used, tail_rate=mu_tail)


def full_value(
    model: AngLiuModel,
    X,
    C: float = 1.0,
    n: int = 100,
    min_tail_rate: float = 1e-4,
) -> ValuationResult:
    rates = model.spot_rates(X, n)
    cf = model.cashflow_expectation(X, n)
    n_used = _finite_prefix(rates, cf)
    mu = rates[:n_used]
    cf = cf[:n_used]
    mu_tail = float(mu[-1])
    cf_tail = float(cf[-1])
    if not np.isfinite(mu_tail) or mu_tail <= min_tail_rate:
        raise PerpetuityDivergesError(
            f"terminal discount rate {mu_tail:.5f} at n={n_used} is non-positive; "
            "the valuation does not converge"
        )
    maturities = np.arange(1, n_used + 1)
    pv = float(C) * float(np.sum(cf * np.exp(-maturities * mu)))
    pv += float(C) * float(
        cf_tail * np.exp(-(n_used + 1) * mu_tail) / (1 - np.exp(-mu_tail))
    )
    return ValuationResult(pv=pv, n_used=n_used, tail_rate=mu_tail)


def isolate_channels(
    model: AngLiuModel,
    X,
    *,
    shut: tuple[str, ...],
    on: Literal["cashflow", "discount", "both"],
    C: float = 1.0,
    n: int = 100,
    min_tail_rate: float = 1e-4,
) -> ValuationResult:
    """Counterfactual value after zeroing named loadings.

    ``on="both"`` is the unmodified model (control).
    """
    spec = model.spec
    shut_idx = [spec.index(name) for name in shut]
    cf = spec.cashflow_index()

    if on == "both":
        return full_value(model, X, C=C, n=n, min_tail_rate=min_tail_rate)

    Phi = model.Phi.copy()
    Lambda = model.Lambda.copy()

    if on == "cashflow":
        for s in shut_idx:
            Phi[cf, s] = 0.0
    elif on == "discount":
        for s in shut_idx:
            for i in range(spec.K):
                if i != cf:
                    Phi[i, s] = 0.0
                Lambda[i, s] = 0.0
                Lambda[s, i] = 0.0
    else:
        raise StateSpecError(
            f"on must be 'cashflow', 'discount', or 'both'; got {on!r}"
        )

    counter = AngLiuModel(
        spec, Phi, model.c, model.Sigma, model.xi, Lambda, model.alpha
    )
    return full_value(counter, X, C=C, n=n, min_tail_rate=min_tail_rate)
