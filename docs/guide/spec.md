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

`horizon=12` on monthly data is the Ang–Liu overlapping-annual design.
Pairs are $(X_t, X_{t+12})$. Standard errors use `nw_lags` Newey–West lags
(twelve, to match the overlap). `estimate_var_panel` forms those pairs
only *inside* `group`.

## Expected return

The one-period expected equity return in this class is

$$
\mu_t = \alpha + r_t + \beta_t \lambda_t, \qquad
\lambda_t = b_0 + b_r r_t + \sum_z b_z z_t.
$$

The product $\beta_t\lambda_t$ is why $\mu_t$ is **quadratic** in $X_t$,
and why the priced recursion has an $H(n)$ matrix. `ExpectedReturnSpec`
turns named coefficients into the arrays $(\xi, \Lambda)$ that
`AngLiuModel` consumes:

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
