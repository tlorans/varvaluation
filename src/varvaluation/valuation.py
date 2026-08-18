"""Present value helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from varvaluation.exceptions import PerpetuityDivergesError
from varvaluation.model import ValuationModel


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
    model: ValuationModel,
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
    model: ValuationModel,
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
