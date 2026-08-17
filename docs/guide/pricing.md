<p class="part-kicker">Part 06 · Firms</p>

# Does the model fit the market?

<p class="you-will"><strong>You will.</strong> Compare every model present value to the same day's market equity, and read the typical log error.</p>

The framework produces a present value: expected cash, discounted
along the curve. The market produces another number: what investors
paid that day. If the model explains prices, those two numbers
should be close, not just for three names you picked, but for the
whole cross-section.

Write $PV$ for the model value and $ME$ for market equity, in the
same units. The ratio $PV/ME$ is 1 when they agree, 2 when the
model is twice the market, $1/2$ when it is half. The **root mean
square error of the log ratio** — $\mathrm{RMSE}$ of
$\log(PV/ME)$ — is the typical size of that miss. A 2× overprice
and a ½× underprice are the same error ($\lvert\log 2\rvert$). An
RMSE of 0 is a perfect fit. An RMSE of $0.81$ is a typical miss of
about $e^{0.81}\approx 2.2$ times.

That is the diagnostic. A median ratio far from 1 is often just
the discount intercept: raise it and every price falls. After you
choose the intercept so the *median* firm matches, the RMSE says
whether the *shape* of the model lines up with the market.

## The call

`pricing_errors` values every row and scores the cross-section.
The state must carry the named variables, the current cash-flow
level (`div`), and market equity (`me`).

```python
from varvaluation import pricing_errors
from varvaluation.pricing import as_of, calibrate_alpha

cross = as_of(state, panel, on=last_date)
raw = pricing_errors(model, cross)
print(raw.n, raw.median_pv_me, raw.rmse_log_pv_me, raw.corr_log)

alpha_star, cal = calibrate_alpha(fit, xi, Lambda, cross, alpha0=0.02)
print(alpha_star, cal.median_pv_me, cal.rmse_log_pv_me)
```

| Number | What it answers |
|---|---|
| Median $PV/ME$ | Is the *level* right? |
| RMSE of $\log(PV/ME)$ | How large is the typical miss? |
| Corr$(\log PV,\log ME)$ | Do expensive model names have expensive market prices? |
| Share within 2× | How often are we in the same octave as the market? |

A high correlation with a high RMSE means the model ranks firms
well and still mis-scales many of them. That is a better report
than three anecdotes.

## What the loop found

Eighty dividend-paying firms, 30 September 2019, cash-flow name
`g`, 2000–2019 window. Four ways to write the cash-flow equation.
[`examples/fit_market.py`](https://github.com/tlorans/varvaluation/blob/main/examples/fit_market.py)
scores them.

```text
uv run python examples/fit_market.py
```

**Raw intercept $\alpha=0.02$.** Every spec is rich. Median
$PV/ME$ sits between 3 and 5. RMSE of the log is 1.35–1.65
(typical miss of about 4×). Only about one firm in five is within
2× of the market. Correlation of the logs is already 0.95: the
ranking is decent; the level is not.

**Intercept chosen so the median ratio is about 1**
($\alpha=0.067$). RMSE of the log falls to about **0.81**. Sixty
percent of names land within 2× of the market. Correlation stays
0.95. Shutting the short rate and inflation out of the cash-flow
equation barely moves the RMSE. The intercept does the work.

| Cash-flow equation | RMSE of $\log(PV/ME)$, raw | RMSE after $\alpha$ |
|---|---|---|
| Unrestricted | 1.57 | 0.81 |
| No short rate or inflation in $g$ | 1.65 | **0.81** |
| Also no consumption–wealth gap in $g$ | 1.53 | 0.82 |
| $g$ on its own lag only | 1.35 | 0.83 |

The walkthrough prints the same two lines, then the three names at
the calibrated intercept. Those three are no longer 10× toys; they
are still not a tight fit. An RMSE of 0.81 is a real diagnostic
and a large remaining error. It is not evidence that a name with
$PV>ME$ is cheap.

## What would count as better

A next specification wins if it **lowers the RMSE** after the
median has been set to one — not if it makes three familiar permnos
look prettier. A longer sample, or a cash-flow equation whose
long-horizon growth is not several percent a year above a sensible
rate, is the place to look. The loop is the test.
