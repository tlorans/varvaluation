# StateSpec

`StateSpec` is the only place names are bound to positions. The engine never
assumes that column 0 is dividend growth, or that any particular name is
present.

```python
from varvaluation import StateSpec

spec = StateSpec(
    names=("g", "beta", "dpo", "r", "cay", "pi"),
    cashflow="g",      # this row is the numerator's growth variable
    date="date",
    group=None,        # "permno" for a panel
    horizon=12,        # annual VAR on monthly rows
    nw_lags=12,
)
spec.index("cay")        # 4
spec.cashflow_index()    # 0
```

`cashflow` is the most important argument. It tells both recursions which
row of $\Phi$ is log cash-flow growth. On Ken French portfolios that is
usually `g` (Hodrick trailing dividend growth). At the firm it is `roe`.
A firm-level spec is the same type:

```python
StateSpec(
    names=("roe", "beta", "bm", "r", "cay", "pi"),
    cashflow="roe",
    group="permno",
)
```

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

- **Profitability mean-reverts, and is forecastable.** Fama and French
  (2000) show that earnings on book equity revert toward economy-wide
  levels over five to ten years, and that value firms have persistently
  higher expected profitability than growth firms. That is the AR
  structure the VAR imposes on `g` or `roe`: persistence $\Phi$, pull
  $c$.
- **ROE has internal structure, linked to rates.** Nissim and Penman
  (2001) decompose ROE into margin and turnover, each with its own
  dynamics, and document that interest rates predict subsequent
  profitability with a *negative* sign.
- **At the firm, cash-flow news dominates.** Vuolteenaho (2002)
  decomposes firm-level stock returns and finds cash-flow news, not
  expected-return news, drives most of the variance. The joint
  distribution the VAR prices is first-order for firms — not a
  refinement.
- **Persistence prices into multiples.** More mean-reverting
  profitability deserves a lower multiple. That is why the own-lag of
  `spec.cashflow` is the first number to inspect before you publish a
  present value.

### What moves expected returns

The discount-rate side is the return-predictability literature, with an
honest survivorship story.

| Predictor | Standing | In a typical $X_t$? |
|---|---|---|
| Dividend yield | Weak since the 1990s | No — deliberately dropped |
| Short rate | Strong at short horizons | Yes — `r` |
| Term spread | Robust for bonds, mixed for equity | No |
| Default spread | Robust | No (parsimony) |
| $\mathit{cay}$ | Significant in- and out-of-sample at quarterly frequency | Yes — `cay` |
| Inflation | Robust negative relation | Yes — `pi` |
| Beta dynamics | Loadings move, hard to estimate precisely | Yes — `beta` (rolling) |

Selecting $X_t$ is applied predictability research, not free taste.
Dividend yield — the most famous predictor — was dropped because its
power collapsed; the short rate and $\mathit{cay}$ were kept because
they survive.

### Why the two sides share a border

Long-run risk (Bansal and Yaron 2004) and productivity as a common
source (Croce 2014) are why the same macro state can drive both cash
flows and discount rates. Cochrane (2011) is the field-level statement:
discount-rate variation is the organizing question. Dividend strips
(van Binsbergen and Koijen 2017) later measured the term structure of
discount rates this system computes.

Read in one sentence: the profitability literature tells you what
forecasts $g_t$; the predictability literature tells you what forecasts
$\mu_t$; the structural literature tells you why the same state can
drive both; and the VAR is the frame where those two territories are
forced to be consistent, because price requires their joint
distribution.

A new candidate enters exactly the way the old ones did: show it
predicts cash flows or expected returns, establish its dynamics, and
add the name to `spec.names`. The engine never assumes a fixed layout.
