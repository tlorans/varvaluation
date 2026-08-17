<div class="hero" markdown>

<p class="hero-kicker">One joint model · cash flows and discount rates</p>

# How to discount cash flows when expected returns move

<p class="hero-lead">
A present value is the expectation of a <strong>product</strong>:
each future cash flow times the path of one-period required returns.
Those two paths have to come from the <strong>same</strong> forecast.
A vector autoregression is the smallest system that does that.
This package implements the idea for residual-income cash flows
(Giacotto, Lin, and Zhao 2020) on top of the Ang and Liu (2004)
recursions, and opens it to any industry.
</p>

[The problem](guide/problem.md){ .md-button .md-button--primary }
[Install](install.md){ .md-button }

</div>

## The idea in one minute

Standard DCF uses **one** discount rate for every horizon:

$$
V_t = \sum_{j=1}^{\infty} \frac{E_t[C_{t+j}]}{(1+r)^j}.
$$

That formula assumes (1) the rate does not move with maturity, and
(2) cash flows and discount rates can be treated separately.
Both are false once expected returns move.

The correct object is

$$
V_t = \sum_{s=1}^{\infty}
  E_t\Bigl[
    \exp\Bigl(-\sum_{k=0}^{s-1}\mu_{t+k}\Bigr)\,C_{t+s}
  \Bigr].
$$

Value is the expectation of a product. You need the **joint**
distribution of cash-flow growth and expected returns. A VAR supplies
it. From that VAR you get a whole **term structure of discount rates**
— a different rate for each maturity — and you can still keep the
usual two-step workflow (forecast cash, then discount).

## Four calls

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

<p class="snippet-caption">
Year one is the conditional CAPM. Years further out are not.
Reproduce with <code>uv run python examples/reproduce_glz2020.py</code>.
Add <code>--wrds</code> for the live 1972–2018 insurance sample.
</p>

## Roadmap

<div class="topic-cards">
<a href="guide/problem/"><span class="part">01</span><strong>The problem</strong><span>Why a flat CAPM rate is the wrong rate at every horizon but one.</span></a>
<a href="guide/system/"><span class="part">02</span><strong>One system, two readings</strong><span>Clean surplus reads cash. The CCAPM reads the required return. Both live in the same VAR.</span></a>
<a href="guide/curve/"><span class="part">03</span><strong>From the VAR to the curve</strong><span>Expected cash and the priced strip become ρ(τ). Four calls.</span></a>
<a href="guide/state/"><span class="part">04</span><strong>Building the state</strong><span>ROE, book growth, Cosemans β, the premium, the Treasury curve.</span></a>
<a href="guide/reproduce/"><span class="part">05</span><strong>Reproduce the paper</strong><span>Insurance, P/C, life, health, and all stocks except insurers.</span></a>
<a href="guide/industries/"><span class="part">06</span><strong>Other industries</strong><span>The same four names. A different SIC range.</span></a>
</div>

The formulas are [Giacotto, Lin, and Zhao (2020)](references.md#glz-2020),
built on [Feltham and Ohlson (1995)](references.md#feltham-ohlson-1995)
and [Ang and Liu (2004)](references.md#ang-liu-2004).
The package is the bench that runs them.
