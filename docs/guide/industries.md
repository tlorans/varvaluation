# Other industries

The paper is an insurance paper. The model is not. The state is still

$$
x' = (\mathrm{ROE},\; g,\; \beta,\; \mathrm{MRP}),
$$

the cash-flow map is still clean surplus, the required return is still the CCAPM, and $y(\tau)$ is still the Treasury curve. What changes is **which firms are averaged into $x$**.

```python
from varvaluation import prepare_industry_state

# paper
state = prepare_industry_state(panel, macro, spec, sic=((6300, 6399),))

# banks
state = prepare_industry_state(panel, macro, spec, sic=((6000, 6199),))

# anything except insurers
state = prepare_industry_state(panel, macro, spec, sic="ex")

# two ranges at once
state = prepare_industry_state(panel, macro, spec, sic=((2830, 2836), (8731, 8731)))
```

`INSURANCE["all"]`, `["pc"]`, `["life"]`, `["health"]` are just those tuples, named.

## What is common and what is not

| Object | Common across industries | Industry-specific |
|---|---|---|
| MRP series (eq. 13) | yes | |
| Treasury curve $y(\tau)$ | yes | |
| Cosemans $\gamma$ (size, BM, lag β) | pooled in the beta step | |
| Firm $\delta$ (macro slopes of β) | | yes |
| Value-weighted (ROE, $g$, β) | | yes |
| The VAR $\Phi,c,\Sigma$ | | yes |
| $\rho(\tau)$ | | yes |

Estimate **one** premium and **one** yield curve. Re-estimate the VAR for each industry. That is why life and property/casualty can have different shapes in the same month: their $\Phi$ and their average $\beta$ differ, not their $y(\tau)$.

## A checklist that does not depend on insurance

1. Build the firm-quarter panel (ROE, $g$, β, size, BM).
2. Value-weight inside the SIC filter; attach the common MRP.
3. `estimate_var` on that single series.
4. `TermStructureModel.from_var` with `ResidualIncome` and `CCAPMSpec`.
5. Read `expected_cashflow` and `cost_of_capital` from the **same** `fit`.
6. Compare $\rho(\tau)$ to the flat CAPM and the one-period CCAPM. Report the annuity discrepancy.

If step 5 ever takes cash from one estimated system and rates from another, stop. That is the mistake the whole package exists to prevent.
