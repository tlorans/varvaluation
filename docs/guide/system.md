<p class="part-kicker">Part 03 · The framework</p>

# The VAR

<p class="you-will"><strong>You will.</strong> Write one system that models cash flows and the discount rate together.</p>

The framework models two things.

**Cash flows.** What cash arrives at each future date. That is the
path you are pricing.

**The discount rate.** The return investors require over each
coming year. When that required return is allowed to change, year
one and year ten do not share a rate, and the price is the
expectation of a product: each cash flow times the sequence of
one-period required returns along the way
([Ang and Liu, 2004](../references.md#ang-liu-2004)).

Those two objects have to be modeled *together*. If you forecast
cash in one model and the required return in another, you miss how
they move together, the two forecasts need not share a horizon, and
they can contradict each other. The price is then not determined.

The smallest system that produces both forecasts, and how they move
together, from one list of variables $X_t$ is a **vector
autoregression**: several ordinary regressions run at the same
time. That is the rest of this page.

## Two ways to write the cash-flow side

They are not the same object.

A **growth** story tracks how fast cash itself changes:
$g_t=\log(C_t/C_{t-1})$. The forecast of future $g$ *is* the
forecast of the cash-flow path. Multiplying that path by the
discount curve is a present value of the claim. In the library that
name is `g`, and `value` is the right call.

A **profitability** story tracks how much the firm earns on the
book it already has: $\mathit{roe}_t=\log(\mathrm{NI}_t/\mathrm{BE}_{t-1})$.
That is a *level* (earnings this year over last year’s book), not a
growth rate of cash paid to owners. Fama and French (2000) show
that this level is forecastable and falls back toward the
economy-wide average. That is useful, and it is a different
mapping. Feeding it to `value` treats a twelve-percent return on
book as if cash grew twelve percent. It did not.

To go from profitability to cash you still need payout (how much
of earnings is paid out) and how book evolves. Residual income —
earnings above a charge on book — is the accounting route to a
price of book ([Ohlson, 1995](../references.md#ohlson-1995)). This
handbook cites that route; it does not compute it. Until the
cash-flow name is growth, or residual income, the framework still
models both sides, but the object it reports on the cash-flow side
is a forecast of profitability, not a present value of the equity.

The firm illustration uses profitability. The landing snippet uses
growth. Keep the two names apart.

## What a VAR is

A VAR is a system of ordinary linear regressions run at the same time.
Stack the variables you care about into a vector and regress **each** of
them on **all** of them, lagged one period. With two variables $x$ and
$y$, a VAR(1) is literally two regressions:

$$
\begin{aligned}
x_{t+1} &= a_1 + b_{11} x_t + b_{12} y_t + u_{t+1}, \\
y_{t+1} &= a_2 + b_{21} x_t + b_{22} y_t + v_{t+1}.
\end{aligned}
$$

Nothing is labelled a cause. $y$ can forecast $x$ ($b_{12}\ne 0$) and
$x$ can forecast $y$ ($b_{21}\ne 0$). In matrix form,

$$
X_{t+1} = c + \Phi X_t + u_{t+1}, \qquad u\sim N(0,\Sigma).
$$

Three named objects, each with a job:

| Object | Job |
|---|---|
| $c$ | pulls every variable toward a long-run average |
| $\Phi$ | persistence: the diagonal is memory, the off-diagonals are cross-forecasts |
| $\Sigma$ | which shocks arrive together |

Gaussian shocks plus linear dynamics is what makes every future horizon
a formula you evaluate rather than a path you simulate — the same
architecture as affine term-structure models (bond yields that are a
constant plus a linear function of a few factors), applied to equity
([Ang and Liu, 2004](../references.md#ang-liu-2004), Proposition I.1).

!!! note "In words — closed form, companion, lag pair"
    **Closed form** means you evaluate a formula. You do not draw
    random paths. A **lag pair** is $(X_t, X_{t+h})$: today’s state
    and the state $h$ periods later. On a firm panel those pairs are
    formed only *inside* one firm (one `permno`, CRSP’s permanent
    identifier), so firm A is never used to forecast firm B.
    **Companion** is used in two senses. In
    time-series textbooks it is a VAR($p$) rewritten as a taller
    VAR(1) by stacking lags. On this site it also means the *fitted*
    $\Phi$ on the 80-firm slice of Section 5 — one pooled law of
    motion. `VARFit` is that fitted object.

In the library the companion is a `VARFit`. On a firm panel the call
is `estimate_var_panel`; lag pairs are formed only inside
`spec.group`. Section 5 reports

```python
from varvaluation import StateSpec, estimate_var_panel

spec = StateSpec(
    names=("roe", "beta", "bm", "r", "cay", "pi"),
    cashflow="roe",
    group="permno",
)
fit = estimate_var_panel(state, spec)
print(fit.nobs, fit.spectral_radius, fit.Phi[spec.cashflow_index(), spec.cashflow_index()])
```

``` text title="Terminal"
2240  0.995  0.458
```

$\Phi_{\mathit{roe},\mathit{roe}}=0.46$ is the pooled own-lag of
$\log(\mathrm{NI}/\mathrm{BE}_{\mathrm{lag}})$ on the **80** longest
histories in the 2015–2019 window of Section 5, not a fade coefficient
from a long firm panel
([Fama and French, 2000](../references.md#ff-2000)).
`fit.spectral_radius` is the largest absolute eigenvalue of $\Phi$.

### Forecasting is recursive bookkeeping

One step ahead: $\mathbb{E}_t[X_{t+1}] = c + \Phi X_t$. Two steps: plug
the one-step forecast back in,

$$
\mathbb{E}_t[X_{t+2}] = (I+\Phi)c + \Phi^2 X_t.
$$

By $j$ steps,

$$
\mathbb{E}_t[X_{t+j}] = (I+\Phi+\cdots+\Phi^{j-1})c + \Phi^j X_t.
$$

Today’s state dies out at the speed of $\Phi^j$. The unconditional mean
is $(I-\Phi)^{-1}c$, provided every eigenvalue of $\Phi$ sits inside the
unit circle. Every “mean reversion” statement in this library is one of
those two formulas read aloud.

A VAR($p$) is not more general in a way that matters here: it can be
rewritten as a taller VAR(1) by stacking lags (the companion form). The
honest constraint is **linearity plus Gaussianity**, which buys the
closed form at the price of no stochastic volatility in the state.

### Affine means constant plus linear

A function is **affine** in $X$ if it equals $a + b'X$: a constant plus
each element of $X$ multiplied by its own coefficient. No powers, no
products. Expected growth being affine in the state just says: a
baseline plus an adjustment for wherever the economy currently is.

When prices are exponentials of affine (or quadratic-Gaussian) objects,
every strip stays computable. That is the load-bearing modelling choice.

### Timing

Write cash-flow growth and the one-period expected return as

$$
g_{t+1} = e_1' X_{t+1}, \qquad
\mu_t = \alpha + \xi' X_t + X_t'\Lambda X_t.
$$

$\mu_t$ is known at $t$: it is the *expected* return, part of today’s
information. $g_{t+1}$ is realized at $t+1$. That asymmetry is what
makes the model a model of expected-return variation rather than
realized-return noise.

The product $\beta_t\lambda_t$ inside a **conditional CAPM** is why
$\mu_t$ is **quadratic** in $X_t$ whenever both beta and the premium
move.

!!! note "In words — CAPM, beta, premium, quadratic"
    The CAPM says expected excess return equals beta times a market
    premium. **Beta** $\beta_t$ is the slope of the firm’s excess
    return on the market’s, here a *rolling* slope, so it is a data
    series. The **premium** $\lambda_t$ is itself a function of the
    state (short rate, $\mathit{cay}$). Their product
    $\beta_t\lambda_t$ contains terms like $\beta_t\times\mathit{cay}_t$
    — a product of two elements of $X_t$. That is why $\mu_t$ is
    quadratic, and why the priced strip needs a matrix $H(n)$ rather
    than a vector $b(n)$ alone. If *either* beta or the premium is
    constant, $\Lambda=0$, $H(n)\equiv 0$, and the solution collapses
    to exponential-affine. Same class; see
    [Valuation](valuation.md). $\alpha$, $\xi$, and $\Lambda$ are just
    the intercept, the linear coefficients, and the quadratic
    coefficients of that $\mu_t$.

## Why a VAR is the right tool

Four requirements, four matches.

**Jointness by construction.** One $\Sigma$ generates the shocks to
cash flows *and* expected returns together. The covariance the price
needs cannot be set to zero by accident, because there is nowhere to
set it.

**Mean reversion for free.** A stable $\Phi$ delivers
$\mathbb{E}_t[\mu_{t+j}]$ gliding back to its unconditional mean at a
speed the data choose. A flat-forever WACC is the special case
$\Phi=0$, $X$ frozen.

**Predictability is symmetric and testable.** Do short rates forecast
dividend growth? Does $\mathit{cay}$ forecast betas? Those are
coefficients of $\Phi$, with Newey–West standard errors (Section 3:
standard errors honest about overlapping annual pairs). The dynamic
relations are estimated and can be rejected.

**Gaussian linearity makes the price closed-form.** Linear dynamics
plus normal shocks imply that every cumulated $S_n=\sum_{i\le n}(g_{t+i}-\mu_{t+i-1})$
is conditionally normal, so $\mathbb{E}_t[e^{S_n}]$ is a two-line
lognormal formula. Change the distribution and you lose the analytic
price.

## Eigenvalues, in words

A variable **mean-reverts** if, when it sits above its long-run
average, it tends to fall back (and vice versa). The speed of that
snap-back is governed by the **eigenvalues** of $\Phi$. An eigenvalue
of $0.9$ means a deviation is still 90% alive after one period, and
$0.9^{10}\approx 35\%$ alive after ten. Near $1$: long memory. Near
$0$: fast forgetting.

`fit.spectral_radius` is the largest absolute eigenvalue. The model
refuses to construct if that number is $\ge 1$: the unconditional mean
does not exist, and the recursions have nowhere to settle.

![Mean-reverting expected-return paths](../assets/figures/mean_reversion.png)
<p class="figure-caption">$\mathbb{E}_t[\mu_{t+n}] = \bar\mu + \phi^{\,n-1}(\mu_1-\bar\mu)$. High persistence ($\phi=0.9$) keeps today’s rate alive for a decade. A flat WACC keeps it alive forever.</p>

## Where the joint distribution enters the price

Because $X$ is Gaussian and $g$, $\mu$ are (at most) quadratic in $X$,
the sum $S_n$ is **conditionally normal** given $X_t$: given what we
know today, the uncertain quantity is a bell curve whose mean and
variance depend on $X_t$. If $S$ is normal, $e^S$ is **lognormal**
(always positive, right-skewed) and

$$
\mathbb{E}_t[e^{S_n}]
  = \exp\!\bigl(\underbrace{\mathbb{E}_t[S_n]}_{\text{point forecasts}}
    + \tfrac12\underbrace{\mathrm{Var}_t[S_n]}_{\text{the new part}}\bigr).
$$

The average of the exponential beats the exponential of the average.
The gap grows with variance. That is Jensen’s inequality: $S\mapsto e^S$
is convex, so uncertainty **raises** the strip before risk is priced.

Expand the variance:

$$
\mathrm{Var}_t[S_n]
  = \mathrm{Var}_t[\textstyle\sum g]
  + \mathrm{Var}_t[\textstyle\sum \mu]
  - 2\,\mathrm{Cov}_t[\textstyle\sum g,\ \textstyle\sum \mu].
$$

- Uncertainty about growth raises value (convexity).
- Uncertainty about discount rates also raises value (same reason).
- The **covariance** is the economically important term. If good news
  about growth arrives together with *higher* discount rates, then
  $\mathrm{Cov}>0$, the $-2\,\mathrm{Cov}$ term is negative, and value
  is **lower** than any DCF that ignores the interaction.

That is why both forecasts have to come from one system. It is not only
about variance decompositions after the fact
([Campbell, 1991](../references.md#campbell-1991)). **The joint
distribution enters the price level.** The $-2\,\mathrm{Cov}$ term is
the precise, quantitative reason a split DCF is not an approximation
but a different (and generally inconsistent) object.

The [Valuation](valuation.md) page turns this Gaussian expectation into
two recursions. [Estimation](estimate.md) shows how $(\Phi,c,\Sigma)$
are measured.
