"""Residual-income term structure: cash flows and discount rates from one VAR.

Giacotto, Lin, and Zhao (2020) write clean-surplus cash flow as a
difference of two log-normals and the one-period required return as a
conditional CAPM. Both live in the same state. The cost of capital at
horizon τ is the rate that equates the known-rate present value
(their eq. 7) with the CCAPM present value (eq. 8). The Treasury
curve y(τ) is supplied from outside the VAR.
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import det, inv

from varvaluation.estimate import VARFit, spectral_radius
from varvaluation.exceptions import (
    NonStationaryVARError,
    RecursionDivergedError,
    TermStructureError,
)
from varvaluation.spec import CCAPMSpec, ResidualIncome, StateSpec


def _expm1_diff(a: float, c: float) -> float:
    """exp(a) - exp(c), factored through the larger exponent."""
    m = max(a, c)
    return float(np.exp(m) * (np.exp(a - m) - np.exp(c - m)))


def _as_yields(y, n: int) -> np.ndarray:
    arr = np.asarray(y, dtype=float)
    if arr.ndim == 0 or arr.size == 1:
        return np.full(n, float(arr.reshape(-1)[0]))
    if arr.shape != (n,):
        raise ValueError(f"y must be a scalar or a length-{n} array; got shape {arr.shape}")
    return arr


class ResidualIncomeModel:
    """Clean-surplus cash flows and a CCAPM curve from one VAR.

    Parameters
    ----------
    spec, Phi, c, Sigma :
        Named state and the companion ``X_{t+1} = c + Φ X_t + u``.
    cashflow :
        Which coordinates are log ROE and log book growth.
    expected_return :
        Which coordinates are β and the market risk premium.
    """

    def __init__(
        self,
        spec: StateSpec,
        Phi,
        c,
        Sigma,
        cashflow: ResidualIncome,
        expected_return: CCAPMSpec,
    ):
        self.spec = spec
        self.Phi = np.asarray(Phi, dtype=float).copy()
        self.c = np.asarray(c, dtype=float).copy()
        self.Sigma = np.asarray(Sigma, dtype=float).copy()
        self.cashflow = cashflow
        self.expected_return = expected_return
        self.K = spec.K
        if self.Phi.shape != (self.K, self.K):
            raise ValueError(f"Phi shape {self.Phi.shape} does not match K={self.K}")
        if self.c.shape != (self.K,):
            raise ValueError(f"c shape {self.c.shape} does not match K={self.K}")
        if self.Sigma.shape != (self.K, self.K):
            raise ValueError(f"Sigma shape {self.Sigma.shape} does not match K={self.K}")
        rho = spectral_radius(self.Phi)
        if rho >= 1.0:
            raise NonStationaryVARError(
                f"spectral radius of Phi is {rho:.6f} >= 1; "
                "the model refuses to construct"
            )
        i_roe, i_g = cashflow.bind(spec)
        self.e_roe = spec.e_vec(cashflow.roe)
        self.e_g = spec.e_vec(cashflow.book_growth)
        self.i_roe = i_roe
        self.i_g = i_g
        self.i_beta = spec.index(expected_return.beta)
        self.i_mrp = spec.index(expected_return.premium)
        self.Theta = expected_return.theta(spec)

    @classmethod
    def from_var(
        cls,
        fit: VARFit,
        cashflow: ResidualIncome | None = None,
        expected_return: CCAPMSpec | None = None,
    ) -> ResidualIncomeModel:
        return cls(
            fit.spec,
            fit.Phi,
            fit.c,
            fit.Sigma,
            cashflow or ResidualIncome(),
            expected_return or CCAPMSpec(),
        )

    def unconditional_mean(self) -> np.ndarray:
        return np.linalg.solve(np.eye(self.K) - self.Phi, self.c)

    def one_period_premium(self, X) -> float:
        """β_t × MRP_t = X' Θ X."""
        X = np.asarray(X, dtype=float)
        return float(X @ self.Theta @ X)

    def flat_ccapm_rate(self, X, y1: float) -> float:
        """Single-period CCAPM rate y(1) + β × MRP."""
        return float(y1) + self.one_period_premium(X)

    def unpriced_coefficients(self, n_max: int):
        """A, B, C, D of eq. 7 (known-rate residual-income value).

        Index 0 is unused. ``E_t[C_{t+τ}]/B_t = exp(A+B'X) - exp(C+D'X)``.
        """
        Phi, c, Sigma = self.Phi, self.c, self.Sigma
        e_roe, e_g = self.e_roe, self.e_g
        K = self.K

        A = np.zeros(n_max + 1)
        B = np.zeros((n_max + 1, K))
        C = np.zeros(n_max + 1)
        D = np.zeros((n_max + 1, K))

        gamma = e_roe.copy()
        lam = e_g.copy()
        sum_g_quad = 0.0
        sum_g_lin = 0.0
        sum_l_quad = 0.0
        sum_l_lin = 0.0

        for tau in range(1, n_max + 1):
            if tau > 1:
                gamma = Phi.T @ gamma + e_g
                lam = Phi.T @ lam + e_g
            sum_g_quad += 0.5 * float(gamma @ Sigma @ gamma)
            sum_g_lin += float(gamma @ c)
            sum_l_quad += 0.5 * float(lam @ Sigma @ lam)
            sum_l_lin += float(lam @ c)
            A[tau] = sum_g_quad + sum_g_lin
            B[tau] = Phi.T @ gamma
            C[tau] = sum_l_quad + sum_l_lin
            D[tau] = Phi.T @ lam

        return A, B, C, D

    def priced_coefficients(self, n_max: int):
        """A, B, C, D, G of eq. 8 (CCAPM residual-income value).

        Index 0 is unused. Both exponential terms share G.
        """
        Phi, c, Sigma, Theta = self.Phi, self.c, self.Sigma, self.Theta
        e_roe, e_g = self.e_roe, self.e_g
        K = self.K

        A = np.zeros(n_max + 1)
        B = np.zeros((n_max + 1, K))
        C = np.zeros(n_max + 1)
        D = np.zeros((n_max + 1, K))
        G = np.zeros((n_max + 1, K, K))

        A[1] = float(e_roe @ c) + 0.5 * float(e_roe @ Sigma @ e_roe)
        B[1] = Phi.T @ e_roe
        C[1] = float(e_g @ c) + 0.5 * float(e_g @ Sigma @ e_g)
        D[1] = Phi.T @ e_g
        G[1] = -0.5 * (Theta + Theta.T)

        Sigma_inv = inv(Sigma)
        cbar = c

        for tau in range(1, n_max):
            Gprev = G[tau]
            try:
                Vmat = inv(Sigma_inv - 2.0 * Gprev)
            except np.linalg.LinAlgError as exc:
                raise RecursionDivergedError(
                    f"ω^{{-1}} - 2G is singular at n={tau}"
                ) from exc

            det_arg = det(np.eye(K) - 2.0 * Gprev @ Sigma)
            if not np.isfinite(det_arg) or det_arg <= 0:
                raise RecursionDivergedError(
                    f"det(I - 2G ω) = {det_arg!r} at n={tau}; "
                    "the residual-income recursion has diverged."
                )
            logdet = float(np.log(det_arg))

            dA = e_g + B[tau]
            qA = dA + 2.0 * Gprev @ cbar
            A[tau + 1] = (
                A[tau]
                + float(dA @ cbar)
                + float(cbar @ Gprev @ cbar)
                + 0.5 * float(qA @ Vmat @ qA)
                - 0.5 * logdet
            )
            B[tau + 1] = Phi.T @ (qA + 2.0 * Gprev @ (Vmat @ qA))

            dC = e_g + D[tau]
            qC = dC + 2.0 * Gprev @ cbar
            C[tau + 1] = (
                C[tau]
                + float(dC @ cbar)
                + float(cbar @ Gprev @ cbar)
                + 0.5 * float(qC @ Vmat @ qC)
                - 0.5 * logdet
            )
            D[tau + 1] = Phi.T @ (qC + 2.0 * Gprev @ (Vmat @ qC))

            Gphi = Gprev @ Phi
            Gnext = -Theta + Phi.T @ Gprev @ Phi + 2.0 * Gphi.T @ Vmat @ Gphi
            G[tau + 1] = 0.5 * (Gnext + Gnext.T)

        return A, B, C, D, G

    def expected_cashflow(self, X, n: int) -> np.ndarray:
        """E_t[C_{t+k}]/B_t for k = 1, ..., n (eq. 6)."""
        X = np.asarray(X, dtype=float)
        A, B, C, D = self.unpriced_coefficients(n)
        out = np.zeros(n)
        for k in range(1, n + 1):
            out[k - 1] = _expm1_diff(A[k] + float(B[k] @ X), C[k] + float(D[k] @ X))
        return out

    def cost_of_capital(self, X, y, n: int) -> np.ndarray:
        """ρ(1), ..., ρ(n) from eq. 9.

        ``y`` is the risk-free yield curve: a scalar (flat) or a
        length-``n`` array. It is not a VAR state.
        """
        X = np.asarray(X, dtype=float)
        y = _as_yields(y, n)
        A7, B7, C7, D7 = self.unpriced_coefficients(n)
        A8, B8, C8, D8, G8 = self.priced_coefficients(n)
        rho = np.zeros(n)
        for k in range(1, n + 1):
            num = _expm1_diff(A7[k] + float(B7[k] @ X), C7[k] + float(D7[k] @ X))
            quad = float(X @ G8[k] @ X)
            den = _expm1_diff(
                A8[k] + float(B8[k] @ X) + quad,
                C8[k] + float(D8[k] @ X) + quad,
            )
            ratio = num / den if den != 0 else np.nan
            if not np.isfinite(ratio) or ratio <= 0:
                raise TermStructureError(
                    f"eq. 9 argument is not positive at τ={k}: "
                    f"unpriced={num!r}, priced={den!r}"
                )
            rho[k - 1] = y[k - 1] + float(np.log(ratio)) / k
        return rho

    def unconditional_curve(self, y_bar, n: int) -> np.ndarray:
        """Eq. 9 evaluated at the VAR long-run mean ``x̄``."""
        return self.cost_of_capital(self.unconditional_mean(), y_bar, n)

    def annuity_value(self, X, y, n: int = 30) -> float:
        """Present value of $1 at the end of each of the next ``n`` years."""
        rho = self.cost_of_capital(X, y, n)
        maturities = np.arange(1, n + 1)
        return float(np.sum(np.exp(-maturities * rho)))


def simulate_paper_state(
    nobs: int = 180,
    *,
    seed: int = 7,
    beta_mean: float = 0.65,
) -> tuple:
    """Quarterly (ROE, g, β, MRP) around insurance-like means.

    Used by the handbook snippet and by offline tests. It is not the
    paper's sample; it only gives the same four names and a stationary
    companion so the API can be exercised without WRDS.
    """
    import datetime as dt

    import polars as pl

    from varvaluation.spec import paper_state_spec

    rng = np.random.default_rng(seed)
    spec = paper_state_spec(horizon=1)
    # Means close to the paper's insurance industry (β ≈ 0.65).
    mu = np.array([0.10, 0.04, beta_mean, 0.055])
    Phi = np.array(
        [
            [0.55, 0.05, 0.00, 0.02],
            [0.08, 0.50, 0.00, 0.00],
            [0.00, 0.00, 0.80, 0.10],
            [0.00, 0.00, 0.05, 0.70],
        ]
    )
    c = (np.eye(4) - Phi) @ mu
    A = rng.normal(size=(4, 4))
    # Keep ROE above book growth on almost every path so residual income
    # stays positive at the long-run mean.
    Sigma = 0.00015 * (A @ A.T / 4 + np.eye(4))
    Sigma[1, 1] = min(Sigma[1, 1], 0.0002)
    X = np.zeros((nobs, 4))
    X[0] = mu
    for t in range(1, nobs):
        X[t] = c + Phi @ X[t - 1] + rng.multivariate_normal(np.zeros(4), Sigma)
    dates = []
    year, q = 1974, 1
    ends = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
    for _ in range(nobs):
        month, day = ends[q]
        dates.append(dt.date(year, month, day))
        q += 1
        if q == 5:
            q, year = 1, year + 1
    frame = pl.DataFrame(
        {
            "date": dates,
            "roe": X[:, 0],
            "g": X[:, 1],
            "beta": X[:, 2],
            "mrp": X[:, 3],
        }
    )
    return frame, spec


TermStructureModel = ResidualIncomeModel


def flat_annuity_value(rate: float, n: int = 30) -> float:
    """Present value of a $1 ordinary annuity at a constant rate."""
    maturities = np.arange(1, n + 1)
    return float(np.sum(np.exp(-maturities * float(rate))))


def valuation_discrepancy(v_term: float, v_flat: float) -> float:
    """(V_flat - V_term) / V_term, the paper's Table 4 definition."""
    if v_term == 0.0 or not np.isfinite(v_term):
        raise TermStructureError("term-structure annuity value is not usable")
    return float((v_flat - v_term) / v_term)
