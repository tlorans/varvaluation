<div class="hero" markdown>

<p class="hero-kicker">One joint VAR · product identity · spot curve</p>

# How to discount cash flows when expected returns move

<p class="hero-lead">
Value is the expectation of a <strong>product</strong>.
A product has a <strong>covariance</strong>, and that covariance
sits in the price. Cash flows and discount rates must therefore
come from the <strong>same</strong> system, a VAR for the state
$X_t$. Bring a Polars state frame; the package returns the spot
curve and present value as Polars frames.
</p>

[Core idea](guide/core.md){ .md-button .md-button--primary }
[Install](install.md){ .md-button }

</div>

## Beginner guide

The six short pages below explain, from first principles, how cash-flow dynamics and expected returns are modelled and how both are linked to the state variable \(X_t\).

<div class="topic-cards">
<a href="guide/core/"><span class="part">1</span><strong>Core idea</strong><span>Value is the expectation of a product. Separate forecasts miss the covariance.</span></a>
<a href="guide/state-variable/"><span class="part">2</span><strong>The state variable</strong><span>What sits in \(X_t\) and why both cash-flow growth and return predictors must be there.</span></a>
<a href="guide/var-dynamics/"><span class="part">3</span><strong>The VAR dynamics</strong><span>\(X_{t+1}=c+\Phi X_t+u_{t+1}\). One law of motion for everything.</span></a>
<a href="guide/cash-flow-dynamics/"><span class="part">4</span><strong>Cash-flow dynamics</strong><span>How expected future cash flows are obtained from the same \(X_t\).</span></a>
<a href="guide/expected-returns/"><span class="part">5</span><strong>Expected returns</strong><span>\(\mu_t\) as an (affine or quadratic) function of \(X_t\) and the resulting spot curve.</span></a>
<a href="guide/putting-together/"><span class="part">6</span><strong>Putting it together</strong><span>Why the joint system is required and how the package evaluates the product.</span></a>
<a href="guide/numerical/"><span class="part">7</span><strong>A numerical walkthrough</strong><span>Two states, every n=1 and n=2 term in numpy, then the βλ product that produces H(n).</span></a>
</div>

## Estimator path

```python
from varvaluation import (
    ExpectedReturnSpec, StateSpec, ValuationModel,
    estimate_var, simulate_state,
)

state, spec = simulate_state(nobs=400, seed=7)  # or your Polars frame
fit = estimate_var(state, spec)
xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(
    spec, {"b0": 0.01}
)
model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.04)
curve = model.spot_curve(fit.X_lag[-1], n=15)   # Polars DataFrame
```

Firm panel: set `spec.group`, call `estimate_var_panel`, then `model.curve_frame(..., id_cols=("firm",))`.

## On the synthetic state

```text
$ python examples/quickstart.py
```

| Maturity $n$ | $\mu_t(n)$ (%) | $E_t[C_{t+n}]/C_t$ |
|---:|---:|---:|
| 1 | 2.37 | 0.999 |
| 5 | 3.78 | 1.008 |
| 10 | 4.09 | 1.021 |
| 15 | 4.19 | 1.034 |

```text
spectral radius : 0.409
strip-sum value : 24.07
flat PV vs curve: +12.8%
```

Closed-form recursions follow [Ang and Liu (2004)](references.md#ang-liu-2004). The empirical check (paper sample, December 2000 curve, post-2000 extension) is [Ang and Liu (2004)](guide/angliu.md).
