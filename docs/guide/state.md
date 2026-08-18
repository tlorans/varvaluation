# Building the state

## Where this sits on the map

The three-step map is complete. This page is only about the **input frame**: a Polars DataFrame of state variables that `estimate_var` (or `estimate_var_panel`) can see.

The package does **not** download data or implement paper-specific loaders. You construct $X_t$ however you like; the estimator only needs named columns and a date.

---

## Minimum columns

| Column | Role |
|---|---|
| `date` (or `spec.date`) | ordered time index for lag pairs |
| one column per name in `spec.names` | the state $X_t$ |
| optional `group` (e.g. `firm`) | for `estimate_var_panel` only |

Mark which column is cash-flow growth with `spec.cashflow`.

```python
from varvaluation import StateSpec, estimate_var

spec = StateSpec(
    names=("g", "beta", "mrp", "rf"),
    cashflow="g",
    date="date",
    horizon=1,
)
fit = estimate_var(state, spec)   # state: Polars DataFrame
```

---

## What typically enters $X_t$

| Coordinate | Examples |
|---|---|
| Cash-flow growth $g_t$ | $\log(C_t/C_{t-1})$, or a growth rate derived from accounting |
| Expected-return drivers | short rate, conditional beta, market premium, other predictors |

If both beta and the premium move, $\mu_t$ is quadratic in $X_t$ and the priced recursion carries $H(n)$. If either is constant, set $\Lambda=0$.

---

## Single series vs firm panel

**One series** (market, industry average, portfolio):

```python
fit = estimate_var(state, spec)
```

**Panel of firms** — lag pairs only within each firm:

```python
spec = StateSpec(
    names=("g", "beta", "mrp"),
    cashflow="g",
    group="firm",
    horizon=1,
)
fit = estimate_var_panel(state, spec)
```

Then read curves for the last observation of each firm:

```python
from varvaluation import ExpectedReturnSpec, ValuationModel

xi, Lambda = ExpectedReturnSpec(rate="…", beta="…", premium=()).xi_lambda(spec, {…})
model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=…)

last = state.sort(["firm", "date"]).group_by("firm").tail(1)
curves = model.curve_frame(last, n=30, id_cols=("firm",))
values = model.value_frame(last, n=40, id_cols=("firm",))
```

Both returns are Polars DataFrames.

---

## Offline synthetic state

For tests and the course figures:

```python
from varvaluation import simulate_state

state, spec = simulate_state(nobs=400, seed=7)
# panel demo:
state, spec = simulate_state(nobs=200, seed=7, group="firm", n_groups=5)
```

!!! warning "The one rule"
    Both recursions must read from the **same** $(\Phi,c,\Sigma)$. Never mix cash from one fit with rates from another.

---

## After this page

You should be able to:

1. Build a `StateSpec` that names your columns and marks growth.
2. Call `estimate_var` or `estimate_var_panel` on a Polars frame.
3. Return curves and values with `spot_curve`, `curve_frame`, and `value_frame`.
