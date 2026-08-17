# The problem

A price is expected cash flows, discounted. If the cash is certain — a Treasury zero — the discount rate is the yield on that zero. There is a different yield at each maturity. Nobody uses the one-year bill rate to discount a thirty-year principal.

Equity cash flows are not certain. The usual practice is still a single rate: the CAPM, or a conditional CAPM, applied to every horizon. That is a flat term structure. [Brennan (1997)](../references.md#brennan-1997) and [Ang and Liu (2004)](../references.md#ang-liu-2004) showed that it cannot be right once expected returns move. [Giacotto, Lin, and Zhao (2020)](../references.md#glz-2020) asked what the curve looks like for insurers, who hold long liabilities and have to pick a rate for each project.

## What a flat rate gets wrong

Write $V(\tau)_t$ for the time-$t$ price of a single cash flow that arrives in $\tau$ years. If a rate $\rho(\tau)_t$ exists,

$$
V(\tau)_t = e^{-\tau\rho(\tau)_t}\,\mathbb{E}_t[C_{t+\tau}].
$$

That is the definition of a zero-coupon equity yield. It is the equity analogue of a Treasury zero. The CAPM gives one number, $\mu_t = R_{f,t} + \beta_t\,\lambda_t$, and uses it at every $\tau$. Then $\rho(\tau)_t = \mu_t$ for all $\tau$. The curve is a horizontal line.

The paper's Fig. 1 is not a horizontal line. For the insurance industry as a whole, evaluated at the long-run mean of the state, the curve starts at 9.61%, rises to 10.23% at ten years, and falls to 8.99% at thirty. The unconditional CAPM sits at 11.74%. Using that one number overstates the long-run cost of capital by about 275 basis points.

Life insurers sit above property/casualty and health. Firms outside insurance sit higher still, because their average beta is 0.97 against 0.65 for insurers. The *shape* is similar. The *level* is not.

## Why the two sides have to be estimated together

The path form of the same price is

$$
V(\tau)_t = \mathbb{E}_t\Bigl[e^{-(\mu_t+\cdots+\mu_{t+\tau-1})}C_{t+\tau}\Bigr].
$$

Present value is the expectation of a **product**. The average of a product is not the product of the averages: $\mathbb{E}[XY]\ne\mathbb{E}[X]\,\mathbb{E}[Y]$. How future cash and future required returns move together is part of the price.

If you forecast cash in one model and the required return in another, three things go wrong.

1. The two forecasts need not share a horizon.
2. They can contradict each other (cash grows, the rate does not know).
3. You miss the covariance that sits in the product.

A vector autoregression is the smallest statistical object that produces both forecasts, and how they move together, from one list of variables $X_t$. That is the rest of this handbook.

## What we will compute

For an industry portfolio $X_t = (\mathrm{ROE}_t,\,g_t,\,\beta_t,\,\mathrm{MRP}_t)$:

- the **expected cash-flow path** from clean surplus,
- the **term-structure cost of capital** $\rho(1),\ldots,\rho(30)$,
- the same objects under a flat CAPM and a flat one-period CCAPM,
- the present value of a thirty-year $1 annuity under each rule.

Insurance first, so the numbers can be checked against the paper. Then any SIC range, with the same four names.

The next page writes the two readings of $X_t$ — cash, and the required return — and the VAR that holds them.
