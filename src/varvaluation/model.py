"""Quadratic-Gaussian valuation: cash-flow and discount-rate forecasts from one VAR."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy.linalg import det, inv

from varvaluation.estimate import VARFit, spectral_radius
from varvaluation.exceptions import NonStationaryVARError, RecursionDivergedError
from varvaluation.spec import StateSpec


class ValuationModel:
    """Valuation model with time-varying expected returns.

    Cash-flow expectations and the discount curve are both functions of the
    same state ``X``. Inputs and curve/value outputs are designed around
    Polars frames (see ``spot_curve``, ``curve_frame``, ``value_frame``).

    Parameters
    ----------
    spec :
        Named state layout. ``spec.cashflow`` is the cash-flow growth variable.
    Phi, c, Sigma :
        VAR(1) companion, intercept, and innovation covariance.
    xi, Lambda, alpha :
        Expected return ``mu = alpha + xi'X + X' Lambda X``.
    """

    def __init__(self, spec: StateSpec, Phi, c, Sigma, xi, Lambda, alpha):
        self.spec = spec
        self.Phi = np.asarray(Phi, dtype=float).copy()
        self.c = np.asarray(c, dtype=float).copy()
        self.Sigma = np.asarray(Sigma, dtype=float).copy()
        self.xi = np.asarray(xi, dtype=float).copy()
        Lambda = np.asarray(Lambda, dtype=float)
        self.Lambda = 0.5 * (Lambda + Lambda.T)
        self.alpha = float(alpha)
        self.K = spec.K
        if self.Phi.shape != (self.K, self.K):
            raise ValueError(f"Phi shape {self.Phi.shape} does not match K={self.K}")
        if self.c.shape != (self.K,):
            raise ValueError(f"c shape {self.c.shape} does not match K={self.K}")
        if self.Sigma.shape != (self.K, self.K):
            raise ValueError(f"Sigma shape {self.Sigma.shape} does not match K={self.K}")
        if self.xi.shape != (self.K,):
            raise ValueError(f"xi shape {self.xi.shape} does not match K={self.K}")
        if self.Lambda.shape != (self.K, self.K):
            raise ValueError(f"Lambda shape {self.Lambda.shape} does not match K={self.K}")
        rho = spectral_radius(self.Phi)
        if rho >= 1.0:
            raise NonStationaryVARError(
                f"spectral radius of Phi is {rho:.6f} >= 1; "
                "the model refuses to construct"
            )
        self.e1 = spec.e_vec(spec.cashflow)

    @classmethod
    def from_var(cls, fit: VARFit, xi, Lambda, alpha) -> ValuationModel:
        return cls(fit.spec, fit.Phi, fit.c, fit.Sigma, xi, Lambda, alpha)

    # back-compat alias used in older call sites / tests
    from_var_ang_liu = from_var

    def is_stationary(self, tol: float = 1.0 - 1e-10) -> bool:
        return spectral_radius(self.Phi) < tol

    def price_recursion(self, n_max: int):
        """Return a(n), b(n), H(n) for n = 1, ..., n_max (index 0 unused)."""
        K = self.K
        Phi, c, Sigma = self.Phi, self.c, self.Sigma
        xi, Lambda, alpha = self.xi, self.Lambda, self.alpha
        e1 = self.e1

        a = np.zeros(n_max + 1)
        b = np.zeros((n_max + 1, K))
        H = np.zeros((n_max + 1, K, K))

        a[1] = -alpha + e1 @ c + 0.5 * e1 @ Sigma @ e1
        b[1] = -xi + Phi.T @ e1
        H[1] = -Lambda

        Sigma_inv = inv(Sigma)

        for n in range(1, n_max):
            D_vec = e1 + b[n] + 2 * H[n] @ c
            M = inv(Sigma_inv - 2 * H[n])

            det_arg = det(np.eye(K) - 2 * Sigma @ H[n])
            if not np.isfinite(det_arg) or det_arg <= 0:
                raise RecursionDivergedError(
                    f"det(I - 2*Sigma*H(n)) = {det_arg!r} at n={n}; "
                    "the quadratic-Gaussian recursion has diverged."
                )
            det_term = np.log(det_arg)

            a[n + 1] = (
                a[n]
                - alpha
                + (e1 + b[n]) @ c
                + c @ H[n] @ c
                - 0.5 * det_term
                + 0.5 * D_vec @ M @ D_vec
            )
            b[n + 1] = (
                -xi
                + Phi.T @ (e1 + b[n])
                + 2 * Phi.T @ H[n] @ c
                + 2 * Phi.T @ H[n] @ M @ D_vec
            )
            H[n + 1] = (
                -Lambda
                + Phi.T @ H[n] @ Phi
                + 2 * Phi.T @ H[n] @ M @ H[n] @ Phi
            )

        return a, b, H

    def cashflow_recursion(self, n_max: int):
        """Affine recursion for E_t[C_{t+n}]/C_t = exp(bar_a(n) + bar_b(n)'X_t)."""
        Phi, c, Sigma = self.Phi, self.c, self.Sigma
        e1 = self.e1

        bar_a = np.zeros(n_max + 1)
        bar_b = np.zeros((n_max + 1, self.K))

        bar_a[1] = e1 @ c + 0.5 * e1 @ Sigma @ e1
        bar_b[1] = Phi.T @ e1

        for n in range(1, n_max):
            eb = e1 + bar_b[n]
            bar_a[n + 1] = bar_a[n] + e1 @ c + bar_b[n] @ c + 0.5 * eb @ Sigma @ eb
            bar_b[n + 1] = Phi.T @ eb

        return bar_a, bar_b

    def spot_discount_coefficients(self, n_max: int):
        a, b, H = self.price_recursion(n_max)
        bar_a, bar_b = self.cashflow_recursion(n_max)

        A = np.zeros(n_max + 1)
        B = np.zeros((n_max + 1, self.K))
        G = np.zeros((n_max + 1, self.K, self.K))

        for n in range(1, n_max + 1):
            A[n] = (bar_a[n] - a[n]) / n
            B[n] = (bar_b[n] - b[n]) / n
            G[n] = -H[n] / n

        return A, B, G

    def spot_rates(self, X, n: int) -> np.ndarray:
        """Spot discount rates mu_t(1), ..., mu_t(n) at state X."""
        X = np.asarray(X, dtype=float)
        A, B, G = self.spot_discount_coefficients(n)
        rates = np.zeros(n)
        for k in range(1, n + 1):
            rates[k - 1] = A[k] + B[k] @ X + X @ G[k] @ X
        return rates

    def cashflow_expectation(self, X, n: int) -> np.ndarray:
        """E_t[C_{t+k}]/C_t for k = 1, ..., n."""
        X = np.asarray(X, dtype=float)
        bar_a, bar_b = self.cashflow_recursion(n)
        ratios = np.zeros(n)
        for k in range(1, n + 1):
            ratios[k - 1] = np.exp(bar_a[k] + bar_b[k] @ X)
        return ratios

    def spot_curve(self, X, n: int = 30) -> pl.DataFrame:
        """Discount curve and cash-flow ratios as a Polars frame.

        Columns: ``maturity``, ``mu``, ``cashflow_ratio``, ``discount_factor``.
        """
        rates = self.spot_rates(X, n)
        cf = self.cashflow_expectation(X, n)
        mat = np.arange(1, n + 1)
        return pl.DataFrame(
            {
                "maturity": mat,
                "mu": rates,
                "cashflow_ratio": cf,
                "discount_factor": np.exp(-mat * rates),
            }
        )

    def curve_frame(
        self,
        states: pl.DataFrame,
        *,
        n: int = 30,
        id_cols: tuple[str, ...] | None = None,
    ) -> pl.DataFrame:
        """Long Polars frame of curves for one or many state rows.

        ``states`` must contain the columns named in ``spec.names``.
        Optional ``id_cols`` (e.g. ``("firm", "date")``) are repeated on
        every maturity row so a firm panel stays tidy.
        """
        names = list(self.spec.names)
        missing = [c for c in names if c not in states.columns]
        if missing:
            raise ValueError(f"states frame missing columns {missing}")

        id_cols = tuple(id_cols or ())
        for c in id_cols:
            if c not in states.columns:
                raise ValueError(f"id column {c!r} not in states frame")

        pieces: list[pl.DataFrame] = []
        for row in states.iter_rows(named=True):
            X = np.array([row[name] for name in names], dtype=float)
            curve = self.spot_curve(X, n=n)
            if id_cols:
                meta = {c: [row[c]] * n for c in id_cols}
                curve = pl.DataFrame(meta).hstack(curve)
            pieces.append(curve)
        return pl.concat(pieces) if pieces else pl.DataFrame()

    def value_frame(
        self,
        states: pl.DataFrame,
        *,
        C: float = 1.0,
        n: int = 100,
        id_cols: tuple[str, ...] | None = None,
        min_tail_rate: float = 1e-4,
    ) -> pl.DataFrame:
        """Present value for each state row as a Polars frame.

        Columns: optional ``id_cols``, then ``pv``, ``n_used``, ``tail_rate``.
        """
        from varvaluation.valuation import full_value

        names = list(self.spec.names)
        missing = [c for c in names if c not in states.columns]
        if missing:
            raise ValueError(f"states frame missing columns {missing}")

        id_cols = tuple(id_cols or ())
        records: list[dict] = []
        for row in states.iter_rows(named=True):
            X = np.array([row[name] for name in names], dtype=float)
            result = full_value(self, X, C=C, n=n, min_tail_rate=min_tail_rate)
            rec = {c: row[c] for c in id_cols}
            rec.update(
                {
                    "pv": result.pv,
                    "n_used": result.n_used,
                    "tail_rate": result.tail_rate,
                }
            )
            records.append(rec)
        return pl.DataFrame(records)

    def unconditional_mean(self) -> np.ndarray:
        return np.linalg.solve(np.eye(self.K) - self.Phi, self.c)

    def unconditional_covariance(self) -> np.ndarray:
        rho = spectral_radius(self.Phi)
        if not rho < 1.0:
            raise NonStationaryVARError(
                f"spectral radius of Phi is {rho:.6f} >= 1; "
                "the unconditional covariance of X_t does not exist."
            )
        K = self.K
        A_mat = np.eye(K * K) - np.kron(self.Phi, self.Phi)
        vec_SigmaX = np.linalg.solve(A_mat, self.Sigma.flatten("F"))
        return vec_SigmaX.reshape((K, K), order="F")

    def _variance_gradient(self, B_n, G_n, X_bar):
        return B_n + 2 * G_n @ X_bar

    def variance_exact(self, n_max: int) -> np.ndarray:
        SigmaX = self.unconditional_covariance()
        X_bar = self.unconditional_mean()
        _, B, G = self.spot_discount_coefficients(n_max)
        var = np.zeros(n_max)
        for n in range(1, n_max + 1):
            v = self._variance_gradient(B[n], G[n], X_bar)
            SG = SigmaX @ G[n]
            var[n - 1] = v @ SigmaX @ v + 2 * np.trace(SG @ SG)
        return var

    def variance_decomposition(self, n_max: int):
        SigmaX = self.unconditional_covariance()
        X_bar = self.unconditional_mean()
        _, B, G = self.spot_discount_coefficients(n_max)
        decomp = np.zeros((n_max, self.K))
        total = np.zeros(n_max)
        for n in range(1, n_max + 1):
            v = self._variance_gradient(B[n], G[n], X_bar)
            Sv = SigmaX @ v
            decomp[n - 1] = v * Sv
            total[n - 1] = v @ Sv
        return decomp, total

    def long_term_rate(self, n_max: int = 200) -> float:
        a, _, _ = self.price_recursion(n_max)
        bar_a, _ = self.cashflow_recursion(n_max)
        return (bar_a[n_max] - a[n_max]) / n_max

    def value(self, X, C: float = 1.0, n: int = 100, min_tail_rate: float = 1e-4):
        """Present value: expected cash flows and the discount curve from ``X``."""
        from varvaluation.valuation import full_value

        return full_value(self, X, C=C, n=n, min_tail_rate=min_tail_rate)

    def perpetuity(self, X, n: int = 100, min_tail_rate: float = 1e-4):
        """Unit-cash-flow present value: freeze the numerator at 1."""
        from varvaluation.valuation import perpetuity_value

        return perpetuity_value(self, X, n=n, min_tail_rate=min_tail_rate)


# Back-compat for older imports
AngLiuModel = ValuationModel
