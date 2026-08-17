# Discounting cash flows when expected returns move

An exposition of the joint VAR, implemented in `varvaluation`

!!! abstract "Abstract"

    If next year’s cash flow and the cash flow in year ten should not
    be discounted at the same rate, a constant-rate DCF is not
    computing present value. Present value is the expectation of a
    product: each cash flow times a path of one-period expected
    returns ([Ang and Liu, 2004](references.md#ang-liu-2004), eq. 2).
    This document is an exposition of that idea and a named-state
    implementation in Python. It does not derive a new closed form.

    Section 5 is a software demonstration on a short CRSP–Compustat
    window. It reports the discount *curve* at three firms, not a
    present value of those firms.

**Keywords.** discount rates; cash-flow news; vector autoregression;
quadratic-Gaussian valuation; time-varying expected returns

---

The picture is the argument. Three firms, one date, three curves.
A single rate is a flat line through this figure.

![Firm spot curves](assets/figures/firm_spot_curves.png)
<p class="figure-caption"><strong>Figure 1.</strong> Spot discount rates $\mu_t(n)$ at 30 September 2019 for three CRSP permnos. The low-beta name slopes up; the high-beta names start high and fade. These curves are the <em>denominator</em>, not firm values. Source: Section 5.</p>

The rest of the site says why the curve has that shape, how it is
estimated, and what a valuator can do with it. The closed forms are
[Ang and Liu (2004)](references.md#ang-liu-2004). The package is the
vehicle of Section 5. Words and symbols are collected in
[Section 1](guide/introduction.md#objects-and-words).

| Section | Content |
|---|---|
| [1. Introduction](guide/introduction.md) | Why one rate is the wrong tool |
| [2. Framework](guide/system.md) | The joint VAR and the two recursions |
| [3. Estimation](guide/estimate.md) | How the pieces are measured |
| [4. Return news](guide/news.md) | What moved last period’s return |
| [5. Illustration](guide/walkthrough.md) | The library on a short firm panel |
| [6. Discussion](guide/practice.md) | What a valuator can take |
| [Software](install.md) | Installation, API, and data extras |
| [References](references.md) | Bibliography |
