# The problem

Asset pricing is the expectation of a *product*. That is the whole subject, once you write it down carefully. The product is a cash flow times a path of discount factors. You cannot replace the expectation of that product by a ratio of two separate forecasts. The extra term is a covariance, and it sits in the *price*, not in a variance table you compute afterwards.

This page writes the product and opens the covariance. The next page puts both sides into one VAR, which is the only statistical object that can produce the covariance rather than set it to zero.

```mermaid
flowchart LR
  A["1 · Product"] --> B["2 · Covariance"] --> C["3 · One VAR"]
```

---

## Value is the expectation of a product

You already know the workhorse formula used in practice:

$$
V_t = \sum_{j=1}^{\infty} \frac{E_t[C_{t+j}]}{(1+r)^j}.
$$

$V_t$ is the value of the claim today. $C_{t+j}$ is the cash flow $j$ periods ahead. $E_t$ is the expectation given what you know at date $t$. And $r$ is one constant discount rate, used at every horizon.

The factor $1/(1+r)^j$ has been taken *outside* the expectation. That step is legitimate only if the discount rate is known in advance (deterministic). Once expected returns move, it is an error.

Start instead from the definition of the one-period expected return $\mu_t$. Let $P_t$ be the ex-dividend price. Then

$$
e^{\mu_t}
  = E_t\!\left[\frac{P_{t+1}+C_{t+1}}{P_t}\right].
$$

$\mu_t$ is known today. Future $\mu_{t+1},\mu_{t+2},\ldots$ are random. Iterate the definition forward and you get the multi-period product identity ([Ang and Liu, 2004](../references.md#ang-liu-2004), eq. 2):

$$
V_t
  = \sum_{s=1}^{\infty}
    E_t\!\left[
      \exp\!\Bigl(-\sum_{k=0}^{s-1} \mu_{t+k}\Bigr)\,C_{t+s}
    \right].
$$

The object inside the expectation is a *product*: a cash flow multiplied by a sequence of one-period discount factors $e^{-\mu}$. Replacing $E[\text{product}]$ by a ratio of two separate forecasts leaves an extra term. That replacement is a first-order error.

```mermaid
flowchart TB
  subgraph flat ["Flat DCF"]
    F["V = E[C] / (1+r)ⁿ<br/>discount factor outside"]
  end
  subgraph prod ["Product identity"]
    A["V = E[ e<sup>−∑μ</sup> · C ]<br/>product stays inside"]
  end
  flat -->|"r moves → error"| prod
```

The constant-rate formula replaces $E[\text{product}]$ by a ratio of expectations. Once expected returns move, that replacement is an error.

---

## The covariance term {#the-covariance-term}

Write cash flows in growth form. Define cash-flow growth as the log change

$$
g_{t+i} = \log\bigl(C_{t+i}/C_{t+i-1}\bigr).
$$

Then the cash flow $n$ periods ahead is just today’s cash flow times the exponential of the sum of those growth rates:

$$
C_{t+n} = C_t\,\exp\!\Bigl(\sum_{i=1}^{n} g_{t+i}\Bigr).
$$

A *strip* is the contribution of a single horizon $n$ to the price-cash-flow ratio. Substitute the growth form into the product identity and that contribution is proportional to

$$
E_t\!\left[
  \exp\!\Bigl(\sum_{i=1}^{n}(g_{t+i}-\mu_{t+i})\Bigr)
\right].
$$

Call the sum inside the exponential $S_n = \sum_{i=1}^{n}(g_{t+i}-\mu_{t+i})$. The strip is $E_t[e^{S_n}]$.

Now assume the shocks that drive $g$ and $\mu$ are jointly normal. Then $S_n$, being a linear combination of those shocks, is also normal. For a normal random variable $S$,

$$
E[e^{S}] = \exp\!\Bigl( E[S] + \tfrac12\mathrm{Var}(S) \Bigr).
$$

Applied conditionally at date $t$,

$$
E_t[e^{S_n}]
  = \exp\!\Bigl(
      E_t[S_n] + \tfrac12\mathrm{Var}_t[S_n]
    \Bigr).
$$

Open the variance. Write $S_n = \sum g - \sum \mu$. The variance of a difference is

$$
\mathrm{Var}_t[S_n]
  = \mathrm{Var}_t\Bigl[\sum g\Bigr]
  + \mathrm{Var}_t\Bigl[\sum \mu\Bigr]
  - 2\,\mathrm{Cov}_t\Bigl[\sum g,\;\sum \mu\Bigr].
$$

Four pieces therefore enter the *level* of the price.


| Term | Effect on value |
|---|---|
| $E_t[\sum g]$ | point-forecast growth (the usual DCF part) |
| $\tfrac12\mathrm{Var}(\sum g)$ | growth uncertainty *raises* value (convexity of the exponential) |
| $\tfrac12\mathrm{Var}(\sum \mu)$ | discount-rate uncertainty *raises* value |
| $-2\,\mathrm{Cov}(\sum g,\sum \mu)$ | the economically important one |

If good news about growth arrives together with *higher* expected returns (the usual aggregate pattern), then $\mathrm{Cov}>0$, the $-2\,\mathrm{Cov}$ term is negative, and value is *lower* than any DCF that ignores the interaction.

```mermaid
flowchart LR
  G["∑g growth"] --- Cov["Cov(∑g, ∑μ) > 0"]
  M["∑μ discount"] --- Cov
  Cov -->|"−2 Cov"| P["Price level ↓"]
```

The covariance shifts the level of the price. A model that forecasts cash and discount rates in separate drawers has already set it to zero.

---

## One system, or the covariance is gone

Forecast cash in one model and the required return in another and three things go wrong at once. The two forecasts need not share a horizon. They can contradict each other. And there is nowhere for $\mathrm{Cov}(\sum g,\sum \mu)$ to live.

A *vector autoregression* is a system of regressions in which every variable is explained by lags of every variable in the list. Put cash-flow growth and the variables that move expected returns into the same state $X_t$, and one shock covariance matrix $\Sigma$ generates the joint surprises while one companion matrix $\Phi$ carries the cross-forecasts. That is the next page.

---

## What a flat rate gets wrong

Even given the right joint model, practice often collapses the curve to one number $\mu_t$ used at every maturity. Write $V_t(n)$ for the strip at horizon $n$. A *spot rate* $\mu_t(n)$ is defined by

$$
V_t(n)
  = \frac{E_t[C_{t+n}]}{\exp\bigl(n\,\mu_t(n)\bigr)}.
$$

In words: $\mu_t(n)$ is the constant rate that, applied over $n$ periods, recovers the correct strip value from expected cash alone. A *flat* rule sets $\mu_t(n)=\mu_t(1)$ for all $n$. The curve is not flat. At short horizons the market risk premium dominates. At long horizons mean reversion in rates and betas matters. Using a constant rate produces large misvaluations.

Mean reversion in the expected return already produces a non-flat curve.

![Mean reversion in expected returns](../assets/figures/mean_reversion.png)

The same synthetic state (seed 7) is used on every page of this course. Build a model, read the spot curve, and compare a 15-year unit annuity under the curve versus under the flat rate $\mu_t(1)$.

```python
import numpy as np
from varvaluation import ExpectedReturnSpec, ValuationModel, estimate_var
from varvaluation.news import simulate_return_var

df, spec = simulate_return_var(nobs=400, seed=7)
fit = estimate_var(df, spec)
xi, Lambda = ExpectedReturnSpec(rate="ret", beta="g", premium=()).xi_lambda(
    spec, {"b0": 0.01}
)
model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.04)
X = fit.X_lag[-1]

n = 15
rates = model.spot_rates(X, n=n)          # μ_t(1), …, μ_t(15)
mat = np.arange(1, n + 1)
curve_pv = float(np.exp(-mat * rates).sum())
flat_pv  = float(np.exp(-mat * rates[0]).sum())
gap = (flat_pv - curve_pv) / curve_pv

print(f"μ_t(1)   = {100 * rates[0]:.2f}%")
print(f"μ_t(15)  = {100 * rates[-1]:.2f}%")
print(f"flat vs curve = {100 * gap:+.1f}%")
```

```text
μ_t(1)   = 2.37%
μ_t(15)  = 4.19%
flat vs curve = +12.8%
```

![Flat versus curve discount factors](../assets/figures/flat_vs_curve_factors.svg)

The shaded region is the mispricing that appears when the product identity is replaced by a ratio of expectations. Year one wants 2.37%. Year fifteen wants 4.19%. A single rate is a flat line through that gap, and on this state it overvalues the annuity by 12.8%. The next page estimates the VAR that produced these rates. The page after that builds the two recursions that produced the curve.

You can also run the isolated script:

```text
python examples/flat_vs_curve.py
```

---

## Four objects from the same matrices

Given a fitted VAR for $X_t$ and a map from the state into the one-period expected return

$$
\mu_t = \alpha + \xi'X_t + X_t'\Lambda X_t,
$$

the rest of the course computes four objects from the same matrices. $\alpha$ is a constant, $\xi$ is a vector of linear loadings, and $\Lambda$ is a matrix of quadratic loadings. The cash-flow recursion produces $E_t[C_{t+n}]/C_t$. The priced recursion produces each strip of the price-cash-flow ratio. Their ratio is the spot curve $\mu_t(1),\ldots,\mu_t(N)$. The present value is the sum of those strips.

All four objects share the same $(\Phi,c,\Sigma)$. The covariance term is estimated once and enters both recursions. That is why both sides of the product sit in one system.
