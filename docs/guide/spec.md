# StateSpec

`StateSpec` is the only place names are bound to positions. Nothing in the core assumes a particular state order.

```python
from varvaluation import StateSpec

spec = StateSpec(
    names=("g", "beta", "dpo", "r", "cay", "pi"),
    cashflow="g",
    date="date",
    group=None,      # "permno" for a panel
    horizon=12,      # annual VAR on monthly rows
    nw_lags=12,
)
spec.index("cay")        # 4
spec.cashflow_index()    # 0
```

A firm-level spec is the same type:

```python
StateSpec(
    names=("roe", "beta", "bm", "r", "cay", "pi"),
    cashflow="roe",
    group="permno",
)
```

Unknown names raise `StateSpecError`. Duplicate or empty names do too.

## Expected return

Ang–Liu write the one-period expected return as

$$
\mu_t = \alpha + r_t + \beta_t \lambda_t, \qquad
\lambda_t = b_0 + b_r r_t + \sum_z b_z z_t.
$$

`ExpectedReturnSpec` turns named coefficients into the arrays $(\xi, \Lambda)$ that `AngLiuModel` consumes:

```python
from varvaluation import ExpectedReturnSpec

er = ExpectedReturnSpec(rate="r", beta="beta", premium=("cay",))
xi, Lambda = er.xi_lambda(spec, {"b0": 0.05, "br": -0.2, "bcay": 2.0})
```

Keys are `b0`, `br`, and `b{name}` for each premium state (`cay` → `bcay`). Missing keys default to 0. If you already have $\xi$ and $\Lambda$, skip the builder.

## Inbound frames

`estimate_var` validates with `state_schema(spec)`: a date column, optional group, one float column per name. News validates returns with `returns_schema` (simple returns in $(-1, 5)$).
