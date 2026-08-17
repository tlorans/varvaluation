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

`estimate_var` is Newey–West OLS of $x_{t+h} = c + \Phi x_t + u$,
with $h$ from `spec.horizon`. `from_var` refuses a companion whose
spectral radius is $\ge 1$ (the system would not mean-revert).

## Expected cash

```python
X = model.unconditional_mean()
cf = model.expected_cashflow(X, n=30)
```

`cf[k-1]` is $E_t[C_{t+k}]/B_t$ at that state (paper eq. 6). It is a
**difference of two log-normals**, not “treat ROE as if it were
growth”. Feeding `roe` alone to a dividend-growth engine is the
mistake this package exists to prevent.

## The cost of capital

Equate the known-rate present value with the CCAPM present value.
Solve for the rate. That is the term-structure cost of capital:

$$
\rho(\tau)_t
= y(\tau)_t
+ \frac{1}{\tau}\ln
\frac{\text{expected cash}}
     {\text{priced cash}}.
$$

The numerator is expected cash from the residual-income map.
The denominator is the same cash, priced under the quadratic-Gaussian
law. $y(\tau)$ is the Treasury curve, supplied from **outside** the
VAR.

```python
y = 0.055                          # or an array of length 30
rho = model.cost_of_capital(X, y, n=30)
rho_bar = model.unconditional_curve(y, n=30)
```

Identities the implementation tests:

- $\rho(1) = y(1) + \beta\cdot\mathrm{MRP}$ (the CCAPM).
- If there is no priced risk, $\rho(\tau) = y(\tau)$.
- `unconditional_curve(y)` is `cost_of_capital` at the long-run mean
  $\bar x = (I-\Phi)^{-1}c$.

!!! note "The practical bridge"
    You can still do valuation in two steps: forecast cash flows
    however you forecast them, then discount. The VAR supplies the
    **curve** $\{\rho(\tau)\}$. The single WACC is replaced by a
    maturity-specific rate. That is Brennan (1997) made analytic,
    with moving betas allowed.

## The two flat lines

```python
ccapm = model.flat_ccapm_rate(X, y1=y)
# CAPM: a constant beta times a constant premium, plus y(1)
capm = y + float(state["beta"].mean() * state["mrp"].mean())
```

| Rule | What it uses |
|---|---|
| **Term structure** $\rho(\tau)$ | Horizon-specific rate from the joint VAR |
| **CCAPM flat** | Today's one-period rate, used at every maturity |
| **CAPM flat** | Sample-average rate, used at every maturity |

Neither flat rule knows $\tau$. The term structure does.

## A thirty-year dollar

```python
from varvaluation import flat_annuity_value, valuation_discrepancy

v_ts = model.annuity_value(X, y, n=30)
v_flat = flat_annuity_value(ccapm, n=30)
gap = valuation_discrepancy(v_ts, v_flat)   # (V_flat - V_ts) / V_ts
```

The paper's Table 4 is this gap at selected dates. In 2009 the curve
is hump-shaped and the flat CAPM *overstates* present values. In other
years the ranking can flip. The object is the **discrepancy**, not a
claim that one number is “the” cost of capital.

## Side by side

| | Flat CAPM / WACC | This framework |
|---|---|---|
| Discount rate | One rate, all horizons | $\rho(\tau)$ mean-reverting; a curve |
| Cash flows | Point forecast path | Conditional distribution (mean *and* variance) |
| Growth–rate interaction | None | Covariance enters the price level |
| Terminal value | Gordon, hand-set | Endogenous limit of the recursion |
| Beta | Single number | Horizon-specific loadings |

## What not to call

`AngLiuModel.value` still exists in the library. It prices a **single
growing payout** $C_t\exp(\sum g)$. That is a different cash-flow map
— the right tool for a dividend strip, the wrong tool for residual
income. The two classes are siblings, not flags on one solver.
