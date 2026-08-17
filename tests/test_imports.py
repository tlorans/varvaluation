import pytest

from varvaluation.exceptions import ExtraNotInstalled


def test_core_importable():
    import varvaluation

    assert varvaluation.__version__ == "0.1.0"


def test_data_extra_missing():
    with pytest.raises(ExtraNotInstalled, match=r"\[data\]"):
        import varvaluation.data  # noqa: F401


def test_wrds_extra_missing():
    with pytest.raises(ExtraNotInstalled, match=r"\[wrds\]"):
        import varvaluation.wrds  # noqa: F401
