# Other portfolios

The state is still

$$
X_t = (g_t,\; \beta_t,\; \ldots)',
$$

the cash-flow recursion is still Ang and Liu’s $\bar a(n),\bar b(n)$,
the priced recursion is still $a(n),b(n),H(n)$, and the spot curve is
still $\mu_t(n)$. What changes is **which names are averaged into
$X_t$**.

```python
from varvaluation import prepare_industry_state

state = prepare_industry_state(panel, macro, spec, sic=((6000, 6199),))  # banks
state = prepare_industry_state(panel, macro, spec, sic=((2830, 2836),))  # drugs
state = prepare_industry_state(panel, macro, spec, sic="ex")             # exclude a range
```

## What is common and what is not

| Object | Common across portfolios | Portfolio-specific |
|---|---|---|
| Premium series $\lambda_t$ | often yes | |
| Treasury curve (if outside the VAR) | yes | |
| Value-weighted $(g,\beta,\ldots)$ | | yes |
| The VAR $\Phi,c,\Sigma$ | | yes |
| $\mu_t(n)$ | | yes |

Estimate shared instruments once if you choose to. Re-estimate the VAR
for each portfolio. Different $\Phi$ and different average $\beta$
produce different curves in the same month.

## Checklist

1. Build the panel (growth, beta, instruments).
2. Value-weight inside the filter; attach shared instruments.
3. `estimate_var` on that series.
4. Build `AngLiuModel` (or `ValuationModel`) with $(\alpha,\xi,\Lambda)$.
5. Read `cashflow_expectation` and `spot_rates` from the **same** fit.
6. `value` as the sum of strips; compare to a flat CAPM at the same date.

!!! warning "The one rule"
    If step 5 ever takes cash from one estimated system and rates from
    another, stop. That is the mistake the whole package exists to
    prevent. Both recursions must share $(\Phi,c,\Sigma)$.
