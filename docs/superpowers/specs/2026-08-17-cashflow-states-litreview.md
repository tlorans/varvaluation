# Lit-review — what moves expected cash flows

**Date:** 2026-08-17
**Mode:** deep-research lit-review (orchestrator synthesis; one retrieval agent stalled)
**AI disclosure:** Sources confirmed by bibliographic databases (year, journal, volume, pages). No unverified titles.

## Question

Which named states move *expected cash flows* — the numerator of present value — and therefore belong in \(X_t\) as value states?

## Settled

Profitability is forecastable and mean-reverts (Fama & French, 2000). ROE has internal structure that fades (Nissim & Penman, 2001). Residual income is the accounting name for a firm *level* (Ohlson, 1995); its linear dynamics get some empirical support but little gain over capitalizing short-term earnings (Dechow, Hutton, & Sloan, 1999). The present-value identity requires that the price–dividend level forecast dividend growth, returns, or a bubble (Campbell & Shiller, 1988; Cochrane, 2008). A slowly moving growth component can drive both the numerator and the denominator (Bansal & Yaron, 2004).

## Disagreement

Postwar U.S. dividend growth looks nearly unforecastable from the dividend yield; prewar it does not (Chen, 2009). Lettau and Ludvigson (2005) recover expected dividend-growth variation that moves with expected returns, using consumption–wealth information. Koijen and Van Nieuwerburgh (2011) survey that split: how you measure dividends and the sample you pick change which side of the identity is “predictable.” Fama and French (2006) and Hou, Xue, and Zhang (2015) put expected profitability and investment into *average-return* models. Those names are valuation objects in the dividend-discount / \(q\) identity; a return sort is not yet a test that they move the numerator path.

## Named cash-flow states for \(X_t\)

1. Profitability *level* (`roe`) — persistence, not a growth rate.
2. Log cash-flow growth (`g`) — the name `value()` needs.
3. Payout / retained earnings — maps earnings into dividends.
4. Residual income (earnings minus a charge on book) — firm *level*.
5. Expected investment — with expected profitability, enters price/book (Fama & French, 2006).
6. Long-run growth (consumption or productivity) — common to both sides; not estimated here.

## Numerator progress tests

1. Own-lag of the cash-flow name is estimated, not typed (Fama & French, 2000).
2. The cash-flow name is growth or residual income, and `value()` is reported as an equity present value.
3. Book-to-market forecasts growth in \(\Phi\), or you say it does not and must forecast returns (Cochrane, 2008).
4. Dividend growth (or residual income) is forecastable in a no-look-ahead vintage, not only in a postwar yield regression (Chen, 2009; Lettau & Ludvigson, 2005).
