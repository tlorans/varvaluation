# varvaluation Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a public `varvaluation` library whose default install estimates a named-state VAR, produces Ang–Liu spot rates and present values, and returns Chen-aware cash-flow / discount-rate news.

**Architecture:** Layered core (`StateSpec` → `VARFit` → `AngLiuModel` / `news_decomposition`). No integer state indexes. Extras (`data`, `wrds`, `climate`) are stubbed in `pyproject.toml` and implemented in a follow-up plan.

**Tech Stack:** Python >=3.11, uv, hatchling, numpy, scipy, polars, pandera (polars), statsmodels, pytest, ruff.

**Spec:** `docs/superpowers/specs/2026-08-17-varvaluation-design.md`

## Global Constraints

- Import name and PyPI name: `varvaluation`
- Python: `>=3.11` (CI: 3.11 and 3.12)
- DataFrames: Polars in, Polars out; Pandera Polars backend
- Default dependencies: `numpy`, `scipy`, `polars`, `pandera`, `statsmodels`
- No network in core; default CI is offline
- No public integer index for cash flow or climate (`StateSpec.index` only)
- CF news is never the residual (`NewsResult.frame["cf"]` is the cash-flow-equation series)
- License: MIT
- Version: `0.1.0`
- Work in `C:\DBD\varvaluation` (`src/` layout)
- Commands: `uv` (never pip)

## File map

| File | Responsibility |
|---|---|
| `pyproject.toml` | package metadata, extras, ruff, pytest, hatch |
| `src/varvaluation/__init__.py` | public exports |
| `src/varvaluation/exceptions.py` | typed errors |
| `src/varvaluation/spec.py` | `StateSpec`, `ExpectedReturnSpec` |
| `src/varvaluation/schemas.py` | `state_schema`, `returns_schema`, output models |
| `src/varvaluation/estimate.py` | `estimate_var`, `estimate_var_panel`, `VARFit` |
| `src/varvaluation/model.py` | `AngLiuModel` |
| `src/varvaluation/valuation.py` | `isolate_channels` |
| `src/varvaluation/news.py` | `news_decomposition`, `treasury_test` |
| `tests/test_spec.py` | name binding, xi/Lambda |
| `tests/test_schemas.py` | inbound validation |
| `tests/test_estimate.py` | recovered Φ, panel groups |
| `tests/test_model.py` | recursions, degeneracy |
| `tests/test_valuation.py` | PV, isolation, tail |
| `tests/test_news.py` | Chen invariant, Treasury, identity |
| `tests/test_imports.py` | extras raise `ExtraNotInstalled` |
| `.github/workflows/ci.yml` | pytest on 3.11/3.12 |
| `LICENSE`, `README.md`, `.gitignore` | project skin |

Follow-up plan (not this file): `[data]`, `[climate]`, `[wrds]`, docs pages, paper migration.

---

### Task 1: Scaffold

**Files:**
- Create: `pyproject.toml`, `LICENSE`, `.gitignore`, `README.md`, `.github/workflows/ci.yml`
- Create: `src/varvaluation/__init__.py`
- Create: `src/varvaluation/exceptions.py`
- Create: `src/varvaluation/data/__init__.py`
- Create: `src/varvaluation/wrds/__init__.py`
- Create: `src/varvaluation/climate/__init__.py`
- Create: `tests/test_imports.py`

**Interfaces:**
- Consumes: nothing
- Produces: installable package; `ExtraNotInstalled`; extra `__init__` modules that raise on import

- [ ] **Step 1: Write `exceptions.py` and extra stubs**

```python
# src/varvaluation/exceptions.py
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
```

Each of `data/__init__.py`, `wrds/__init__.py`, `climate/__init__.py`:

```python
from varvaluation.exceptions import ExtraNotInstalled

raise ExtraNotInstalled(
    "varvaluation.data requires the [data] extra. "
    "Install with: uv add 'varvaluation[data]'"
)
```

Use the matching extra name in each message (`[data]`, `[wrds]`, `[climate]`).

**However:** if we raise at import time unconditionally, then *installing* the extra still cannot import the package until the real loaders exist. For this task, raise only when a sentinel module-level check fails:

```python
from importlib.util import find_spec
from varvaluation.exceptions import ExtraNotInstalled

_EXTRA = "data"
_MARKER = "pandas_datareader"  # wrds -> "wrds"; climate is always importable once implemented

if find_spec(_MARKER) is None:
    raise ExtraNotInstalled(
        f"varvaluation.{_EXTRA} requires the [{_EXTRA}] extra. "
        f"Install with: uv add 'varvaluation[{_EXTRA}]'"
    )
```

For `climate` in this task (no extra-only dependency yet), raise `ExtraNotInstalled` with message `varvaluation.climate is not implemented in v0.1 core; install from a later release or implement the extra.` — **No.** Spec says climate is an extra in this repo. Stub climate with:

```python
# climate extra has no unique dependency in v0.1 core plan.
# Export a constant so the package imports; real functions come in the extras plan.
__all__: list[str] = []
```

Only `data` and `wrds` raise when their marker package is missing.

- [ ] **Step 2: Write `tests/test_imports.py`**

```python
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
```

- [ ] **Step 3: Write `pyproject.toml`**

```toml
[project]
name = "varvaluation"
version = "0.1.0"
description = "VAR-based valuation and Chen-aware cash-flow / discount-rate news"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
authors = [{ name = "Thomas Lorans" }]
dependencies = [
    "numpy>=1.26",
    "scipy>=1.11",
    "polars>=1.0",
    "pandera>=0.20",
    "statsmodels>=0.14",
]

[project.optional-dependencies]
data = ["pandas-datareader>=0.11", "pyarrow>=15.0", "openpyxl>=3.1"]
wrds = ["wrds>=3.2", "python-dotenv>=1.0"]
climate = []
dev = ["pytest>=8.0", "pytest-cov>=5.0", "ruff>=0.6"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/varvaluation"]

[tool.uv]
package = true

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

`src/varvaluation/__init__.py`:

```python
from varvaluation.exceptions import (
    EstimationError,
    ExtraNotInstalled,
    NonStationaryVARError,
    PerpetuityDivergesError,
    RecursionDivergedError,
    SchemaError,
    StateSpecError,
    VarValuationError,
)

__version__ = "0.1.0"
__all__ = [
    "EstimationError",
    "ExtraNotInstalled",
    "NonStationaryVARError",
    "PerpetuityDivergesError",
    "RecursionDivergedError",
    "SchemaError",
    "StateSpecError",
    "VarValuationError",
]
```

MIT license text in `LICENSE`. Standard Python `.gitignore` (`.venv`, `__pycache__`, `.pytest_cache`, `dist`, `.ruff_cache`, `.env`). README states the 10-line target API and extras table. CI:

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv python pin ${{ matrix.python-version }}
      - run: uv sync --extra dev
      - run: uv run pytest -q
```

- [ ] **Step 4: Create the environment and run the import tests**

```powershell
cd C:\DBD\varvaluation
uv venv
uv sync --extra dev
uv run pytest tests/test_imports.py -v
```

Expected: PASS (data/wrds extras are not installed, so `ExtraNotInstalled` fires).

- [ ] **Step 5: Commit**

```powershell
git init
git add pyproject.toml LICENSE .gitignore README.md .github src tests docs
git commit -m "chore: scaffold varvaluation package and extras stubs"
```

---

### Task 2: StateSpec, ExpectedReturnSpec, schemas

**Files:**
- Create: `src/varvaluation/spec.py`
- Create: `src/varvaluation/schemas.py`
- Create: `tests/test_spec.py`
- Create: `tests/test_schemas.py`
- Modify: `src/varvaluation/__init__.py` (export `StateSpec`, `ExpectedReturnSpec`, `state_schema`, `returns_schema`)

**Interfaces:**
- Consumes: exceptions from Task 1
- Produces:
  - `StateSpec(names: tuple[str, ...], cashflow: str, date: str = "date", group: str | None = None, horizon: int = 12, nw_lags: int = 12)` with `.K`, `.index(name) -> int`, `.cashflow_index() -> int`
  - `ExpectedReturnSpec(rate: str = "r", beta: str = "beta", premium: tuple[str, ...] = ("cay",)).xi_lambda(spec, coeffs) -> tuple[np.ndarray, np.ndarray]`
  - `state_schema(spec) -> type[pa.DataFrameModel]`
  - `returns_schema(date: str = "date", return_col: str = "ret") -> type[pa.DataFrameModel]`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_spec.py
import numpy as np
import pytest
from varvaluation import ExpectedReturnSpec, StateSpec, StateSpecError


def test_index_and_cashflow():
    spec = StateSpec(names=("g", "beta", "r", "cay"), cashflow="g")
    assert spec.K == 4
    assert spec.index("cay") == 3
    assert spec.cashflow_index() == 0


def test_unknown_name_raises():
    spec = StateSpec(names=("g", "r"), cashflow="g")
    with pytest.raises(StateSpecError, match="Y"):
        spec.index("Y")


def test_cashflow_must_be_in_names():
    with pytest.raises(StateSpecError, match="cashflow"):
        StateSpec(names=("g", "r"), cashflow="roe")


def test_duplicate_names_raise():
    with pytest.raises(StateSpecError, match="duplicate"):
        StateSpec(names=("g", "g"), cashflow="g")


def test_xi_lambda_symmetry_and_slots():
    spec = StateSpec(names=("g", "beta", "r", "cay", "Y"), cashflow="g")
    er = ExpectedReturnSpec(rate="r", beta="beta", premium=("cay", "Y"))
    xi, Lam = er.xi_lambda(spec, {"b0": 0.05, "br": -0.2, "bcay": 2.0, "bY": 0.8})
    assert xi[spec.index("r")] == pytest.approx(1.0)
    assert xi[spec.index("beta")] == pytest.approx(0.05)
    assert Lam[spec.index("beta"), spec.index("Y")] == pytest.approx(0.4)
    assert Lam[spec.index("Y"), spec.index("beta")] == pytest.approx(0.4)
    np.testing.assert_allclose(Lam, Lam.T)
```

```python
# tests/test_schemas.py
import polars as pl
import pytest
from varvaluation import SchemaError, StateSpec, state_schema, returns_schema


def test_state_schema_rejects_missing_column():
    spec = StateSpec(names=("g", "r"), cashflow="g")
    df = pl.DataFrame({"date": [pl.date(2000, 1, 31)], "g": [0.01]})
    schema = state_schema(spec)
    with pytest.raises(SchemaError):
        schema.validate(df)


def test_returns_schema_accepts_simple_returns():
    df = pl.DataFrame({
        "date": [pl.date(2000, 1, 31)],
        "ret": [0.01],
    })
    returns_schema().validate(df)
```

- [ ] **Step 2: Run tests — expect FAIL** (`StateSpec` not exportable)

```powershell
uv run pytest tests/test_spec.py tests/test_schemas.py -v
```

- [ ] **Step 3: Implement `spec.py` and `schemas.py`**

`StateSpec.__post_init__`: reject empty names, duplicates, empty strings, `cashflow not in names`, `horizon < 1`, `nw_lags < 0`. Use `object.__setattr__` only if needed; prefer a frozen dataclass that validates in `__post_init__`.

`ExpectedReturnSpec.xi_lambda`:
- require `rate` and `beta` in `spec.names`, each `premium` name in `spec.names`
- `xi = 0`; `xi[rate] = 1`; `xi[beta] = coeffs.get("b0", 0)`
- `Lambda = 0`; `Lambda[beta, rate] = Lambda[rate, beta] = coeffs.get("br", 0) / 2`
- for `z` in `premium`: `key = "b" + z` (`cay` → `bcay`, `Y` → `bY`); `Lambda[beta, z] = Lambda[z, beta] = coeffs.get(key, 0) / 2`
- ignore unknown keys

`state_schema(spec)` builds a `pa.DataFrameModel` dynamically (`pa.create_model` or an inner class with annotations). Date column: `pl.Date`. State columns: `float`, nullable. Group column if `spec.group`: integer or string, not nullable.

Wrap Pandera `SchemaError` / `SchemaErrors` into `varvaluation.SchemaError`.

Provide `validate_state(df, spec) -> pl.DataFrame` and `validate_returns(df, date, return_col) -> pl.DataFrame` that call `.validate` and re-raise.

`returns_schema`: `date` as `pl.Date`, return column float with `gt=-1.0`, `lt=5.0`.

- [ ] **Step 4: Run tests — expect PASS**

```powershell
uv run pytest tests/test_spec.py tests/test_schemas.py -v
```

- [ ] **Step 5: Commit**

```powershell
git add src/varvaluation/spec.py src/varvaluation/schemas.py src/varvaluation/__init__.py tests/test_spec.py tests/test_schemas.py
git commit -m "feat: add StateSpec, ExpectedReturnSpec, and Pandera schemas"
```

---

### Task 3: VAR estimation

**Files:**
- Create: `src/varvaluation/estimate.py`
- Create: `tests/test_estimate.py`
- Modify: `src/varvaluation/__init__.py`

**Interfaces:**
- Consumes: `StateSpec`, `validate_state`, `EstimationError`
- Produces:
  - `VARFit(spec, Phi, c, Sigma, se, nobs, spectral_radius)`
  - `estimate_var(df: pl.DataFrame, spec: StateSpec) -> VARFit`
  - `estimate_var_panel(df: pl.DataFrame, spec: StateSpec) -> VARFit`
  - `spectral_radius(Phi: np.ndarray) -> float`

Convention: `Phi[i, j]` is the loading of lagged `names[j]` in the equation for `names[i]`. `se` is `(K+1, K)` with row 0 the intercept.

- [ ] **Step 1: Write failing tests**

```python
import numpy as np
import polars as pl
from varvaluation import StateSpec, estimate_var, estimate_var_panel, EstimationError
import pytest


def _sim_var(n=800, seed=0):
    rng = np.random.default_rng(seed)
    Phi = np.array([[0.4, 0.1], [0.0, 0.7]])
    c = np.array([0.01, 0.0])
    X = np.zeros((n, 2))
    for t in range(1, n):
        X[t] = c + Phi @ X[t - 1] + rng.normal(scale=0.02, size=2)
    dates = pl.date_range(pl.date(1960, 1, 31), n, "1mo", eager=True)
    # month-end range may need construction via datetime
    return X, Phi, c


def test_estimate_var_recovers_companion():
    X, Phi, c = _sim_var()
    n = len(X)
    df = pl.DataFrame({
        "date": pl.date_range(pl.datetime(1960, 1, 1), pl.datetime(1960, 1, 1) + pl.duration(days=32*(n-1)), "1mo", eager=True).dt.month_end().cast(pl.Date),
        "g": X[:, 0],
        "r": X[:, 1],
    })
    spec = StateSpec(names=("g", "r"), cashflow="g", horizon=1, nw_lags=2)
    fit = estimate_var(df, spec)
    np.testing.assert_allclose(fit.Phi, Phi, atol=0.05)
    np.testing.assert_allclose(fit.c, c, atol=0.02)
    assert fit.nobs == n - 1
    assert fit.spectral_radius < 1.0


def test_panel_does_not_cross_groups():
    spec = StateSpec(names=("g", "r"), cashflow="g", group="permno", horizon=1, nw_lags=1)
    # two firms, 5 rows each; lag pairs must stay inside permno
    rows = []
    for permno, level in ((1, 0.0), (2, 10.0)):
        for i in range(5):
            rows.append({"permno": permno, "date": pl.date(2000, i + 1, 1), "g": level, "r": 0.0})
    df = pl.DataFrame(rows).with_columns(pl.col("date").cast(pl.Date))
    fit = estimate_var_panel(df, spec)
    assert fit.nobs == 8  # 4 pairs per firm


def test_too_few_obs_raises():
    spec = StateSpec(names=("g", "r"), cashflow="g", horizon=12)
    df = pl.DataFrame({
        "date": [pl.date(2000, 1, 31), pl.date(2000, 2, 29)],
        "g": [0.0, 0.0],
        "r": [0.0, 0.0],
    })
    with pytest.raises(EstimationError):
        estimate_var(df, spec)
```

Fix the date-range construction so the test actually runs (use a simple list of month-end dates if `pl.date_range` is awkward).

- [ ] **Step 2: Run tests — expect FAIL**

```powershell
uv run pytest tests/test_estimate.py -v
```

- [ ] **Step 3: Implement `estimate.py`**

Port Newey–West from `climate_var_valuation.estimation.core.newey_west_se` and `estimate_var` / `estimate_var_panel`. Differences:

- Select columns via `spec.names` after `validate_state(df, spec)`.
- Drop rows with any non-finite state value before forming lag pairs.
- Panel: sort by `[spec.group, spec.date]`; a pair `(t, t+h)` is valid only if `group[t] == group[t+h]`.
- Require `nobs >= K + 1`; else `EstimationError`.
- `spectral_radius = max(|eig(Phi)|)`.

Do not refuse estimation when the radius is ≥ 1; store it on `VARFit`.

- [ ] **Step 4: Run tests — expect PASS**

```powershell
uv run pytest tests/test_estimate.py tests/test_spec.py tests/test_schemas.py -v
```

- [ ] **Step 5: Commit**

```powershell
git add src/varvaluation/estimate.py src/varvaluation/__init__.py tests/test_estimate.py
git commit -m "feat: estimate named-state VAR(1) with Newey-West errors"
```

---

### Task 4: AngLiuModel

**Files:**
- Create: `src/varvaluation/model.py`
- Create: `tests/test_model.py`
- Modify: `src/varvaluation/__init__.py`

**Interfaces:**
- Consumes: `StateSpec`, `VARFit`, `NonStationaryVARError`, `RecursionDivergedError`
- Produces:
  - `AngLiuModel(spec, Phi, c, Sigma, xi, Lambda, alpha)`
  - `AngLiuModel.from_var(fit, xi, Lambda, alpha) -> AngLiuModel`
  - `price_recursion(n) -> tuple[a, b, H]`
  - `cashflow_recursion(n) -> tuple[bar_a, bar_b]`
  - `spot_rates(X, n) -> np.ndarray` length `n`
  - `cashflow_expectation(X, n) -> np.ndarray` length `n`
  - `unconditional_mean() -> np.ndarray`
  - `unconditional_covariance() -> np.ndarray`
  - `variance_exact(n)`, `variance_decomposition(n)`, `long_term_rate(n=200)`

Recursion arrays are 1-indexed: `a[1]` is maturity 1; `a[0] = 0`.

Port the loops from `climate_var_valuation.model.core.AngLiuModel` but replace `self.e1` with `e_vec(spec.cashflow_index(), K)`.

- [ ] **Step 1: Write failing tests** (port the paper degeneracy and n=1 identity)

```python
import numpy as np
import pytest
from varvaluation import AngLiuModel, ExpectedReturnSpec, NonStationaryVARError, StateSpec


def _base(K_names=("g", "beta", "dpo", "r", "cay", "pi"), seed=20260813):
    rng = np.random.default_rng(seed)
    K = len(K_names)
    spec = StateSpec(names=K_names, cashflow="g")
    Phi = rng.normal(scale=0.2, size=(K, K))
    Phi *= 0.7 / np.max(np.abs(np.linalg.eigvals(Phi)))
    c = rng.normal(scale=0.01, size=K)
    A = rng.normal(size=(K, K))
    Sigma = 0.01 * (A @ A.T / K + np.eye(K))
    er = ExpectedReturnSpec()
    xi, Lam = er.xi_lambda(spec, {"b0": 0.047, "br": -0.150, "bcay": 2.189})
    return spec, dict(Phi=Phi, c=c, Sigma=Sigma, xi=xi, Lambda=Lam, alpha=0.002)


def test_spot_rate_n1_equals_mu():
    spec, p = _base()
    m = AngLiuModel(spec, **p)
    rng = np.random.default_rng(1)
    X = rng.normal(scale=0.05, size=spec.K)
    mu = p["alpha"] + p["xi"] @ X + X @ p["Lambda"] @ X
    assert m.spot_rates(X, 1)[0] == pytest.approx(mu, rel=1e-10)


def test_disconnected_state_does_not_change_curve():
    spec6, p6 = _base()
    m6 = AngLiuModel(spec6, **p6)
    names7 = spec6.names + ("Y",)
    spec7 = StateSpec(names=names7, cashflow="g")
    Phi = np.zeros((7, 7)); Phi[:6, :6] = p6["Phi"]; Phi[6, 6] = 0.5
    c = np.zeros(7); c[:6] = p6["c"]
    Sigma = np.zeros((7, 7)); Sigma[:6, :6] = p6["Sigma"]; Sigma[6, 6] = 1e-4
    xi = np.zeros(7); xi[:6] = p6["xi"]
    Lam = np.zeros((7, 7)); Lam[:6, :6] = p6["Lambda"]
    m7 = AngLiuModel(spec7, Phi, c, Sigma, xi, Lam, p6["alpha"])
    rng = np.random.default_rng(2)
    X6 = rng.normal(scale=0.05, size=6)
    X7 = np.concatenate([X6, [0.3]])
    np.testing.assert_allclose(m7.spot_rates(X7, 40), m6.spot_rates(X6, 40), rtol=1e-10, atol=1e-12)


def test_lambda_zero_is_affine():
    spec, p = _base()
    p["Lambda"] = np.zeros((spec.K, spec.K))
    m = AngLiuModel(spec, **p)
    _, _, H = m.price_recursion(15)
    np.testing.assert_allclose(H, 0.0, atol=1e-12)


def test_nonstationary_raises():
    spec, p = _base()
    p["Phi"] = p["Phi"] * 1.05 / np.max(np.abs(np.linalg.eigvals(p["Phi"])))
    with pytest.raises(NonStationaryVARError):
        AngLiuModel(spec, **p)


def test_cashflow_expectation_positive():
    spec, p = _base()
    m = AngLiuModel(spec, **p)
    X = np.zeros(spec.K)
    assert np.all(m.cashflow_expectation(X, 10) > 0)


def test_variance_decomp_sums_to_total():
    spec, p = _base()
    m = AngLiuModel(spec, **p)
    decomp, total = m.variance_decomposition(12)
    np.testing.assert_allclose(decomp.sum(axis=1), total, rtol=1e-10)
```

- [ ] **Step 2: Run tests — expect FAIL**

```powershell
uv run pytest tests/test_model.py -v
```

- [ ] **Step 3: Implement `model.py`**

Copy the numeric loops from `C:\DBD\corpo_research_papers\papers\01-discounting\code\src\climate_var_valuation\model\core.py` (`price_recursion`, `cashflow_recursion`, `spot_discount_rates`, `cashflow_expectation`, `unconditional_*`, `variance_*`, `long_term_rate`). Changes required:

- Constructor takes `spec` first; `self.e1 = unit vector at spec.cashflow_index()`.
- `from_var` raises `NonStationaryVARError` if `fit.spectral_radius >= 1`.
- Direct constructor also checks `spectral_radius(Phi) >= 1`.
- Symmetrize `Lambda = 0.5 * (Lambda + Lambda.T)`.
- `spot_rates` / `cashflow_expectation` return length-`n` arrays (drop the unused 0 slot).
- `variance_decomposition` returns `(decomp, total)` with `decomp.shape == (n, K)` and a names-aligned column order (`spec.names`).

- [ ] **Step 4: Run tests — expect PASS**

```powershell
uv run pytest tests/test_model.py -v
```

- [ ] **Step 5: Commit**

```powershell
git add src/varvaluation/model.py src/varvaluation/__init__.py tests/test_model.py
git commit -m "feat: add dimension-agnostic Ang-Liu pricing model"
```

---

### Task 5: Valuation and channel isolation

**Files:**
- Create: `src/varvaluation/valuation.py`
- Create: `tests/test_valuation.py`
- Modify: `src/varvaluation/model.py` (add `value` and `perpetuity` methods)
- Modify: `src/varvaluation/__init__.py`

**Interfaces:**
- Consumes: `AngLiuModel`, `PerpetuityDivergesError`
- Produces:
  - `ValuationResult(pv: float, n_used: int, tail_rate: float)`
  - `AngLiuModel.value(X, C=1.0, n=100, min_tail_rate=1e-4) -> ValuationResult`
  - `AngLiuModel.perpetuity(X, n=100, min_tail_rate=1e-4) -> ValuationResult`
  - `isolate_channels(model, X, *, shut: tuple[str, ...], on: Literal["cashflow","discount","both"], C=1.0, n=100) -> ValuationResult`

Formulas: port `full_valuation` and `perpetuity_value` from `climate_var_valuation.valuation.core`. Isolation rules are in the spec (zero named Φ / Λ entries).

- [ ] **Step 1: Write failing tests**

```python
import numpy as np
import pytest
from varvaluation import (
    AngLiuModel,
    ExpectedReturnSpec,
    PerpetuityDivergesError,
    StateSpec,
    isolate_channels,
)


def _model(alpha=0.12):
    spec = StateSpec(names=("g", "beta", "r", "cay", "Y"), cashflow="g")
    K = spec.K
    rng = np.random.default_rng(3)
    Phi = rng.normal(scale=0.15, size=(K, K))
    Phi *= 0.6 / np.max(np.abs(np.linalg.eigvals(Phi)))
    Phi[spec.index("g"), spec.index("Y")] = 0.2
    c = np.zeros(K); c[0] = 0.02
    Sigma = 0.01 * np.eye(K)
    xi, Lam = ExpectedReturnSpec(premium=("cay", "Y")).xi_lambda(
        spec, {"b0": 0.04, "br": -0.1, "bcay": 1.0, "bY": 0.5}
    )
    return AngLiuModel(spec, Phi, c, Sigma, xi, Lam, alpha), spec


def test_value_positive_finite():
    m, spec = _model()
    out = m.value(np.zeros(spec.K), n=30)
    assert np.isfinite(out.pv) and out.pv > 0
    assert out.n_used > 0


def test_nonpositive_tail_raises():
    m, spec = _model(alpha=-0.5)
    with pytest.raises(PerpetuityDivergesError):
        m.perpetuity(np.zeros(spec.K), n=10)


def test_shut_cashflow_changes_value():
    m, spec = _model()
    X = np.zeros(spec.K); X[spec.index("Y")] = 0.4
    both = isolate_channels(m, X, shut=("Y",), on="both", n=30)
    cf = isolate_channels(m, X, shut=("Y",), on="cashflow", n=30)
    assert both.pv != pytest.approx(cf.pv, rel=1e-8)
```

- [ ] **Step 2: Run tests — expect FAIL**

```powershell
uv run pytest tests/test_valuation.py -v
```

- [ ] **Step 3: Implement methods + `isolate_channels`**

`on="both"` returns `model.value(...)`.
`on="cashflow"` copies `Phi`, zeros `Phi[cf, s]` for `s` in `shut`, rebuilds `AngLiuModel`.
`on="discount"` zeros `Phi[i, s]` for all `i != cf`, and zeros `Lambda[i, s]` and `Lambda[s, i]` for all `i`.
Unknown names in `shut` raise `StateSpecError`.

- [ ] **Step 4: Run tests — expect PASS**

```powershell
uv run pytest tests/test_valuation.py tests/test_model.py -v
```

- [ ] **Step 5: Commit**

```powershell
git add src/varvaluation/valuation.py src/varvaluation/model.py src/varvaluation/__init__.py tests/test_valuation.py
git commit -m "feat: add present value and named-state channel isolation"
```

---

### Task 6: Chen-aware news

**Files:**
- Create: `src/varvaluation/news.py`
- Create: `tests/test_news.py`
- Modify: `src/varvaluation/__init__.py`

**Interfaces:**
- Consumes: `VARFit`, `validate_returns`, `StateSpecError`, `NonStationaryVARError`
- Produces:
  - `NewsResult(frame, shares, rho, return_state)`
  - `NewsShares(var_cf, var_dr, cov, var_unexpected, residual_share)`
  - `news_decomposition(fit, returns, *, return_col="ret", return_state=None, xi=None, Lambda=None, alpha=0.0, rho=None, valuation_ratio=None) -> NewsResult`
  - `treasury_test(nobs=600, *, seed=0) -> NewsResult`

Formulas (spec):

- `N_DR = λ' ρΦ (I − ρΦ)^{-1} u`
- `N_CF = e_cf' (I − ρΦ)^{-1} u`
- `λ = ξ + 2Λ X̄` if `xi`/`Lambda` given, else `e_{return_state}`
- exactly one of (`return_state`) or (`xi` and `Lambda`)
- `residual = unexpected − (cf − dr)`
- default `rho = 0.96`

`treasury_test`: simulate a 2-state VAR `(ret, g)` with `g` identically 0 (known cash flows), estimate with `horizon=1`, decompose with `return_state="ret"`. Assert `var(cf) ≈ 0`.

- [ ] **Step 1: Write failing tests**

```python
import numpy as np
import polars as pl
import pytest
from varvaluation import (
    ExpectedReturnSpec,
    StateSpec,
    StateSpecError,
    estimate_var,
    news_decomposition,
    treasury_test,
)


def test_treasury_cf_near_zero():
    news = treasury_test(nobs=800, seed=1)
    assert news.shares.var_cf == pytest.approx(0.0, abs=1e-6)


def test_identity_residual():
    news = treasury_test(nobs=400, seed=2)
    f = news.frame
    got = f["unexpected"] - (f["cf"] - f["dr"])
    np.testing.assert_allclose(got.to_numpy(), f["residual"].to_numpy(), atol=1e-10)


def test_cf_ignores_return_residual_scramble():
    news = treasury_test(nobs=400, seed=3)
    cf0 = news.frame["cf"].to_numpy().copy()
    # Re-run with scrambled returns: cf must be unchanged because it comes from the g equation
    fit_returns = news.frame.select(["date", "unexpected"]).rename({"unexpected": "ret"})
    # treasury_test must expose enough to rebuild; if not, implement the scramble inside news.py tests
    # by constructing the same synthetic VAR as treasury_test and permuting only `ret`.
    assert cf0.std() >= 0.0  # placeholder replaced in implementation by the scramble test below
```

Replace the last test with a full constructed VAR (copy the simulator used inside `treasury_test` into the test module, or export `_simulate_treasury`). Required assertion: permuting `ret` does not change `cf`.

Also test that passing both `return_state` and `xi` raises `StateSpecError`, and passing neither raises `StateSpecError`.

- [ ] **Step 2: Run tests — expect FAIL**

```powershell
uv run pytest tests/test_news.py -v
```

- [ ] **Step 3: Implement `news.py`**

Implementation notes:

- Align `returns` to the estimation sample by `date`. The VAR residual `u_{t+h}` corresponds to the observation at `t+h`. Build `u` by applying the fitted `c`, `Phi` to the validated state frame that produced `fit` — **problem:** `VARFit` does not store the state frame.

**Decision locked here:** `news_decomposition` requires the caller to pass the same state frame, or `VARFit` stores residuals.

Store residuals on the fit so news does not need the original frame:

```python
@dataclass(frozen=True)
class VARFit:
    ...
    residuals: np.ndarray   # (nobs, K)  u_{t+h}
    residual_dates: tuple    # date of t+h for each row, length nobs
```

Add `residuals` and `residual_dates` in Task 3 if not already present. If Task 3 already landed without them, extend `VARFit` in this task and update `estimate_var` / `estimate_var_panel`.

`unexpected` is aligned to `residual_dates`. If `return_state` is set, `E_t r` is the fitted equation for that state at those dates (need lagged X). Cleaner: also store `X_lag` on the fit, or recompute unexpected from the returns series minus its mean when using the gradient path.

For the gradient path, unexpected = `return_col` minus sample mean (spec).
For the named-return path, unexpected = residual of that VAR equation (the matching column of `residuals`).

- [ ] **Step 4: Run full suite — expect PASS**

```powershell
uv run pytest -q
```

- [ ] **Step 5: Commit**

```powershell
git add src/varvaluation/news.py src/varvaluation/estimate.py src/varvaluation/__init__.py tests/test_news.py
git commit -m "feat: add Chen-aware cash-flow and discount-rate news"
```

---

### Task 7: Public README and version surface

**Files:**
- Modify: `README.md`
- Modify: `src/varvaluation/__init__.py` (export every name listed in the spec’s public surface)

**Interfaces:**
- Produces the 10-line import path as documented.

- [ ] **Step 1: Export check test**

```python
# tests/test_api.py
import varvaluation as v

def test_public_names():
    for name in (
        "StateSpec", "ExpectedReturnSpec", "state_schema", "returns_schema",
        "estimate_var", "estimate_var_panel", "VARFit", "AngLiuModel",
        "isolate_channels", "news_decomposition", "treasury_test",
        "NewsResult", "NewsShares", "ValuationResult",
    ):
        assert hasattr(v, name), name
```

- [ ] **Step 2: Run — expect FAIL on missing exports, then add them, then PASS**

```powershell
uv run pytest tests/test_api.py -q
uv run pytest -q
```

- [ ] **Step 3: README**

Title, one-paragraph pitch, install lines, 10-line example (synthetic, no download), extras table, link to `https://github.com/tlorans/var_valuation`, link to the two papers, MIT.

- [ ] **Step 4: Commit**

```powershell
git add README.md src/varvaluation/__init__.py tests/test_api.py
git commit -m "docs: document the public API and complete exports"
```

---

## Self-review

**Spec coverage**

| Spec section | Task |
|---|---|
| Scaffold, extras stubs, CI, MIT | 1 |
| StateSpec, ExpectedReturnSpec, schemas | 2 |
| estimate_var / panel, VARFit, Newey–West | 3 |
| AngLiuModel recursions, degeneracy, moments | 4 |
| value, perpetuity, isolate_channels | 5 |
| news_decomposition, treasury_test, Chen invariant | 6 |
| Public surface, README | 7 |
| `[data]` / `[wrds]` / `[climate]` loaders | follow-up plan |
| Paper migration | follow-up in the paper repo |

**Placeholder scan:** Task 6 originally had a placeholder scramble assertion; the step now requires a real constructed-VAR scramble test. `VARFit.residuals` is an additive field documented in Task 6 so news does not need the original frame.

**Type consistency:** `StateSpec`, `VARFit`, `AngLiuModel`, `ValuationResult`, `NewsResult`, `NewsShares` names are stable across tasks. `isolate_channels(..., on=)` uses `"cashflow" | "discount" | "both"`. Coefficient keys are `b0`, `br`, `b{name}`.
