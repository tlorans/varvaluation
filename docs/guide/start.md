<p class="part-kicker">Part 02 · Getting started</p>

# Start here

<p class="you-will"><strong>You will.</strong> Discount the same claim at one rate and at a moving curve, and name the objects you will carry.</p>

The landing printed three numbers. Reproduce them.

```text
uv run python examples/flat_vs_curve.py
```

```text
mu(1)  2.37%
mu(10) 4.09%
flat PV vs curve  +8.0%
```

A ten-year stream of one-dollar cash flows — one dollar at each year, nothing after — is worth 8% more if you discount every date at today’s one-year rate than if you use the curve. Year one wants 2.37%. Year ten wants 4.09%. A single rate is a flat line through that gap.

Write $\mu(1)$ for the one-year rate and $\mu(10)$ for the ten-year rate on the curve. Those are the names in the printout.

The script is [`examples/flat_vs_curve.py`](https://github.com/tlorans/varvaluation/blob/main/examples/flat_vs_curve.py). It draws two series, estimates how each depends on yesterday’s values of both, and values the claim two ways. There is no download and no firm-level vendor file. You already have the object.

## Why the gap exists

Present value is not a forecast of cash flows divided by a forecast of the rate. It is the expectation of a *product*: each cash flow times a path of one-period expected returns ([Ang and Liu, 2004](../references.md#ang-liu-2004), eq. 2). The average of a product is not the product of the averages: $\mathbb{E}[XY]\ne\mathbb{E}[X]\,\mathbb{E}[Y]$. How cumulated growth and cumulated expected returns move together sits in the price. Separate models of the two sides omit that co-movement, need not share a horizon, and can contradict each other.

The smallest statistical object that produces both forecasts, and how they move together, from one list of variables $X_t$ is a **vector autoregression**: several ordinary regressions run at the same time. That is [Part 03](system.md). Before you write it down, the next page derives the product and names the pieces (one horizon’s contribution, the rate at each horizon, the whole curve). They are collected in [Why a product](introduction.md#objects-and-words).

## Where you go next

You have felt the error. The [research program](program.md) is which named variables move that gap. The next hour is the *framework*: one joint system of regressions, so both sides of the product come from the same law, and names for every coordinate.

Public files — Ken French portfolios and FRED macros, then a discount curve estimated from them — are [Part 04](data.md). Individual firms are [Part 06](wrds.md). Do not start there.
