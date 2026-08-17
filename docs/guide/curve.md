# From the VAR to the curve

Four calls take you from a state frame to the objects in the paper.

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
```

`estimate_var` is Newey–West OLS of $x_{t+h}=c+\Phi x_t+u$, with $h$ from `spec.horizon`. `from_var` refuses a companion whose spectral radius is $\ge 1$.

## Expected cash

```python
X = model.unconditional_mean()
cf = model.expected_cashflow(X, n=30)
```

`cf[k-1]` is $\mathbb{E}_t[C_{t+k}]/B_t$ at that state (paper eq. 6). It is a **difference of two log-normals**, not “treat ROE as if it were growth”. Feeding `roe` to the older dividend-growth engine is the mistake the previous handbook warned about and then made.

## The cost of capital

Equate the known-rate present value (eq. 7) with the CCAPM present value (eq. 8). Solve for the rate. That is eq. 9:

$$
\rho(\tau)_t
= y(\tau)_t
+ \frac{1}{\tau}\ln
\frac{e^{A_7+B_7'x}-e^{C_7+D_7'x}}
     {e^{A_8+B_8'x+x'G x}-e^{C_8+D_8'x+x'G x}}.
$$

The numerator is expected cash. The denominator is the same cash, priced. $y(\tau)$ is the Treasury curve, supplied from **outside** the VAR.

```python
y = 0.055                          # or an array of length 30
rho = model.cost_of_capital(X, y, n=30)
rho_bar = model.unconditional_curve(y, n=30)
```

Identities the implementation tests:

- $\rho(1) = y(1) + \beta\cdot\mathrm{MRP}$ (the CCAPM).
- If $\Theta=0$ (no priced risk), $\rho(\tau)=y(\tau)$.
- `unconditional_curve(y)` is `cost_of_capital` at $\bar x = (I-\Phi)^{-1}c$.

## The two flat lines in Fig. 1

```python
ccapm = model.flat_ccapm_rate(X, y1=y)
# CAPM: a constant beta times a constant premium, plus y(1)
capm = y + float(state["beta"].mean() * state["mrp"].mean())
```

The CCAPM is today's one-period rate, used at every maturity. The CAPM is the sample-average rate, used at every maturity. Neither knows $\tau$.

## A thirty-year dollar (Table 4)

```python
from varvaluation import flat_annuity_value, valuation_discrepancy

v_ts = model.annuity_value(X, y, n=30)
v_flat = flat_annuity_value(ccapm, n=30)
gap = valuation_discrepancy(v_ts, v_flat)   # (V_flat - V_ts) / V_ts
```

The paper's Table 4 is this gap, at 2018 Q4, 2014 Q4, 2009 Q2, and 2007 Q3. In 2009 the curve is hump-shaped and the flat CAPM *overstates* present values. In 2014 the ranking can flip. The object is the discrepancy, not a claim that one number is “the” cost of capital.

## What not to call

`AngLiuModel.value` still exists. It prices a **single growing payout** $C_t\exp(\sum g)$. That is a different cash-flow map. It is the right tool for a dividend strip. It is the wrong tool for residual income. The two classes are siblings, not flags on one solver.
