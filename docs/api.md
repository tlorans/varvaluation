# API

Public surface (`import varvaluation as v`). The package is an estimator: Polars state in, VAR fit, Polars curve / value out.

## Core

| Name | Role |
|---|---|
| `StateSpec` | Named state layout; `cashflow` marks growth; optional `group` for panels |
| `ExpectedReturnSpec` | Builds $(\xi,\Lambda)$ for $\mu_t=\alpha+\xi'X+X'\Lambda X$ |
| `estimate_var` | Newey-West VAR(1) on one series |
| `estimate_var_panel` | Same, lag pairs only inside `spec.group` |
| `VARFit` | $\Phi$, $c$, $\Sigma$, residuals, `X_lag`, spectral radius |
| `ValuationModel` | Recursions; Polars `spot_curve` / `curve_frame` / `value_frame` |
| `simulate_state` | Offline synthetic Polars state (optional `group`) |

### StateSpec

```python
StateSpec(
    names=("ret", "g"),   # columns in the Polars frame
    cashflow="g",
    date="date",
    group=None,           # e.g. "firm" for estimate_var_panel
    horizon=1,
    nw_lags=12,
)
```

### ValuationModel

```python
model = ValuationModel.from_var(fit, xi=..., Lambda=..., alpha=...)
```

| Method | Returns |
|---|---|
| `spot_rates(X, n)` | `ndarray` of $\mu_t(1),\ldots,\mu_t(n)$ |
| `cashflow_expectation(X, n)` | `ndarray` of $E_t[C_{t+k}]/C_t$ |
| `spot_curve(X, n)` | Polars frame: `maturity`, `mu`, `cashflow_ratio`, `discount_factor` |
| `curve_frame(states, n=, id_cols=)` | Polars long curves for many state rows |
| `value_frame(states, n=, id_cols=)` | Polars `pv`, `n_used`, `tail_rate` per row |
| `value(X, C=, n=)` | `ValuationResult` for one state vector |

### Estimation

| Call | What it does |
|---|---|
| `estimate_var(df, spec)` | pairs $(X_t, X_{t+h})$ on one series |
| `estimate_var_panel(df, spec)` | same, only within `spec.group` |

`df` is a Polars DataFrame with `spec.date`, the columns in `spec.names`, and optionally `spec.group`.

## Exceptions

| Exception | When |
|---|---|
| `StateSpecError` | unknown or invalid state names |
| `SchemaError` | frame fails validation |
| `EstimationError` | too few lag pairs |
| `NonStationaryVARError` | spectral radius $\ge 1$ |
| `RecursionDivergedError` | quadratic-Gaussian integral fails |
| `PerpetuityDivergesError` | non-positive terminal spot |
