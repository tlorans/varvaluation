# Discounting cash flows when expected returns move

A joint VAR framework, implemented in `varvaluation`

!!! abstract "Abstract"

    Standard discounted-cash-flow practice prices a claim as a sequence
    of expected cash flows divided by a constant rate. That construction
    is valid only if expected returns are deterministic. Once they move,
    value is the conditional expectation of a product: future cash flows
    times a path of stochastic discount rates. The product is identified
    only from the joint law of growth and expected returns
    ([Ang and Liu, 2004](references.md#ang-liu-2004)). This document
    states that law as a Gaussian vector autoregression of a named state
    $X_t$, derives the two closed-form recursions (an affine cash-flow
    forecast and a quadratic-Gaussian discount curve), and defines
    cash-flow news as the revision in the cash-flow equation rather than
    as the residual of a return identity
    ([Campbell, 1991](references.md#campbell-1991);
    [Chen, Da, and Zhao, 2013](references.md#chen-da-zhao-2013)).
    The Python library `varvaluation` is the operational form of the
    same argument. Section 5 runs it on a CRSP–Compustat firm panel,
    so that each object defined in the text appears as a number at
    named permnos.

**Keywords.** discount rates; cash-flow news; vector autoregression;
quadratic-Gaussian valuation; time-varying expected returns; present
value

---

## Organisation

The document is a paper on the framework. The package is the
illustration, not the subject.

| Section | Content |
|---|---|
| [1. Introduction](guide/introduction.md) | Why a constant-rate DCF is the wrong object once expected returns move |
| [2. Framework](guide/system.md) | The joint VAR, the two recursions, and the content of $X_t$ |
| [3. Estimation](guide/estimate.md) | How $(\Phi,c,\Sigma,\xi,\Lambda)$ are measured |
| [4. Return news](guide/news.md) | The same VAR, a different question |
| [5. Illustration](guide/walkthrough.md) | The framework computed in `varvaluation` on CRSP–Compustat firms |
| [6. Discussion](guide/practice.md) | What changes relative to a textbook DCF, and what remains fragile |
| [Software](install.md) | Installation, API, and data extras |
| [References](references.md) | Bibliography |

![Firm spot curves](assets/figures/firm_spot_curves.png)
<p class="figure-caption"><strong>Figure 1.</strong> Spot discount rates $\mu_t(n)$ at 30 September 2019 for three CRSP permnos. The low-beta name slopes up; the high-beta names start high and fade. The curve is the denominator of the present value. Source: Section 5.</p>
