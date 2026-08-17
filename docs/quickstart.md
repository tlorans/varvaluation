# Offline check

No downloads. A synthetic state, one VAR, the two Ang–Liu recursions
and the spot curve $\mu_t(n)$. This is a check on the implementation.

```python
from varvaluation import (
    AngLiuModel,
    estimate_var,
    simulate_paper_state,
)

state, spec = simulate_paper_state(nobs=160, seed=11)
fit = estimate_var(state, spec)
model = AngLiuModel.from_var(fit)   # set xi, Lambda, alpha as needed

# Once the model carries expected-return loadings:
# X     = ...
# spots = model.spot_rates(X, n=30)            # μ_t(n)
# cf    = model.cashflow_expectation(X, n=30)  # cash-flow recursion
# V     = model.value(X, C0=1.0)               # sum of strips + tail
```

Identity to watch: $\mu_t(1)$ equals the one-period $\mu_t$. That is the
definition of the spot curve. The same path on live data is the
[worked example](guide/reproduce.md).

```text
uv run python examples/reproduce_glz2020.py
```
