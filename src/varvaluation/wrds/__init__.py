"""WRDS extra: CRSP–Compustat firm panel."""

from importlib.util import find_spec

from varvaluation.exceptions import ExtraNotInstalled

if find_spec("wrds") is None:
    raise ExtraNotInstalled(
        "varvaluation.wrds requires the [wrds] extra. "
        "Install with: uv add 'varvaluation[wrds]'"
    )
