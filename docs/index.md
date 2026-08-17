<div class="hero" markdown>

<p class="hero-kicker">A joint VAR · residual income · a term structure</p>

# Cash flows and discount rates from one system

<p class="hero-lead">A present value is the expectation of a <strong>product</strong>: each future cash flow multiplied by the path of one-period required returns along the way. Those two paths have to come from the <strong>same</strong> forecast. A vector autoregression is the smallest system that does that. This package implements that idea as in Giacotto, Lin, and Zhao (2020), and opens it to any industry.</p>

[The problem](guide/problem.md){ .md-button .md-button--primary }
[Install](install.md){ .md-button }

</div>

The insurance paper is the worked example. Four names go into one VAR: profitability, book growth, market beta, and the market risk premium. Clean surplus turns the first two into expected cash. The conditional CAPM turns the last two into a required return. The term-structure cost of capital is the rate that reconciles them at each horizon.

```python
from varvaluation import (
    CCAPMSpec,
    ResidualIncome,
    TermStructureModel,
    estimate_var,
    simulate_paper_state,
)

state, spec = simulate_paper_state(nobs=160, seed=11)
fit = estimate_var(state, spec)
model = TermStructureModel.from_var(fit, ResidualIncome(), CCAPMSpec())
y = 0.055  # risk-free curve, outside the VAR
rho = model.unconditional_curve(y, n=30)
print(f"ρ(1)  {100 * rho[0]:.2f}%")
print(f"ρ(10) {100 * rho[9]:.2f}%")
print(f"ρ(30) {100 * rho[29]:.2f}%")
print(f"CCAPM {100 * model.flat_ccapm_rate(model.unconditional_mean(), y):.2f}%")
```

```text
ρ(1)  9.26%
ρ(10) 9.24%
ρ(30) 9.23%
CCAPM 9.26%
```

<p class="snippet-caption">Year one is the conditional CAPM. Years further out are not. Reproduce the printed objects with <code>uv run python examples/reproduce_glz2020.py</code>. The live insurance sample is the same file with <code>--wrds</code>.</p>

## The roadmap

<div class="topic-cards">
<a href="guide/problem/"><span class="part">01</span><strong>The problem</strong><span>A flat CAPM rate is the wrong rate at every horizon but one.</span></a>
<a href="guide/system/"><span class="part">02</span><strong>One system, two readings</strong><span>Clean surplus reads cash. The CCAPM reads the required return. Both live in the same VAR.</span></a>
<a href="guide/curve/"><span class="part">03</span><strong>From the VAR to the curve</strong><span>Expected cash and the priced strip become ρ(τ). Four calls.</span></a>
<a href="guide/state/"><span class="part">04</span><strong>Building the state</strong><span>ROE, book growth, Cosemans β, the premium, the Treasury curve.</span></a>
<a href="guide/reproduce/"><span class="part">05</span><strong>Reproduce the paper</strong><span>Insurance, P/C, life, health, and all stocks except insurers.</span></a>
<a href="guide/industries/"><span class="part">06</span><strong>Other industries</strong><span>The same four names. A different SIC range.</span></a>
</div>

The formulas are [Giacotto, Lin, and Zhao (2020)](references.md#glz-2020), built on [Feltham and Ohlson (1995)](references.md#feltham-ohlson-1995) and [Ang and Liu (2004)](references.md#ang-liu-2004). The package is the bench that runs them.
