<p class="part-kicker">Part 01 · The research program</p>

# What would count as explaining value

<p class="you-will"><strong>You will.</strong> See the open question, the tests of progress, and three threads a next paper could take.</p>

## The question

Empirical asset pricing has been strong on *returns* — what you earned
after the fact. Factors (portfolios that line stocks up by a
characteristic) and sorts (the lining-up itself) ask: what moved the
payoff you already received? This handbook is the sibling craft. It
asks what the claim is *worth today* when next year’s cash flow and
the cash flow in year ten should not share a rate.

Expected returns move ([Cochrane, 2011](../references.md#cochrane-2011)).
Present value is then the expectation of a product — each cash flow
times a path of one-period expected returns — which is equation (2)
of [Ang and Liu (2004)](../references.md#ang-liu-2004). Write $C$ for
a cash flow and $\mu$ for a one-period expected return. You cannot
recover the present value from a forecast of $C$ divided by a
forecast of $\mu$. In general the average of a product is not the
product of the averages: $\mathbb{E}[XY]\ne\mathbb{E}[X]\,\mathbb{E}[Y]$.
The two sides can move together, and that co-movement sits in the
price. The program is to treat the product as something you measure.

## Why it is still open

Serious practice is not a cartoon. It already lets the risk-free rate
change, takes an equity premium from history or from the price
itself, updates a stock’s sensitivity to the market (its **beta**),
and types a **fade** — a hand-set speed at which growth or the
premium is assumed to revert. What it still types, more often than
it estimates, is the *shape* of the discount curve: how fast the
rate at year ten should come back toward a long-run rate.

Formulas for that shape exist. They are rarely estimated as a
valuation. Two desks — a cash-flow team and a cost-of-capital team —
can each be careful and still fail to determine a unique price,
because the co-movement is missing, the horizons need not match, and
the two forecasts can contradict each other.

Whether a variable that seems to forecast returns still works on
*later* data, unseen when the forecast was fit, is contested. That
does not close the program. The accounting identity that links
today’s price to future cash flows and future returns still requires
some mix of revisions to cash-flow forecasts and revisions to
discount-rate forecasts. Someone has to say which mix, on which
list of variables, and whether the resulting curve is a number you
would take to a claim.

Claims that pay only the dividends of a given year have been traded.
The returns on those claims are a term structure — a rate at each
horizon — of *payoffs*, not a solved present value
([van Binsbergen, Brandt, and Koijen, 2012](../references.md#vbbk-2012);
[van Binsbergen and Koijen, 2017](../references.md#vbk-2017)). The
object here is the price.

## What would count as progress

A paper advances the program when it can point to one of these and
mean it.

- A discount curve whose *shape* is estimated from the persistence of
  the state, not typed as a fade.
- A cash-flow series that is actually growth (or the accounting
  cousin below), so the formula reports a present value of the
  equity — not only a curve.
- The co-movement of growth and rates sitting inside the *price*,
  not only in a variance table computed after the fact.
- Predictors built from information that was available at the time,
  that still work on later data.
- Firm evidence that is not a handful of survivors of a four-year
  window, pooled as if they were one series.
- A split of last period’s surprise that comes from the cash-flow
  equation itself, and that comes close to adding back up to the
  surprise ([Chen, Da, and Zhao, 2013](../references.md#chen-da-zhao-2013)).
- The accounting companion — **residual income**, book plus the
  present value of earnings above a charge on book
  ([Ohlson, 1995](../references.md#ohlson-1995);
  [Feltham and Ohlson, 1995](../references.md#feltham-ohlson-1995);
  [Ang and Liu, 2001](../references.md#ang-liu-2001)) — computed, not
  only cited.
- A serious comparison to those traded dividend claims.

None of those is a software feature. Each is a paper, or the core of
one.

## How this handbook places you

You will feel the flat-rate error in [Getting started](start.md),
write one joint system of regressions in [The joint system](system.md),
estimate it on public files in [Measurement](data.md), then on firms
in [Part 06](walkthrough.md). Only then will you see what the current
illustration cannot claim.

The package is the bench, not the result. It names the cash-flow slot
instead of hiding it in column zero. On a firm panel it forms
yesterday-and-today pairs only inside one firm, so firm A is never
used to forecast firm B. It takes the cash-flow piece of a return
surprise from the cash-flow equation and stores the leftover as a
check. The formulas are [Ang and Liu (2004)](../references.md#ang-liu-2004).
What you do with a named state, a longer panel, or a better
cash-flow name is the program.

## Pick up a thread

Three live gaps, each one sentence, each pointing at a later chapter.

1. Use a cash-flow name that is growth (or residual income) and
   report an equity present value ([Present value](valuation.md),
   [Three curves](walkthrough.md)).
2. Re-estimate the firm system on a sample that starts in 1965 and
   ask whether the curve’s shape survives ([Estimate](estimate.md),
   [Firm panel](wrds.md)).
3. Compute residual income and compare it to the discount-curve path
   ([For valuators](practice.md)).

When you are ready to do something, start [here](start.md).
