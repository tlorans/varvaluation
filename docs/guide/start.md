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

A ten-period unit claim — one dollar at each horizon, nothing after — is worth 8% more if you discount every date at today’s $\mu(1)$ than if you use the fitted curve. Year one wants 2.37%. Year ten wants 4.09%. A single rate is a flat line through that gap.

The script is [`examples/flat_vs_curve.py`](https://github.com/tlorans/varvaluation/blob/main/examples/flat_vs_curve.py). It draws a two-state VAR, estimates it, and values the claim two ways. There is no download and no WRDS. You already have the object.

## Why the gap exists

Present value is not a forecast of cash flows divided by a forecast of the rate. It is the expectation of a *product*: each cash flow times a path of one-period expected returns ([Ang and Liu, 2004](../references.md#ang-liu-2004), eq. 2). $\mathbb{E}[XY]\ne\mathbb{E}[X]\,\mathbb{E}[Y]$. The covariance of cumulated growth and cumulated expected returns sits in the price. Separate models of the two sides omit it, need not share a horizon, and can contradict each other.

The smallest statistical object that produces both forecasts, and their covariance, from one state $X_t$ is a vector autoregression. That is [Part 03](system.md). Before you write it down, keep the words next to you: product, strip, spot curve, term structure. They are collected in [Why a product](introduction.md#objects-and-words), with the derivation.

## Where you go next

You have felt the error. The [research program](program.md) said what would count as explaining it from data. The next hour is the joint system: one law of motion, a closed form for the product, and names for every coordinate.

Public data — Ken French, FRED, a real $\mu(n)$ — is [Part 04](data.md). Firms and WRDS are [Part 06](wrds.md). Do not start there.
