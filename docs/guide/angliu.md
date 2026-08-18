<p class="part-kicker">Part 06 · Check</p>

# Ang and Liu (2004)

<p class="you-will"><strong>You will.</strong> Rebuild the paper this package implements, one object at a time, on the paper’s sample. The last figure is the December 2000 curve. The last table asks whether that curve is still there after 2000.</p>

The closed-form recursions are [Ang and Liu (2004)](../references.md#ang-liu-2004). The earlier pages used a synthetic state (seed 7). This page uses **their** state, **their** window, and **their** valuation date. A single command runs the whole path; the sections below are that command, unpacked.

```text
uv add "varvaluation[data]"
uv run python examples/reproduce_angliu2004.py
```

```mermaid
flowchart LR
  A["1 · Public files"] --> B["2 · State X"]
  B --> C["3 · λ_t"]
  C --> D["4 · VAR"]
  D --> E["5 · μ_t(n)"]
  E --> F["6 · Perpetuity"]
  F --> G["7 · After 2000"]
```

Offline, no downloads: `--synthetic`. Paper sample only: `--paper-only`. Compustat $\Delta p$: `--wrds` (needs `[wrds]` and credentials).

---

## 1 · Public files

Ken French value-weight book-to-market deciles, with and without dividends, plus the macro block (FF3, one-year Treasury, CPI, $\mathit{cay}$). Nothing here is WRDS.

```python
from varvaluation.data import load_bm_deciles, load_macro, prepare_portfolio_state

total, capgains = load_bm_deciles()
macro = load_macro()
```

On the vintage this page was built from:

| File | Window |
|---|---|
| BE/ME deciles | 1926-07 → 2026-06 |
| Macro (FF3 + GS1 + CPI) | 1926-07 → 2026-06 |
| $\mathit{cay}$ (published, else FRED reconstruction) | 1959-01 → 2026-01 |

The paper’s **estimation** window is shorter. Cut it in the next step, not here — $\beta$ needs sixty months of history before July 1965.

---

## 2 · Name the state and cut the sample

Their six coordinates, overlapping annual pairs, Newey–West 12:

```python
from datetime import date
from varvaluation.angliu import BM_START, PAPER_END, VALUATION_DATE, paper_spec

spec = paper_spec()
# StateSpec(names=("g","beta","dpo","r","cay","pi"),
#           cashflow="g", horizon=12, nw_lags=12)

state = prepare_portfolio_state(
    total, capgains, macro, spec,
    portfolio="D6",              # growth D1, neutral D6, value D10
    start=BM_START,              # "1965-07"
    end=PAPER_END,               # "2000-12"
)
```

| Name | Paper | What the loader builds |
|---|---|---|
| $g$ | Hodrick trailing-12m log dividend growth | `total − capgains`, summed twelve months, then $\log(D_t/D_{t-12})$ |
| $\beta$ | 60-month rolling CAPM, window ends at $t-1$ | log excess return on the FF market |
| $\Delta p$ (`dpo`) | Compustat earnings | **capital-gains proxy** on this path; Compustat on `--wrds` |
| $r$ | one-year rate, continuously compounded | FRED GS1, $\log(1+y)$ |
| $\mathit{cay}$ | Lettau–Ludvigson | published CSV, else FRED reconstruction |
| $\pi$ | 12-month log CPI | FRED CPIAUCSL |

$n=426$ monthly observations for each decile on 1965-07 → 2000-12. Valuation date: **31 December 2000**.

The one construction that is not theirs is `dpo`. Keep going; the check for that is step 8.

---

## 3 · The premium $\lambda_t$

One overlapping annual regression, not a second VAR:

$$
y^m_{t+1} - r_t = b_0 + b_r r_t + b_{\mathit{cay}}\,\mathit{cay}_t + \varepsilon_{t+1}.
$$

```python
from varvaluation.angliu import (
    expected_return_loadings, fit_premium, lambda_series,
)

rp = fit_premium(macro, BM_START, PAPER_END)
xi, Lambda = expected_return_loadings(spec, rp)
lam = lambda_series(macro, rp)
```

`ExpectedReturnSpec(premium=("cay",))` turns $(b_0,b_r,b_{\mathit{cay}})$ into $(\xi,\Lambda)$ so that

$$
\mu_t = \alpha + r_t + \beta_t\lambda_t = \alpha + \xi'X_t + X_t'\Lambda X_t.
$$

**Table. Risk premium, Ken French market, July 1965 – December 2000.** $n=426$, $R^2=0.187$.

| | estimate | s.e. | $t$ |
|---|---:|---:|---:|
| $b_0$ | $+0.095$ | $0.062$ | $1.52$ |
| $b_r$ | $-0.59$ | $0.89$ | $-0.66$ |
| $b_{\mathit{cay}}$ | $+3.02$ | $0.96$ | $3.16$ |

$\mathit{cay}$ is the in-sample instrument they used. The short-rate slope is not identified. $\alpha$ is not in this table: it is the portfolio’s own annualised CAPM intercept, computed next.

---

## 4 · One VAR per portfolio

```python
from varvaluation import ValuationModel, estimate_var
from varvaluation.angliu import capm_alpha, constant_capm_rate

alpha, beta_capm = capm_alpha(total, macro, "D6", start=BM_START, end=PAPER_END)
fit = estimate_var(state, spec)
model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=alpha)

X = state.select(list(spec.names)).filter(
    state["date"] <= VALUATION_DATE
).to_numpy()[-1]
```

`from_var` refuses a companion with spectral radius $\ge 1$. On this vintage every decile is inside: $\rho(\Phi)=0.75$ (D1), $0.74$ (D6), $0.82$ (D10).

**Table. Companion $\Phi$ for Neutral (D6), paper sample.** Newey–West s.e. in parentheses. Row = equation, column = lag.

| eq | $g$ | $\beta$ | $\Delta p$ | $r$ | $\mathit{cay}$ | $\pi$ |
|---|---:|---:|---:|---:|---:|---:|
| $g$ | $-0.32$ | $+0.00$ | $-0.01$ | $-0.94$ | $-0.17$ | $+0.85$ |
| | $(0.12)$ | $(0.26)$ | $(0.09)$ | $(0.76)$ | $(0.54)$ | $(0.58)$ |
| $\beta$ | $+0.01$ | $+0.42$ | $-0.02$ | $+0.53$ | $-0.54$ | $-0.53$ |
| $r$ | $+0.06$ | $+0.03$ | $-0.04$ | $+0.57$ | $+0.02$ | $+0.26$ |
| $\mathit{cay}$ | $-0.01$ | $-0.01$ | $-0.02$ | $-0.01$ | $+0.56$ | $+0.21$ |
| $\pi$ | $+0.03$ | $+0.07$ | $-0.03$ | $-0.16$ | $-0.11$ | $+0.89$ |

Own-lags on $r$, $\mathit{cay}$, and $\pi$ are the persistent block. The $g$ row is noisy — that is the cash-flow equation on overlapping annual dividends, not a bug.

---

## 5 · The spot curve at December 2000

```python
curve = model.spot_curve(X, n=30)          # Polars: maturity, mu, …
rates = model.spot_rates(X, n=30)

# Identity that must hold:
assert abs(rates[0] - (alpha + xi @ X + X @ Lambda @ X)) < 1e-12
```

**Table. $\mu_t(n)$ on 31 December 2000.**

| Portfolio | $\mu(1)$ | $\mu(5)$ | $\mu(10)$ | $\mu(30)$ | slope 30−1 |
|---|---:|---:|---:|---:|---:|
| Growth (D1) | 7.30% | 7.98% | 7.87% | 8.24% | $+0.94$ pp |
| Neutral (D6) | 10.64% | 10.39% | 10.19% | 10.94% | $+0.30$ pp |
| Value (D10) | 12.99% | 13.68% | 15.04% | 16.47% | $+3.48$ pp |

Identity holds to machine precision on all three. All three slopes are positive. That is the paper’s December 2000 picture: an upward curve, cheap at the short end relative to a constant CAPM.

![December 2000 spot curves](../assets/figures/angliu_dec2000_curves.png)
<p class="figure-caption"><strong>Figure 1.</strong> $\mu_t(n)$ for D1 / D6 / D10 at the paper’s valuation date. Dashed lines are each portfolio’s constant CAPM rate $\alpha+\bar r+\bar\beta\,\bar\lambda$. Source: <code>examples/reproduce_angliu2004.py</code>.</p>

---

## 6 · Unit perpetuity vs a flat rate

They value a perpetuity of an *expected* cash flow of $1, so the cash-flow recursion is switched off and only the curve matters.

```python
from varvaluation.angliu import perpetuity_comparison

capm_rate = constant_capm_rate(state, lam, alpha=alpha, beta_capm=beta_capm)
perp = perpetuity_comparison(model, X, capm_rate=capm_rate)
# perp["v_ts"], perp["v_capm"], perp["gap_capm_pct"]
```

The gap is $(V_{\mathrm{flat}}-V_{\mathrm{TS}})/V_{\mathrm{TS}}$. Negative means the flat rate **undervalues**.

**Table. Unit perpetuity at December 2000.**

| Portfolio | $V_{\mathrm{TS}}$ | $V_{\mathrm{CAPM}}$ | gap | $\mu_{\mathrm{CAPM}}$ |
|---|---:|---:|---:|---:|
| Growth (D1) | 11.81 | 11.11 | **−5.9%** | 8.62% |
| Neutral (D6) | 8.95 | 7.44 | **−16.9%** | 12.62% |
| Value (D10) | 6.19 | 6.11 | **−1.3%** | 15.16% |

Same *sign* as the paper. Smaller *percentage* than their “over 50%”: they compared to a textbook historical DDM rate; this table compares to the model’s own constant CAPM, where the fitted $\bar\lambda$ is only about 4%. We do not inflate that constant to chase 50%.

**Table. Share of $\mathrm{var}(\mu_t(n))$ at $n=1$ and $n=30$ (D6).**

| $n$ | $g$ | $\beta$ | $\Delta p$ | $r$ | $\mathit{cay}$ | $\pi$ |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0 | −1 | 0 | 6 | **95** | 0 |
| 30 | 0 | −2 | −1 | −1 | 46 | **58** |

Short end: the premium. Long end: $\mathit{cay}$ and inflation. Rolling $\beta$ does not dominate on this vintage.

![Variance shares](../assets/figures/angliu_varshare.png)
<p class="figure-caption"><strong>Figure 2.</strong> Share of $\mathrm{var}(\mu_t(n))$ by state, D1 / D6 / D10. Short end is $\mathit{cay}$. Long end is $\mathit{cay}$ and $\pi$.</p>

Industries on the same recipe (January 1964 – December 2000): Food, Oil, Rtail, Banks are upward and below CAPM (gaps −8% to −27%). Util is refused ($\rho(\Phi)=1.03$). Softw has no trailing-dividend pairs. Steel slopes down because $\alpha=-4.7\%$ pins $\mu(1)$ above the tail. Failures are printed, not dropped.

---

## 7 · Extension: the same system after 2000

Not in the 2004 paper. Re-estimate on July 1965 → latest $\mathit{cay}$ (January 2026 on this vintage) and value at the **last** month.

```python
rp_long = fit_premium(macro, BM_START, "2026-01")
xi_long, Lam_long = expected_return_loadings(spec, rp_long)

state_long = prepare_portfolio_state(
    total, capgains, macro, spec,
    portfolio="D6", start=BM_START, end="2026-01",
)
# then estimate_var / from_var / spot_rates as above, at state_long["date"][-1]
```

**Table. Premium, long sample.** $n=720$, $R^2=0.050$.

| | estimate | $t$ |
|---|---:|---:|
| $b_0$ | $+0.096$ | $3.47$ |
| $b_r$ | $-0.74$ | $-1.51$ |
| $b_{\mathit{cay}}$ | $+0.67$ | $1.65$ |

The $\mathit{cay}$ slope that was $t=3.16$ on 1965–2000 is $t=1.65$ here. That is the Goyal–Welch fade, not a software defect.

**Table. Spot curve at January 2026 (long-sample companion).**

| Portfolio | $\mu(1)$ | $\mu(30)$ | slope | TS gap vs CAPM |
|---|---:|---:|---:|---:|
| Growth (D1) | 4.74% | 8.38% | $+3.65$ pp | **−17.3%** |
| Neutral (D6) | 6.99% | 10.42% | $+3.42$ pp | **−15.9%** |
| Value (D10) | 7.40% | 11.33% | $+3.93$ pp | **−19.9%** |

The term-structure gap survived. It is larger than at December 2000, because both the short rate and the fitted premium are low. A flat CAPM at the sample mean is the wrong rate for every horizon of a 2026 growth name.

---

## 8 · Compustat $\Delta p$ (optional, WRDS)

The paper’s payout state uses Compustat earnings. The public path proxies earnings growth with the annual capital-gains return. Those are not the same series.

```text
uv add "varvaluation[data,wrds]"
uv run python examples/reproduce_angliu2004.py --wrds
```

```python
from varvaluation.angliu.payout import (
    attach_compustat_dpo, crsp_vw_returns, market_compustat_dpo, proxy_vs_compustat,
)

total_m, cap_m = crsp_vw_returns(start="1960-01", end="2000-12-31")
dpo_cs = market_compustat_dpo(start="1960-01", end="2000-12-31")
proxy_vs_compustat(total_m, cap_m, dpo_cs, portfolio="MKT")
# n=445, corr=−0.12, sd proxy=0.16, sd Compustat=0.08
```

This is a **market** aggregate (TTM CRSP dividends over TTM Compustat NI), not a rebuilt French decile. Correlation **−0.12**. The proxy is not a stand-in.

The *curve* is more robust. On the CRSP value-weighted market at November 2000, $\mu(1)=9.19\%$ under either $\Delta p$; $\mu(30)$ is 9.8% (proxy) vs 9.7% (Compustat). Both upward, both below CAPM. $\Delta p$ is not what moves $\mu_t$ at the short end; $\mathit{cay}$ is.

---

## What matched the paper, and what did not

| Claim in §IV | This vintage | Match? |
|---|---|---|
| Dec 2000 curve upward | D1 +0.9 pp, D6 +0.3 pp, D10 +3.5 pp | Yes |
| Curve below a constant CAPM | $\mu(1)$ 7.3 / 10.6 / 13.0% vs 8.6 / 12.6 / 15.2% | Yes |
| Short-horizon variance is the premium | $\mathit{cay}\approx 95\%$ of $\mathrm{var}(\mu(1))$ | Yes |
| $\mathit{cay}$ forecasts $\lambda_t$ in-sample | $t=3.16$ | Yes |
| $\mu(1)=\alpha+\xi'X+X'\Lambda X$ | machine precision | Yes — the implementation check |
| Mispricing over 50% vs a *textbook* DDM | 6–17% vs the *fitted* CAPM | Same sign, smaller |

Two constructions also differ, so cells will not match their typesetting to the third decimal: revised Ken French / FRED / $\mathit{cay}$ vintages, and the capital-gains $\Delta p$ unless you pass `--wrds`.

A failed identity, or a downward curve at December 2000 on the *paper* sample, would be a bug. Neither happened.

---

## After this page

You should be able to:

1. Point at the six objects in order — files, $X_t$, $\lambda_t$, $\Phi$, $\mu_t(n)$, perpetuity gap — and the snippet that produces each one.
2. State which construction is not the paper’s (`dpo`) and how to turn it off.
3. Say whether the term-structure gap survived the post-2000 sample — it did.
4. Separate a vintage difference from a failed identity.

The two recursions: [The two recursions](curve.md). Full citation: [Ang and Liu (2004)](../references.md#ang-liu-2004). The script: `examples/reproduce_angliu2004.py`.
