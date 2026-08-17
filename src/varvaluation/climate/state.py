"""Persistent temperature-change state Y_t."""

from __future__ import annotations

import numpy as np
import polars as pl

Y_PERSISTENCE = 0.962
Y_BURN_IN = 240


def build_climate_state(
    temp: pl.DataFrame,
    *,
    persistence: float = Y_PERSISTENCE,
    burn_in: int = Y_BURN_IN,
    temp_col: str = "temp",
    date_col: str = "date",
) -> pl.DataFrame:
    """Construct the Melin–Zhang persistent temperature-change state.

        Y_{t+1} = persistence * Y_t + (T_{t+1} - T_t)

    from a monthly temperature frame. Initialised at Y_0 = 0; the first
    ``burn_in`` months are discarded.
    """
    if temp_col not in temp.columns or date_col not in temp.columns:
        raise ValueError(f"temperature frame must have {date_col!r} and {temp_col!r}")
    ordered = temp.sort(date_col)
    temps = ordered[temp_col].to_numpy().astype(float)
    dT = np.diff(temps, prepend=temps[0])
    Y = np.zeros(len(temps))
    for i in range(1, len(temps)):
        increment = dT[i] if np.isfinite(dT[i]) else 0.0
        Y[i] = persistence * Y[i - 1] + increment
    df = pl.DataFrame({date_col: ordered[date_col].to_list(), "Y": Y})
    if burn_in > 0:
        df = df.slice(burn_in)
    return df
