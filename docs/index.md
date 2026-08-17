<div class="hero" markdown>

<p class="hero-kicker">Ang &amp; Liu (2004) · one joint VAR</p>

# How to discount cash flows when expected returns move

<p class="hero-lead">
A present value is the expectation of a <strong>product</strong>:
each future cash flow times the path of one-period required returns.
Those two paths have to come from the <strong>same</strong> forecast.
A vector autoregression is the smallest system that does that.
This package implements the closed-form recursions of
<a href="references.md#ang-liu-2004">Ang and Liu (2004)</a>:
a cash-flow recursion, a priced recursion, and the term structure of
spot discount rates $\mu_t(n)$ that sits between them.
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

The correct object is Ang and Liu’s equation (2):

$$
V_t = \sum_{s=1}^{\infty}
  E_t\Bigl[
    \exp\Bigl(-\sum_{k=0}^{s-1}\mu_{t+k}\Bigr)\,C_{t+s}
  \Bigr].
$$

Value is the expectation of a product. A VAR for the state $X_t$
supplies the joint law. From that VAR the package evaluates two
recursions — expected cash flows horizon by horizon, and the priced
strip at each horizon — and reads off the **spot discount rates**
$\mu_t(n)$ that make the usual two-step workflow (forecast, then
discount) exact inside the model.

## Four calls

```python
from varvaluation import (
    AngLiuModel,
    estimate_var,
    paper_state_spec,
    simulate_paper_state,
)

state, spec = simulate_paper_state(nobs=160, seed=11)
fit = estimate_var(state, spec)
model = AngLiuModel.from_var(fit)   # or ValuationModel.from_var(...)
X = fit.unconditional_mean() if hasattr(fit, "unconditional_mean") else state
# preferred path: build model with expected-return loadings, then
#   spots = model.spot_rates(X, n=30)
#   cf    = model.cashflow_expectation(X, n=30)
#   V     = model.value(X, C0)
```

The handbook walks the objects in order: the problem, the joint system,
the two recursions, the spot curve $\mu_t(n)$, and how to build $X_t$
from data.

## Roadmap

<div class="topic-cards">
<a href="guide/problem/"><span class="part">01</span><strong>The problem</strong><span>Why a flat rate is the wrong rate at every horizon but one.</span></a>
<a href="guide/system/"><span class="part">02</span><strong>One system</strong><span>Cash-flow growth and expected returns share one VAR for $X_t$.</span></a>
<a href="guide/curve/"><span class="part">03</span><strong>The two recursions</strong><span>Cash-flow recursion, priced recursion, spot rates $\mu_t(n)$.</span></a>
<a href="guide/state/"><span class="part">04</span><strong>Building the state</strong><span>What goes into $X_t$: growth, beta, premium, rates.</span></a>
<a href="guide/reproduce/"><span class="part">05</span><strong>Worked example</strong><span>Estimate, recurse, read the curve.</span></a>
<a href="guide/industries/"><span class="part">06</span><strong>Other portfolios</strong><span>Same state names, different universe.</span></a>
</div>

The formulas are [Ang and Liu (2004)](references.md#ang-liu-2004).
The residual-income map of [Ang and Liu (2001)](references.md#ang-liu-2001)
and [Feltham and Ohlson (1995)](references.md#feltham-ohlson-1995) is
an optional numerator. The package is the bench that runs the
recursions.
