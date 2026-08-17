# Offline check

No downloads. A four-state draw, one VAR, the term-structure cost of capital. This is a check on the implementation, not a substitute for the insurance sample.

```python
from varvaluation import (
    CCAPMSpec,
    ResidualIncome,
    TermStructureModel,
    estimate_var,
    simulate_paper_state,
)

state, spec = simulate_paper_state(nobs=160, seed=11)
fit = estimate_var(state, spec)
model = TermStructureModel.from_var(fit, ResidualIncome(), CCAPMSpec())
X = model.unconditional_mean()
y = 0.055
rho = model.cost_of_capital(X, y, n=30)
cf = model.expected_cashflow(X, n=30)
print(f"ρ(1)  {100 * rho[0]:.2f}%   CCAPM {100 * model.flat_ccapm_rate(X, y):.2f}%")
print(f"ρ(10) {100 * rho[9]:.2f}%")
print(f"E[C_{{t+1}}]/B  {cf[0]:.4f}")
```

`ρ(1)` equals the CCAPM. That identity is tested in `tests/test_residual.py`. The same four calls on the live insurance panel are [Reproduce the paper](guide/reproduce.md).

```text
uv run python examples/reproduce_glz2020.py
```
