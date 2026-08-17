<p class="part-kicker">Part 03 · The framework</p>

# The state

<p class="you-will"><strong>You will.</strong> Name every coordinate, including the cash-flow slot.</p>

The VAR is a grammar. Which names sit in $X_t$ is a judgment inherited
from two literatures: what forecasts profitability, and what forecasts
expected returns ([Cochrane, 2011](../references.md#cochrane-2011)).
In the library, `StateSpec` is the only place those names are bound to
positions. No integer index is public. The engine does not assume that
column 0 is dividend growth.

```python
from varvaluation import StateSpec

spec = StateSpec(
    names=("roe", "beta", "bm", "r", "cay", "pi"),
    cashflow="roe",
    group="permno",
    horizon=12,
    nw_lags=12,
)
spec.index("cay")         # 4
spec.cashflow_index()     # 0
```

``` text title="Terminal"
names=('roe', 'beta', 'bm', 'r', 'cay', 'pi')  cashflow=roe  cashflow_index=0  group=permno
```

Section 5 builds this spec on 2,673 firms; the companion is the 80
longest histories. A single-series spec omits `group` and may name
`g` in place of `roe`.

`cashflow` is the most important argument. It tells both recursions
which row of $\Phi$ is the growth (or profitability) variable. At the
firm that name is `roe`. That `roe` is
$\log(\mathrm{NI}/\mathrm{BE}_{\mathrm{lag}})$: a profitability
*level*, built only when $\mathrm{NI}>0$. It is not log dividend
growth, and it is not [Vuolteenaho’s](../references.md#vuolteenaho-2002)
$e_t=\log(1+X_t/B_{t-1})$ (clean-surplus earnings, return units).

!!! note "In words — clean surplus, level versus growth"
    **Clean surplus** is the accounting identity
    $B_t=B_{t-1}+X_t-D_t$: the change in book equals earnings minus
    dividends (no gains or losses booked straight to equity).
    Vuolteenaho’s $e_t=\log(1+X_t/B_{t-1})$ is then in the same
    *units as a return*. This library’s `roe` is
    $\log(\mathrm{NI}/\mathrm{BE}_{\mathrm{lag}})$, a log *ratio of
    levels*, built only when $\mathrm{NI}>0$. A reading of $-2.08$
    is an ROE of about $12.5\%$, not a $-208\%$ growth rate. Feeding
    that series to `value` treats it as log growth and is the wrong
    call.

Unknown, duplicate, or empty names raise `StateSpecError`. There is no
integer index in the public API.

`horizon=12` on monthly data is an **overlapping annual** design.

!!! note "In words — overlapping annual, Newey–West, group"
    You want *annual* dynamics (how this year forecasts next year)
    but you observe the state every *month*. So you pair January
    with next January, February with next February, and so on.
    Adjacent pairs share eleven months: their errors are
    mechanically correlated. Ordinary standard errors would pretend
    those pairs were independent and overstate confidence.
    **Newey–West** standard errors estimate that overlap and inflate
    the uncertainty. `nw_lags=12` means “honest about twelve months
    of shared data.” `estimate_var_panel` forms those pairs only
    *inside* `group` (here `permno`): a firm needs more than
    `horizon` months or it contributes no pairs.

## Expected return

The one-period expected equity return in this class is

$$
\mu_t = \alpha + r_t + \beta_t \lambda_t, \qquad
\lambda_t = b_0 + b_r r_t + \sum_z b_z z_t.
$$

The product $\beta_t\lambda_t$ is why $\mu_t$ is **quadratic** in $X_t$,
and why the priced recursion has an $H(n)$ matrix.

!!! note "In words — from $(b_0,b_r,b_{\mathit{cay}})$ to $(\xi,\Lambda)$"
    Expand $\mu_t=\alpha+r_t+\beta_t(b_0+b_r r_t+b_{\mathit{cay}}\mathit{cay}_t)$.
    The terms that are linear in one state ($r_t$, $\beta_t$) land in
    the vector $\xi$. The product $\beta_t\mathit{cay}_t$ lands in the
    matrix $\Lambda$ (symmetrized, so the $(i,j)$ and $(j,i)$ entries
    each carry half the coefficient). `ExpectedReturnSpec` does that
    bookkeeping from names. Keys are `b0`, `br`, and `b{name}`
    (`cay` $\to$ `bcay`). Missing keys are $0$. If you already have
    $\xi$ and $\Lambda$ from another model of $\mu_t$, skip the
    builder and pass the arrays.

`ExpectedReturnSpec` turns named coefficients into the arrays
$(\xi, \Lambda)$ that `ValuationModel` consumes:

```python
from varvaluation import ExpectedReturnSpec

er = ExpectedReturnSpec(rate="r", beta="beta", premium=("cay",))
xi, Lambda = er.xi_lambda(spec, {"b0": 0.05, "br": -0.2, "bcay": 2.0})
```

## Inbound frames

`estimate_var` validates with `state_schema(spec)`: a date column, an
optional group, one float column per name. News validates returns with
`returns_schema` (simple returns in $(-1, 5)$). Failures raise
`SchemaError` and name the schema. The schemas are Pandera contracts
— typed checks on the inbound frame — so a missing column or a
return of $-1.2$ fails with a named error rather than a silent
`NaN` downstream.

## Where the names come from

The VAR is only a frame — a grammar for joint dynamics. Everything
interesting about *which* variables sit in $X_t$ is a judgment inherited
from two neighboring literatures: what forecasts **profitability**, and
what forecasts **expected returns**. Any improvement of the model will
come from improving those two maps.

### What moves cash flows

The cash-flow side is half of the [research program](program.md):
which named variables move expected cash flows. The notes below
are the first papers; they are not the whole half.

- **Profitability mean-reverts, and is forecastable.**
  [Fama and French (2000)](../references.md#ff-2000) show that
  earnings on book equity are highly forecastable and revert toward
  economy-wide levels. That is the AR structure the VAR imposes on
  `g` or `roe`: persistence $\Phi$, pull $c$.
- **ROE has internal structure.**
  [Nissim and Penman (2001)](../references.md#nissim-penman-2001)
  decompose return on common equity (ROCE) into profit margin, asset
  turnover, and a leverage spread, and document multi-year fade in
  those pieces. They do **not** estimate a negative
  rates-to-profitability regression; do not hang
  $\Phi[\texttt{roe}, r]<0$ on that paper.
- **Vuolteenaho’s object is different.**
  [Vuolteenaho (2002)](../references.md#vuolteenaho-2002) decomposes
  firm-level returns using clean-surplus
  $e_t=\log(1+X_t/B_{t-1})$ and finds, for a typical stock,
  cash-flow-news variance more than twice expected-return-news
  variance. This library’s `roe` is not that $e_t$. Section 5 does
  not reproduce the decomposition and does not confirm the finding.
- **Persistence prices into multiples.** More mean-reverting
  profitability deserves a lower multiple. That is why the own-lag of
  `spec.cashflow` is the first number to inspect before you call
  `value`. When the name is a *level*, do not call `value`.

### What moves expected returns

The discount-rate side is the return-predictability literature, with an
honest survivorship story.

| Predictor | Standing | In a typical $X_t$? |
|---|---|---|
| Dividend yield | Weak in- and out-of-sample ([Goyal and Welch, 2003](../references.md#goyal-welch-2003); [Goyal and Welch, 2008](../references.md#goyal-welch-2008)). The present-value identity can still imply return predictability ([Cochrane, 2008](../references.md#cochrane-2008); [van Binsbergen and Koijen, 2010](../references.md#vbk-2010)) | No — deliberately dropped |
| Short rate | The robust short-horizon instrument ([Fama and Schwert, 1977](../references.md#fama-schwert-1977)) | Yes — `r` |
| Term spread | Long minus short yield; more a bond result than an equity one | No |
| Default spread | Risky minus safe corporate yield; used in some return systems | No (parsimony) |
| $\mathit{cay}$ | Strong *in-sample* quarterly predictor ([Lettau and Ludvigson, 2001](../references.md#lettau-ludvigson-2001)). Whether it survives look-ahead-free and out-of-sample tests is disputed ([Goyal and Welch, 2008](../references.md#goyal-welch-2008)) | Yes — `cay`, with that caveat |
| Inflation | Negative relation with stock returns ([Fama and Schwert, 1977](../references.md#fama-schwert-1977)) | Yes — `pi` |
| Beta dynamics | Loadings move ([Fama and French, 1997](../references.md#ff-1997)). Short-window slopes are noisy ([Lewellen and Nagel, 2006](../references.md#lewellen-nagel-2006)) | Yes — `beta` (rolling) |

Selecting $X_t$ is applied predictability research, not free taste.
Dividend yield — the most famous predictor — was dropped because its
forecasting power collapsed out of sample. The short rate is kept
because the short-horizon relation is robust. $\mathit{cay}$ is kept
as an in-sample state, not as a settled out-of-sample predictor.
Section 5’s FRED reconstruction is not Lettau and Ludvigson’s
cointegrating residual.

!!! note "In words — $\mathit{cay}$, cointegration, FRED"
    Lettau and Ludvigson estimate a long-run relation
    $c_t=\alpha+\beta_a a_t+\beta_y y_t+$ residual among log
    consumption, asset wealth, and labour income. If those three
    series share a trend (**cointegration**), the residual
    $\mathit{cay}_t$ is a gap that should close — and that gap
    forecasts returns in sample. **FRED** is the St. Louis Fed’s
    public data service. When the published $\mathit{cay}$ file is
    missing, this library rebuilds a residual from FRED series
    (consumption, household net worth, wages) on 1952–2019Q3. That
    is a cousin of their residual, not the published series.

Citations for this table sit on
[References](../references.md).

### Why the two sides share a border

**Long-run risk**
([Bansal and Yaron, 2004](../references.md#bansal-yaron-2004)) is
the idea that a slowly moving component of consumption growth is
what a long-horizon investor fears; productivity as a common source
([Croce, 2014](../references.md#croce-2014)) is a production-based
version of the same thought. Both are reasons the same macro
state *can* drive cash flows and discount rates. They are not
estimated here.

[Cochrane (2011)](../references.md#cochrane-2011) is the field-level
statement: discount-rate variation is the organizing question of the
field. Traded dividend claims
([van Binsbergen and Koijen, 2017](../references.md#vbk-2017)) later
measured a term structure of *returns* on the cash-flow strip — a
cousin of $\mu_t(n)$, not a direct test of a fitted curve.

Read in one sentence: the profitability literature tells you what
forecasts $g_t$; the predictability literature tells you what forecasts
$\mu_t$; the structural literature tells you why the same state can
drive both; and the VAR is the frame where those two territories are
forced to be consistent, because price requires their joint
distribution.

A new candidate enters exactly the way the old ones did: show it
predicts cash flows or expected returns, establish its dynamics, and
add the name to `spec.names`. The engine never assumes a fixed layout.
