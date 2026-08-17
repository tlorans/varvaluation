# 1. Introduction

Discounted-cash-flow practice writes value as a sum of expected cash
flows divided by one rate $r$, then attaches a Gordon terminal value
$C/(r-g)$ at a finite horizon. The construction embeds two claims.
The discount rate is the same at every maturity. Cash flows and
discount rates may be forecast separately.

Neither claim survives once expected returns vary. Discount-rate
variation is the organising fact of empirical asset pricing
([Cochrane, 2011](../references.md#cochrane-2011)). The object that
remains well defined is the expectation of a *product*. Iterating
$e^{\mu_t}=\mathbb{E}_t[(P_{t+1}+C_{t+1})/P_t]$ gives

$$
V_t
  = \sum_{s=1}^{\infty}
    \mathbb{E}_t\!\left[
      \exp\!\Bigl(-\sum_{k=0}^{s-1} \mu_{t+k}\Bigr)\,C_{t+s}
    \right],
$$

which is equation (2) of [Ang and Liu (2004)](../references.md#ang-liu-2004).
The first factor in the inner sum is $\mu_t$, known at $t$, not a
realized return $r_{t+1}$. Separating $\mathbb{E}_t[C]$ from
$\mathbb{E}_t[\mu]$ and dividing is legitimate only if $\mu$ is
deterministic. In general $\mathbb{E}[XY]\ne\mathbb{E}[X]\,\mathbb{E}[Y]$.
The covariance of cumulated growth and cumulated expected returns
enters the price level, not merely a variance decomposition computed
after the fact.

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
exponential-quadratic and an $H(n)$ recursion appears. Constant
$\mu$ and constant expected growth — their special case 1 — nest the
Gordon model; $\Phi=\Sigma=0$ is a further degeneracy, not that case.
The same paper, following [Brennan (1997)](../references.md#brennan-1997),
replaces the single WACC by a maturity-specific spot curve $\mu_t(n)$,
so that a two-step workflow (forecast cash flows, then discount) can
be kept while the rate depends on horizon and on $X_t$.

A neighbouring question uses the same VAR. Unexpected returns decompose
into cash-flow news minus discount-rate news
([Campbell, 1991](../references.md#campbell-1991);
[Vuolteenaho, 2002](../references.md#vuolteenaho-2002)). Defining
cash-flow news as the residual of a discount-rate model absorbs every
misspecification of that model
([Chen and Zhao, 2009](../references.md#chen-zhao-2009);
[Chen, Da, and Zhao, 2013](../references.md#chen-da-zhao-2013)). The
direct construction takes cash-flow news from the cash-flow equation.

The content of $X_t$ is not free. Profitability is forecastable and
mean-reverts ([Fama and French, 2000](../references.md#ff-2000)).
Expected-return instruments are contested. The short rate is a
classical predictor ([Fama and Schwert, 1977](../references.md#fama-schwert-1977)).
The dividend yield is weak out of sample
([Goyal and Welch, 2003](../references.md#goyal-welch-2003);
[Goyal and Welch, 2008](../references.md#goyal-welch-2008)), though
the present-value identity can still imply return predictability
([Cochrane, 2008](../references.md#cochrane-2008)). Consumption–wealth
$\mathit{cay}$ is a strong *in-sample* quarterly predictor in
[Lettau and Ludvigson (2001)](../references.md#lettau-ludvigson-2001);
whether it survives look-ahead-free and out-of-sample tests is
disputed. Long-run risk
([Bansal and Yaron, 2004](../references.md#bansal-yaron-2004);
[Croce, 2014](../references.md#croce-2014)) is a structural reason
the same state *can* drive both sides. It is not estimated here.

## What this document is

This is an exposition and a library, not a new closed form. The
recursions, the spot curve, and Gordon as a nest are
[Ang and Liu (2004)](../references.md#ang-liu-2004). The residual-income
companion that would price book and abnormal earnings is
[Ang and Liu (2001)](../references.md#ang-liu-2001) and
[Ohlson (1995)](../references.md#ohlson-1995); it is cited, not
implemented.

What is not in those papers, and is the increment this site claims:

1. **Named-state binding.** `StateSpec` makes the cash-flow row a
   name, not column 0.
2. **A panel estimator** that forms overlapping pairs only inside
   the firm (`estimate_var_panel`).
3. **Direct cash-flow news**, with the residual stored as a diagnostic
   ([Chen, Da, and Zhao, 2013](../references.md#chen-da-zhao-2013)).
4. **A callable implementation** (`ValuationModel`) of the 2004
   priced and cash-flow recursions.

Section 5 is a software demonstration on a WRDS extract: a prepared
state of 2,673 firms, and a *pooled companion on the 80 longest
histories* over March 2015–September 2019. Those are not the same
sample. The companion has spectral radius $0.995$. The market premium
regression that supplies $(\xi,\Lambda)$ uses returns through December
2024, after the September 2019 valuation date — look-ahead, disclosed
in Section 3. The illustration reports $\mu_t(n)$ and
$\mathbb{E}_t[\mathit{roe}_{t+n}]$. It does not report a present
value of those equities, because $\mathit{roe}=\log(\mathrm{NI}/\mathrm{BE}_{\mathrm{lag}})$
is not log cash-flow growth and is not Vuolteenaho’s
$e_t=\log(1+X_t/B_{t-1})$.

Section 2 states the joint system. Section 3 records staged
estimation, including the seam between a market premium regression
and a firm VAR — the same staging as Ang and Liu (2004, §III), not
a single-equation identification of the product. Section 4 treats
news. Section 5 runs the library. Section 6 says what a valuator
can take from the curve, and what this sample cannot show.
