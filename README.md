# varvaluation

Discount curves and present values from one VAR on a Polars state frame.

You bring the state variables. The package estimates a joint VAR, runs the two closed-form recursions, and returns the spot curve and present value as Polars frames. Optional firm panel via `estimate_var_panel`.

Handbook: [tlorans.github.io/varvaluation](https://tlorans.github.io/varvaluation/).

Three claims, in order:

1. Product: value is $E[\text{discount path}\times\text{cash flow}]$.
2. Covariance: that product expands to a covariance term that enters the price level.
3. One VAR: cash-flow growth and expected returns must share one law of motion.

## Install

```text
uv add varvaluation
```

Python 3.11+. Core dependencies: numpy, scipy, polars, statsmodels.

## Core path

```python
from varvaluation import (
    ExpectedReturnSpec,
    StateSpec,
    ValuationModel,
    estimate_var,
    simulate_state,
)

state, spec = simulate_state(nobs=400, seed=7)   # or your own Polars frame
fit = estimate_var(state, spec)

xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(
    spec, {"b0": 0.01}
)
model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.04)
X = fit.X_lag[-1]

curve = model.spot_curve(X, n=15)          # Polars: maturity, mu, cashflow_ratio, …
value = model.value_frame(
    state.tail(1).select(list(spec.names)), n=40
)                                          # Polars: pv, n_used, tail_rate
```

Firm panel (within-group lag pairs):

```python
state, spec = simulate_state(nobs=200, seed=7, group="firm", n_groups=5)
fit = estimate_var_panel(state, spec)
# last observation per firm → curves
last = state.sort(["firm", "date"]).group_by("firm").tail(1)
curves = model.curve_frame(last, n=15, id_cols=("firm",))
```

Offline check:

```text
python examples/quickstart.py
```

Two-state numerical walkthrough (every n=1 and n=2 term in numpy):

```text
python examples/numerical_toy.py
```

Ang and Liu (2004) reproduction (Ken French / FRED / cay):

```text
uv add "varvaluation[data]"
uv run python examples/reproduce_angliu2004.py
```

Handbook page: [Ang and Liu (2004)](https://tlorans.github.io/varvaluation/guide/angliu/).

## License

MIT
