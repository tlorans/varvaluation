# 2.3 The state

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

Unknown, duplicate, or empty names raise `StateSpecError`. There is no
integer index in the public API.

`horizon=12` on monthly data is an overlapping annual design. Pairs are
$(X_t, X_{t+12})$. Standard errors use `nw_lags` Newey–West lags (twelve,
to match the overlap). `estimate_var_panel` forms those pairs only
*inside* `group`.

## Expected return

The one-period expected equity return in this class is

$$
\mu_t = \alpha + r_t + \beta_t \lambda_t, \qquad
\lambda_t = b_0 + b_r r_t + \sum_z b_z z_t.
$$

The product $\beta_t\lambda_t$ is why $\mu_t$ is **quadratic** in $X_t$,
and why the priced recursion has an $H(n)$ matrix. `ExpectedReturnSpec`
turns named coefficients into the arrays $(\xi, \Lambda)$ that
`ValuationModel` consumes:

```python
from varvaluation import ExpectedReturnSpec

er = ExpectedReturnSpec(rate="r", beta="beta", premium=("cay",))
xi, Lambda = er.xi_lambda(spec, {"b0": 0.05, "br": -0.2, "bcay": 2.0})
```

Keys are `b0`, `br`, and `b{name}` for each premium state (`cay` →
`bcay`). Missing keys default to 0. If you already have $\xi$ and
$\Lambda$ from another model of $\mu_t$, skip the builder and pass the
arrays.

## Inbound frames

`estimate_var` validates with `state_schema(spec)`: a date column, an
optional group, one float column per name. News validates returns with
`returns_schema` (simple returns in $(-1, 5)$). Failures raise
`SchemaError` and name the schema.

## Where the names come from

The VAR is only a frame — a grammar for joint dynamics. Everything
interesting about *which* variables sit in $X_t$ is a judgment inherited
from two neighboring literatures: what forecasts **profitability**, and
what forecasts **expected returns**. Any improvement of the model will
come from improving those two maps.

### What moves cash flows

The cash-flow side is the profitability-forecasting literature.

- **Profitability mean-reverts, and is forecastable.**
  [Fama and French (2000)](../references.md#ff-2000) show that
  earnings on book equity are highly forecastable and revert toward
  economy-wide levels. That is the AR structure the VAR imposes on
  `g` or `roe`: persistence $\Phi$, pull $c$.
- **ROE has internal structure.**
  [Nissim and Penman (2001)](../references.md#nissim-penman-2001)
  decompose ROCE into profit margin, asset turnover, and a leverage
  spread, and document multi-year fade in those pieces. They do
  **not** estimate a negative rates-to-profitability regression; do
  not hang $\Phi[\texttt{roe}, r]<0$ on that paper.
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
| Term spread | More a bond result than an equity one | No |
| Default spread | Used in some return systems | No (parsimony) |
| $\mathit{cay}$ | Strong *in-sample* quarterly predictor ([Lettau and Ludvigson, 2001](../references.md#lettau-ludvigson-2001)). Whether it survives look-ahead-free and out-of-sample tests is disputed ([Goyal and Welch, 2008](../references.md#goyal-welch-2008)) | Yes — `cay`, with that caveat |
| Inflation | Negative relation with stock returns ([Fama and Schwert, 1977](../references.md#fama-schwert-1977)) | Yes — `pi` |
| Beta dynamics | Loadings move ([Fama and French, 1997](../references.md#ff-1997)). Short-window slopes are noisy ([Lewellen and Nagel, 2006](../references.md#lewellen-nagel-2006)) | Yes — `beta` (rolling) |

Selecting $X_t$ is applied predictability research, not free taste.
Dividend yield — the most famous predictor — was dropped because its
forecasting power collapsed out of sample. The short rate is kept
because the short-horizon relation is robust. $\mathit{cay}$ is kept
as an in-sample state, not as a settled out-of-sample predictor.
Section 5’s FRED reconstruction is not Lettau and Ludvigson’s
cointegrating residual. Citations for this table sit on
[References](../references.md).

### Why the two sides share a border

Long-run risk
([Bansal and Yaron, 2004](../references.md#bansal-yaron-2004)) and
productivity as a common source
([Croce, 2014](../references.md#croce-2014)) are why the same macro
state can drive both cash flows and discount rates.
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
