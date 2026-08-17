# API

The public surface of the library that implements Sections 2–4.
Top-level imports (`import varvaluation as v`).

## Types

| Name | Role |
|---|---|
| `StateSpec` | Named state layout. `cashflow` picks the growth row of $\Phi$ |
| `ExpectedReturnSpec` | Builds $(\xi,\Lambda)$ from $b_0, b_r, b_z$ |
| `VARFit` | $\Phi$, $c$, $\Sigma$, Newey–West `se`, residuals, `X_lag`, `spectral_radius` |
| `ValuationModel` | Cash-flow and priced recursions from the same $X$ |
| `ValuationResult` | `pv`, `n_used`, `tail_rate` |
| `NewsResult` | `frame` (`date, cf, dr, unexpected, residual`) and `shares` |
| `NewsShares` | `var_cf`, `var_dr`, `cov`, `var_unexpected`, `residual_share` |

## Estimation

| Call | What it does |
|---|---|
| `estimate_var(df, spec)` | Newey–West VAR(1) on a single series. Pairs are $(X_t, X_{t+h})$ with $h=$ `spec.horizon` |
| `estimate_var_panel(df, spec)` | Same, lag pairs formed only inside `spec.group` |
| `spectral_radius(Phi)` | Largest absolute eigenvalue |

`VARFit` fields: `spec`, `Phi` ($K\times K$), `c` ($K$,), `Sigma`
($K\times K$), `se` (regressors $\times$ equations), `nobs`,
`spectral_radius`, `residuals`, `residual_dates`, `X_lag`.

## ValuationModel

Construct with `ValuationModel.from_var(fit, xi, Lambda, alpha)` or
`ValuationModel(spec, Phi, c, Sigma, xi, Lambda, alpha)`. `from_var`
raises `NonStationaryVARError` if the spectral radius is $\ge 1$.

| Method | Returns |
|---|---|
| `cashflow_recursion(n)` | $\bar a(n),\bar b(n)$ — affine $\mathbb{E}_t[C_{t+n}]/C_t$ |
| `cashflow_expectation(X, n)` | those expectations at state $X$, length $n$ |
| `price_recursion(n)` | $a(n), b(n), H(n)$ — priced quadratic-Gaussian strips |
| `spot_discount_coefficients(n)` | $A(n), B(n), G(n)$ of $\mu_t(n)$ |
| `spot_rates(X, n)` | $\mu_t(1),\ldots,\mu_t(n)$ |
| `value(X, C=1.0, n=100)` | present value when `cashflow` is log growth; both sides from $X$ |
| `perpetuity(X, n=100)` | unit cash flow, curve only (`unit_curve_pv` in Section 5) |
| `unconditional_mean()` | $(I-\Phi)^{-1}c$ |
| `unconditional_covariance()` | vec-solved $\mathrm{Var}(X)$ |
| `variance_exact(n)` | $\mathrm{Var}(\mu_t(k))$ for $k=1,\ldots,n$ |
| `variance_decomposition(n)` | state-by-state shares of that variance |
| `long_term_rate(n=200)` | $\mu_t(n)$ as $n$ grows |

`isolate_channels(model, X, shut, on=)` rebuilds a counterfactual
model. `on` is `"cashflow"`, `"discount"`, or `"both"`.

## Fit to the market

| Call | What it does |
|---|---|
| `pricing_errors(model, state)` | Value every row; score $PV$ against `me` |
| `calibrate_alpha(fit, xi, Lambda, state)` | Pick the discount intercept so median $PV/ME$ is nearest 1 |
| `as_of(state, panel, on)` | State on one date, with `me` from `prc × shrout` |

`PricingFit` fields: `n`, `n_failed`, `median_pv_me`, `mean_log_pv_me`,
`rmse_log_pv_me` (the headline miss), `corr_log`, `share_within_2x`,
`frame`. The argument is on [Fit to the market](guide/pricing.md).

## News

| Call | What it does |
|---|---|
| `news_decomposition(fit, returns, ...)` | Direct CF news from the cash-flow equation; DR news from $\lambda$ |
| `treasury_test(nobs=600)` | Synthetic known-cash-flow check: `var_cf` $\approx 0$ |

Pass **either** `xi` and `Lambda` (expected-return gradient) **or**
`return_state` (a named return equation). Passing both, or neither,
raises `StateSpecError`. `residual` is the identity leftover, never the
definition of cash-flow news.

## Schemas

`state_schema(spec)` and `returns_schema(...)` are the Pandera inbound
contracts. `estimate_var` and `news_decomposition` validate on the way
in.

## Exceptions

| Exception | When |
|---|---|
| `StateSpecError` | unknown, duplicate, or empty names; bad news arguments |
| `SchemaError` | inbound frame fails Pandera |
| `EstimationError` | too few lag pairs |
| `NonStationaryVARError` | spectral radius $\ge 1$ at construct or unconditional moments |
| `RecursionDivergedError` | $\det(I-2\Sigma H(n))$ left the positive reals |
| `PerpetuityDivergesError` | non-positive terminal spot rate |
| `ExtraNotInstalled` | `varvaluation.data` or `.wrds` imported without the extra |

## Subpackages

Not re-exported at top level.

- `varvaluation.data` — `load_ff3`, `load_bm_deciles`, `load_industry49`,
  `load_gs1`, `load_cpi`, `load_cay`, `load_macro`,
  `prepare_portfolio_state`
- `varvaluation.wrds` — `load_firm_panel`, `prepare_firm_state`
- `varvaluation.news.simulate_return_var` — two-state synthetic panel
  used by `treasury_test` and the software check

Docstrings on the objects are the contract.
