# Discounting cash flows when expected returns move

An exposition of the joint VAR, implemented in `varvaluation`

!!! abstract "Abstract"

    Most of the movement in the stock market is not news about cash
    flows. It is news about the rates at which those cash flows are
    discounted. Almost all variation in the market’s price–dividend
    ratio is variation in expected returns
    ([Cochrane, 2011](references.md#cochrane-2011), restating
    [Campbell and Shiller, 1988](references.md#campbell-shiller-1988)).
    At the firm the decomposition flips: for a typical stock,
    cash-flow-news variance is more than twice expected-return-news
    variance ([Vuolteenaho, 2002](references.md#vuolteenaho-2002)).
    Profitability itself mean-reverts
    ([Fama and French, 2000](references.md#ff-2000)). Since 2012 the
    near-term dividend on the index has been a traded claim
    ([van Binsbergen, Brandt, and Koijen, 2012](references.md#vbbk-2012)).
    The equity term structure is a measured object.

    Present value is then the expectation of a product: each cash
    flow times a path of one-period expected returns
    ([Ang and Liu, 2004](references.md#ang-liu-2004), eq. 2). A
    constant-rate DCF forecasts cash flows, divides them by one $r$,
    and calls the sum a value. Those calculations agree only when
    expected returns do not move. This document is an exposition of
    the product and a named-state implementation in Python. It does
    not derive a new closed form. What is not in the 2004 paper is
    `StateSpec`, a panel VAR that forms lag pairs only inside the
    firm, and cash-flow news taken from the cash-flow equation rather
    than from the residual
    ([Chen, Da, and Zhao, 2013](references.md#chen-da-zhao-2013);
    [Chen and Zhao, 2009](references.md#chen-zhao-2009)).

    Section 5 is a computational illustration on a short
    CRSP–Compustat window, not an empirical contribution. It reports
    the discount *curve* and a mean-reverting profitability path at
    three permnos. It does not report a present value of those firms:
    the cash-flow slot is $\log(\mathrm{NI}/\mathrm{BE}_{\mathrm{lag}})$,
    a profitability *level*, not log dividend growth.

**Keywords.** discount rates; cash-flow news; vector autoregression;
quadratic-Gaussian valuation; time-varying expected returns

---

## Why this field is worth reading

Three facts, all measured, rearrange valuation.

1. **The market moves on rates.** The dividend yield forecasts
   returns more reliably than it forecasts dividend growth
   ([Campbell and Shiller, 1988](references.md#campbell-shiller-1988)).
   If it does not forecast growth, the present-value identity says it
   must forecast returns
   ([Cochrane, 2008](references.md#cochrane-2008)). By 2011 the
   stronger reading was standard: price–dividend variation is
   discount-rate variation
   ([Cochrane, 2011](references.md#cochrane-2011)).
2. **The firm moves on cash flows.** Apply the same return identity
   name by name and the weights reverse
   ([Vuolteenaho, 2002](references.md#vuolteenaho-2002)). Aggregation
   is not a detail. A high-ROE name is also, on average, on its way
   back toward the pack
   ([Fama and French, 2000](references.md#ff-2000)).
3. **The curve is no longer a metaphor.** Put–call parity on index
   options isolates the claim to next year’s dividend
   ([van Binsbergen, Brandt, and Koijen, 2012](references.md#vbbk-2012);
   [van Binsbergen and Koijen, 2017](references.md#vbk-2017)).
   Near-term dividend claims do not earn the same premium as the
   index. Later work has debated the slope. That the object *exists*
   is enough: equity has a term structure, the way bonds do.

A spreadsheet that picks one $r$ and a terminal $g$ is then answering
a different question from the one the data pose. [Ang and Liu
(2004)](references.md#ang-liu-2004), following
[Brennan (1997)](references.md#brennan-1997), keep the two-step
workflow — forecast cash flows, then discount — and replace the
single rate by a curve $\mu_t(n)$ that mean-reverts with the state.
This site is that argument, with a library attached.

Predictors are contested. The dividend yield is weak out of sample
([Goyal and Welch, 2008](references.md#goyal-welch-2008)).
$\mathit{cay}$ is a strong *in-sample* quarterly predictor
([Lettau and Ludvigson, 2001](references.md#lettau-ludvigson-2001)).
The field is honest about both. Section 5 does not add a fourth fact.
It shows the machinery on a short firm extract.

## Organisation

Symbols and first-use words sit in
[Section 1, Objects and words](guide/introduction.md#objects-and-words).

| Section | Content |
|---|---|
| [1. Introduction](guide/introduction.md) | The facts, the product, the 2004 law, and what this document adds |
| [2. Framework](guide/system.md) | The joint VAR, the two recursions, and the content of $X_t$ |
| [3. Estimation](guide/estimate.md) | Staged measurement of $(\Phi,c,\Sigma,\xi,\Lambda)$ |
| [4. Return news](guide/news.md) | Direct cash-flow news on the same companion |
| [5. Illustration](guide/walkthrough.md) | Software demonstration on a short firm panel |
| [6. Discussion](guide/practice.md) | What a valuator can take, and what this sample cannot show |
| [Software](install.md) | Installation, API, and data extras |
| [References](references.md) | Bibliography |

![Firm spot curves](assets/figures/firm_spot_curves.png)
<p class="figure-caption"><strong>Figure 1.</strong> Spot discount rates $\mu_t(n)$ at 30 September 2019 for three CRSP permnos in the 80-firm companion of Section 5. The low-beta name slopes up; the high-beta names start high and fade. These curves are the <em>denominator</em>, not firm values. Twelve-month rolling betas.</p>
