# Research brief — which states drive values

**Date:** 2026-08-17
**Mode:** deep-research quick
**AI disclosure:** Brief assembled with AI-assisted search against the project bibliography. Citations below are papers already in `docs/references.md`.

## Primary question

Which named state variables drive the *level* of equity values (price–dividend, price–book, or a maturity-specific discount curve) when cash-flow forecasts and discount-rate forecasts may both move?

## Framework (not the program)

Present value is the expectation of a product. A joint vector autoregression is the smallest law that produces both forecasts and their co-movement (Ang & Liu, 2004). That is settled method. “Use a VAR” is background.

## Program (the open question)

The contents of the state. Cochrane (2011) organizes asset pricing around discount-rate *variation* and the prices it implies, not around characteristics that line up average returns (the factor/sort craft). Campbell & Shiller (1988) write the price–dividend level as expected future cash flows minus expected future discount rates. A coordinate belongs in the state if it moves one of those objects, or the curve that prices them.

## Candidate states (verified in the project bibliography)

- Short rate and inflation: short-horizon expected-return states (Fama & Schwert, 1977).
- Consumption–wealth gap: strong in-sample premium state (Lettau & Ludvigson, 2001); weak or broken out of sample (Goyal & Welch, 2008).
- Dividend yield: a level state by identity even when the return regression is fragile (Cochrane, 2008); weak out of sample (Goyal & Welch).
- Profitability: forecastable and mean-reverting (Fama & French, 2000); firm-level news is mostly cash-flow news when earnings are in return units (Vuolteenaho, 2002).
- Residual income: the accounting name for a firm *level* (Ohlson, 1995).
- Beta: a valuation state only if it changes the *shape* of the firm curve, not only average returns.
- Dividend strips: a term structure of *returns* on claims (van Binsbergen, Brandt, & Koijen, 2012) — a cousin of the curve, not a factor test.

## Progress tests

A state earns its place if it moves \(\mu(n)\), \(\mathrm{pd}\), or a firm present value under a no-look-ahead vintage — not if it only raises an in-sample return \(R^2\). Cash-flow news must come from the cash-flow equation (Chen, Da, & Zhao, 2013).
