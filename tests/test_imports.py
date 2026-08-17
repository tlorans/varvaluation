import importlib.util

import pytest

from varvaluation.exceptions import ExtraNotInstalled


def test_core_importable():
    import varvaluation

    assert varvaluation.__version__ == "0.1.0"


@pytest.mark.skipif(
    importlib.util.find_spec("pandas_datareader") is not None,
    reason="data extra is installed",
)
def test_data_extra_missing():
    with pytest.raises(ExtraNotInstalled, match=r"\[data\]"):
        import varvaluation.data  # noqa: F401


@pytest.mark.skipif(
    importlib.util.find_spec("pandas_datareader") is None,
    reason="data extra is not installed",
)
def test_data_extra_importable():
    import varvaluation.data as data

    assert hasattr(data, "load_ff3")
    assert hasattr(data, "prepare_portfolio_state")


@pytest.mark.skipif(
    importlib.util.find_spec("wrds") is not None,
    reason="wrds extra is installed",
)
def test_wrds_extra_missing():
    with pytest.raises(ExtraNotInstalled, match=r"\[wrds\]"):
        import varvaluation.wrds  # noqa: F401


@pytest.mark.skipif(
    importlib.util.find_spec("wrds") is None,
    reason="wrds extra is not installed",
)
def test_wrds_extra_importable():
    import varvaluation.wrds as wrds

    assert hasattr(wrds, "prepare_firm_state")
    assert hasattr(wrds, "load_firm_panel")
