# Building the state

The three-step map is complete. This page is only about the *input frame*: a Polars DataFrame of state variables that `estimate_var` (or `estimate_var_panel`) can see.

The package does not download data or implement paper-specific loaders. You construct $X_t$ however you like. The estimator only needs named columns and a date.

---

## What the frame must contain

Every frame needs an ordered time index, `date` or whatever you put in `spec.date`, so the estimator can form lag pairs. It needs one column per name in `spec.names`. Those columns *are* the state $X_t$. Mark which column is cash-flow growth with `spec.cashflow`. A panel of firms adds an optional `group` column (`firm`, say), and that column is used only by `estimate_var_panel`.

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

What typically enters $X_t$ is one cash-flow-growth coordinate ($\log(C_t/C_{t-1})$, or a growth rate derived from accounting) plus the variables that move expected returns: the short rate, conditional beta, the market premium, other predictors. If both beta and the premium move, $\mu_t$ is quadratic in $X_t$ and the priced recursion carries $H(n)$. If either is constant, set $\Lambda=0$.

---

## One series or a firm panel

For a single series (a market, an industry average, a portfolio), call `estimate_var`.

```python
fit = estimate_var(state, spec)
```

For a panel of firms, lag pairs are formed only *inside* each firm. A firm is never lagged into another firm.

```python
spec = StateSpec(
    names=("g", "beta", "mrp"),
    cashflow="g",
    group="firm",
    horizon=1,
)
fit = estimate_var_panel(state, spec)
```

Then read curves for the last observation of each firm.

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

## An offline synthetic state

For tests and the course figures,

```python
from varvaluation import simulate_state

state, spec = simulate_state(nobs=400, seed=7)
# panel demo:
state, spec = simulate_state(nobs=200, seed=7, group="firm", n_groups=5)
```

!!! warning "The one rule"
    Both recursions must read from the **same** $(\Phi,c,\Sigma)$. Never mix cash from one fit with rates from another. That is how the covariance disappears.

Name the columns, mark growth, call `estimate_var` or `estimate_var_panel`, and read the curve and the value with `spot_curve`, `curve_frame`, and `value_frame`. The economics lived on the previous pages. This page is only the frame those pages read.
