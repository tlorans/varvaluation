<div class="hero" markdown>

<p class="hero-kicker">Open handbook · Python · A research program</p>

# Explain asset values from data

<p class="hero-lead">The framework models cash flows and the discount rate together. When the required return is allowed to change, present value is the expectation of a <strong>product</strong>: each future cash flow multiplied by the sequence of one-period required returns along the way. The <strong>research program</strong> is which observed variables belong in that joint forecast.</p>

[The research program](guide/program.md){ .md-button .md-button--primary }
[Install](install.md){ .md-button }

</div>

Year one and year ten do not share a rate. The snippet values a ten-year stream of one-dollar cash flows two ways: with a different discount rate at each horizon (the **curve**), and with a single rate equal to today's one-year rate. No downloads. The printed `mu(1)` is that one-year rate; `mu(10)` is the rate the curve assigns to a cash flow ten years out.

```python
from varvaluation import ExpectedReturnSpec, ValuationModel, estimate_var
from varvaluation.news import simulate_return_var
import numpy as np

df, spec = simulate_return_var(nobs=400, seed=7)
fit = estimate_var(df, spec)
xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(
    spec, {"b0": 0.01}
)
model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.04)
X = fit.X_lag[-1]
rates = model.spot_rates(X, n=10)
n = np.arange(1, 11)
curve = float(np.sum(np.exp(-n * rates)))
flat = float(np.sum(np.exp(-n * rates[0])))
print(f"mu(1) {100*rates[0]:.2f}%   mu(10) {100*rates[-1]:.2f}%")
print(f"flat PV vs curve {(flat/curve - 1)*100:+.1f}%")
```

```text
mu(1) 2.37%   mu(10) 4.09%
flat PV vs curve +8.0%
```

<p class="snippet-caption">Today's one-year rate is 2.37%. The ten-year rate on the curve is 4.09%. Using 2.37% at every horizon overstates the claim by 8%. The gap is the object. Reproduce it with <code>uv run python examples/flat_vs_curve.py</code>.</p>

## Browse the handbook

<div class="topic-cards">
<a href="guide/program/"><span class="part">Part 01</span><strong>The research program</strong><span>What we know about future cash and future required returns, and what is still open.</span></a>
<a href="guide/start/"><span class="part">Part 02</span><strong>Getting started</strong><span>Feel why one rate is the wrong tool, then learn the words you will carry.</span></a>
<a href="guide/system/"><span class="part">Part 03</span><strong>The framework</strong><span>Model cash flows and the discount rate in one system. Growth of cash is not the same object as profitability.</span></a>
<a href="guide/data/"><span class="part">Part 04</span><strong>Measurement</strong><span>Estimate that system on freely published files and print a discount curve from data.</span></a>
<a href="guide/news/"><span class="part">Part 05</span><strong>What moved the return</strong><span>Ask what part of last period's surprise came from cash flows, and what part from discount rates.</span></a>
<a href="guide/walkthrough/"><span class="part">Part 06</span><strong>Firms</strong><span>Repeat the same steps on individual firms and draw three curves.</span></a>
</div>

The formulas that evaluate the product without simulation are [Ang and Liu (2004)](references.md#ang-liu-2004). That is the framework. The package is the bench for asking which states move the curve. If you already have a cash-flow forecast and only need the denominator, skip to [For valuators](guide/practice.md).
