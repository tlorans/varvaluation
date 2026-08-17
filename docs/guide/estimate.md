# 3. Estimation

The closed forms of Section 2 are useful only if every coefficient
can be measured. The stages below are ordinary linear regressions on
overlapping annual pairs, with
[Newey and West (1987)](../references.md#newey-west-1987) standard
errors. What is not ordinary is the refusal to keep cash flows and
expected returns in separate drawers
([Ang and Liu, 2004](../references.md#ang-liu-2004), §III). The
library calls `estimate_var` and `ExpectedReturnSpec` implement those
stages. Section 5 reports the numbers they produce.

## 1. Build the observables

Name a state and put one column per name in a frame. At the firm the
layout of Section 5 is

$$
X_t = (\mathit{roe}_t,\ \beta_t,\ \mathit{bm}_t,\ r_t,\ \mathit{cay}_t,\ \pi_t)'.
$$

| Name | What it is | How this library builds it |
|---|---|---|
| `g` | log cash-flow growth | Hodrick trailing dividends from total vs. ex-div returns |
| `roe` | log profitability | $\log(\mathrm{NI}_t / \mathrm{BE}_{t-1})$ at the firm |
| `beta` | rolling CAPM slope | 60-month window on excess returns |
| `dpo` | payout | log dividends minus log earnings, when both exist |
| `bm` | book-to-market | firm panel |
| `r` | one-year rate | FRED GS1, continuously compounded |
| `cay` | consumption–wealth gap | Lettau–Ludvigson, or a FRED reconstruction |
| `pi` | inflation | 12-month log CPI |

`roe`, `bm`, and `beta` are built only when those names sit in
`spec.names`. Everything else is joined from the macro frame by column.

```python
from varvaluation.data import load_macro
from varvaluation.wrds import load_firm_panel, prepare_firm_state

macro = load_macro()
panel = load_firm_panel(start="2014-01", end="2019-12-31")
state = prepare_firm_state(panel, macro, spec, start="2015-01", end="2019-09")
```

``` text title="Terminal"
state  67884 firm-months  2673 firms  2015-03-31 → 2019-09-30
```

See [WRDS](wrds.md).

Why *these* names, and not dividend yield? That judgment comes from two
literatures and is the subject of [StateSpec](spec.md#where-the-names-come-from).

## 2. Estimate time-varying betas

A rolling regression of the firm’s log excess return on the market’s
log excess return. The slope in each window *is* $\beta_t$ — a data
series, not an assumption. Section 5 uses a twelve-month window
because the CRSP sample is short; `BETA_WINDOW = 60` in
`varvaluation.betas` is the longer convention.

Rolling betas are noisy. They genuinely move; they are also estimated
with a short window. Treat them as a measured input, not a fact.

## 3. Estimate the risk premium

One predictive regression of annual market excess returns on the states
that are supposed to forecast expected returns. The usual pair is the
short rate and $\mathit{cay}$:

$$
y^m_{t+1} - r_t = b_0 + b_r r_t + b_{\mathit{cay}}\,\mathit{cay}_t + \varepsilon_{t+1}.
$$

The fitted value *defines* $\lambda_t$. `ExpectedReturnSpec` turns
$(b_0, b_r, b_{\mathit{cay}})$ into the arrays $(\xi, \Lambda)$ of

$$
\mu_t = \alpha + r_t + \beta_t\lambda_t
      = \alpha + \xi' X_t + X_t'\Lambda X_t.
$$

Section 5 runs this regression with Newey–West (12-lag) standard
errors on overlapping annual market returns. The fitted coefficients
become $(\xi,\Lambda)$ through `ExpectedReturnSpec`. In the firm
illustration, $b_0=+0.095$ ($t=3.41$), $b_r=-0.737$ ($t=-1.49$),
$b_{\mathit{cay}}=+0.708$ ($t=1.72$).

The premium regression is the fragile link. Coefficients at an annual
horizon are imprecise; $\mathit{cay}$’s predictive power weakens
without look-ahead. The framework at least tells you *which* link is
fragile.

## 4. Estimate the VAR

`estimate_var(df, spec)` stacks the named columns and regresses each
variable on all of them, lagged `spec.horizon` rows:

$$
X_{t+h} = c + \Phi X_t + u_{t+h}.
$$

On monthly data, `horizon=12` is an overlapping annual design. Adjacent
pairs share eleven months, so ordinary standard errors would overstate
confidence. `nw_lags=12` Newey–West standard errors
([Newey and West, 1987](../references.md#newey-west-1987)) are the
correction: they estimate the covariance of the errors over a window of
lags and inflate the uncertainty. Read “Newey–West, 12 lags” as
“standard errors honest about the overlap.”

`estimate_var_panel` does the same thing on a firm panel, but forms
lag pairs **only inside** `spec.group`. A firm needs more months than
`horizon` or it contributes no pairs.

```python
from varvaluation import estimate_var_panel

fit = estimate_var_panel(state, spec)
print(fit.nobs, fit.spectral_radius)
print(fit.Phi[spec.cashflow_index()])
```

``` text title="Terminal"
nobs=2240  spectral_radius=0.995  Phi[roe,roe]=+0.458
```

`VARFit` holds $\Phi$, $c$, $\Sigma$, Newey–West `se`, residuals, the
lagged design `X_lag`, and `spectral_radius`. The inbound frame is
validated by `state_schema(spec)` before any regression runs.

## 5. Read off the priced objects

```python
from varvaluation import ValuationModel

model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.02)
rates = model.spot_rates(X, n=10)
perp = model.perpetuity(X, n=40)
```

`from_var` refuses a companion with spectral radius $\ge 1$
(`NonStationaryVARError`). That is the same stationarity condition as
in [Section 2.1](system.md): without it the unconditional mean does not
exist and the tail of the sum has nowhere to settle.

The two recursions are [Section 2.2](valuation.md). The numbers at
named permnos are [Section 5](walkthrough.md).

## The division of labor

Cash flows and expected returns are estimated by *different ordinary
tools* (dividend accounting; rolling betas and a predictive
regression). They are then **glued together inside one VAR**. Each
piece is standard. The covariance that pricing requires is estimated
rather than assumed away.

## What can go wrong

| Fragile link | Symptom | What to inspect |
|---|---|---|
| Own-lag of $g$ near $1$ | $\mathbb{E}_t[C_{t+n}]/C_t$ explodes | `fit.Phi[spec.cashflow_index(), spec.cashflow_index()]` |
| Spectral radius $\ge 1$ | `from_var` refuses | `fit.spectral_radius` |
| Noisy rolling betas | $\mu_t(n)$ jitters at the short end | beta window, `var(beta)` |
| Weak premium regression | $\lambda_t$ barely moves | $t$-stats on $b_r$, $b_{\mathit{cay}}$ |
| Stambaugh bias | persistence overstated in short samples | long-horizon `value` vs `perpetuity` |
| Terminal rate $\le 0$ | `PerpetuityDivergesError` | last `spot_rates` entry |

You have traded a WACC you can argue about over coffee for statistical
assumptions that are harder to interrogate and just as consequential.
[Stambaugh (1999)](../references.md#stambaugh-1999) bias guarantees that
persistence is overstated in short samples with persistent predictors;
the priced recursion then compounds that bias into $\Phi^n$. Use the
system to read the *shape* of the curve and the *sign* of the
growth–rate interaction. Be skeptical of the third decimal place.
[What changes](practice.md) returns to this caveat.
