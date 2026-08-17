# Building the state

The VAR only sees the named coordinates of $X_t$. Everything else is
how those coordinates are measured. Ang and Liu’s empirical system is
six-dimensional; the package lets you name any subset and mark which
row is cash-flow growth.

## Cash-flow growth $g_t$

For a dividend claim, $g_t = \log(C_t/C_{t-1})$ from returns with and
without dividends, summed to the estimation horizon to remove
seasonality.

For an accounting claim, clean surplus supplies the map from
profitability and book growth:

$$
\mathrm{ROE}_{t} = \ln\bigl(1 + \mathrm{NI}_{t}/B_{t-1}\bigr),
\qquad
g^{B}_{t} = \ln(B_t/B_{t-1}),
$$

with $C_t = B_{t-1}(e^{\mathrm{ROE}_t} - e^{g^{B}_t})$. The package
stores identity-consistent logs so the residual-income reading stays
exact.

```python
from varvaluation.industry import compute_book_growth, compute_quarterly_roe

panel = compute_quarterly_roe(panel)   # needs ibq, ceqq
panel = compute_book_growth(panel)
```

## Conditional beta $\beta_t$

Rolling-window OLS of excess returns on the market, or a precision-
weighted combination with a characteristics-based prior
([Cosemans et al., 2016](../references.md#cosemans-2016)).

```python
from varvaluation.wrds import attach_posterior_beta, quarter_end_betas

qe = quarter_end_betas(daily, daily_market)
panel = attach_posterior_beta(panel, qe, method="cosemans")
```

## Market risk premium $\lambda_t$

A predictive regression of market excess returns on instruments (short
rate, dividend yield, default and term spreads, …). The fitted value
is $\lambda_t$. In the conditional CAPM,

$$
\mu_t = \alpha + r_t + \beta_t\,\lambda_t,
$$

so both $\beta_t$ and $\lambda_t$ can sit in $X_t$ and make $\mu_t$
quadratic.

```python
from varvaluation.data import fit_mrp, load_paper_macro

macro = load_paper_macro()
macro = fit_mrp(macro).predict(macro)
```

## Risk-free rate / Treasury curve

The short rate can be a coordinate of $X_t$. Alternatively a full
Treasury curve $y(\tau)$ is kept **outside** the VAR and passed into
the spot-rate calculation as data (FRED `GS1`…`GS30`, continuously
compounded, interpolated to integer years).

```python
from varvaluation.data import interpolate_yields, load_treasury_curve

curve = load_treasury_curve()
y = interpolate_yields(curve.row(-1, named=True), n=30)
```

## Naming the state

```python
from varvaluation import StateSpec, estimate_var

spec = StateSpec(
    names=("g", "beta", "mrp", "rf"),
    cashflow="g",
    horizon=1,
)
fit = estimate_var(state, spec)   # → Φ, c, Σ
```

`spec.cashflow` marks the row that feeds the cash-flow recursion.
Everything else can still move $\mu_t$ through $\xi$ and $\Lambda$.

## Portfolio or industry averages

Value-weight firm-level growth, beta, and profitability inside a
filter; attach a common premium series. That is the series the VAR
sees.

```python
from varvaluation import prepare_industry_state

state = prepare_industry_state(panel, macro, spec, sic=((6000, 6199),))
```

The next page runs estimate → recurse → curve on a worked example.
