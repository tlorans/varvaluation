"""Typed errors for varvaluation."""


class VarValuationError(Exception):
    """Base error for varvaluation."""


class StateSpecError(VarValuationError, ValueError):
    """Invalid StateSpec or unknown state name."""


class SchemaError(VarValuationError, ValueError):
    """Inbound DataFrame failed its Pandera schema."""


class NonStationaryVARError(VarValuationError, ValueError):
    """Spectral radius >= 1; unconditional moments do not exist."""


class RecursionDivergedError(VarValuationError, ArithmeticError):
    """Quadratic-Gaussian recursion lost positive definiteness."""


class PerpetuityDivergesError(VarValuationError, ArithmeticError):
    """Terminal discount rate is non-positive."""


class ExtraNotInstalled(VarValuationError, ImportError):
    """Optional extra imported but not installed."""


class EstimationError(VarValuationError, ValueError):
    """Not enough usable observations to estimate the VAR."""
