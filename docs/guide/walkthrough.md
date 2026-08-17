# 5. Illustration

This section computes the objects of Sections 2–4 on a CRSP–Compustat
firm panel, joined to a FRED macro state. There is no portfolio
aggregation. The cash-flow variable is firm
$\mathit{roe}=\log(\mathrm{NI}/\mathrm{BE}_{\mathrm{lag}})$, the
object of [Vuolteenaho (2002)](../references.md#vuolteenaho-2002).
Each subsection names the library call, then reports the number it
returns. The script is
[`examples/walkthrough.py`](https://github.com/tlorans/varvaluation/blob/main/examples/walkthrough.py).

```text
uv add "varvaluation[data,wrds]"
uv run python examples/walkthrough.py
```

WRDS credentials live in `.env`. Queries cache under
`~/.cache/varvaluation`. The firm window after a twelve-month beta
burn-in is March 2015–September 2019.

## 5.1 Macro and the firm panel

`load_macro` and `load_firm_panel` (or the cached CRSP / Compustat /
CCM pieces) are the inbound objects of Section 3.

```python
from varvaluation.data import load_macro
from varvaluation.wrds import load_firm_panel

macro = load_macro()
panel = load_firm_panel(start="2014-01", end="2019-12-31")
```

``` text title="Terminal"
macro  1926-07-31 → 2026-06-30  n=1200
macro columns: ['mkt_rf', 'smb', 'hml', 'rf', 'date', 'mkt', 'r', 'pi', 'cay']
CRSP–Compustat  2014-01-31 → 2019-12-31  rows=356620  permno=6790
```

Cay is reconstructed from FRED when the published file of
[Lettau and Ludvigson (2001)](../references.md#lettau-ludvigson-2001)
is missing.

## 5.2 The named state

`StateSpec` binds names. `cashflow="roe"` tells both recursions which
row of $\Phi$ is profitability.
`prepare_firm_state` builds `roe`, `bm`, and `beta` when those names
are present, joins `r`, `cay`, `pi` from `macro`, and drops
financials and utilities.

```python
from varvaluation import StateSpec
from varvaluation.wrds import prepare_firm_state

spec = StateSpec(
    names=("roe", "beta", "bm", "r", "cay", "pi"),
    cashflow="roe",
    group="permno",
    horizon=12,
    nw_lags=12,
)
state = prepare_firm_state(
    panel, macro, spec, start="2015-01", end="2019-09", beta_window=12
)
print(spec.cashflow_index(), state.height, state["permno"].n_unique())
```

``` text title="Terminal"
names=('roe', 'beta', 'bm', 'r', 'cay', 'pi')  cashflow=roe  cashflow_index=0  group=permno
state  67884 firm-months  2673 firms  2015-03-31 → 2019-09-30
```

## 5.3 The premium, as $(\xi,\Lambda)$

The one-period expected return is still a market premium applied to
the firm’s $\beta_t$. `ExpectedReturnSpec.xi_lambda` turns
$(b_0,b_r,b_{\mathit{cay}})$ into the arrays of Section 2.2.

```python
from varvaluation import ExpectedReturnSpec

xi, Lambda = ExpectedReturnSpec(premium=("cay",)).xi_lambda(
    spec, {"b0": 0.095, "br": -0.737, "bcay": 0.708}
)
```

``` text title="Terminal"
sample 1965-07-31 → 2024-12-31  n=714  R2=0.053
b0=+0.095 (t=+3.41)  br=-0.737 (t=-1.49)  bcay=+0.708 (t=+1.72)
xi[r]=+1.000  xi[beta]=+0.095  Lambda[beta,cay]=+0.354
```

$b_0$ is precise. $b_r$ has the expected negative sign and
$b_{\mathit{cay}}$ the expected positive sign; neither $t$-statistic
would survive a referee. $\xi[r]=1$ is the identity that puts the
short rate into $\mu_t$ one-for-one.

## 5.4 The panel VAR

`estimate_var_panel` forms lag pairs only inside `permno`. The
companion below is pooled on the 80 firms with the longest histories.

```python
from varvaluation import estimate_var_panel

fit = estimate_var_panel(slim, spec)
print(fit.nobs, fit.spectral_radius)
print(fit.Phi[spec.cashflow_index()])
```

``` text title="Terminal"
nobs=2240  spectral_radius=0.995  Phi[roe,roe]=+0.458
Phi[roe, ·]  roe=+0.458  beta=-0.019  bm=-0.205  r=-7.207  cay=-0.640  pi=+4.205
```

$\Phi_{\mathit{roe},\mathit{roe}}=0.46$: firm profitability
mean-reverts. That is the cash-flow fact the framework needs
([Fama and French, 2000](../references.md#ff-2000);
[Vuolteenaho, 2002](../references.md#vuolteenaho-2002)). The
companion is barely stationary (`spectral_radius = 0.995`). The
short-rate and inflation loadings on the `roe` row are large: a short
panel plus persistent macro columns. Trust the own-lag.

## 5.5 The curve and the profitability path

`ValuationModel.from_var` refuses a companion with spectral radius
$\ge 1$. At each firm’s last state the model returns the spot curve
(Section 2.2) and the VAR path of $\mathit{roe}$. `roe = -2.08` is
an ROE of $e^{-2.08}\approx 12.5\%$, not a growth rate of $-208\%$.
The object to read on the cash-flow side is
$\mathbb{E}_t[\mathit{roe}_{t+n}]$, not
`cashflow_expectation` treated as if $\mathit{roe}$ were log dividend
growth. `perpetuity` isolates the denominator.

```python
from varvaluation import ValuationModel

model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.02)
X = state.filter(pl.col("permno") == 10026).select(list(spec.names)).to_numpy()[-1]
rates = model.spot_rates(X, n=10)
perp = model.perpetuity(X, n=40)
```

``` text title="Terminal"
permno=10026  2019-09-30  roe=-2.080  NI/BE=0.125  beta=+0.39  bm=-1.470
  spot mu(n) %   n=1, 5, 10: 5.51, 9.31, 9.47
  E[roe]         n=1, 5, 10: -1.940, -1.975, -2.158   (implied NI/BE 0.144, 0.139, 0.116)
  perpetuity=24.70  tail_rate=2.84%
permno=11707  2019-09-30  roe=-1.774  NI/BE=0.170  beta=+1.83  bm=-1.121
  spot mu(n) %   n=1, 5, 10: 11.79, 11.00, 10.39
  E[roe]         n=1, 5, 10: -1.899, -2.118, -2.288   (implied NI/BE 0.150, 0.120, 0.101)
  perpetuity=21.27  tail_rate=3.13%
permno=13046  2019-09-30  roe=+0.022  NI/BE=1.022  beta=+2.11  bm=-4.404
  spot mu(n) %   n=1, 5, 10: 13.03, 10.47, 9.59
  E[roe]         n=1, 5, 10: -0.408, -1.005, -1.355   (implied NI/BE 0.665, 0.366, 0.258)
  perpetuity=28.65  tail_rate=2.47%
```

Three facts.

The low-beta name (10026) has an *upward* curve: 5.5% at one year,
9.5% at ten. The high-beta names start higher and mean-revert down.
A single WACC is the wrong rate at every firm.

Profitability mean-reverts. Even permno 13046, sitting at
$\mathrm{NI}/\mathrm{BE}\approx 1$, is forecast to fade toward 26%
by year ten. That fade *is* the numerator of a residual-income
reading of the model
([Ang and Liu, 2001](../references.md#ang-liu-2001)).

`perpetuity` is finite at all three names (21–29). The denominator
is well behaved. `isolate_channels(..., on="discount")` on this
short panel hits `PerpetuityDivergesError`: shutting $\mathit{cay}$
in $\Phi$ and $\Lambda$ drives the terminal rate negative. The
exception is the framework reporting that the counterfactual curve
does not exist.

![Firm spot curves](../assets/figures/firm_spot_curves.png)
<p class="figure-caption"><strong>Figure 2.</strong> $\mu_t(n)$ at 30 September 2019 for three CRSP permnos. The low-beta name slopes up; the high-beta names start high and fade. Source: this section.</p>

A variance decomposition of $\mu_t(10)$ on this window puts most of
the curve on $\beta$ and $\mathit{bm}$, not on $g$-style cash flow:

``` text title="Terminal"
var share of mu(n=10): roe=-5.1%  beta=57.4%  bm=47.5%  r=0.1%  cay=0.0%  pi=-0.0%
```

Shares need not sum to 100 (covariances are double-counted). That
$\mathit{roe}$ is negligible *for the curve* does not mean cash flows
do not matter for prices. They drive the numerator, which this
decomposition does not show.

## 5.6 News from the same VAR

`news_decomposition` takes the fitted panel VAR and a returns frame.
Cash-flow news is the `roe` equation. Here the returns are the
equal-weighted monthly mean of the 80 firms.

```python
from varvaluation import news_decomposition

news = news_decomposition(fit, ew_returns, return_col="ret", xi=xi, Lambda=Lambda)
print(news.shares.var_cf, news.shares.var_dr, news.shares.residual_share)
```

``` text title="Terminal"
var(cf)=5.3563  var(dr)=0.0011  residual_share=2433.69  rho=0.96
news.frame columns: ['date', 'cf', 'dr', 'unexpected', 'residual']
```

Direct CF news dominates DR news, as
[Vuolteenaho (2002)](../references.md#vuolteenaho-2002) leads one to
expect at the firm. `residual_share` is enormous because the
unexpected-return series is monthly equal-weighted returns and the
VAR is an overlapping annual companion with no return equation. The
identity does not close. That is a diagnostic
([Chen, Da, and Zhao, 2013](../references.md#chen-da-zhao-2013)), not
a third kind of news.

## Results in brief

| Call | Object | What the firms said |
|---|---|---|
| `load_firm_panel` | CRSP–Compustat | 6,790 permnos, 2014–2019 |
| `StateSpec` / `prepare_firm_state` | $X_t$ | 2,673 firms, 67,884 months |
| `ExpectedReturnSpec` | $(\xi,\Lambda)$ | $b_0$ precise; $b_r$, $b_{\mathit{cay}}$ correctly signed |
| `estimate_var_panel` | $(\Phi,c,\Sigma)$ | $\Phi_{\mathit{roe},\mathit{roe}}=0.46$; $\rho(\Phi)=0.995$ |
| `spot_rates` / `perpetuity` | curve | upward at low $\beta$, downward at high $\beta$; PV 21–29 |
| `news_decomposition` | $N_{\mathrm{CF}}, N_{\mathrm{DR}}$ | CF dominates; residual share flags the return mismatch |

Section 6 interprets these results against a constant-rate DCF.
