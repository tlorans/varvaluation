<div class="hero" markdown>

<p class="hero-kicker">Open handbook · Python · A research program</p>

# Explain asset values from data

<p class="hero-lead">Present value is the expectation of a product: each cash flow times a path of one-period expected returns. One rate for every horizon is a degeneracy, not a method. This handbook is how you enter the research program that treats that product as something you can measure.</p>

[The research program](guide/program.md){ .md-button .md-button--primary }
[Install](install.md){ .md-button }

</div>

Year one and year ten do not share a rate. The snippet values a ten-period unit claim two ways — the fitted curve, and a flat rate equal to today's $\mu(1)$. No downloads.

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

<p class="snippet-caption">Using today's 2.37% for every horizon overstates the claim by 8%. The gap is the object. Reproduce it with <code>uv run python examples/flat_vs_curve.py</code>.</p>

## Browse the handbook

<div class="topic-cards">
<a href="guide/program/"><span class="part">Part 01</span><strong>The research program</strong><span>What would count as explaining asset values from data, and which paper you could write next.</span></a>
<a href="guide/start/"><span class="part">Part 02</span><strong>Getting started</strong><span>Feel why a flat rate is the wrong tool, and learn the words (product, strip, spot curve).</span></a>
<a href="guide/system/"><span class="part">Part 03</span><strong>The joint system</strong><span>Write one law of motion that carries cash flows, expected returns, and their covariance.</span></a>
<a href="guide/data/"><span class="part">Part 04</span><strong>Measurement</strong><span>Estimate that system on public data and print a real discount curve. No WRDS yet.</span></a>
<a href="guide/news/"><span class="part">Part 05</span><strong>What moved the return</strong><span>Build cash-flow news from the cash-flow equation, not from a leftover.</span></a>
<a href="guide/walkthrough/"><span class="part">Part 06</span><strong>Firms</strong><span>Repeat on a CRSP–Compustat panel and draw three curves.</span></a>
</div>

The closed forms are [Ang and Liu (2004)](references.md#ang-liu-2004). The package is the bench. A valuator who already has a cash-flow path can skip to [For valuators](guide/practice.md).
