# The idea

A valuation is a sum of future cash flows, each shrunk to today. Two things
enter every term: **what you expect to receive**, and **the rate at which you
shrink it**. Call the first the *numerator* and the second the *denominator*.

The Damodaran DCF you already know writes

$$
V_t = \sum_{j=1}^{\infty} \frac{\mathbb{E}_t[D_{t+j}]}{(1+r)^j}.
$$

Two assumptions are buried in that line. The denominator is **one** $r$ at
every horizon. The numerator is whatever cash-flow path you typed into the
spreadsheet, treated as if it were statistically independent of $r$.

When expected returns move, neither assumption survives. The right definition
of value is the expectation of a **product**,

$$
V_t = \sum_{j=1}^{\infty}
\mathbb{E}_t\!\left[
  D_{t+j}\,\exp\!\Bigl(-\sum_{i=1}^{j} r_{t+i}\Bigr)
\right].
$$

You cannot take $\mathbb{E}_t[D]$ and $\mathbb{E}_t[r]$ separately and then
divide. The joint distribution is the minimum required object. That is why a
VAR of cash-flow growth **and** expected-return states is the right tool: it
is one system that produces both forecasts, and their covariance, from the
same $\Phi$, $c$, and $\Sigma$.

## Two objects, two recursions

Write cash flows in growth form, $g_{t+i} = \log(C_{t+i}/C_{t+i-1})$. Then
each strip is an exponential of cumulated growth minus cumulated discount
rates. Under a Gaussian VAR those expectations have closed forms.

| Side | What it is | Recursion | Method |
|---|---|---|---|
| Numerator | $\mathbb{E}_t[C_{t+n}]/C_t$ | affine in $X_t$ | `cashflow_expectation` |
| Denominator | spot rate $\mu_t(n)$ | quadratic-Gaussian | `spot_rates` |

Ang and Liu (2004) derive **both**. Then, in the published application, they
set the numerator to $1$ at every horizon and report only the discount curve.
This library exposes the two choices as two methods:

- `model.perpetuity(X)` — their design. Cash flow held at one. All variation
  is the curve.
- `model.value(X, C)` — both recursions live. The numerator moves with $X_t$.

The [Valuation](valuation.md) page walks the numerator recursion line by
line. The [News](news.md) page is a different question (what moved last
period’s unexpected return), answered from the **same** fitted VAR.

## What you name, not where you put it

The cash-flow growth variable is whatever you pass as `spec.cashflow`. On Ken
French portfolios it is log dividend growth `g`. At the firm it is log ROE
`roe`. The engine never assumes “column 0 is $g$.” See [StateSpec](spec.md).
