<p class="part-kicker">Part 01 · The research program</p>

# Which variables drive asset values

<p class="you-will"><strong>You will.</strong> Read what is known about the two sides of a price — the cash you expect, and the rate you discount it at — and see which questions are still open.</p>

## The question

A large part of empirical finance asks why some stocks earned more
than others, on average. That work lines firms up by a trait
(size, book-to-market, profitability) and reports the return
difference. This handbook asks a different question: *what is the
firm worth today?* Year one and year ten should not share a rate
when the rate you require is allowed to change
([Cochrane, 2011](../references.md#cochrane-2011)). So the price
has to come from a forecast of future cash and a forecast of future
required returns, together
([Campbell and Shiller, 1988](../references.md#campbell-shiller-1988)).

The research program is: **which observed variables belong in that
forecast?** A variable belongs if, when it moves, today’s price
moves, or the path of expected cash moves, or the rate applied to a
given year moves. It does not belong merely because firms with a
high value of that variable happened to earn more, on average, in a
historical sort.

## One system, two forecasts

The framework in [Part 03](system.md) models cash flows and the
discount rate together. If the rate you require next year can
differ from the rate you require in year ten, you cannot take a
cash-flow forecast from one model, a required-return forecast from
another, and divide. The two can move together, and that joint
movement is part of the price
([Ang and Liu, 2004](../references.md#ang-liu-2004)).

Cash flow itself can be written two ways, and they are not
interchangeable. **Growth** is how fast cash changes from one date
to the next. That path *is* the cash you are pricing.
**Profitability** is how much the firm earns this year on the book
it already has. That level is forecastable
([Fama and French, 2000](../references.md#ff-2000)), but it is not
a growth rate of cash paid to owners. The literature below is
evidence on which observed variables belong on each side. The
algebra of the joint system is [Part 03](system.md).

That evidence has two literatures. One asks what we can say today
about future cash (dividends, earnings, earnings above a charge on
book). The other asks what we can say today about future required
returns. A variable can appear in both. The accounting identity
that links the price to those two paths says that *something* must
forecast cash growth, or required returns, or both; otherwise the
price is a bubble
([Campbell and Shiller, 1988](../references.md#campbell-shiller-1988);
[Cochrane, 2008](../references.md#cochrane-2008)). Which variables
do the work, and in which sample, is still disputed
([Koijen and Van Nieuwerburgh, 2011](../references.md#kvn-2011)).

## What moves expected cash flows

Fama and French (2000) show that a firm’s earnings relative to its
book equity can be forecast: when that ratio sits above the
economy-wide average, it tends to fall back, and when it sits
below, it tends to rise. Nissim and Penman (2001) split the same
ratio into a profit margin, how much revenue the assets generate,
and leverage, and show that those pieces also come back toward
normal over several years. That is the cash-flow half of the
program at the firm: how fast profits revert, and which pieces of
the ratio do the reverting. It is not a statement about interest
rates.

For the market as a whole the cash paid to owners is dividends.
Whether today’s price–dividend ratio tells you about future
dividend growth depends on the period. Chen (2009) finds that
before the Second World War, the ratio mostly forecasts dividend
growth; after the war, it mostly forecasts returns. Lettau and
Ludvigson (2005) show that information in consumption, asset
wealth, and labour income can still recover variation in expected
dividend growth, and that this variation moves with expected
returns. So “dividends cannot be forecast” is not a settled fact.
It is a postwar finding about one particular ratio.

Accounting gives another name for the cash-flow path. Ohlson
(1995) writes the equity price as book value plus the present
value of earnings above a charge on book. Dechow, Hutton, and
Sloan (1999) find that the simple dynamics Ohlson assumes are
broadly consistent with the data, but that using them does not
clearly beat taking a short earnings forecast and treating it as
permanent. Ang and Liu (2001) give the closed-form companion when
the charge on book is allowed to move. This handbook cites that
companion; it does not compute it.

Fama and French (2006) start from the same present-value arithmetic:
given book-to-market, higher expected profits raise the price, and
higher expected investment (more of those profits retained in the
firm) lowers the return investors should require. Hou, Xue, and
Zhang (2015) then use profitability and investment to explain
average *returns* across stocks. That is useful, and it is a
different test. Showing that profitable firms earned more is not
the same as showing that profitability moved the path of expected
cash.

At the firm, Vuolteenaho (2002) finds that most of the unexpected
return is a revision in expected earnings, not a revision in
required returns — the opposite of the usual finding for the market
as a whole. His earnings measure is in the same units as a return.
The profitability ratio this library builds is not that measure.

A last strand says a slow component of growth — in consumption
([Bansal and Yaron, 2004](../references.md#bansal-yaron-2004)) or
in productivity ([Croce, 2014](../references.md#croce-2014)) — can
move expected cash and required returns at the same time. Those
papers are structural reasons the two halves can share a variable.
They are not estimated here.

## What moves expected returns

Required returns move
([Cochrane, 2011](../references.md#cochrane-2011)). The oldest
robust pattern is that a higher short-term interest rate, and
higher inflation, go with lower expected stock returns over the
near term ([Fama and Schwert, 1977](../references.md#fama-schwert-1977)).
If those variables belong in a valuation, they should change the
rate applied to the next few years more than the rate applied to
year ten.

The dividend–price ratio is the most famous candidate. By the
present-value identity it must forecast dividend growth, or
returns, or a bubble ([Cochrane, 2008](../references.md#cochrane-2008)).
On later samples that were not used to fit the original
regressions, it is a weak return forecast
([Goyal and Welch, 2003](../references.md#goyal-welch-2003);
[Goyal and Welch, 2008](../references.md#goyal-welch-2008)).
Lettau and Ludvigson (2001) propose instead the gap between
consumption and wealth: when consumption is high relative to
assets and labour income, expected returns are high in the sample
they study. The same out-of-sample tests that weaken the dividend
yield also weaken that gap ([Goyal and Welch, 2008](../references.md#goyal-welch-2008)).

How much a stock moves with the market changes over time
([Fama and French, 1997](../references.md#ff-1997)). If that
loading belongs in a valuation, two firms on the same date should
not share a discount curve: the high-loading name should start
expensive to discount and then come down; the low-loading name
should start cheap and then rise. If the loading only lines firms
up by average historical return, it is doing the factor job, not
the valuation job.

A newer market test uses claims that pay only the dividends of a
given year ([van Binsbergen, Brandt, and Koijen, 2012](../references.md#vbbk-2012)).
The returns on those claims are a schedule of payoffs by horizon,
not a solved present value. They are a cousin of the discount
curve: a variable that belongs on the required-return side should
move the rate at the horizons those claims identify.

## What is still open

Taken together, the cash-flow papers say profits revert and that
dividend growth is sometimes forecastable. The required-return
papers say the short rate is robust, and that the famous price
ratios are fragile once you leave the original sample. Neither
literature has produced a short, agreed list of variables that
move *today’s price* once both sides are estimated together, on
information that was available at the time.

A next paper on the cash-flow side would replace a profitability
*ratio* with a growth rate, or with earnings above a charge on
book, and report a present value of the equity — not only a
discount curve. It would also say whether book-to-market forecasts
that growth, or does not, and therefore must forecast returns
([Cochrane, 2008](../references.md#cochrane-2008)).

A next paper on the required-return side would rebuild the
consumption–wealth gap, or the premium regression, stopping at the
valuation date, and ask whether the discount curve still moves. It
would also check whether a stock’s market loading changes the
*shape* of that curve on one day.

A next paper on both sides would take a long firm sample and ask
the two questions at once: does profitability forecast the cash
path, and does the market loading change the curve — or do both
variables only line up average returns?

The illustration later in this handbook is a software run on a
short window. It does not answer those questions. It shows how to
ask them.

## Where to go next

[Getting started](start.md) shows why one rate for every year is
the wrong object. [Part 03](system.md) writes the joint
regressions. [Public data](data.md) and [firms](wrds.md) are where
you put named variables in and see which side they move.
