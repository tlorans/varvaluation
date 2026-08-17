# 1. Introduction

Discounted-cash-flow practice writes value as a sum of expected cash
flows divided by one rate $r$, then attaches a Gordon terminal value
$C/(r-g)$ at a finite horizon. The construction is the workhorse of
corporate finance courses and of most applied models. It embeds two
claims. The discount rate is the same at every maturity. Cash flows
and discount rates may be forecast separately.

Neither claim survives once expected returns vary. Discount-rate
variation is the organising fact of empirical asset pricing
([Cochrane, 2011](../references.md#cochrane-2011)). The object that
remains well defined is the expectation of a *product*,

$$
V_t
  = \sum_{j=1}^{\infty}
    \mathbb{E}_t\!\left[
      C_{t+j}\,\exp\!\Bigl(-\sum_{i=1}^{j} r_{t+i}\Bigr)
    \right].
$$

The discount factor sits inside the expectation. Separating
$\mathbb{E}_t[C]$ from $\mathbb{E}_t[r]$ and dividing is legitimate
only if $r$ is deterministic. In general
$\mathbb{E}[XY]\ne\mathbb{E}[X]\,\mathbb{E}[Y]$. The covariance of
cumulated growth and cumulated expected returns enters the price
level, not merely a variance decomposition computed after the fact
([Ang and Liu, 2004](../references.md#ang-liu-2004)).

The identification problem is therefore joint. A forecast of cash
flows from one model and a forecast of expected returns from another
do not determine the product: they omit the covariance, they need not
share a horizon structure, and they can contradict each other. The
minimum statistical object is one law of motion for a state $X_t$
that contains both cash-flow growth and the variables that move
expected returns.

[Ang and Liu (2004)](../references.md#ang-liu-2004) give that law as a
Gaussian VAR(1) and the associated closed forms. When the one-period
expected return is affine in $X_t$, each strip of the price–cash-flow
ratio is exponential-affine. When expected return is quadratic (the
product of a moving beta and a moving premium), the strip is
exponential-quadratic and an $H(n)$ recursion appears. Gordon growth
is the degenerate case $\Phi=\Sigma=0$. The same paper replaces the
single WACC by a maturity-specific spot curve $\mu_t(n)$, so that a
two-step workflow (forecast cash flows, then discount) can be kept
while the rate is allowed to depend on horizon and on $X_t$.

A neighbouring question uses the same VAR. Unexpected returns decompose
into cash-flow news minus discount-rate news
([Campbell, 1991](../references.md#campbell-1991);
[Vuolteenaho, 2002](../references.md#vuolteenaho-2002)). Defining
cash-flow news as the residual of a discount-rate model absorbs every
misspecification of that model
([Chen, Da, and Zhao, 2013](../references.md#chen-da-zhao-2013)). The
direct construction takes cash-flow news from the cash-flow equation,
the same row of $\Phi$ that feeds the numerator recursion.

The content of $X_t$ is not free. Profitability is forecastable and
mean-reverts ([Fama and French, 2000](../references.md#ff-2000)). At
the firm, cash-flow news dominates return variance
([Vuolteenaho, 2002](../references.md#vuolteenaho-2002)). Expected
returns load on the short rate and on the consumption–wealth residual
$\mathit{cay}$, not on the dividend yield whose predictive power had
collapsed by 2000
([Fama and Schwert, 1977](../references.md#fama-schwert-1977);
[Lettau and Ludvigson, 2001](../references.md#lettau-ludvigson-2001);
[Goyal and Welch, 2003](../references.md#goyal-welch-2003)). Long-run
risk supplies a reason why the same state can drive both sides
([Bansal and Yaron, 2004](../references.md#bansal-yaron-2004);
[Croce, 2014](../references.md#croce-2014)).

This document occupies that niche in two ways. First, it states the
framework as a single argument: definition, VAR, two recursions, news,
and the limits of the construction. Second, it makes the argument
computable. The library `varvaluation` binds names to positions
(`StateSpec`), estimates the companion with overlapping Newey–West
pairs, and returns `spot_rates`, `perpetuity`, and
`news_decomposition` from one fitted object. Section 5 is not a
tutorial appended to a theory note. It is the illustration of
Sections 2–4 on a CRSP–Compustat panel: 2,673 firms,
$\Phi_{\mathit{roe},\mathit{roe}}=0.46$, and firm-level discount
curves that slope with $\beta_t$. Those numbers are the framework
speaking.

Section 2 states the joint system and the closed forms. Section 3
records how the parameters are measured. Section 4 treats news.
Section 5 computes the objects. Section 6 discusses what changes
relative to a constant-rate DCF and where estimation risk compounds.
Software installation and the public API sit after the argument,
because they implement it.
