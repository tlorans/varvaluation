# The problem

You already know the workhorse formula of every valuation course:

$$
V_t = \sum_{j=1}^{\infty} \frac{E_t[C_{t+j}]}{(1+r)^j}.
$$

One rate $r$ (a WACC, a CAPM cost of equity) discounts every horizon.
A Gordon terminal value $C/(r-g)$ is bolted on at the end. Two
assumptions are buried inside that line:

1. **One rate for all horizons.** Year 1 and year 30 use the same $r$.
2. **Cash flows and discount rates are independent.** The discount
   factor slides out of the expectation: $E[XY] = E[X]\,E[Y]$.

Both are wrong once expected returns move.

## The correct definition

[Ang and Liu (2004)](../references.md#ang-liu-2004) start from the
definition of the one-period expected (log) return $\mu_t$:

$$
e^{\mu_t}
  = E_t\!\left[\frac{P_{t+1}+C_{t+1}}{P_t}\right].
$$

$\mu_t$ is known today. Iterate the identity forward. Value is the
expectation of a **product**:

$$
V_t
  = \sum_{s=1}^{\infty}
    E_t\!\left[
      \exp\!\Bigl(-\sum_{k=0}^{s-1} \mu_{t+k}\Bigr)\,C_{t+s}
    \right].
$$

That is their equation (2). The average of a product is not the product
of the averages:

$$
E[XY] \ne E[X]\,E[Y].
$$

How future cash and future required returns move together is part of
the price itself.

!!! note "Punchline"
    Damodaran’s formula pulls the discount factor out of the
    expectation. That is legitimate only if $\mu$ is deterministic.
    Once expected returns move, you need the joint distribution.

## What a flat rate gets wrong

Write $V_t(n)$ for the contribution of horizon $n$ to value — the
**strip**. If a single spot rate $\mu_t(n)$ exists for that horizon,

$$
V_t(n)
  = \frac{E_t[C_{t+n}]}{\exp\bigl(n\,\mu_t(n)\bigr)}.
$$

That is the equity analogue of a Treasury zero. The usual practice
still takes one CAPM number $\mu_t = r_t + \beta_t\lambda_t$ and uses
it at every maturity: $\mu_t(n) = \mu_t$ for all $n$. The curve is a
horizontal line.

Ang and Liu show that the curve is not flat. At short horizons it is
driven mainly by the market risk premium; at long horizons by the risk-
free rate and by time-varying betas. Using a constant rate produces
large misvaluations — in their portfolio data, often more than 15% on
a unit perpetuity, and much larger in the worst industries.

## Why the two sides have to be estimated together

If you forecast cash in one model and the required return in another,
three things go wrong:

1. The two forecasts need not share a horizon.
2. They can contradict each other (cash grows; the rate does not know).
3. You miss the covariance that sits inside the product.

A **vector autoregression** for a state $X_t$ that contains both
cash-flow growth and the variables that move expected returns is the
smallest statistical object that produces both forecasts, and how they
move together, from one list of variables. That is the rest of this
handbook.

## What we will compute

Given a fitted VAR for $X_t$ and a one-period expected return
$\mu_t = \alpha + \xi'X_t + X_t'\Lambda X_t$:

- the **cash-flow recursion** — $E_t[C_{t+n}]/C_t$ horizon by horizon,
- the **priced recursion** — each strip of the price–cash-flow ratio,
- the **spot curve** $\mu_t(1),\ldots,\mu_t(N)$ that reconciles them,
- the **present value** as the sum of those strips (plus a tail at the
  terminal spot, not a hand-set Gordon pair).

The next page writes the VAR and the two sides of $X_t$.
