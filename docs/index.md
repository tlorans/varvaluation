# Cash flows and discount rates from one system

A valuation is a sum of future cash flows, each shrunk to today. Two things
enter every term: **what you expect to receive**, and **the rate at which you
shrink it**. Call the first the *numerator* and the second the *denominator*.

The textbook DCF writes

$$
V_t = \sum_{j=1}^{\infty} \frac{\mathbb{E}_t[D_{t+j}]}{(1+r)^j}.
$$

Two assumptions are buried in that line. The denominator is **one** $r$ at
every horizon. The numerator is whatever cash-flow path you typed into the
spreadsheet, treated as if it were statistically independent of $r$.

When expected returns move, neither assumption survives. The right definition
of value is the expectation of a **product**,

$$
V_t = \sum_{j=1}^{\infty}
\mathbb{E}_t\!\left[
  D_{t+j}\,\exp\!\Bigl(-\sum_{i=1}^{j} r_{t+i}\Bigr)
\right].
$$

You cannot take $\mathbb{E}_t[D]$ and $\mathbb{E}_t[r]$ separately and then
divide. The joint distribution is the minimum required object. That is why a
VAR of cash-flow growth **and** expected-return states is the right tool: it
is one system that produces both forecasts, and their covariance, from the
same state $X_t$ and the same $(\Phi, c, \Sigma)$.

## Both sides from $X_t$

Write cash flows in growth form, $g_{t+i} = \log(C_{t+i}/C_{t+i-1})$. Each
strip is then an exponential of cumulated growth minus cumulated discount
rates. Under a Gaussian VAR those expectations have closed forms.

| Side | What it is | From $X_t$ | Method |
|---|---|---|---|
| Numerator | $\mathbb{E}_t[C_{t+n}]/C_t$ | the cash-flow row of $\Phi$ | `cashflow_expectation` |
| Denominator | spot rate $\mu_t(n)$ | the priced recursion | `spot_rates` |
| Value | their product, summed | **both** | `value` |

`model.value(X, C)` forecasts expected cash flows *and* the discount curve
from the same $X_t$. You do not paste a spreadsheet into the numerator and
you do not apply one WACC to every horizon. A two-state synthetic VAR is
enough to see both sides (no downloads):

```python
from varvaluation import (
    ExpectedReturnSpec,
    ValuationModel,
    estimate_var,
    news_decomposition,
)
from varvaluation.news import simulate_return_var

df, spec = simulate_return_var(nobs=400, seed=7)
fit = estimate_var(df, spec)

xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(
    spec, {"b0": 0.01}
)
model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.04)
X = fit.X_lag[-1]

rates = model.spot_rates(X, n=10)
cf = model.cashflow_expectation(X, n=10)
val = model.value(X, C=1.0, n=40)
news = news_decomposition(
    fit, df.select(["date", "ret"]), return_col="ret", return_state="ret"
)

print(f"spectral radius: {fit.spectral_radius:.3f}")
print(
    "spot mu(n) %      n=1, 5, 10:",
    ", ".join(f"{100 * rates[k]:.2f}" for k in (0, 4, 9)),
)
print(
    "E[C]/C            n=1, 5, 10:",
    ", ".join(f"{cf[k]:.3f}" for k in (0, 4, 9)),
)
print(f"value: {val.pv:.2f}")
print(f"news var  cf={news.shares.var_cf:.4f}  dr={news.shares.var_dr:.4f}")
```

``` text title="Terminal"
spectral radius: 0.409
spot mu(n) %      n=1, 5, 10: 2.37, 3.78, 4.09
E[C]/C            n=1, 5, 10: 0.999, 1.008, 1.021
value: 24.07
news var  cf=0.0002  dr=0.0001
```

The curve slopes up, so one rate is the wrong shrinker at long horizons.
The numerator grows slowly with $n$. `value` is the product of those two
series, summed.

`perpetuity(X)` freezes the numerator at $1$ so that only the curve can
move. Use it when you want to isolate the denominator, or when the
cash-flow own-lag is near a unit root and the growth forecast is not yet
trustworthy.

The cash-flow growth variable is whatever you pass as `spec.cashflow`
(log dividend growth `g` on a portfolio, log ROE `roe` at a firm). The
engine never assumes “column 0 is $g$.” See [StateSpec](guide/spec.md).

The [Valuation](guide/valuation.md) page walks the two recursions line by
line. [News](guide/news.md) asks a different question — what moved last
period’s unexpected return — of the **same** fitted VAR.

![Spot discount curves for BE/ME deciles](assets/figures/spot_curves.png)
<p class="figure-caption">Spot discount rates at the last sample state for Ken French book-to-market deciles, 1965–2024. The curve slopes up: a single WACC is the wrong rate at long horizons. These curves are the <em>denominator</em>. The present value multiplies each strip by the VAR’s expected cash flow at that horizon.</p>

## How to read these pages

| Page | What it is |
|---|---|
| [Worked application](guide/walkthrough.md) | Seven steps on Ken French, FRED, and WRDS, with the terminal output |
| [The VAR](guide/system.md) | What a VAR is, why one system, how the joint distribution enters the price |
| [StateSpec](guide/spec.md) | How names bind to positions, and where those names come from |
| [Estimation](guide/estimate.md) | Five stages from raw series to $(\Phi,c,\Sigma)$ |
| [Valuation](guide/valuation.md) | The two recursions, the curve, Gordon as the degenerate case |
| [News](guide/news.md) | What moved last period’s unexpected return |
| [What changes](guide/practice.md) | Side-by-side with a textbook DCF, and the honest caveat |

Citations sit on [References](references.md).

## Extras

| Extra | What it adds |
|---|---|
| core | Named-state VAR; cash-flow and discount-rate forecasts from $X$; news |
| `[data]` | Ken French, FRED, cay, portfolio state |
| `[wrds]` | CRSP–Compustat firm panel and firm-level state |

## License

MIT. Source: [tlorans/varvaluation](https://github.com/tlorans/varvaluation).
