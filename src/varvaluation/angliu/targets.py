"""Published Ang and Liu (2004) objects and shape checks.

Point estimates are taken from the Journal of Finance article (December 2000
valuation date). Series have been revised (Ken French, FRED, cay), so CI
asserts shape and sign, not the third decimal. Soft comparison bands are
printed by the driver.
"""

from __future__ import annotations

from dataclasses import dataclass

# Qualitative claims in the abstract / §IV.
# At December 2000 the fitted curve is upward-sloping and lies below a
# constant CAPM / DDM rate; using that constant rate misvalues a unit
# perpetuity by tens of percent (the paper reports cases above 50%).
PAPER_CLAIMS = {
    "valuation_date": "2000-12",
    "curve_upward": True,
    "curve_below_capm": True,
    "abs_perpetuity_gap_pct_min": 10.0,
}

# Soft targets extracted from the published tables (order of magnitude).
# Filled from the JF text and Table IV / V style objects: growth / value
# curves at Dec 2000 sit in the mid-single-digit to low-teens percent range,
# well below an 11–13% historical CAPM. Exact cells vary by vintage.
PAPER_CURVE_BAND = {
    "mu_1_min": 0.02,
    "mu_1_max": 0.12,
    "mu_30_min": 0.04,
    "mu_30_max": 0.16,
}


@dataclass(frozen=True)
class ShapeReport:
    name: str
    asof: str
    identity_ok: bool
    stationary: bool
    upward: bool
    below_capm: bool
    large_gap: bool
    identity_err: float
    slope: float
    gap_capm_pct: float
    mu_1: float
    mu_30: float
    spectral_radius: float

    @property
    def ok(self) -> bool:
        return (
            self.identity_ok
            and self.stationary
            and self.upward
            and self.below_capm
        )


def check_shape(
    name: str,
    *,
    asof,
    rates,
    mu_capm: float,
    gap_capm_pct: float,
    identity_err: float,
    spectral_radius: float,
    identity_tol: float = 1e-8,
) -> ShapeReport:
    mu1 = float(rates[0])
    mu30 = float(rates[min(29, len(rates) - 1)])
    return ShapeReport(
        name=name,
        asof=str(asof),
        identity_ok=abs(float(identity_err)) < identity_tol,
        stationary=float(spectral_radius) < 1.0,
        upward=mu30 > mu1,
        below_capm=mu1 < float(mu_capm),
        large_gap=abs(float(gap_capm_pct)) >= PAPER_CLAIMS["abs_perpetuity_gap_pct_min"],
        identity_err=float(identity_err),
        slope=mu30 - mu1,
        gap_capm_pct=float(gap_capm_pct),
        mu_1=mu1,
        mu_30=mu30,
        spectral_radius=float(spectral_radius),
    )
