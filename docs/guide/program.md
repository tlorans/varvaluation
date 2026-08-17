<p class="part-kicker">Part 01 · The research program</p>

# Which variables drive asset values

<p class="you-will"><strong>You will.</strong> See the two halves of the program — which variables move expected cash flows, and which move expected returns — and keep the joint system as background.</p>

## The question

Empirical asset pricing has been strong on *returns* — what you earned
after the fact. **Factors** are portfolios that line stocks up by a
characteristic; **sorts** are the lining-up itself. That craft asks
which characteristics line up average returns. This handbook is the
sibling craft. It asks which variables drive the *level* of value:
what the claim is worth today, when next year’s cash flow and the
cash flow in year ten should not share a rate.

Write a **state** for the short list of variables that are supposed
to carry those forecasts. The research program is the contents of
that list. A variable earns a place if it moves a value object —
the price relative to dividends, the price relative to book, or the
discount rate at a stated horizon — not if it only lines up average
returns ([Cochrane, 2011](../references.md#cochrane-2011);
[Campbell and Shiller, 1988](../references.md#campbell-shiller-1988)).

## The framework is not the program

Expected returns move ([Cochrane, 2011](../references.md#cochrane-2011)).
Present value is then the expectation of a product — each cash flow
times a path of one-period expected returns
([Ang and Liu, 2004](../references.md#ang-liu-2004), eq. 2). Write
$C$ for a cash flow and $\mu$ for a one-period expected return. You
cannot recover the present value from a forecast of $C$ divided by a
forecast of $\mu$. The two sides can move together, and that
co-movement sits in the price.

The smallest statistical object that produces both forecasts, and
how they move together, from one state is a **vector
autoregression**: several ordinary regressions run at the same time.
That joint system is the *framework*. It is background. You need it
in order to ask the question coherently. It is not the contribution,
and learning it is not the program. [Part 03](system.md) writes it
out.

## Why the contents of the state are still open

The program has two halves. One half asks which variables move
**expected cash flows** — the numerator: the path of dividends,
earnings, or residual income you are discounting. The other half
asks which variables move **expected returns** — the denominator:
the curve. A variable can sit in both. The identity that links
today’s price to those two paths requires that *someone* forecast
growth, or returns, or a bubble
([Campbell and Shiller, 1988](../references.md#campbell-shiller-1988);
[Cochrane, 2008](../references.md#cochrane-2008)). Which names do
the work is open
([Koijen and Van Nieuwerburgh, 2011](../references.md#kvn-2011)
survey how that split depends on the sample and on how dividends are
measured).

Serious practice already types a **fade** — a hand-set speed at
which growth or the premium is assumed to revert — and a premium
for the rate. What it still types, more often than it estimates, is
*which* variables are allowed to move each side.

### Half 1 — What moves expected cash flows

- **Profitability** — earnings on book — is forecastable and
  mean-reverts toward an economy-wide level
  ([Fama and French, 2000](../references.md#ff-2000)). That is why
  a profitability name has an own-lag in the joint system. A
  *level* is not yet a growth rate, and it is not yet a present
  value of the equity.
- **Return on equity has pieces.** Profit margin, asset turnover,
  and leverage fade over years
  ([Nissim and Penman, 2001](../references.md#nissim-penman-2001)).
  Those pieces are cash-flow states. That paper is not a regression
  of profitability on interest rates.
- **Dividend growth** — the change in cash paid to owners — is the
  name a present value of equity needs. After the war, the dividend
  yield forecasts returns more than it forecasts dividend growth;
  before the war the reverse is closer to the truth
  ([Chen, 2009](../references.md#chen-2009)). Information in consumption, asset wealth, and labour income can
  still recover expected dividend-growth variation that moves with
  expected returns
  ([Lettau and Ludvigson, 2005](../references.md#lettau-ludvigson-2005)).
- **Residual income** — book plus the present value of earnings
  above a charge on book
  ([Ohlson, 1995](../references.md#ohlson-1995)) — is the accounting
  name for a firm *level*. Linear dynamics for that object get some
  support; they do not clearly beat capitalizing a short earnings
  forecast ([Dechow, Hutton, and Sloan, 1999](../references.md#dhs-1999)).
  This handbook cites the companion, it does not compute it
  ([Ang and Liu, 2001](../references.md#ang-liu-2001)).
- **Expected profitability and expected investment** enter the
  price–book level in the dividend-discount identity
  ([Fama and French, 2006](../references.md#ff-2006)). The same
  names later line up average *returns*
  ([Hou, Xue, and Zhang, 2015](../references.md#hxz-2015)). A return
  sort is not yet a test that they move the numerator path.
- At the firm, unexpected returns are mostly cash-flow news when
  earnings are written in return units
  ([Vuolteenaho, 2002](../references.md#vuolteenaho-2002)). The
  library’s profitability name is not that object.
- A slowly moving component of growth can drive *both* cash flows
  and discount rates ([Bansal and Yaron, 2004](../references.md#bansal-yaron-2004);
  [Croce, 2014](../references.md#croce-2014)). It is not estimated
  here.

### Half 2 — What moves expected returns

- The **short rate** and inflation are classical short-horizon
  expected-return variables
  ([Fama and Schwert, 1977](../references.md#fama-schwert-1977)).
  They should tilt the near end of the curve. If they do not, they
  are not value states.
- The **dividend yield** (dividends over price) must forecast
  returns, cash-flow growth, or a bubble — that is an identity, not
  a taste ([Campbell and Shiller, 1988](../references.md#campbell-shiller-1988);
  [Cochrane, 2008](../references.md#cochrane-2008)). Whether it still
  forecasts on later data is contested
  ([Goyal and Welch, 2008](../references.md#goyal-welch-2008)).
- The **consumption–wealth gap** is a strong in-sample quarterly
  predictor of returns ([Lettau and Ludvigson, 2001](../references.md#lettau-ludvigson-2001)).
  **In-sample** means: it works on the window used to fit it. It
  weakens or fails on later data
  ([Goyal and Welch, 2008](../references.md#goyal-welch-2008)).
- **Beta** — a stock’s sensitivity to the market — belongs on the
  curve if it changes the curve’s *shape* on one date, not only if
  it lines up average returns.
- Claims that pay only the dividends of a given year have been
  traded. The returns on those claims are a term structure of
  *payoffs*, not a solved present value
  ([van Binsbergen, Brandt, and Koijen, 2012](../references.md#vbbk-2012)).
  A state is a value state if it moves the discount rate at the
  horizons those claims identify.

A variable that only raises an in-sample return regression is a
factor candidate. A variable that moves the expected cash-flow
path, or the curve, under a construction that does not peek at
later data, is a value state.

## What would count as progress

A paper advances the program when a *named* state can point to one
of these and mean it.

On the numerator:

- The own-lag of the cash-flow name is estimated, not typed
  ([Fama and French, 2000](../references.md#ff-2000)).
- The cash-flow name is growth, or residual income, and you report
  a present value of the equity — not only a curve.
- Book-to-market forecasts growth in the joint system, or you say
  it does not and must forecast returns
  ([Cochrane, 2008](../references.md#cochrane-2008)).
- Dividend growth (or residual income) is forecastable in a vintage
  that does not use later data, not only in a postwar yield
  regression ([Chen, 2009](../references.md#chen-2009);
  [Lettau and Ludvigson, 2005](../references.md#lettau-ludvigson-2005)).

On the denominator:

- The short rate moves the near end of the discount curve. Shut it
  off and the near end must change.
- The consumption–wealth gap, built from information available at
  the valuation date, still moves the curve — not only an in-sample
  return fit.
- Beta changes the *shape* of a firm’s curve on one date (low-beta
  slopes up; high-beta starts high and fades).

On the joint object:

- Last period’s surprise, split using the cash-flow equation
  itself, comes close to adding back up
  ([Chen, Da, and Zhao, 2013](../references.md#chen-da-zhao-2013)).
  A large leftover means a missing or misspecified state, not a
  third kind of news.

None of those is “we used a vector autoregression.” Each is a claim
about a named coordinate.

## How this handbook places you

First you will feel why one rate is the wrong object
([Getting started](start.md)). Then you will learn the joint system
— the framework — in [Part 03](system.md). Then you will put named
states on public files and on firms, and ask which ones move the
curve. Only then will you see what the current illustration cannot
claim.

The package is the bench. It names every coordinate, including the
cash-flow slot. On a firm panel it never uses firm A to forecast
firm B. It reads the cash-flow piece of a surprise from the
cash-flow equation. What you put in the state, and which value
object it moves, is the program.

## Pick up a thread

Three live gaps, one on each half and one on the joint object.

1. **Numerator.** Put a growth name (or residual income) in the
   cash-flow slot and report an equity present value
   ([Present value](valuation.md), [Three curves](walkthrough.md)).
2. **Denominator.** Rebuild the consumption–wealth gap, or the
   premium regression, with no data after the valuation date, and
   ask whether the curve still moves ([Estimate](estimate.md)).
3. **Both.** On a long firm sample, ask whether profitability
   forecasts the cash-flow path and whether beta changes the shape
   of $\mu_t(n)$ — the discount rate $n$ periods ahead — or only
   lines up average returns ([Firm panel](wrds.md)).

When you are ready to do something, start [here](start.md).
