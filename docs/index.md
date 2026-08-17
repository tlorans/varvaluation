# Cash flows and discount rates from one system

!!! abstract "Purpose"

    When expected returns move, the present value of a claim is not a
    discounted point forecast. It is the conditional expectation of a
    **product**: future cash flows times a path of stochastic discount
    rates ([Ang and Liu, 2004](references.md#ang-liu-2004)). That
    expectation is identified only from the *joint* law of growth and
    expected returns. This library estimates that law as one Gaussian
    VAR of a named state $X_t$, and from the same
    $(\Phi,c,\Sigma)$ returns three objects: a horizon-specific
    discount curve $\mu_t(n)$, a cash-flow path
    $\mathbb{E}_t[C_{t+n}]/C_t$, and a news decomposition in which
    cash-flow news is the cash-flow equation, not a residual
    ([Campbell, 1991](references.md#campbell-1991);
    [Chen, Da, and Zhao, 2013](references.md#chen-da-zhao-2013)).

    The purpose is therefore not another DCF spreadsheet. It is to
    replace an asserted WACC and a typed-in growth path with two
    forecasts, and their covariance, that come from one estimated
    system.

**Read in this order.** [Install](install.md), then the
[worked application](guide/walkthrough.md): seven steps on Ken French,
FRED, and WRDS. The pages under Understand are the argument. This page
states the claim.

---

## The claim

The textbook DCF writes

$$
V_t = \sum_{j=1}^{\infty} \frac{\mathbb{E}_t[D_{t+j}]}{(1+r)^j}.
$$

Two assumptions are buried in that line. The denominator is **one** $r$
at every horizon. The numerator is a cash-flow path treated as
statistically independent of $r$. Both fail as soon as expected returns
vary. Discount-rate variation is the organizing fact of modern
empirical asset pricing ([Cochrane, 2011](references.md#cochrane-2011)).
The definition that survives is the expectation of a product,

$$
V_t = \sum_{j=1}^{\infty}
\mathbb{E}_t\!\left[
  D_{t+j}\,\exp\!\Bigl(-\sum_{i=1}^{j} r_{t+i}\Bigr)
\right].
$$

You cannot take $\mathbb{E}_t[D]$ and $\mathbb{E}_t[r]$ separately and
then divide: $\mathbb{E}[XY]\ne\mathbb{E}[X]\,\mathbb{E}[Y]$. The
minimum required object is the joint distribution of cash-flow growth
and expected returns. A VAR of those states is the instrument that
delivers it ([Ang and Liu, 2004](references.md#ang-liu-2004), §III).

## Both sides from $X_t$

Write cash flows in growth form, $g_{t+i}=\log(C_{t+i}/C_{t+i-1})$.
Each strip is then an exponential of cumulated growth minus cumulated
discount rates. Under a Gaussian VAR those expectations have closed
forms: exponential-affine in $X_t$ for the numerator, and
exponential-quadratic once the one-period expected return is itself
quadratic in the state (the $\beta_t\lambda_t$ product).

| Side | Object | From $X_t$ | Method |
|---|---|---|---|
| Numerator | $\mathbb{E}_t[C_{t+n}]/C_t$ | cash-flow row of $\Phi$ | `cashflow_expectation` |
| Denominator | spot rate $\mu_t(n)$ | priced recursion | `spot_rates` |
| Value | their product, summed | both | `value` |

`value` is the present value in the sense of the definition above.
`spot_rates` is the practitioner’s curve: keep the two-step workflow
(forecast, then discount), but replace one WACC by
$\mu_t(n)=A(n)+B(n)'X_t+X_t'G(n)X_t$
([Ang and Liu, 2004](references.md#ang-liu-2004), Definition II.1).
`perpetuity` freezes the numerator at $1$ so that only the curve can
move.

![Spot discount curves for BE/ME deciles](assets/figures/spot_curves.png)
<p class="figure-caption"><strong>Figure.</strong> Spot discount rates $\mu_t(n)$ at the last sample state for Ken French book-to-market deciles, 1965–2024. The curve slopes up: a single WACC is the wrong rate at long horizons. These curves are the denominator. The present value also multiplies each strip by $\mathbb{E}_t[C_{t+n}]/C_t$. Source: <a href="guide/walkthrough.md">worked application</a>.</p>

The cash-flow variable is whatever `spec.cashflow` names — log dividend
growth $g$ on a portfolio, log profitability $\mathit{roe}$ at a firm
([Vuolteenaho, 2002](references.md#vuolteenaho-2002)). The engine never
assumes that column 0 is $g$.

## Where this sits

Two neighbouring literatures supply the *content* of $X_t$.
Profitability is forecastable and mean-reverts
([Fama and French, 2000](references.md#ff-2000)); at the firm,
cash-flow news dominates return variance
([Vuolteenaho, 2002](references.md#vuolteenaho-2002)). Expected
returns load on the short rate and on $\mathit{cay}$, not on the
dividend yield whose predictive power had collapsed by 2000
([Fama and Schwert, 1977](references.md#fama-schwert-1977);
[Lettau and Ludvigson, 2001](references.md#lettau-ludvigson-2001);
[Goyal and Welch, 2003](references.md#goyal-welch-2003)). Long-run
risk and productivity give an economic reason why the same state can
drive both sides ([Bansal and Yaron, 2004](references.md#bansal-yaron-2004);
[Croce, 2014](references.md#croce-2014)). The VAR is the frame that
forces those two maps to be consistent, because the price requires
their joint distribution. The names and the evidence are collected
under [StateSpec](guide/spec.md); the bibliography is
[References](references.md).

**Next:** the [worked application](guide/walkthrough.md). Then
[The VAR](guide/system.md) and [Valuation](guide/valuation.md).

## Extras

| Extra | What it adds |
|---|---|
| core | Named-state VAR; cash-flow and discount-rate forecasts from $X$; news |
| `[data]` | Ken French, FRED, cay, portfolio state |
| `[wrds]` | CRSP–Compustat firm panel and firm-level state |

## License

MIT. Source: [tlorans/varvaluation](https://github.com/tlorans/varvaluation).
