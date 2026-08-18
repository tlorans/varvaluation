# API

The public surface. Top-level imports (`import varvaluation as v`).

## Core path

| Name | Role |
|---|---|
| `StateSpec` | Named state layout; `cashflow` marks the growth row |
| `ExpectedReturnSpec` | Builds $(\xi,\Lambda)$ for $\mu_t=\alpha+\xi'X+X'\Lambda X$ |
| `ValuationModel` / `AngLiuModel` | Cash-flow recursion, priced recursion, $\mu_t(n)$, `value` |
| `estimate_var` / `estimate_var_panel` | Newey–West VAR(1) |
| `isolate_channels` | Counterfactual value after zeroing named loadings |
| `news_decomposition` / `treasury_test` | CF / DR news |
| `pricing_errors` / `calibrate_alpha` | Model PV against market equity |
| `simulate_paper_state` | Offline synthetic state for smoke tests |

### ValuationModel (alias `AngLiuModel`)

Construct with `ValuationModel.from_var(fit, xi=..., Lambda=..., alpha=...)`.
Refuses a spectral radius $\ge 1$.

| Method | Returns |
|---|---|
| `cashflow_expectation(X, n)` | $E_t[C_{t+k}]/C_t$ from the cash-flow recursion, length $n$ |
| `cashflow_recursion(n)` | coefficients $(\bar a(k),\bar b(k))$ |
| `price_recursion(n)` | coefficients $(a(k),b(k),H(k))$ |
| `spot_rates(X, n)` | $\mu_t(1),\ldots,\mu_t(n)$ |
| `value(X, C)` | sum of strips + geometric tail at $\mu_t(N)$ |

### Estimation

| Call | What it does |
|---|---|
| `estimate_var(df, spec)` | Newey–West VAR(1). Pairs $(X_t, X_{t+h})$, $h=$ `spec.horizon` |
| `estimate_var_panel(df, spec)` | Same, pairs only inside `spec.group` |
| `spectral_radius(Phi)` | Largest absolute eigenvalue |

`VARFit` fields: `spec`, `Phi`, `c`, `Sigma`, `se`, `nobs`, `spectral_radius`, `residuals`, `residual_dates`, `X_lag`.

## Optional residual-income numerator

Same discount-rate side; cash flows from clean surplus instead of a
single growth coordinate.

| Name | Role |
|---|---|
| `ResidualIncome` | Clean-surplus map: $C = B(\exp(\mathrm{ROE})-\exp(g))$ |
| `CCAPMSpec` | $\mu = R_f + \beta\cdot\mathrm{MRP}$ |
| `TermStructureModel` | Residual-income reading of the same recursions |
| `prepare_industry_state` / `select_sic` | Value-weighted industry series |
| `flat_annuity_value` / `valuation_discrepancy` | Strip-sum diagnostics under a flat rate |

### TermStructureModel

`TermStructureModel.from_var(fit, ResidualIncome(), CCAPMSpec())`.

| Method | Returns |
|---|---|
| `expected_cashflow(X, n)` | $E_t[C_{t+k}]/B_t$ under clean surplus |
| `cost_of_capital(X, y, n)` | horizon-specific rates given an external Treasury curve $y$ |
| `unconditional_curve(y, n)` | curve at $\bar x = (I-\Phi)^{-1}c$ |
| `flat_ccapm_rate(X, y1)` | one-period $y(1)+\beta\cdot\mathrm{MRP}$ |
| `annuity_value(X, y, n)` | strip sum under the curve |

## `[data]`

Not re-exported at top level. `import varvaluation.data`.

`load_paper_macro()`, `load_treasury_curve()`, `interpolate_yields()`,
`load_corporate_spread()`, `fit_mrp()`, `dividend_yield_from_returns()`,
plus Ken French / FRED loaders.

## `[wrds]`

`import varvaluation.wrds`.

`load_compustat_quarterly()`, `load_crsp_daily()`, `load_crsp_dsi()`,
`quarter_end_betas()`, `attach_posterior_beta()`, plus the firm panel.

## Exceptions

| Exception | When |
|---|---|
| `StateSpecError` | unknown, duplicate, or empty names |
| `SchemaError` | inbound frame fails Pandera |
| `EstimationError` | too few lag pairs |
| `NonStationaryVARError` | spectral radius $\ge 1$ |
| `RecursionDivergedError` | a Gaussian integral left the positive reals |
| `PerpetuityDivergesError` | non-positive terminal spot rate |
| `ExtraNotInstalled` | `.data` or `.wrds` imported without the extra |
