# varvaluation

A Python library for **VAR-based valuation** and **cash-flow / discount-rate
news**.

A price is a sum of future cash flows, each shrunk to today. Two things
enter every term: what you expect to receive (the **numerator**) and the
rate at which you shrink it (the **denominator**). When expected returns
move, those two objects are not independent. They have to come from **one
joint model**. That model is a VAR of cash-flow growth and expected-return
states.

You name the state, estimate the VAR, and get three things from the same
fit:

1. An Ang and Liu (2004) **spot discount curve** $\mu_t(n)$
2. An expected cash-flow path $\mathbb{E}_t[C_{t+n}]/C_t$ from the cash-flow
   **equation**, not from a spreadsheet
3. **News**: last period’s unexpected return split into cash-flow news and
   discount-rate news

Ang and Liu derived (1) and (2), then in the published application froze
the numerator at $1$ (a unit perpetuity) and reported only the curve. This
library exposes both choices: `perpetuity` is their design; `value`
switches the cash-flow recursion on. The [Valuation](guide/valuation.md)
page is written as a short course on that distinction.

Cash-flow **news** is never the leftover after discount-rate news. That
residual is a diagnostic (Chen, Da, Zhao 2013). See [News](guide/news.md).

```python
from varvaluation import StateSpec, estimate_var, AngLiuModel, news_decomposition

spec = StateSpec(names=("g", "beta", "dpo", "r", "cay", "pi"), cashflow="g")
fit = estimate_var(df, spec)
model = AngLiuModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=alpha)
rates = model.spot_rates(X_t, n=30)           # denominator
cf    = model.cashflow_expectation(X_t, n=30) # numerator
perp  = model.perpetuity(X_t)                 # Ang–Liu: numerator = 1
val   = model.value(X_t, C=1.0)               # both sides live
news  = news_decomposition(fit, returns, xi=xi, Lambda=Lambda)
```

![Spot discount curves for BE/ME deciles](assets/figures/spot_curves.png)
<p class="figure-caption">Spot discount rates at the last sample state for Ken French book-to-market deciles, 1965–2024. The curve slopes up: a single WACC is the wrong rate at long horizons. These curves are the <em>denominator</em>.</p>

Start at [The idea](guide/idea.md), then [Valuation](guide/valuation.md).
The teaching course that walks the derivation from Damodaran to the VAR is
[Dynamic DCF](https://github.com/tlorans/var_valuation). This site is the
library.

## Extras

| Extra | What it adds |
|---|---|
| *(default)* | Named-state VAR, both recursions, Chen-aware news |
| `[data]` | Ken French, FRED, cay, portfolio state |
| `[wrds]` | CRSP–Compustat firm panel and firm-level state |

## License

MIT. Source: [tlorans/varvaluation](https://github.com/tlorans/varvaluation).
