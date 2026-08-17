# Discounting cash flows when expected returns move

An exposition of the joint VAR, implemented in `varvaluation`

!!! abstract "Abstract"

    Once expected returns move, a constant-rate DCF is a different
    random variable from the present value. The well-defined object is
    the conditional expectation of a product: cash flows times a path
    of one-period expected returns
    ([Ang and Liu, 2004](references.md#ang-liu-2004), eq. 2). This
    document is an exposition of that framework and a named-state
    implementation in Python. It does not derive a new closed form.
    What is not in the 2004 paper is the public binding of names to
    positions (`StateSpec`), a panel VAR that forms lag pairs only
    inside the firm, and a news routine that takes cash-flow news from
    the cash-flow equation rather than from the residual
    ([Chen, Da, and Zhao, 2013](references.md#chen-da-zhao-2013);
    [Chen and Zhao, 2009](references.md#chen-zhao-2009)).

    Section 5 is a computational illustration on a short CRSP–Compustat
    window, not an empirical contribution. It reports the discount
    *curve* and a mean-reverting profitability path at three permnos.
    It does not report a present value of those firms: the cash-flow
    slot is $\log(\mathrm{NI}/\mathrm{BE}_{\mathrm{lag}})$, a
    profitability *level*, not log dividend growth.

**Keywords.** discount rates; cash-flow news; vector autoregression;
quadratic-Gaussian valuation; time-varying expected returns

---

## Organisation

This site is a handbook plus a library. The closed forms are
[Ang and Liu (2004)](references.md#ang-liu-2004). The package is the
subject of the software sections and the vehicle of Section 5.

| Section | Content |
|---|---|
| [1. Introduction](guide/introduction.md) | The product, the 2004 law, and what this document adds |
| [2. Framework](guide/system.md) | The joint VAR, the two recursions, and the content of $X_t$ |
| [3. Estimation](guide/estimate.md) | Staged measurement of $(\Phi,c,\Sigma,\xi,\Lambda)$ |
| [4. Return news](guide/news.md) | Direct cash-flow news on the same companion |
| [5. Illustration](guide/walkthrough.md) | Software demonstration on a short firm panel |
| [6. Discussion](guide/practice.md) | What a valuator can take, and what this sample cannot show |
| [Software](install.md) | Installation, API, and data extras |
| [References](references.md) | Bibliography |

![Firm spot curves](assets/figures/firm_spot_curves.png)
<p class="figure-caption"><strong>Figure 1.</strong> Spot discount rates $\mu_t(n)$ at 30 September 2019 for three CRSP permnos in the 80-firm companion of Section 5. The low-beta name slopes up; the high-beta names start high and fade. These curves are the <em>denominator</em>, not firm values. Twelve-month rolling betas.</p>
