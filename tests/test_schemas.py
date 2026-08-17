import datetime as dt

import polars as pl
import pytest

from varvaluation import SchemaError, StateSpec, returns_schema, state_schema


def test_state_schema_rejects_missing_column():
    spec = StateSpec(names=("g", "r"), cashflow="g")
    df = pl.DataFrame({"date": [dt.date(2000, 1, 31)], "g": [0.01]})
    schema = state_schema(spec)
    with pytest.raises((SchemaError, Exception)):
        schema.validate(df)


def test_validate_state_wraps_error():
    from varvaluation.schemas import validate_state

    spec = StateSpec(names=("g", "r"), cashflow="g")
    df = pl.DataFrame({"date": [dt.date(2000, 1, 31)], "g": [0.01]})
    with pytest.raises(SchemaError):
        validate_state(df, spec)


def test_returns_schema_accepts_simple_returns():
    df = pl.DataFrame(
        {
            "date": [dt.date(2000, 1, 31)],
            "ret": [0.01],
        }
    )
    returns_schema().validate(df)
