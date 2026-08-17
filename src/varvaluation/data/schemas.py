"""Pandera schemas for public-data frames."""

from __future__ import annotations

import pandera.polars as pa
import polars as pl

from varvaluation.exceptions import SchemaError


def _validate(schema: pa.DataFrameSchema, df: pl.DataFrame, label: str) -> pl.DataFrame:
    try:
        return schema.validate(df)
    except Exception as exc:
        raise SchemaError(f"{label} failed validation: {exc}") from exc


ff3_schema = pa.DataFrameSchema(
    {
        "date": pa.Column(pl.Date, nullable=False),
        "mkt_rf": pa.Column(float, nullable=False),
        "smb": pa.Column(float, nullable=False),
        "hml": pa.Column(float, nullable=False),
        "rf": pa.Column(float, nullable=False),
        "mkt": pa.Column(float, nullable=False),
    },
    coerce=True,
    strict=False,
)

treasury_schema = pa.DataFrameSchema(
    {
        "date": pa.Column(pl.Date, nullable=False),
        "r": pa.Column(float, nullable=False),
    },
    coerce=True,
    strict=False,
)

inflation_schema = pa.DataFrameSchema(
    {
        "date": pa.Column(pl.Date, nullable=False),
        "pi": pa.Column(float, nullable=False),
    },
    coerce=True,
    strict=False,
)

cay_schema = pa.DataFrameSchema(
    {
        "date": pa.Column(pl.Date, nullable=False),
        "cay": pa.Column(float, nullable=True),
    },
    coerce=True,
    strict=False,
)
