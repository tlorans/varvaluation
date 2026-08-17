# 5. Illustration

This section computes the objects of Sections 2–4 on Ken French
book-to-market deciles, FRED macro series, and a CRSP–Compustat firm
window. The computations use `varvaluation`. Each subsection states
the object, shows the call that produces it, and reports the number
the data return. The script is
[`examples/walkthrough.py`](https://github.com/tlorans/varvaluation/blob/main/examples/walkthrough.py).

```text
uv add "varvaluation[data]"
uv run python examples/walkthrough.py
```

Steps 1–6 require the `[data]` extra. Step 7 requires `[wrds]` and
WRDS credentials in `.env`. Downloads cache under
`~/.cache/varvaluation`. The portfolio sample is July 1965–December
2024. The firm sample is March 2015–September 2019, the overlap that
survives a twelve-month beta window and cay.

The subsections that follow reuse the step labels of the script so
that the terminal blocks remain one-to-one with the source.

## Step 1 — Load the public data

Ken French BE/ME deciles (with and without dividends) plus the macro
state: FF3, the one-year rate, inflation, and cay.

```python
from varvaluation.data import load_bm_deciles, load_macro

total, capgains = load_bm_deciles()
macro = load_macro()
print(f"BE/ME deciles  {total['date'][0]} → {total['date'][-1]}  n={total.height}")
print(f"macro          {macro['date'][0]} → {macro['date'][-1]}  n={macro.height}")
print("macro columns:", list(macro.columns))
```

``` text title="Terminal"
BE/ME deciles  1926-07-31 → 2026-06-30  n=1200
macro          1926-07-31 → 2026-06-30  n=1200
macro columns: ['mkt_rf', 'smb', 'hml', 'rf', 'date', 'mkt', 'r', 'pi', 'cay']
cay            1959-01-31 → 2026-01-31
```

Cay here is reconstructed from FRED (PCEC, household net worth,
wages) when the published file of
[Lettau and Ludvigson (2001)](../references.md#lettau-ludvigson-2001)
is missing, and then extended through the latest quarter. That is why
it starts in 1959, not 1952.

---

## Step 2 — Build the portfolio state

Name the system. `cashflow="g"` tells both recursions that the
numerator is Hodrick trailing dividend growth.

```python
from varvaluation import StateSpec
from varvaluation.data import prepare_portfolio_state

spec = StateSpec(names=("g", "beta", "dpo", "r", "cay", "pi"), cashflow="g")
state = prepare_portfolio_state(
    total, capgains, macro, spec, portfolio="D1", start="1965-07", end="2024-12"
)
```

`prepare_portfolio_state` builds `g`, `beta`, and `dpo` from the
decile returns, and joins `r`, `cay`, `pi` from `macro`. Same call
with `portfolio="D10"` is the value decile. Last observed state:

``` text title="Terminal"
D1  1965-07-31 → 2024-12-31  months=714
  last X: g=+0.101, beta=+1.059, dpo=-0.188, r=+0.041, cay=-0.069, pi=+0.028
D10  1965-07-31 → 2024-12-31  months=714
  last X: g=-0.071, beta=+1.319, dpo=-0.230, r=+0.041, cay=-0.069, pi=+0.028
```

Growth (D1) is paying more (`g = +0.10`) with a market-like beta.
Value (D10) has shrinking dividends (`g = −0.07`) and a higher beta.
The macro piece — `r`, `cay`, `pi` — is shared.

---

## Step 3 — Estimate the risk premium

One overlapping annual regression of market excess returns on the short
rate and cay. The fitted value is $\lambda_t$.

```python
from varvaluation import ExpectedReturnSpec

# y^m_{t+1} - r_t = b0 + br r_t + bcay cay_t + e
# (HAC, 12 lags; see examples/walkthrough.py)
xi, Lambda = ExpectedReturnSpec(premium=("cay",)).xi_lambda(
    spec, {"b0": 0.095, "br": -0.737, "bcay": 0.708}
)
```

``` text title="Terminal"
sample 1965-07-31 → 2024-12-31  n=714  R2=0.053
b0=+0.095 (t=+3.41)  br=-0.737 (t=-1.49)  bcay=+0.708 (t=+1.72)
```

The intercept is the only precise coefficient. `br` has the expected
negative sign (a high short rate forecasts low excess returns) and
`bcay` the expected positive sign, but neither *t*-stat would survive
a referee. That is the fragile link: $\lambda_t$ is measured, and
measured noisily. The VAR will still glue it to cash-flow growth.

---

## Step 4 — Estimate the VAR

```python
from varvaluation import estimate_var

fit = estimate_var(state, spec)
print(fit.nobs, fit.spectral_radius)
print(fit.Phi[spec.cashflow_index()])
```

``` text title="Terminal"
D1  nobs=702  spectral radius=0.890  Phi[g,g]=-0.128
  Phi[g, ·]  g=-0.128  beta=-0.113  dpo=+0.136  r=-0.647  cay=+0.585  pi=-0.287
D10  nobs=702  spectral radius=0.864  Phi[g,g]=+0.821
  Phi[g, ·]  g=+0.821  beta=+0.151  dpo=-0.735  r=+0.248  cay=+0.087  pi=+0.708
```

Both companions are stationary. The cash-flow rows are not the same
object. On D1, $\Phi_{g,g}=-0.13$: growth is noisy and mean-reverts
immediately. On D10, $\Phi_{g,g}=+0.82$: a high-dividend year is still
mostly there next year. That single number decides whether `value` is
a price you can publish.

---

## Step 5 — Both sides from $X$

```python
from varvaluation import ValuationModel

model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=alpha)
X = state.select(list(spec.names)).to_numpy()[-1]
rates = model.spot_rates(X, n=30)
cf = model.cashflow_expectation(X, n=30)
val = model.value(X, C=1.0, n=80)
perp = model.perpetuity(X, n=80)
```

`alpha` is a CAPM intercept, annualized, so each portfolio matches its
average excess return.

``` text title="Terminal"
D1  alpha=-0.009
  spot mu(n) %   n=1, 5, 10, 30: 4.90, 6.38, 7.64, 8.80
  E[C]/C         n=1, 5, 10, 30: 1.009, 1.193, 1.562, 5.878
  value=33.51  perpetuity=11.77  n_used=80
D10  alpha=-0.008
  spot mu(n) %   n=1, 5, 10, 30: 5.35, 6.66, 7.76, 8.92
  E[C]/C         n=1, 5, 10, 30: 1.181, 1.963, 3.932, 60.842
  value=1082.51  perpetuity=11.58  n_used=80
```

Read it as two columns.

**The denominator** slopes up on both deciles. A single WACC is the
wrong rate at $n=30$. `perpetuity` (numerator frozen at $1$) is about
12 on D1 and 12 on D10: the *curve* is well behaved.

**The numerator** is where they part. On D1, expected cash flow grows
to 1.56 at ten years and `value = 33.5` is a number you can discuss.
On D10, $\Phi_{g,g}=0.82$ stacks growth that barely mean-reverts:
$\mathbb{E}_t[C_{t+30}]/C_t = 61$ and `value = 1083` is not a price.
The recursion is telling you the $g$ equation is not a usable
cash-flow model at that aggregation. Keep the curve; do not publish
the full PV.

![Spot discount curves](../assets/figures/spot_curves.png)
<p class="figure-caption">The same recipe on D1, D6, and D10. These curves are the denominator. The terminal above is the last-state slice of D1 and D10.</p>

---

## Step 6 — News from the same VAR

```python
from varvaluation import news_decomposition

news = news_decomposition(fit, annual_returns, return_col="ret", xi=xi, Lambda=Lambda)
print(news.shares.var_cf, news.shares.var_dr, news.shares.residual_share)
```

``` text title="Terminal"
D1  var(cf)=0.0276  var(dr)=0.0034  residual_share=1.82
D10  var(cf)=0.1118  var(dr)=0.0038  residual_share=2.00
```

Cash-flow news is the $g$ equation, not the leftover. Value (D10) is
CF-dominated, an order of magnitude above D1. Discount-rate news is
small once $\lambda$ is the expected-return gradient rather than a
return equation inside the VAR.

`residual_share` is above one because this VAR contains no equity
return: the unexpected-return series you handed in (trailing
twelve-month decile returns) is not the object the VAR prices. That
is a diagnostic, not a third kind of news. See [News](news.md).

![Cash-flow vs discount-rate news](../assets/figures/news_shares.png)
<p class="figure-caption">Direct CF news versus DR news on the same three deciles.</p>

---

## Step 7 — Firms from WRDS

Credentials in `.env`. The public call is `load_firm_panel`; the
script uses the cached CRSP / Compustat / CCM pieces so a second run
does not hit WRDS again.

```python
from varvaluation import estimate_var_panel
from varvaluation.wrds import load_firm_panel, prepare_firm_state

panel = load_firm_panel(start="2014-01", end="2019-12-31")
spec_f = StateSpec(
    names=("roe", "beta", "bm", "r", "cay", "pi"),
    cashflow="roe",
    group="permno",
)
state_f = prepare_firm_state(
    panel, macro, spec_f, start="2015-01", end="2019-09", beta_window=12
)
fit_f = estimate_var_panel(state_f, spec_f)
```

On this machine the window after the beta burn-in is 2,673 firms,
67,884 firm-months. The VAR below is pooled on the 80 firms with the
longest histories.

``` text title="Terminal"
panel  67884 firm-months  2673 firms  2015-03-31 → 2019-09-30
VAR on 80 longest firms  nobs=2240  spectral radius=0.995  Phi[roe,roe]=+0.458
  Phi[roe, ·]  roe=+0.458  beta=-0.019  bm=-0.205  r=-7.207  cay=-0.640  pi=+4.205
one firm at 2019-09-30  permno=10026  roe=-2.080  NI/BE=0.125  bm=-1.470
  spot mu(n) %   n=1, 5, 10: 5.51, 9.31, 9.47
```

Three things to take from that block.

1. **`roe` is $\log(\mathrm{NI}/\mathrm{BE}_{\mathrm{lag}})$**, the
   firm-level cash-flow state of
   [Vuolteenaho (2002)](../references.md#vuolteenaho-2002), not a
   net-return. `roe = −2.08` is an ROE of $e^{-2.08}\approx 12.5\%$, a
   normal profitable firm. Do not feed it into `value` as if it were
   log dividend growth of −208%.
2. **$\Phi_{\mathit{roe},\mathit{roe}}=0.46$.** Firm profitability
   mean-reverts. That is why a cash-flow recursion is more trustworthy
   here than on D10, where $\Phi_{g,g}=0.82$.
3. **The companion is barely stationary** (`spectral radius = 0.995`).
   The short-rate and inflation loadings on the `roe` row are huge:
   a short panel plus persistent macro columns. Trust the own-lag;
   do not lean on the third decimal of a 30-year strip.

The discount curve at that firm still slopes up — 5.5% at one year,
9.5% at ten — the same qualitative object as the portfolio curve.

---

## Results in brief

| Step | Object | What the data said |
|---|---|---|
| 1 | Raw series | 1,200 months of deciles and macro, cay from 1959 |
| 2 | $X_t$ | 714 months of a named six-state system |
| 3 | $\lambda_t$ | $b_0$ is precise; $b_r$ and $b_{\mathit{cay}}$ have the right sign and wide standard errors |
| 4 | $(\Phi,c,\Sigma)$ | Stationary; D1 growth mean-reverts, D10 growth does not |
| 5 | Curve and value | Both curves slope up; D1 `value` is usable; D10 `value` is not |
| 6 | News | Direct CF news dominates, especially on D10 |
| 7 | Firms | 2,673 names; $\Phi_{\mathit{roe},\mathit{roe}}=0.46$ |

Section 6 interprets these results against a constant-rate DCF. A
two-state synthetic check, with no downloads, is in
[Software](../quickstart.md).
