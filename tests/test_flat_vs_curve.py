import importlib.util
from pathlib import Path

import numpy as np


def _load():
    path = Path(__file__).resolve().parents[1] / "examples" / "flat_vs_curve.py"
    spec = importlib.util.spec_from_file_location("flat_vs_curve", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_flat_vs_curve_three_numbers():
    mu1, mu10, gap = _load().flat_vs_curve(seed=7)
    assert np.isfinite([mu1, mu10, gap]).all()
    assert mu1 != mu10
    assert abs(gap) > 0.01
    assert abs(100 * mu1 - 2.37) < 0.02
    assert abs(100 * mu10 - 4.09) < 0.02
    assert abs(100 * gap - 8.0) < 0.2
