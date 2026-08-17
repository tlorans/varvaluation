# 6. Discussion

The question that matters is whether the rate at year ten is today’s
short rate, a historical average, or a forecast that mean-reverts
with the state ([Ang and Liu, 2004](../references.md#ang-liu-2004),
§IV). This section states what a valuator can take from the *curve*,
and what the sample of Section 5 cannot show.

## What a valuator can take

The object Section 5 identifies is $\mu_t(n)$, a maturity-specific
spot curve
([Brennan, 1997](../references.md#brennan-1997);
[Ang and Liu, 2004](../references.md#ang-liu-2004), Definition II.1).
It is usable without taking the VAR’s cash-flow equation. Discount a
path you already have — an analyst schedule, a residual-income path
([Ohlson, 1995](../references.md#ohlson-1995);
[Feltham and Ohlson, 1995](../references.md#feltham-ohlson-1995);
[Ang and Liu, 2001](../references.md#ang-liu-2001)), or an internal
model — at `spot_rates`. That construction is in
[Section 2.2](valuation.md#8-discounting-a-path-you-already-have).

On the 80-firm companion of Section 5 the short end of $\mu_t(n)$
moves with $\beta_t$. The low-beta name (permno 10026) slopes up from
5.5% to 9.5%. The high-beta names start above 11% and fade. A single
rate taken from either end is the wrong rate at the other.

![Firm spot curves](../assets/figures/firm_spot_curves.png)
<p class="figure-caption"><strong>Figure 1</strong> (reprised). $\mu_t(n)$ at three CRSP permnos, 30 September 2019. A single rate is a flat line through this picture. Source: Section 5.</p>

A variance decomposition of $\mu_t(10)$ on that window puts 57% on
$\beta$ and 48% on $\mathit{bm}$. $\mathit{roe}$ is negligible *for
the curve*. That does not mean cash flows do not matter for prices.
They drive the numerator, which this decomposition does not show.
$\mathit{cay}$ contributes 0.0% of curve variance here: the premium
state the design kept after dropping the dividend yield does not move
$\mu_t(10)$ on this vintage.

## What this is not competing with

Serious practice is not a cartoon WACC taken from a table and held
flat forever. It already uses a changing risk-free rate, an implied
or historical equity premium, rolling or fundamental betas
([Fama and French, 1997](../references.md#ff-1997);
[Lewellen and Nagel, 2006](../references.md#lewellen-nagel-2006)),
multi-stage fade, and residual income. The increment here is
narrower.

| Object | Already in practice | What the joint VAR adds |
|---|---|---|
| Discount rate | CAPM or multi-factor cost of equity, sometimes with a fading premium | A curve $\mu_t(n)$ whose *shape* is disciplined by $\Phi$, not by a hand-set fade |
| Cash flows | Analyst or internal forecasts; residual income | An optional VAR numerator; not required, and not identified as growth in Section 5 |
| $g$–$\mu$ interaction | Implicit in scenarios, or ignored | $-2\,\mathrm{Cov}_t(\sum g,\sum\mu)$ inside the *price* if both sides come from $X$ |
| Terminal value | Gordon or a fade to a long-run $(r,g)$ | The tail of the same recursion, when the cash-flow name is growth |
| Duration | Sensitivity tables | $b(n)$ and $H(n)$ that vary with horizon |

!!! note "In words — duration, implied premium, fade"
    **Duration** is how much value moves when the discount rate
    moves. Long-dated cash flows have more of it, so a wrong rate
    at year ten hurts a growth name more than a short-cash-flow
    name. An **implied equity premium** is the $r$ that equates a
    DCF to the market price; a **historical** premium is an average
    of past excess returns. **Fade** is a hand-set speed at which
    growth or the premium is assumed to revert. The VAR replaces
    that fade with $\Phi^n$, estimated rather than typed.

The comparison that matters is not “spreadsheet versus VAR.” It is
whether the rate at year ten is today’s short rate, a historical
average, or a forecast that mean-reverts at an estimated speed
([Ang and Liu, 2004](../references.md#ang-liu-2004), §IV). A flat
rate at *today’s* high $\mu_t(1)$ discounts every horizon too hard.
A historical-average rate on a date when the fitted curve sits
*below* that average is too high at the short end. Signed error
$(\text{wrong}-\text{correct})/\text{correct}$ is negative when the
wrong model produces the smaller present value. The error scales with
duration.

Traded dividend claims
([van Binsbergen, Brandt, and Koijen, 2012](../references.md#vbbk-2012);
[van Binsbergen and Koijen, 2017](../references.md#vbk-2017)) later
measured a term structure of *returns* on the cash-flow strip — a
cousin of $\mu_t(n)$, not a direct test of a fitted curve.

Isolation (`isolate_channels`) asks the counterfactual version of the
same question: shut a named state on one side and revalue. On the
Section 5 companion the discount-side call raises
`PerpetuityDivergesError`. That counterfactual curve does not exist
here.

## What this sample cannot show

Section 5 is a software demonstration. The caveats are load-bearing.

- **80 firms, not 2,673.** The prepared state has 2,673 names. The
  companion is pooled on the 80 longest histories. Those are not the
  same sample. The 80 are survivors of a short window.
- **2015–2019, not 1965–2019.** A research firm panel would start in
  1965 or 1973. Overlapping annual pairs on four years are few; the
  $r$ and $\pi$ loadings on the `roe` row are short-panel artifacts.
- **Look-ahead in $(\xi,\Lambda)$.** The premium regression uses
  market returns through December 2024 to value a September 2019
  state. $b_0$ is precise ($t=3.41$). The slopes that make
  $\lambda_t$ *move* have $|t|<2$. $\alpha=0.02$ is a calibration
  intercept, not an estimate.
- **Twelve-month betas.** The library convention is 60 months
  ([Lewellen and Nagel, 2006](../references.md#lewellen-nagel-2006)
  discuss the noise in short-window slopes).
- **`roe` is not a cash-flow growth rate** and is not Vuolteenaho’s
  $e_t$. No equity present value is reported. Residual income is
  cited, not computed.
- **The news identity does not close.**
  `residual_share`$\,=2434$ is a failed diagnostic, not a
  confirmation of [Vuolteenaho (2002)](../references.md#vuolteenaho-2002).

[Stambaugh (1999)](../references.md#stambaugh-1999) bias still
applies: persistence is overstated in short samples with persistent
predictors, and the priced recursion compounds $\Phi^n$. Use the
system to read the **shape** of the discount curve and, when both
sides come from $X$, the **sign** of the growth–rate interaction. Be
skeptical of the third decimal place. The checklist is on
[Estimation](estimate.md#what-can-go-wrong).
