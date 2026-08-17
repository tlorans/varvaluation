"""Public-data extra: Ken French, FRED, Lettau–Ludvigson cay."""

from importlib.util import find_spec

from varvaluation.exceptions import ExtraNotInstalled

if find_spec("pandas_datareader") is None:
    raise ExtraNotInstalled(
        "varvaluation.data requires the [data] extra. "
        "Install with: uv add 'varvaluation[data]'"
    )
