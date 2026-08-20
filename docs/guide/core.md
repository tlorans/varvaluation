# Core idea

The core idea of this package is to value something (a stock, a portfolio, a firm) by treating its present value as the **expectation of a product**: future cash flows multiplied by a path of discount factors that come from moving expected returns.

You cannot compute that product correctly by forecasting cash flows in one model and expected returns in another separate model. The two must share **one joint law of motion**, because the price depends on how they move *together* (including their covariance). That joint law is a simple Vector Autoregression (VAR) on a state vector called \(X_t\).

!!! note "In one sentence"
    Value is \(E[\text{discount path} \times \text{cash flow}]\). Separate forecasts of the two pieces miss the covariance that sits inside the price level. One VAR on a common state \(X_t\) is the minimal object that keeps the covariance.

The rest of this beginner guide walks through the pieces one by one:

1. What the state variable \(X_t\) is.
2. How its dynamics are written (the VAR).
3. How cash-flow growth is modelled and linked to \(X_t\).
4. How expected returns are modelled and linked to \(X_t\).
5. Why the joint system is required for a correct present value.

Everything is exact inside the Gaussian VAR class used by [Ang and Liu (2004)](../references.md#ang-liu-2004). The package simply evaluates the closed-form recursions that paper derived. [A numerical walkthrough](numerical.md) does both recursions on a 2×2 toy, term by term, in numpy.
