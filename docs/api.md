# API

The public surface. Top-level imports (`import varvaluation as v`).

## Paper path

| Name | Role |
|---|---|
| `paper_state_spec()` | `(roe, g, beta, mrp)`, `horizon=4` |
| `ResidualIncome` | Clean-surplus map: `C = B (exp(ROE) - exp(g))` |
| `CCAPMSpec` | $\mu = R_f + \beta\cdot\mathrm{MRP}$; $\Theta$ has the $\beta$–MRP cell |
| `TermStructureModel` | Eqs. 6–9. Alias of `ResidualIncomeModel` |
| `INSURANCE` | SIC presets: `all`, `pc`, `life`, `health` |
| `prepare_industry_state` | Value-weighted industry series of the four names |
| `select_sic` | Keep a SIC range, or `"ex"` for all-but-insurers |
| `capm_tests` / `slope_tests` | Tables 2 and 3 |
| `curve_panel` | $\rho(\tau)$ on every date |
| `flat_annuity_value` / `valuation_discrepancy` | Table 4 |
| `simulate_paper_state` | Offline four-state draw |

### TermStructureModel

Construct with `TermStructureModel.from_var(fit, ResidualIncome(), CCAPMSpec())`. Refuses a spectral radius $\ge 1$.

| Method | Returns |
|---|---|
| `expected_cashflow(X, n)` | $\mathbb{E}_t[C_{t+k}]/B_t$, length $n$ |
| `cost_of_capital(X, y, n)` | $\rho(1),\ldots,\rho(n)$; `y` is a scalar or a length-$n$ Treasury curve |
| `unconditional_curve(y, n)` | eq. 9 at $\bar x$ |
| `flat_ccapm_rate(X, y1)` | $y(1)+\beta\cdot\mathrm{MRP}$ |
| `annuity_value(X, y, n=30)` | $\sum_{k=1}^{n} e^{-k\rho(k)}$ |
| `unconditional_mean()` | $(I-\Phi)^{-1}c$ |
| `one_period_premium(X)` | $\beta\cdot\mathrm{MRP}$ |

### Estimation

| Call | What it does |
|---|---|
| `estimate_var(df, spec)` | Newey–West VAR(1). Pairs are $(X_t, X_{t+h})$, $h=$ `spec.horizon` |
| `estimate_var_panel(df, spec)` | Same, pairs only inside `spec.group` |
| `spectral_radius(Phi)` | Largest absolute eigenvalue |

`VARFit` fields: `spec`, `Phi`, `c`, `Sigma`, `se`, `nobs`, `spectral_radius`, `residuals`, `residual_dates`, `X_lag`.

## Also in the library

These are not the paper path. They stay imported.

| Name | Role |
|---|---|
| `StateSpec` | Named state layout. `cashflow` is the growth row for the dividend-growth engine |
| `ExpectedReturnSpec` | Builds $(\xi,\Lambda)$ for $\mu=\alpha+r+\beta\lambda$ |
| `AngLiuModel` / `ValuationModel` | Single growing payout; `spot_rates`, `value`, `perpetuity` |
| `isolate_channels` | Counterfactual value after zeroing named loadings |
| `news_decomposition` / `treasury_test` | Chen-aware CF/DR news |
| `pricing_errors` / `calibrate_alpha` | Model PV against market equity |

## `[data]`

Not re-exported at top level. `import varvaluation.data`.

`load_paper_macro()`, `load_treasury_curve()`, `interpolate_yields()`, `load_corporate_spread()`, `fit_mrp()`, `dividend_yield_from_returns()`, plus the older Ken French / FRED / cay loaders.

## `[wrds]`

`import varvaluation.wrds`.

`load_compustat_quarterly()`, `load_crsp_daily()`, `load_crsp_dsi()`, `quarter_end_betas()`, `attach_posterior_beta()`, plus the older annual firm panel.

## Exceptions

| Exception | When |
|---|---|
| `StateSpecError` | unknown, duplicate, or empty names |
| `SchemaError` | inbound frame fails Pandera |
| `EstimationError` | too few lag pairs |
| `NonStationaryVARError` | spectral radius $\ge 1$ |
| `RecursionDivergedError` | a Gaussian integral left the positive reals |
| `TermStructureError` | eq. 9 argument is not positive |
| `PerpetuityDivergesError` | non-positive terminal spot rate (dividend-growth engine) |
| `ExtraNotInstalled` | `.data` or `.wrds` imported without the extra |
