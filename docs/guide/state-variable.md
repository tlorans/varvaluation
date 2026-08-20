# The state variable \(X_t\)

Think of \(X_t\) as a short list of numbers that describe “the current economic situation” for the asset you care about.

Examples of what can sit in \(X_t\):

- Cash-flow growth \(g_t\) (how fast dividends or earnings are growing right now)
- A return or interest-rate variable
- Conditional beta
- A market risk premium predictor (for example \(\mathit{cay}\))
- Inflation, book-to-market, short rate, etc.

You decide which variables go into the list. The package only needs them as named columns in a table (a Polars DataFrame). One of those columns is specially marked as the *cash-flow* variable via `StateSpec`.

```python
from varvaluation import StateSpec

spec = StateSpec(
    names=("g", "beta", "mrp", "rf"),  # whatever you bring
    cashflow="g",                     # the growth coordinate
    date="date",
)
```

Nothing in the package downloads data or forces a particular set of predictors. You construct \(X_t\) however you like. The estimator only needs the named columns and an ordered time index so it can form lag pairs.

A panel of firms is also supported: add a group column and call `estimate_var_panel`. Lag pairs are then formed only *inside* each firm.

The content of \(X_t\) is not free in economic terms. It must contain both a cash-flow growth coordinate *and* the variables that move expected returns. Otherwise the product identity cannot be evaluated.
