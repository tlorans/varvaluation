<p class="part-kicker">Part 01 · The research program</p>

# Which variables drive asset values

<p class="you-will"><strong>You will.</strong> Separate the framework you must know from the open question: which named variables move what a claim is worth.</p>

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

Serious practice already lets the risk-free rate change, takes an
equity premium from history or from the price, and updates a stock’s
sensitivity to the market (its **beta**). What it still types, more
often than it estimates, is *which* variables are allowed to move
the curve, and whether they move the numerator, the denominator, or
both.

The candidates are known. They are not settled.

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
- **Profitability** is forecastable and mean-reverts
  ([Fama and French, 2000](../references.md#ff-2000)). At the firm,
  unexpected returns are mostly cash-flow news when earnings are
  written in return units
  ([Vuolteenaho, 2002](../references.md#vuolteenaho-2002)). A
  profitability *level* is not yet a growth rate, and it is not yet
  a present value of the equity.
- **Residual income** — book plus the present value of earnings
  above a charge on book
  ([Ohlson, 1995](../references.md#ohlson-1995)) — is the accounting
  name for a firm *level*. It is cited in this handbook, not
  computed.
- Claims that pay only the dividends of a given year have been
  traded. The returns on those claims are a term structure of
  *payoffs*, not a solved present value
  ([van Binsbergen, Brandt, and Koijen, 2012](../references.md#vbbk-2012)).
  A state is a value state if it moves the discount rate at the
  horizons those claims identify.

A variable that only raises an in-sample return regression is a
factor candidate. A variable that moves the curve, or the
price–dividend level, under a construction that does not peek at
later data, is a value state.

## What would count as progress

A paper advances the program when a *named* state can point to one
of these and mean it.

- The short rate moves the near end of the discount curve. Shut it
  off and the near end must change.
- The consumption–wealth gap, built from information available at
  the valuation date, still moves the curve — not only an in-sample
  return fit.
- Book-to-market forecasts growth, or forecasts returns, and you
  say which. The identity requires one or the other
  ([Cochrane, 2008](../references.md#cochrane-2008)).
- Beta changes the *shape* of a firm’s curve on one date (low-beta
  slopes up; high-beta starts high and fades). If it only lines up
  average returns in a sort, it is a factor, not a value state.
- Profitability is replaced by a growth name, or by residual
  income, and you report a present value of the equity.
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

Three live gaps, each about a named state.

1. Put a growth name (or residual income) in the cash-flow slot and
   report an equity present value ([Present value](valuation.md),
   [Three curves](walkthrough.md)).
2. Rebuild the consumption–wealth gap, or the premium regression,
   with no data after the valuation date, and ask whether the curve
   still moves ([Estimate](estimate.md)).
3. On a long firm sample, ask whether beta and book-to-market still
   change the shape of $\mu_t(n)$ — the discount rate $n$ periods
   ahead — or only line up average returns
   ([Firm panel](wrds.md)).

When you are ready to do something, start [here](start.md).
