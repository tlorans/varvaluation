"""Pandera schemas built from a StateSpec, plus fixed output models."""

from __future__ import annotations

import pandera.polars as pa
import polars as pl

from varvaluation.exceptions import SchemaError
from varvaluation.spec import StateSpec


def state_schema(spec: StateSpec) -> pa.DataFrameSchema:
    """Inbound state frame: date, optional group, one float column per name."""
    columns: dict[str, pa.Column] = {
        spec.date: pa.Column(pl.Date, nullable=False),
    }
    if spec.group is not None:
        columns[spec.group] = pa.Column(int, nullable=False)
    for name in spec.names:
        columns[name] = pa.Column(float, nullable=True)
    return pa.DataFrameSchema(columns, coerce=True, strict=False)


def returns_schema(date: str = "date", return_col: str = "ret") -> pa.DataFrameSchema:
    """Inbound simple-return frame."""
    return pa.DataFrameSchema(
        {
            date: pa.Column(pl.Date, nullable=False),
            return_col: pa.Column(float, nullable=False, checks=pa.Check.in_range(-1.0, 5.0, include_min=False, include_max=False)),
        },
        coerce=True,
        strict=False,
    )


def _validate(schema: pa.DataFrameSchema, df: pl.DataFrame, label: str) -> pl.DataFrame:
    try:
        return schema.validate(df)
    except Exception as exc:
        raise SchemaError(f"{label} failed validation: {exc}") from exc


def validate_state(df: pl.DataFrame, spec: StateSpec) -> pl.DataFrame:
    return _validate(state_schema(spec), df, "state frame")


def validate_returns(
    df: pl.DataFrame,
    date: str = "date",
    return_col: str = "ret",
) -> pl.DataFrame:
    return _validate(returns_schema(date, return_col), df, "returns frame")


spot_curve_schema = pa.DataFrameSchema(
    {
        "n": pa.Column(int, nullable=False),
        "mu": pa.Column(float, nullable=False),
    },
    coerce=True,
)

news_schema = pa.DataFrameSchema(
    {
        "date": pa.Column(pl.Date, nullable=False),
        "cf": pa.Column(float, nullable=False),
        "dr": pa.Column(float, nullable=False),
        "unexpected": pa.Column(float, nullable=False),
        "residual": pa.Column(float, nullable=False),
    },
    coerce=True,
)

valuation_schema = pa.DataFrameSchema(
    {
        "pv": pa.Column(float, nullable=False),
        "n_used": pa.Column(int, nullable=False),
        "tail_rate": pa.Column(float, nullable=False),
    },
    coerce=True,
)
