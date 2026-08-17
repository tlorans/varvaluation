# varvaluation — Design

**Date:** 2026-08-17
**Status:** Approved in conversation (sections 1–7)
**Repo:** `tlorans/varvaluation` (public)
**Local path:** `C:\DBD\varvaluation`
**Import / PyPI name:** `varvaluation`
**License:** MIT

A Python library for VAR-based valuation and cash-flow / discount-rate news decomposition. The math comes from Ang and Liu (2004) and Campbell (1991) / Vuolteenaho (2002). Cash-flow news is never defined as the residual (Chen, Da, Zhao 2013).

This document is the source of truth for the public package. The teaching site `tlorans/var_valuation` stays a static course page. The manuscript package `climate_var_valuation` will depend on this library and drop its vendored math.

---

## Problem

Researchers and students who want a time-varying discount curve, a present value, or a CF/DR news split today either:

- copy a paper script with hardcoded state slots (`ROE_IDX = 0`, `Y_IDX = 6`), or
- implement Campbell (1991) with cash-flow news as the leftover after discount-rate news.

The first is not a library. The second is the bias Chen, Da, Zhao document (Treasury test: known cash flows, residual still nonzero).

`climate_var_valuation` already has working recursions, Newey–West VAR(1), Pandera schemas, and portfolio/firm/climate construction. It is a manuscript pipeline, not a public API: state layout is integers, extras are mandatory, Python is pinned to 3.11 only.

## Goals

1. A `uv`-managed public package whose default install is a state-agnostic engine.
2. Named states (`StateSpec`) — no public integer index for “cash flow” or “climate.”
3. Ang–Liu quadratic-Gaussian valuation (price recursion, cash-flow recursion, spot curve, PV).
4. Chen-aware news: CF news from the cash-flow equation; residual is a diagnostic.
5. Pandera (Polars) schemas built from the spec, validated on the way in.
6. Optional extras that reproduce the paper stack: public data, WRDS firm panel, climate scenarios.
7. The paper folder becomes a consumer, not a second copy of the math.

## Non-goals (v0.1)

- I/B/E/S analyst revisions or implied cost of capital (`[forecasts]`, later).
- A public switch that defines CF news as the Campbell residual.
- Matplotlib figure helpers or a CLI that writes manuscript CSVs.
- Kalman-filter VAR estimation (van Binsbergen–Koijen style).
- Publishing to PyPI on day one (repo is PyPI-ready; first release can follow CI).
- Changing the course site except a later link to this package.

---

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Package shape | Layered library + extras | Default install stays small; paper stack is `uv add "varvaluation[wrds,climate]"` |
| Chen et al. in v1 | VAR news, Chen-aware | CF from the cash-flow equation; Treasury test as diagnostic; no IBES |
| Relation to paper code | This repo is the source of truth | Paper keeps tables/figures and depends on the package |
| Name | `varvaluation` | Distinct from the course repo `var_valuation` |
| Python | `>=3.11` | Drop the paper pin to `<3.12`; CI on 3.11 and 3.12 |
| DataFrames | Polars in, Polars out | Matches the paper code; Pandera Polars backend |
| Expected return | `ExpectedReturnSpec` → `xi`, `Lambda` | CAPM-style \(\mu_t = \alpha + r_t + \beta_t\lambda_t\) is a builder, not the only constructor |
| Isolation vs news | Separate APIs | `isolate_channels` is a valuation counterfactual; `news_decomposition` is a return identity |
| `safe_evaluate` | Not public | Callers catch typed exceptions |
| Network in core | Forbidden | Downloads live in extras; default CI is offline |

---

## Architecture

```
src/varvaluation/
  __init__.py          public surface (core only)
  exceptions.py        typed errors
  spec.py              StateSpec, ExpectedReturnSpec
  schemas.py           Pandera models built from StateSpec
  estimate.py          VAR(1), panel VAR, Newey–West
  model.py             AngLiuModel (dimension-agnostic)
  valuation.py         value, perpetuity, isolate_channels
  news.py              news_decomposition, treasury_test
  data/                extra [data]
  wrds/                extra [wrds]
  climate/             extra [climate]
```

Default dependencies: `numpy`, `scipy`, `polars`, `pandera`, `statsmodels`.

```text
uv add varvaluation                 # engine
uv add "varvaluation[data]"         # Ken French / FRED / cay
uv add "varvaluation[wrds,climate]" # paper stack
```

Importing `varvaluation.wrds` (or `.data`, `.climate`) without the extra raises `ExtraNotInstalled` and names the extra.

**Hard rule:** nothing in the core knows that state 0 is ROE, that state 6 is temperature, or that the sample is Ken French.

### Data flow

```
StateSpec  →  validated frame  →  VARFit  →  AngLiuModel  →  value / spot_rates
                              ↘           ↘
                               news_decomposition
```

Extras only produce frames and `X_t`. They do not change the four core calls.

---

## Core types

### `StateSpec`

Frozen dataclass. The only place names are bound to positions.

```python
@dataclass(frozen=True)
class StateSpec:
    names: tuple[str, ...]
    cashflow: str
    date: str = "date"
    group: str | None = None
    horizon: int = 12
    nw_lags: int = 12

    @property
    def K(self) -> int: ...
    def index(self, name: str) -> int: ...
    def cashflow_index(self) -> int: ...
```

Rules:

- `names` nonempty, unique, nonempty strings.
- `cashflow` must be in `names`.
- `index(name)` raises `StateSpecError` on unknown names (used by isolation and expected-return builders).
- A firm-level spec is the same type with `cashflow="roe"` and `group="permno"`.
- Climate is the same type plus `"Y"` in `names`.

### `ExpectedReturnSpec`

Builds \(\mu_t = \alpha + r_t + \beta_t \lambda_t\) with
\(\lambda_t = b_0 + b_r r_t + \sum_k b_k z_{k,t}\).

```python
@dataclass(frozen=True)
class ExpectedReturnSpec:
    rate: str = "r"
    beta: str = "beta"
    premium: tuple[str, ...] = ("cay",)

    def xi_lambda(
        self,
        spec: StateSpec,
        coeffs: Mapping[str, float],
    ) -> tuple[np.ndarray, np.ndarray]: ...
```

Coefficient keys:

- `b0` — intercept of \(\lambda_t\) (loads on `beta`).
- `br` — loading of `rate` inside \(\lambda_t\) (symmetric \(\Lambda[\beta, r] = b_r/2\)).
- for each name `z` in `premium`: key `b{z}` (e.g. `bcay`, `bY`), same symmetric pair.

`xi[rate] = 1`. Unknown keys in `coeffs` are ignored. Missing `b0` / `br` / `b{z}` default to 0.

If the caller already has \(\xi\) and \(\Lambda\), they skip this builder.

### `VARFit`

```python
@dataclass(frozen=True)
class VARFit:
    spec: StateSpec
    Phi: np.ndarray          # (K, K)  Phi[i, j] = loading of X_j on equation i
    c: np.ndarray            # (K,)
    Sigma: np.ndarray        # (K, K)
    se: np.ndarray           # (K+1, K) Newey–West, row 0 = intercept
    nobs: int
    spectral_radius: float
```

`estimate_var(df, spec) -> VARFit` and `estimate_var_panel(df, spec) -> VARFit`.

Estimation is OLS of \(X_{t+h} = c + \Phi X_t + u\) with `h = spec.horizon`. Standard errors are Newey–West with `spec.nw_lags`. Panel pairs are formed only within `spec.group`.

`estimate_var` does not download data. It validates `df` with `state_schema(spec)` first.

A spectral radius \(\ge 1\) is stored on the fit (the companion can still be inspected) but `AngLiuModel.from_var` refuses to construct.

### Pandera

- `state_schema(spec) -> type[pa.DataFrameModel]` — `date` (or `spec.date`) as `pl.Date`, one float column per name, optional `group` as integer or string. Cash-flow and return-like columns are not range-clipped beyond finite floats; inbound *return* frames used by news use a tighter schema.
- `returns_schema(date, return_col) -> type[pa.DataFrameModel]` — `date` plus one float return column in `(-1, 5)`.
- Output models (fixed, not spec-built):
  - `SpotCurveSchema`: `n` (int), `mu` (float)
  - `NewsSchema`: `date`, `cf`, `dr`, `unexpected`, `residual`
  - `ValuationSchema`: `pv`, `n_used`, `tail_rate`

Every public function that accepts a DataFrame validates on the way in. Valuation methods take numpy state vectors already aligned to `spec.names`.

---

## News (Chen-aware)

Campbell (1991): unexpected return \(= N_{\mathrm{CF}} - N_{\mathrm{DR}}\).

v1 never uses the residual as the definition of cash-flow news.

### Formula

Let \(u_{t+1}\) be the VAR residual at the estimation horizon. Let \(e_{\mathrm{cf}}\) be the unit vector for `spec.cashflow`. Let \(\rho \in (0,1)\) be the linearization parameter. Let \(\lambda'\) be the mapping from a state shock to a one-period expected-return shock (defined below).

\[
N_{\mathrm{DR},t+1} = \lambda' \,\rho\Phi (I - \rho\Phi)^{-1} u_{t+1}
\]

\[
N_{\mathrm{CF},t+1}^{\mathrm{direct}} = e_{\mathrm{cf}}' (I - \rho\Phi)^{-1} u_{t+1}
\]

The headline series is the **direct** cash-flow news.

**How \(\lambda\) is chosen** (exactly one):

1. **Expected-return gradient (default for Ang–Liu).** Caller passes `xi`, `Lambda`, and `alpha` (or an `ExpectedReturnSpec` plus `coeffs`). Then \(\mu(X) = \alpha + \xi'X + X'\Lambda X\) and \(\lambda = \xi + 2\Lambda \bar X\), with \(\bar X\) the VAR unconditional mean. This is the first-order revision in future \(\mu\), which is what the valuation model calls the discount rate. The Ang–Liu state `(g, beta, dpo, r, cay, pi)` has no equity-return equation; this is the intended path.
2. **Named return equation (Campbell–Shiller).** Caller passes `return_state` as a name in `spec.names`. Then \(\lambda = e_{\mathrm{return}}\). Use this when the VAR itself contains the return (the textbook `(ret, g, pd)` system).

Passing both is a `StateSpecError`. Passing neither is a `StateSpecError`.

**Return alignment.** `news_decomposition` takes a validated returns frame (`date` + `return_col`) aligned to the estimation dates. Unexpected return is \(r_{t+1} - \widehat{E}_t r_{t+1}\). If `return_state` is set and `return_col` is that same series, \(\widehat{E}_t r_{t+1}\) is the fitted VAR equation. Otherwise \(\widehat{E}_t r_{t+1}\) is the sample mean of `return_col` (the identity residual then measures whatever the expected-return model missed — intended, and reported as `news.residual`).

Default `rho`: if the returns frame (or an optional `valuation_ratio` column) is a log price-dividend or book-to-market, use \(\rho = \overline{pd}/(1+\overline{pd})\) on the *level* ratio when a level column is supplied; otherwise `rho=0.96` (annual Campbell–Shiller default). Callers pass `rho` explicitly for replication.

### Public API

```python
@dataclass(frozen=True)
class NewsResult:
    frame: pl.DataFrame          # NewsSchema
    shares: NewsShares
    rho: float
    return_state: str | None

@dataclass(frozen=True)
class NewsShares:
    var_cf: float
    var_dr: float
    cov: float
    var_unexpected: float
    residual_share: float        # var(residual) / var(unexpected)

def news_decomposition(
    fit: VARFit,
    returns: pl.DataFrame,
    *,
    return_col: str = "ret",
    return_state: str | None = None,
    xi: np.ndarray | None = None,
    Lambda: np.ndarray | None = None,
    alpha: float = 0.0,
    rho: float | None = None,
    valuation_ratio: str | None = None,
) -> NewsResult: ...

def treasury_test(
    nobs: int = 600,
    *,
    seed: int = 0,
) -> NewsResult: ...
```

`treasury_test` builds a synthetic VAR whose cash-flow equation is identically zero (known coupons), estimates it, and runs `news_decomposition`. Invariant: `news.cf` is approximately 0; `news.residual` absorbs whatever the discount-rate model missed. This is a test helper and a documented example, not a data dependency.

### Forbidden

- No I/B/E/S.
- No implied cost of capital.
- No `method="residual"` default that reintroduces the bias.

`news.residual = unexpected - (cf - dr)` is always present as a diagnostic.

---

## Valuation

`AngLiuModel` is the quadratic-Gaussian engine. Given \(\Phi, c, \Sigma, \xi, \Lambda, \alpha\), it is exact for

\[
\mu_t = \alpha + \xi' X_t + X_t' \Lambda X_t.
\]

Dimension is `spec.K`. The cash-flow basis vector is `spec.cashflow`, not slot 0.

### Construction

```python
model = AngLiuModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=alpha)
model = AngLiuModel(spec, Phi, c, Sigma, xi, Lambda, alpha)
```

Stationarity is checked at construct time. Spectral radius \(\ge 1\) raises `NonStationaryVARError`.

Shapes: `Phi`, `Sigma`, `Lambda` are `(K, K)`; `c`, `xi` are `(K,)`. `Lambda` is symmetrized as \((\Lambda+\Lambda')/2\) on ingest.

### Methods

| method | paper object |
|---|---|
| `price_recursion(n)` | \(a(n), b(n), H(n)\) — Ang–Liu Proposition 1 |
| `cashflow_recursion(n)` | \(\bar a(n), \bar b(n)\) — affine, no discounting |
| `spot_rates(X, n)` | \(\mu_t(n)\) — Proposition 2, length `n` |
| `cashflow_expectation(X, n)` | \(E_t[C_{t+n}]/C_t\), length `n` |
| `value(X, C=1, n=100, min_tail_rate=1e-4)` | full PV + geometric tail |
| `perpetuity(X, n=100, min_tail_rate=1e-4)` | unit cash flow, discount curve only |
| `variance_decomposition(n)` | Corollary 2, shares labeled by `spec.names` |
| `variance_exact(n)` | Corollary 1 |
| `unconditional_mean()` / `unconditional_covariance()` | exist only if stationary |
| `long_term_rate(n=200)` | \((\bar a(n) - a(n))/n\) |

Recursion arrays are 1-indexed in the paper sense: `a[1]` is maturity 1; `a[0]` is unused (zero). This matches the existing paper implementation so ported tests stay readable.

`value` and `perpetuity` return:

```python
@dataclass(frozen=True)
class ValuationResult:
    pv: float
    n_used: int
    tail_rate: float
```

Negative short rates are allowed. A non-positive terminal rate raises `PerpetuityDivergesError`. \(\det(I-2\Sigma H(n))\le 0\) raises `RecursionDivergedError`.

If \(\Lambda = 0\), \(H(n)\equiv 0\) and the solution is exponential-affine (course playground). Same class; no second solver. Tests assert this degeneracy.

### Channel isolation

```python
def isolate_channels(
    model: AngLiuModel,
    X: np.ndarray,
    *,
    shut: tuple[str, ...],
    on: Literal["cashflow", "discount", "both"],
    C: float = 1.0,
    n: int = 100,
) -> ValuationResult: ...
```

`shut` is names. Let \(S\) be those indices.

- `on="cashflow"`: zero `Phi[cashflow, s]` for each `s` in `shut`, then `value`.
- `on="discount"`: zero `Phi[i, s]` for all rows \(i\) except the cash-flow row, and zero `Lambda[i, s]` and `Lambda[s, i]` for all `i`, then `value`.
- `on="both"`: the original model’s `value` (control).

This is a counterfactual, not news. The climate extra is one caller.

---

## Extras

Each extra is an optional install. Importing it without the extra raises `ExtraNotInstalled`.

### `[data]`

Dependencies: `pandas-datareader`, `pyarrow`, `openpyxl`.

| function | source | columns |
|---|---|---|
| `load_ff3()` | Ken French | `date, mkt_rf, smb, hml, rf, mkt` |
| `load_bm_deciles()` / `load_industry49()` | Ken French, VW, with and without dividends | `date` + named portfolios |
| `load_gs1()` / `load_cpi()` | FRED | `date, r` / `date, pi` |
| `load_cay()` | Lettau–Ludvigson | `date, cay` |

`prepare_portfolio_state(total, capgains, macro, spec)` builds `g`, `beta`, `dpo` (Hodrick trailing dividends, rolling CAPM beta) and joins macro. Lives in `[data]`, not core.

Loaders may cache under `~/.cache/varvaluation/` (or `VARVALUATION_CACHE`). Tests use fixtures in `tests/fixtures/`; default CI does not hit the network.

### `[wrds]`

Dependencies: `wrds`, `python-dotenv`.

Requires `WRDS_USERNAME` (and `.pgpass` / `.env`). Nothing is committed.

```python
panel = load_firm_panel(start="1965-07", end=None)
state = prepare_firm_state(panel, macro, spec)
fit = estimate_var_panel(state, spec)
```

`spec.cashflow == "roe"`, `spec.group == "permno"`. Compustat column choices (SEQ/CEQ, NI, DVT) are documented and schema-checked. This extra does not write manuscript tables.

### `[climate]`

Dependencies: none beyond `[data]` if temperature is loaded from GISTEMP; `build_climate_state` accepts any monthly temperature frame.

```python
Y = build_climate_state(temp, persistence=...)
dyn = scenario_dynamics("Net Zero 2050")
Phi_s, c_s, Sigma_s = override_var(fit, dyn, state="Y")
```

`override_var` is generic: replace the named state’s intercept, own-lag, and innovation variance with AR(1) moments. The NGFS / Melin–Zhang parameter table ships as package data inside this extra.

### Not in v0.1 extras

- `[forecasts]` (IBES / ICC)
- Matplotlib helpers
- Manuscript CLI

---

## Errors and invariants

| exception | when |
|---|---|
| `StateSpecError` | unknown name, duplicates, empty spec, `cashflow` not in `names` |
| `SchemaError` | Pandera failure on an inbound frame |
| `NonStationaryVARError` | spectral radius \(\ge 1\) at `AngLiuModel` construct or unconditional moments |
| `RecursionDivergedError` | \(\det(I-2\Sigma H(n))\le 0\) |
| `PerpetuityDivergesError` | terminal \(\mu(N) \le\) `min_tail_rate` |
| `ExtraNotInstalled` | extra imported but not installed |
| `EstimationError` | too few usable pairs after lag/group filtering |

`SchemaError` wraps the Pandera error and names the schema.

### Invariants

1. **Names, not slots.** No public function takes `Y_IDX` or “column 0 is cash flow.”
2. **CF news is never the residual.** `NewsResult.frame["cf"]` is always the cash-flow-equation series.
3. **Validate on the way in.** Loaders and `estimate_var` validate. `AngLiuModel` assumes a consistent `VARFit`.
4. **Stationary or refuse.** Unconditional moments and variance decompositions do not run on a unit-root \(\Phi\).
5. **Short rates may be negative. The tail may not.**
6. **No network in core.**

`safe_evaluate` from the paper code is not public.

---

## Tests, docs, repo

### Tests

Pytest. Default CI: no network, no WRDS.

Ported from the paper (against `StateSpec`):

- Extra disconnected state with zero loading does not change \(\mu(n)\) or \(a(n),b(n),H(n)\).
- \(\Lambda=0\) reproduces the affine closed form.
- Spot rate at \(n=1\) equals \(\alpha + \xi'X + X'\Lambda X\).
- Cash-flow recursion is affine; expectations are positive.
- Variance decomposition sums to total.
- Monte Carlo check of `variance_exact` on small \(n\).
- Guards: non-stationary \(\Phi\), diverging \(H(n)\), bad `StateSpec` names.

New:

- Chen invariant: mutating the return residual does not change `news.cf`.
- Treasury fixture: `news.cf ≈ 0`.
- Identity: `unexpected - (cf - dr) == residual`.
- `state_schema(spec)` rejects a missing named column.
- Extra import raises `ExtraNotInstalled` when the extra is absent.

`[data]` / `[wrds]` / `[climate]` tests live in `tests/data`, `tests/wrds`, `tests/climate` and skip unless the extra is installed. WRDS tests are local-only (`@pytest.mark.wrds`).

### Docs

- README: 10-line path, extras table, link to the course site `https://github.com/tlorans/var_valuation`.
- `docs/`: StateSpec, valuation formulas, news formulas, Chen residual note, Treasury test.
- One example script per extra under `examples/`, using `tests/fixtures/` so CI stays offline.

### Tooling

- `uv` + hatchling, `src/` layout
- ruff
- pytest + pytest-cov
- CI: `uv sync --extra data` + pytest on Python 3.11 and 3.12
- Version: `0.1.0`

### Paper migration (follow-up, not this repo’s opening commits)

The paper folder deletes vendored `src/climate_var_valuation/model`, `estimation`, `valuation` math and depends on `varvaluation[wrds,climate]`. Pipeline scripts stay in the paper repo.

---

## Public surface (`varvaluation.__init__`)

Exported:

- `StateSpec`, `ExpectedReturnSpec`
- `state_schema`, `returns_schema`
- `estimate_var`, `estimate_var_panel`, `VARFit`
- `AngLiuModel`
- `isolate_channels` (module function). `value` and `perpetuity` are methods on `AngLiuModel`
- `news_decomposition`, `treasury_test`, `NewsResult`, `NewsShares`
- `ValuationResult`
- All exceptions listed above

Not exported at top level: extra subpackages.

### Ten-line path

```python
import polars as pl
from varvaluation import StateSpec, estimate_var, AngLiuModel, news_decomposition

spec = StateSpec(names=("g", "beta", "dpo", "r", "cay", "pi"), cashflow="g")
fit = estimate_var(df, spec)
model = AngLiuModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=alpha)
rates = model.spot_rates(X_t, n=30)
news = news_decomposition(fit, returns)
```

---

## Open Questions

None remaining. Decisions resolved in conversation:

- Chen et al. enter as VAR news, Chen-aware (no IBES in v1).
- Full research stack ships as extras, not a second package.
- This repo is the source of truth; the paper depends on it.
- Layered library + extras (not a single `FittedSystem`, not two PyPI names).

Resolved in this spec without a further question:

- Default `rho = 0.96` unless the caller passes `rho` or a level valuation-ratio column.
- Discount-rate news is either the expected-return gradient (`xi`, `Lambda`) or a named `return_state`, never both, never neither.
- Cache directory for `[data]`: `~/.cache/varvaluation`.
- First GitHub push is public; PyPI upload is a later tagged release.

---

## PR Plan

Each PR is independently reviewable and leaves `main` installable.

### PR 1 — Scaffold

- `pyproject.toml` (uv, hatchling, extras stubs, ruff, pytest), `LICENSE`, `.gitignore`, empty `src/varvaluation`, CI workflow.
- README with the intended 10-line path marked as the target API.

### PR 2 — Spec, schemas, exceptions

- `StateSpec`, `ExpectedReturnSpec.xi_lambda`, `state_schema`, typed exceptions.
- Tests: name binding, unknown names, schema reject, xi/Lambda symmetry.

### PR 3 — Estimation

- `estimate_var`, `estimate_var_panel`, `VARFit`, Newey–West, `EstimationError`.
- Tests: recovered \(\Phi\) on a simulated VAR; panel respects group boundaries.

### PR 4 — AngLiuModel

- Price and cash-flow recursions, spot rates, unconditional moments, degeneracy tests ported from the paper.

### PR 5 — Valuation

- `value`, `perpetuity`, `isolate_channels`, `ValuationResult`.
- Tests: tail refusal, channel shut-off changes PV, \(\Lambda=0\) affine match.

### PR 6 — News

- `news_decomposition`, `treasury_test`, Chen invariant, identity residual.

### PR 7 — `[data]` extra

- Public loaders + `prepare_portfolio_state` + fixtures. CI runs these offline against fixtures.

### PR 8 — `[climate]` extra

- `build_climate_state`, `scenario_dynamics`, `override_var` (generic).

### PR 9 — `[wrds]` extra

- `load_firm_panel`, `prepare_firm_state`, schemas. Tests skip in CI.

### PR 10 — Docs and examples

- `docs/` formula pages, examples, README polish. Link from the course site is a separate PR on `var_valuation`.

---

## Success criteria

A stranger can:

```text
uv add varvaluation
```

pass a named-state Polars frame, and obtain (i) a spot discount curve, (ii) a present value, (iii) CF and DR news series whose CF column does not move when the return residual is scrambled.

`uv add "varvaluation[data]"` runs the Ang–Liu portfolio recipe on Ken French without WRDS.

The paper pipeline can switch to this package without copying recursion code.
