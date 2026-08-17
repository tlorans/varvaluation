<p class="part-kicker">Part 01 · The research program</p>

# What would count as explaining value

<p class="you-will"><strong>You will.</strong> See the open question, the tests of progress, and three threads a next paper could take.</p>

## The question

Empirical asset pricing has been strong on *returns*. Factors, sorts, and the craft that [Tidy Finance](https://www.tidy-finance.org/index.html) teaches so well ask: what moved the payoff you already earned? This handbook is the sibling craft. It asks what the claim is *worth* when next year’s cash flow and the cash flow in year ten should not share a rate.

Expected returns move ([Cochrane, 2011](../references.md#cochrane-2011)). Present value is then the expectation of a product — each cash flow times a path of one-period expected returns — which is equation (2) of [Ang and Liu (2004)](../references.md#ang-liu-2004). You cannot recover that number from a forecast of $C$ divided by a forecast of $\mu$. $\mathbb{E}[XY]\ne\mathbb{E}[X]\,\mathbb{E}[Y]$. The program is to treat the product as something you measure.

## Why it is still open

Serious practice is not a cartoon. It already uses a changing risk-free rate, an implied or historical premium, rolling betas, multi-stage fade, and residual income. What it still types, more often than it estimates, is the *shape* of the discount curve: how fast year ten should come back toward a long-run rate.

Closed forms for that shape exist. They are rarely estimated as a valuation. Two desks — a cash-flow team and a cost-of-capital team — can each be careful and still fail to identify the product, because the covariance is missing, the horizons need not match, and the two forecasts can contradict each other.

Return predictors are contested out of sample. That does not close the program. The present-value identity still requires some mix of cash-flow news and discount-rate news. Someone has to say which mix, on which state, and whether the resulting curve is a number you would take to a claim.

Traded dividend strips later measured a term structure of *returns* on cash-flow claims ([van Binsbergen, Brandt, and Koijen, 2012](../references.md#vbbk-2012); [van Binsbergen and Koijen, 2017](../references.md#vbk-2017)). That is a cousin of $\mu_t(n)$, not a solved valuation. The strip return is what you earned on a claim that had already been priced. The object here is the price.

## What would count as progress

A paper advances the program when it can point to one of these and mean it.

- A discount curve $\mu_t(n)$ whose *shape* is $\Phi^n$, estimated, not a hand-set fade.
- A cash-flow name that is actually growth or residual income, so `value()` is a present value of the equity — not only a curve.
- The growth–rate covariance sitting inside the *price*, not only in a variance decomposition computed after the fact.
- Instruments that survive look-ahead-free construction and out-of-sample tests.
- Firm systems that are not a pooled companion on eighty survivors of a four-year window.
- Direct cash-flow news that comes close to closing the return identity ([Chen, Da, and Zhao, 2013](../references.md#chen-da-zhao-2013)).
- The accounting companion — residual income ([Ohlson, 1995](../references.md#ohlson-1995); [Feltham and Ohlson, 1995](../references.md#feltham-ohlson-1995); [Ang and Liu, 2001](../references.md#ang-liu-2001)) — implemented, not only cited.
- A serious comparison to dividend-strip evidence.

None of those is a software feature. Each is a paper, or the core of one.

## How this handbook places you

You will feel the flat-rate error in [Getting started](start.md), write one joint VAR in [The joint system](system.md), estimate it on public data in [Measurement](data.md), then on firms in [Part 06](walkthrough.md). Only then will you see what the current illustration cannot claim.

The package is the bench, not the result. `StateSpec` names the cash-flow slot instead of hiding it in column zero. `estimate_var_panel` forms lag pairs only inside a firm, so firm A is never used to forecast firm B. `news_decomposition` takes cash-flow news from the cash-flow equation and stores the leftover as a diagnostic. The closed forms are [Ang and Liu (2004)](../references.md#ang-liu-2004). What you do with a named state, a longer panel, or a better cash-flow name is the program.

## Pick up a thread

Three live gaps, each one sentence, each pointing at a later chapter.

1. Replace `roe` with a growth (or residual-income) name and report an equity present value ([Present value](valuation.md), [Three curves](walkthrough.md)).
2. Re-estimate the firm system on a 1965– sample and ask whether the curve’s shape survives ([Estimate](estimate.md), [WRDS / firm panel](wrds.md)).
3. Implement the accounting companion and compare it to the discount-curve path ([For valuators](practice.md)).

When you are ready to do something, start [here](start.md).
