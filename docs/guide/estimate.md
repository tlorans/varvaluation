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
| `g` | log cash-flow growth | Trailing twelve-month dividends from the gap between total and ex-dividend returns ([Hodrick, 1992](../references.md#hodrick-1992)), then $g_t=\log(D_t/D_{t-1})$ |
| `roe` | log profitability *level* | $\log(\mathrm{NI}_t / \mathrm{BE}_{t-1})$; not Vuolteenaho $e_t$ |
| `beta` | rolling CAPM slope | 60-month window of log excess returns on the market; Section 5 uses 12 |
| `dpo` | payout | $\log D-\log$ earnings, when both exist and earnings are positive |
| `bm` | log book-to-market | $\log(\mathrm{BE}/\mathrm{ME})$; a reading of $-1.47$ is a high multiple, not a negative ratio |
| `r` | one-year rate | FRED GS1 (one-year Treasury yield), converted to a continuously compounded rate, $\log(1+y)$ |
| `cay` | consumption–wealth gap | Lettau–Ludvigson, or a FRED reconstruction (Section 2.3) |
| `pi` | inflation | 12-month log change in CPI |

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
because the CRSP extract is short; `BETA_WINDOW = 60` in
`varvaluation.betas` is the longer convention
([Lewellen and Nagel, 2006](../references.md#lewellen-nagel-2006)
discuss the noise in short-window slopes).

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
errors on overlapping annual market returns
([Hodrick, 1992](../references.md#hodrick-1992);
[Newey and West, 1987](../references.md#newey-west-1987)). The
fitted coefficients become $(\xi,\Lambda)$ through
`ExpectedReturnSpec`. In the firm illustration,
$b_0=+0.095$ ($t=3.41$), $b_r=-0.737$ ($t=-1.49$),
$b_{\mathit{cay}}=+0.708$ ($t=1.72$). The sample is July 1965–
December 2024. The valuation date in Section 5 is September 2019.
That is **look-ahead**: later returns enter $(\xi,\Lambda)$ used to
price an earlier $X_t$. A no-look-ahead vintage would stop the
premium regression at 2019-09.

$b_0$ is precise. The two slopes that make $\lambda_t$ *move* have
$|t|<2$. On this vintage the quadratic term $H(n)$ is not identified.
$\alpha=0.02$ in `ValuationModel.from_var` is a **calibration
intercept**, not an estimate. It shifts every spot rate by about two
percentage points.

The premium regression is the fragile link. Coefficients at an annual
horizon are imprecise; $\mathit{cay}$’s predictive power weakens
without look-ahead
([Goyal and Welch, 2008](../references.md#goyal-welch-2008)). The
staging at least tells you *which* link is fragile. It is the same
staging as Ang and Liu (2004, §III), not a single-equation
identification of the product.

## 4. Estimate the VAR

`estimate_var(df, spec)` stacks the named columns and regresses each
variable on all of them, lagged `spec.horizon` rows:

$$
X_{t+h} = c + \Phi X_t + u_{t+h}.
$$

On monthly data, `horizon=12` is an overlapping annual design
([Hodrick, 1992](../references.md#hodrick-1992)). Adjacent
pairs share eleven months, so ordinary standard errors would overstate
confidence. `nw_lags=12` Newey–West standard errors
([Newey and West, 1987](../references.md#newey-west-1987)) are the
correction: they estimate the covariance of the errors over a window of
lags and inflate the uncertainty. Read “Newey–West, 12 lags” as
“standard errors honest about the overlap.” Stacked Newey–West on the
Section 5 panel is not date-clustered; no standard errors are printed
there.

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

Those 2,240 pairs are the **80** longest firms, not the 2,673 in the
prepared state. $\Phi_{\mathit{roe},\mathit{roe}}=0.46$ is a pooled
own-lag of profitable-year $\log(\mathrm{NI}/\mathrm{BE})$ in
2015–2019.

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
| Own-lag of $g$ near $1$, or a *level* in the CF slot | $\mathbb{E}_t[C_{t+n}]/C_t$ is not a price | `fit.Phi[spec.cashflow_index(), spec.cashflow_index()]`; use `spot_rates` on a path you have |
| Spectral radius $\ge 1$ | `from_var` refuses | `fit.spectral_radius` |
| Noisy rolling betas | $\mu_t(n)$ jitters at the short end | 12 vs 60-month window, `var(beta)` |
| Weak premium regression | $\lambda_t$ barely moves; $H(n)$ unidentified | $t$-stats on $b_r$, $b_{\mathit{cay}}$ |
| Look-ahead in $(\xi,\Lambda)$ | later returns price an earlier $X_t$ | premium sample end vs valuation date |
| Calibration $\alpha$ | every spot rate shifts by $\alpha$ | do not treat $0.02$ as an estimate |
| Stambaugh bias | persistence overstated in short samples | long-horizon `value` vs `perpetuity` |
| Terminal rate $\le 0$ | `PerpetuityDivergesError` | last `spot_rates` entry |

You have traded a rate you can argue about over coffee for statistical
assumptions that are harder to interrogate and just as consequential.

!!! note "In words — $t$-stat, date-clustered, Stambaugh"
    A **$t$-statistic** is coefficient over standard error. Roughly
    $\lvert t\rvert>2$ is the usual “detectable at 5%” rule of thumb
    in large samples. $b_r$ and $b_{\mathit{cay}}$ in Section 5 miss
    that bar. **Date-clustered** standard errors treat all firms on
    the same month as one shock; stacked Newey–West on the 80-firm
    panel does **not** do that, which is why no SEs are printed
    there. **Stambaugh (1999) bias**: if a predictor is persistent
    and its innovations are correlated with returns (the dividend
    yield is the textbook case), the OLS slope on that predictor is
    biased upward in small samples. Persistence is overstated, and
    the priced recursion compounds that bias into $\Phi^n$.

Use the system to read the *shape* of the curve and the *sign* of the
growth–rate interaction. Be skeptical of the third decimal place.
[What changes](practice.md) returns to this caveat.
