<p class="part-kicker">Part 02 · Getting started</p>

# Why a product

<p class="you-will"><strong>You will.</strong> Write present value as the expectation of a product and keep the objects table next to you.</p>

You have already seen that a flat rate and a moving curve do not
price the same claim. The reason is not taste. Expected returns move
([Cochrane, 2011](../references.md#cochrane-2011)). Year one and
year ten then need different rates, and the well-defined object is
the expectation of a *product*.

Write $\mu_t$ for the one-period expected (log) return at date $t$,
and $\mathbb{E}_t$ for the average over outcomes using only
information known at $t$. Let $P_t$ be today’s ex-cash-flow price
and $C_{t+1}$ the cash flow paid next period. By definition

$$
e^{\mu_t}
  = \mathbb{E}_t\!\left[\frac{P_{t+1}+C_{t+1}}{P_t}\right].
$$

$\mu_t$ is known today. It is not the return that will be observed
tomorrow. Solve for $P_t$, replace $P_{t+1}$ by the same relation
dated $t+1$, and keep going. The result is

$$
V_t
  = \sum_{s=1}^{\infty}
    \mathbb{E}_t\!\left[
      \exp\!\Bigl(-\sum_{k=0}^{s-1} \mu_{t+k}\Bigr)\,C_{t+s}
    \right],
$$

which is equation (2) of [Ang and Liu (2004)](../references.md#ang-liu-2004).
The first factor inside the inner sum is $\mu_t$, known at $t$.
Separating $\mathbb{E}_t[C]$ from $\mathbb{E}_t[\mu]$ and dividing is
legitimate only if $\mu$ is deterministic. In general
$\mathbb{E}[XY]\ne\mathbb{E}[X]\,\mathbb{E}[Y]$. The covariance of
cumulated growth and cumulated expected returns enters the price
level, not merely a variance decomposition computed after the fact.

!!! note "In words — product, closed form, identification"
    A **product** here is cash flow times a path of discount factors.
    You cannot price it from two separate forecasts: you need their
    joint distribution, including the covariance. A **closed form** is
    a formula you evaluate (no simulation). **Identification** means:
    the numbers you feed the formula are enough to determine the
    price. A cash-flow model plus a separate expected-return model
    does not identify the product, because the covariance is missing,
    the horizons need not match, and the two forecasts can contradict
    each other.

The minimum statistical object is one law of motion for a state $X_t$
that contains both cash-flow growth and the variables that move
expected returns. A **vector autoregression** (VAR) is that law:
each variable is regressed on yesterday’s value of every variable.
[Part 03](system.md) writes it out. Write $\Phi$ for the matrix of
those slopes (persistence) and $\Sigma$ for the covariance of the
shocks. [Ang and Liu (2004)](../references.md#ang-liu-2004) take the
VAR to be Gaussian of order one and give the closed forms.

!!! note "In words — strip, spot curve, term structure"
    A **strip** is one horizon’s contribution to the price: the
    present value of the cash flow that arrives in year $n$, and
    nothing else. A **spot rate** $\mu_t(n)$ is the single number
    that, raised to $n$, discounts that expected cash flow correctly.
    The **term structure** (the *curve*) is the list
    $\mu_t(1),\mu_t(2),\ldots$, drawn as a line — the equity analogue
    of a bond yield curve. It can slope up, down, or be humped, and
    it moves with $X_t$.

Two facts about the *shape* of $\mu_t$ decide the shape of the
price.

- If the one-period expected return is **affine** in $X_t$ — a
  constant plus a linear function, $a+b'X$, no products — each strip
  of the price–cash-flow ratio is exponential-affine:
  $\exp(a(n)+b(n)'X_t)$.
- If expected return is **quadratic** (the product of a moving beta
  and a moving premium, $\beta_t\lambda_t$), the strip is
  exponential-quadratic,
  $\exp(a(n)+b(n)'X_t+X_t'H(n)X_t)$, and an $H(n)$ recursion
  appears. $H(n)$ is the matrix that multiplies the quadratic term
  at horizon $n$.

Constant $\mu$ and constant expected growth — their special case 1 —
nest the constant-growth formula often called Gordon (a fixed
growth rate, a fixed discount rate, an infinite tail). Setting
$\Phi=\Sigma=0$ is a further special case (no dynamics, no shocks),
not that case. The same paper, following
[Brennan (1997)](../references.md#brennan-1997), replaces a single
rate for every maturity by the spot curve $\mu_t(n)$: one rate per
horizon, so that a two-step workflow (forecast cash flows, then
discount) can be kept while the rate depends on horizon and on $X_t$.

A neighbouring question uses the same VAR. An *unexpected* return is
the part of the realized return that was not expected yesterday.
That surprise decomposes into **cash-flow news** minus
**discount-rate news**
([Campbell, 1991](../references.md#campbell-1991);
[Vuolteenaho, 2002](../references.md#vuolteenaho-2002)). News means a
*revision*: after a shock arrives, how much do you change your
forecast of future cash flows, or of future expected returns?
Defining cash-flow news as the residual of a discount-rate model
absorbs every misspecification of that model
([Chen and Zhao, 2009](../references.md#chen-zhao-2009);
[Chen, Da, and Zhao, 2013](../references.md#chen-da-zhao-2013)). The
direct construction takes cash-flow news from the cash-flow equation.

The content of $X_t$ is not free. Profitability is forecastable and
**mean-reverts** — when it sits above its long-run average it tends
to fall back
([Fama and French, 2000](../references.md#ff-2000)).
Expected-return instruments are contested. **In-sample** means: the
predictor works on the window used to fit it. **Out-of-sample**
means: it still works on later data that the fit did not see.
**Look-ahead** is a different sin: using later information to
construct a variable that is then treated as if it had been known
earlier. The short rate is a classical predictor
([Fama and Schwert, 1977](../references.md#fama-schwert-1977)).
The **dividend yield** (dividends over price) is weak out of sample
([Goyal and Welch, 2003](../references.md#goyal-welch-2003);
[Goyal and Welch, 2008](../references.md#goyal-welch-2008)), though
the present-value identity can still imply return predictability
([Cochrane, 2008](../references.md#cochrane-2008)).

Consumption–wealth $\mathit{cay}$ is a strong *in-sample* quarterly
predictor in
[Lettau and Ludvigson (2001)](../references.md#lettau-ludvigson-2001).
It is the residual from a cointegrating relation among consumption,
asset wealth, and labour income — the gap that should forecast
returns if those three series share a long-run trend. Whether it
survives look-ahead-free and out-of-sample tests is disputed.
**Long-run risk**
([Bansal and Yaron, 2004](../references.md#bansal-yaron-2004);
[Croce, 2014](../references.md#croce-2014)) is a structural reason
the same state *can* drive both cash flows and discount rates: a
slowly moving component of growth that a long-horizon investor
cares about. It is not estimated here.

**Residual income** — abnormal earnings
$(\mathrm{ROE}_{t+j}-k_{t+j})B_{t+j-1}$, book plus the present
value of earnings above a charge on book
([Ohlson, 1995](../references.md#ohlson-1995);
[Ang and Liu, 2001](../references.md#ang-liu-2001)) — is the
accounting companion that would price book. It is cited, not
implemented.

## What the library adds

The step-by-step formulas that build the price horizon by horizon
(the **recursions**), the spot curve, and Gordon as a nest are
[Ang and Liu (2004)](../references.md#ang-liu-2004). The residual-income
companion is cited, not implemented. The closed forms are not new.

What is not in those papers, and is the increment this handbook
uses as a bench:

1. **Named-state binding.** `StateSpec` makes the cash-flow row a
   name (`"roe"`, `"g"`), not “whatever sits in column 0.”
2. **A panel estimator** that forms yesterday-and-today pairs only
   inside the firm (`estimate_var_panel`). A firm is never lagged
   into another firm.
3. **Direct cash-flow news**, with the residual stored as a diagnostic
   ([Chen, Da, and Zhao, 2013](../references.md#chen-da-zhao-2013)).
4. **A callable implementation** (`ValuationModel`) of the 2004
   priced and cash-flow recursions.

**WRDS** is the academic vendor for US market and accounting data.
**CRSP** is the monthly stock-return file; **Compustat** is the annual
fundamentals file; a **permno** is CRSP’s permanent firm identifier.
[Three curves](walkthrough.md) runs those calls on a WRDS extract.
The prepared state has 2,673 firms. The *pooled companion* — one
$\Phi$ estimated on stacked lag pairs — uses the 80 longest
histories over March 2015–September 2019. Those are not the same
sample. The companion has **spectral radius** $0.995$: the largest
absolute eigenvalue of $\Phi$. If that number is $\ge 1$, the
unconditional mean does not exist and the library refuses to build
the model.

The market premium regression that supplies the linear and quadratic
pieces of $\mu_t$, written $(\xi,\Lambda)$, uses returns through
December 2024, after the September 2019 valuation
date — look-ahead, disclosed in [Estimation](estimate.md). The
illustration reports $\mu_t(n)$ and
$\mathbb{E}_t[\mathit{roe}_{t+n}]$. It does not report a present
value of those equities, because
$\mathit{roe}=\log(\mathrm{NI}/\mathrm{BE}_{\mathrm{lag}})$
(GAAP net income over lagged book equity) is a profitability
*level*, not log cash-flow growth, and not Vuolteenaho’s
$e_t=\log(1+X_t/B_{t-1})$ (clean-surplus earnings in return units).

[The joint system](system.md) states the VAR. [Estimation](estimate.md)
records staged measurement, including the seam between a market
premium regression and a firm VAR — the same staging as Ang and Liu
(2004, §III), not a single-equation identification of the product.
[What moved the return](news.md) treats news. [Firms](walkthrough.md)
runs the library. [For valuators](practice.md) says what you can take
from the curve when you already have a path.

## Objects and words

Every later section uses this table. A first-use box in the chapter
repeats the definition in context.

| Object | Meaning |
|---|---|
| $V_t$ | Present value at $t$ of the claim to future cash flows |
| $C_t$, $g_t$ | Cash flow, and $g_t=\log(C_t/C_{t-1})$ when the name is growth |
| $\mu_t$ | One-period expected return, known at $t$ |
| $\mu_t(n)$ | Spot discount rate for a cash flow $n$ periods ahead |
| $X_t$ | State vector: everything the VAR tracks |
| $\Phi$, $c$, $\Sigma$ | VAR companion (persistence), intercept, shock covariance |
| $\xi$, $\Lambda$, $\alpha$ | Linear, quadratic, and intercept pieces of $\mu_t=\alpha+\xi'X+X'\Lambda X$ |
| $H(n)$ | Quadratic coefficient of the priced strip at horizon $n$ |
| $\beta_t$, $\lambda_t$ | Conditional CAPM loading, and the market premium it multiplies |
| $\mathit{roe}$ | $\log(\mathrm{NI}/\mathrm{BE}_{\mathrm{lag}})$: a profitability *level* |
| $\mathit{cay}$ | Consumption–wealth cointegrating residual (or a FRED reconstruction) |
| $\mathit{bm}$ | Log book-to-market |
| Spectral radius $\rho(\Phi)$ | Largest $\lvert\text{eigenvalue}\rvert$ of $\Phi$; must be $<1$ |
| Companion | (1) a VAR($p$) rewritten as a taller VAR(1); (2) the fitted $\Phi$ on the 80-firm slice |
| Closed form | A formula you evaluate, not a simulation |
| Strip | One horizon’s contribution to the price |
| Term structure | The curve $\mu_t(1),\mu_t(2),\ldots$ |
| WACC | Single blended required return, all horizons |
| Gordon | $C/(r-g)$ when $r$ and $g$ are constant |
| Residual income | $(\mathrm{ROE}-k)\times$ lagged book; cited, not implemented |
| News | Revision in forecasts after a shock arrives |
| Look-ahead | Later data used to estimate something treated as known earlier |
| In- / out-of-sample | Fit and test on the same window / on a later window |
| Overlapping annual | Monthly pairs twelve months apart; adjacent pairs share eleven months |
| Newey–West | Standard errors honest about that overlap |
| Simple return | $(P_{t+1}+C_{t+1})/P_t-1$, not a log |
| WRDS / CRSP / Compustat / permno | Vendor / stock file / fundamentals file / firm id |
