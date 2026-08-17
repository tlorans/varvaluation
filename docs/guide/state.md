# Building the state

The VAR only sees four named columns. Everything else is how those
columns are measured.

## ROE and book growth

Compustat *quarterly*. Income before extraordinary items is `ibq`.
Book equity is `ceqq`.

$$
\mathrm{ROE}^{\mathrm{simple}}_t
= \frac{E_t + E_{t-1/4} + E_{t-1/2} + E_{t-3/4}}{B_{t-1}},
\qquad
g^{\mathrm{simple}}_t = \frac{B_t}{B_{t-4}}.
$$

The package stores the identity-consistent logs,
$\ln(1+\mathrm{ROE}^{\mathrm{simple}})$ and $\ln(B_t/B_{t-4})$, so
$C = B(e^{\mathrm{ROE}}-e^{g})$ is clean surplus rather than an
approximation.

```python
from varvaluation.industry import compute_book_growth, compute_quarterly_roe

panel = compute_quarterly_roe(panel)   # needs ibq, ceqq
panel = compute_book_growth(panel)     # annual, four-quarter lag
```

## Beta

The paper combines two estimates ([Cosemans et al., 2016](../references.md#cosemans-2016)):

1. A **125-trading-day** rolling-window OLS of daily excess return on
   the market, ending the day before $t$.
2. A **characteristic** regression of that beta on macro and firm
   variables (DEF, DIV, $R_f$, TERM, market volatility, size,
   book-to-market, lagged beta).
3. A precision-weighted average of the two.

```python
from varvaluation.wrds import attach_posterior_beta, quarter_end_betas

qe = quarter_end_betas(daily, daily_market)          # 125-day RW
panel = attach_posterior_beta(panel, qe, method="cosemans")
# method="rolling" skips the shrink
```

Cosemans sets the *level* of industry beta (≈ 0.65 for insurers,
≈ 0.97 outside). Skipping it will miss the level differences across
portfolios.

## The market risk premium

$$
R_{m,t+1}-R_{f,t}
= \lambda_0 + \lambda_1\mathrm{DIV}_t + \lambda_2\mathrm{DEF}_t
+ \lambda_3 R_{f,t} + \lambda_4\mathrm{TERM}_t + e_t.
$$

DIV is the trailing-year dividend yield. DEF is Moody's Baa minus Aaa.
TERM is the ten-year yield minus the one-year yield. $R_f$ is the
annualized T-bill.

```python
from varvaluation.data import fit_mrp, load_paper_macro

macro = load_paper_macro()          # FF3 + DEF + Treasury + TERM
# join a `div` series, then
macro = fit_mrp(macro).predict(macro)
```

The fitted series is the **same** for every industry. What changes by
industry is $\beta$, ROE, and $g$.

## The Treasury curve $y(\tau)$

FRED series `GS1` … `GS30`, converted to continuously compounded
yields and interpolated to integer years. Missing long tenors are
filled from the last available knot.

```python
from varvaluation.data import interpolate_yields, load_treasury_curve

curve = load_treasury_curve()
y = interpolate_yields(curve.row(-1, named=True), n=30)
```

This array is an argument of `cost_of_capital`. It is **not** a column
of $x$.

## Industry averages

Value-weight the firm-level (ROE, $g$, $\beta$) inside a SIC filter.
Attach the common MRP. That is the series the VAR sees.

```python
from varvaluation import INSURANCE, paper_state_spec, prepare_industry_state

spec = paper_state_spec()          # horizon=4: quarterly data, annual steps
state = prepare_industry_state(panel, macro, spec, sic=INSURANCE["life"])
```

`INSURANCE` names the paper's ranges: `all` 6300–6399, `pc` 6330–6331,
`life` 6310–6319, `health` 6320–6329. `"ex"` is every firm outside
6300–6399. Any other `sic=((lo, hi), ...)` is a different industry
with the same four names.

The next page runs the five paper portfolios.
