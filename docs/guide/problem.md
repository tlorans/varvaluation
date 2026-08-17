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

Both are wrong once expected returns move. That is the whole paper
in one sentence.

## What a flat rate gets wrong

Write $V(\tau)_t$ for the price today of a single cash flow that
arrives in $\tau$ years. If a rate $\rho(\tau)_t$ exists,

$$
V(\tau)_t = e^{-\tau\,\rho(\tau)_t}\,E_t[C_{t+\tau}].
$$

That is a **zero-coupon equity yield** — the equity analogue of a
Treasury zero. Nobody discounts a thirty-year principal at the
one-year bill rate. Equity practice still does the equivalent: the
CAPM (or a conditional CAPM) supplies one number
$\mu_t = R_{f,t} + \beta_t\lambda_t$ and uses it at every maturity.
Then $\rho(\tau)_t = \mu_t$ for all $\tau$. The curve is a horizontal
line.

[Giacotto, Lin, and Zhao (2020)](../references.md#glz-2020) asked what
the curve actually looks like for insurers. At the long-run mean of
the state, the insurance industry curve starts near 9.6%, rises to
about 10.2% at ten years, and falls back toward 9% at thirty. The
unconditional CAPM sits near 11.7%. Using that one number overstates
the long-run cost of capital by roughly 275 basis points.

Life insurers sit above property/casualty and health. Firms outside
insurance sit higher still (average beta ≈ 0.97 versus ≈ 0.65 for
insurers). The *shape* is similar across groups. The *level* is not.

!!! note "Punchline"
    A flat CAPM rate is the right rate at **one** horizon — the
    one-period rate itself. At every other horizon it is an
    approximation, and the error compounds for long-duration claims.

## Why the two sides have to be estimated together

The path form of the same price is

$$
V(\tau)_t
  = E_t\Bigl[
      e^{-(\mu_t + \cdots + \mu_{t+\tau-1})}\,C_{t+\tau}
    \Bigr].
$$

Present value is the expectation of a **product**. The average of a
product is not the product of the averages:

$$
E[XY] \ne E[X]\,E[Y].
$$

How future cash and future required returns move together is part of
the price itself — not a variance decomposition computed after the
fact.

If you forecast cash in one model and the required return in another,
three things go wrong:

1. The two forecasts need not share a horizon.
2. They can contradict each other (cash grows; the rate does not know).
3. You miss the covariance that sits inside the product.

A **vector autoregression** is the smallest statistical object that
produces both forecasts, and how they move together, from one list of
variables $X_t$. That is the rest of this handbook.

## What this package computes

For an industry portfolio
$X_t = (\mathrm{ROE}_t,\, g_t,\, \beta_t,\, \mathrm{MRP}_t)$:

- the **expected cash-flow path** from clean surplus,
- the **term-structure cost of capital** $\rho(1),\ldots,\rho(30)$,
- the same objects under a flat CAPM and a flat one-period CCAPM,
- the present value of a thirty-year $1 annuity under each rule.

Insurance first, so the numbers can be checked against the paper.
Then any SIC range, with the same four names.

The next page writes the two readings of $X_t$ — cash, and the
required return — and the VAR that holds them.
