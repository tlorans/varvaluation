# varvaluation

A Python library for **VAR-based valuation** and **cash-flow / discount-rate news**.

You name the state, estimate a VAR(1), and get three objects from the same fit:

1. An Ang and Liu (2004) spot discount curve and present value
2. Cash-flow news taken from the cash-flow equation
3. Discount-rate news from expected-return revisions

Cash-flow news is **never** the leftover after discount-rate news. That residual is a diagnostic (Chen, Da, Zhao 2013).

```python
from varvaluation import StateSpec, estimate_var, AngLiuModel, news_decomposition

spec = StateSpec(names=("g", "beta", "dpo", "r", "cay", "pi"), cashflow="g")
fit = estimate_var(df, spec)
model = AngLiuModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=alpha)
rates = model.spot_rates(X_t, n=30)
news = news_decomposition(fit, returns, xi=xi, Lambda=Lambda)
```

![Spot discount curves for BE/ME deciles](assets/figures/spot_curves.png)
<p class="figure-caption">Spot discount rates at the last sample state for Ken French book-to-market deciles. Sample 1965–2024. The curve slopes up: a single WACC is the wrong rate at long horizons.</p>

The teaching course that walks the derivation is [Dynamic DCF](https://github.com/tlorans/var_valuation). This site is the library.

## Extras

| Extra | What it adds |
|---|---|
| *(default)* | Named-state VAR, Ang–Liu valuation, Chen-aware news |
| `[data]` | Ken French, FRED, cay, GISTEMP, portfolio state |
| `[climate]` | Persistent temperature state $Y_t$, NGFS scenarios, `override_var` |
| `[wrds]` | CRSP–Compustat firm panel and firm-level state |

## License

MIT. Source: [tlorans/varvaluation](https://github.com/tlorans/varvaluation).
