<p class="part-kicker">Part 03 · The joint system</p>

# Present value

<p class="you-will"><strong>You will.</strong> Evaluate the closed form for the product and the spot curve it implies.</p>

Given the VAR of [The VAR](system.md) and a one-period expected return
$\mu_t=\alpha+\xi'X_t+X_t'\Lambda X_t$, the numerator
$\mathbb{E}_t[C_{t+n}]/C_t$ and the spot curve $\mu_t(n)$ are exact
functions of $X_t$
([Ang and Liu, 2004](../references.md#ang-liu-2004), Propositions I.1
and II.1). Three library calls use those objects differently.

- `value` multiplies the VAR numerator by the curve. That product *is*
  the present value of the [Introduction](introduction.md) **when**
  `spec.cashflow` is log cash-flow growth.
- `perpetuity` freezes the numerator at $1$ and isolates the curve.
- A path you already have — analyst forecasts, a residual-income
  schedule, an internal model — is discounted at `spot_rates`. The VAR
  is then required only for the denominator
  ([Brennan, 1997](../references.md#brennan-1997)).

Section 5 reports the second object. The cash-flow slot there is a
profitability *level*, so `value` is the wrong call.

```python
from varvaluation import ValuationModel

model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.02)
X = state.filter(pl.col("permno") == 10026).select(list(spec.names)).to_numpy()[-1]
rates = model.spot_rates(X, n=10)
perp = model.perpetuity(X, n=40)
```

``` text title="Terminal"
spot mu(n) %   n=1, 5, 10: 5.51, 9.31, 9.47
unit_curve_pv=24.70  terminal_spot=2.84%
```

At permno 10026 on 30 September 2019 the curve slopes up. The
denominator is finite. $24.70$ is the present value of a **unit** cash
flow under that curve, not an equity value. At the firm the cash-flow
state is $\mathit{roe}=\log(\mathrm{NI}/\mathrm{BE}_{\mathrm{lag}})$;
`cashflow_expectation` would treat that series as log growth and
should not be published as a price. The path
$\mathbb{E}_t[\mathit{roe}_{t+n}]$ is in Section 5.

`from_var` refuses a companion with spectral radius $\ge 1$
(`NonStationaryVARError`). Negative *short* rates are allowed. A
non-positive *terminal* rate raises `PerpetuityDivergesError`.

If $\Lambda = 0$, the quadratic term is off, $H(n)\equiv 0$, and the
solution is exponential-affine — the case in which beta or the premium
is constant, the setting of earlier affine present-value models
([Ang and Liu, 2001](../references.md#ang-liu-2001)). Letting **both**
move at once is what the $H(n)$ recursion is for. Same class. No
second solver.

---

## 1. Two sides of every strip

A present value is a sum of strips. Each strip has a **numerator** (what you
expect to receive $n$ years from now) and a **denominator** (how hard you
discount that receipt).

A constant-rate DCF writes the denominator as $(1+r)^n$ with one $r$ for
all $n$, and takes the numerator from a spreadsheet. Here both objects are
forecasts from the VAR of $X_t$. `value` multiplies them.

!!! note "In words — strip"
    Think of the claim as a bundle of zero-coupon equity claims, one
    per year. Each **strip** is “the cash flow that arrives in year
    $n$, and nothing else.” The present value is the sum of the
    strips. The **numerator** of strip $n$ is how large you expect
    that cash flow to be. The **denominator** is how hard you
    discount it. The spot rate $\mu_t(n)$ is defined so that
    dividing the expected cash flow by $e^{n\mu_t(n)}$ recovers the
    strip — including the covariance corrections of Section 2.1.

!!! note "Three numerators"
    `value(X, C)` takes expected cash flows *and* the discount curve from
    $X_t$. `perpetuity(X)` freezes the numerator at $1$ so only the curve
    can move. A list of cash flows you already have is discounted at
    `spot_rates(X)` — the two-step workflow with the VAR supplying only
    the denominator.

---

## 2. Cash flows in growth form

Write the cash flow as a product of growth rates. Let $g$ stand for
whatever you named as `spec.cashflow` — log dividend growth on a
portfolio, log ROE at a firm:

$$
g_{t+i} = \log\frac{C_{t+i}}{C_{t+i-1}},
\qquad
C_{t+n} = C_t \exp\!\Bigl(\sum_{i=1}^{n} g_{t+i}\Bigr).
$$

Then

$$
\frac{\mathbb{E}_t[C_{t+n}]}{C_t}
  = \mathbb{E}_t\!\left[\exp\!\Bigl(\sum_{i=1}^{n} g_{t+i}\Bigr)\right].
$$

This is **not** $\exp(\mathbb{E}_t[\sum g])$. Because $g$ is random, Jensen
adds a variance term. If $S_n = \sum_{i\le n} g_{t+i}$ is Gaussian,

$$
\mathbb{E}_t[e^{S_n}]
  = \exp\!\bigl(\mathbb{E}_t[S_n] + \tfrac12\mathrm{Var}_t[S_n]\bigr).
$$

The first piece is a point forecast of growth. The second is new:
uncertainty about growth **raises** expected cash flow in levels. Both
pieces are produced by the VAR. You do not type them in.

!!! tip "A modelling object, not a spreadsheet"
    Nothing in this construction says “paste next year’s consensus EPS.”
    $\mathbb{E}_t[C_{t+n}]$ is whatever the $g$ (or `roe`) **equation of
    the VAR** forecasts, horizon by horizon, given today’s $X_t$. If that
    equation is poorly estimated, the numerator is poorly estimated. There
    is no side door.

---

## 3. The cash-flow recursion

$g$ is one row of a Gaussian VAR,

$$
X_{t+1} = c + \Phi X_t + u_{t+1}, \qquad u\sim N(0,\Sigma).
$$

Let $e_1$ be the unit vector that picks `spec.cashflow` (so $g_t = e_1'X_t$).
Then $S_n$ is a linear function of the path of $X$, hence Gaussian, and
$\mathbb{E}_t[e^{S_n}]$ is exponential-**affine** in today’s state:

$$
\frac{\mathbb{E}_t[C_{t+n}]}{C_t}
  = \exp\!\bigl(\bar a(n) + \bar b(n)'X_t\bigr).
$$

No discounting enters this expectation, so there is no quadratic $H(n)$
term. The coefficients start at

$$
\bar a(1) = e_1'c + \tfrac12 e_1'\Sigma e_1,
\qquad
\bar b(1) = \Phi'e_1
$$

and iterate

$$
\bar a(n+1)
  = \bar a(n) + e_1'c + \bar b(n)'c
  + \tfrac12(e_1+\bar b(n))'\Sigma(e_1+\bar b(n)),
$$

$$
\bar b(n+1) = \Phi'(e_1 + \bar b(n)).
$$

That is `model.cashflow_recursion(n)` and
`model.cashflow_expectation(X, n)`.

### What the symbols mean in words

- $\bar b(1) = \Phi'e_1$ is “how does **today’s entire state** forecast
  **next period’s** cash-flow growth?” Every column of the $g$ (or `roe`)
  row of $\Phi$ is in there.
- $\bar b(n)$ accumulates those forecasts $n$ steps out. It is the
  loading of **cumulated** expected growth on $X_t$.
- $\bar a(n)$ collects intercepts and Jensen terms along the way. The
  $\tfrac12(\,\cdot\,)'\Sigma(\,\cdot\,)$ pieces are
  $\tfrac12\mathrm{Var}(\text{cumulated growth shocks})$.

A state $s$ moves the numerator **only** if it loads on the cash-flow
equation: $\Phi[\texttt{cashflow}, s] \ne 0$. If that entry is zero, $s$
can still move the **discount curve** (through $\beta$, $r$, $\mathit{cay}$,
$\Lambda$) without moving expected cash flows.

`isolate_channels(..., on="cashflow")` zeros those $\Phi$ entries on
purpose, so you can see the numerator channel by itself.

---

## 4. The priced recursion

The cash-flow recursion ignored discounting. The **priced** recursion
does not. Each strip of the price–cash-flow ratio is the expectation of
an exponential of cumulated growth *minus* cumulated expected returns.
Under the quadratic-Gaussian law that expectation is

$$
\exp\!\bigl(a(n) + b(n)'X_t + X_t' H(n) X_t\bigr).
$$

$H(n)$ is there because $\mu_t$ is quadratic in $X_t$ whenever $\beta_t$
and $\lambda_t$ both move. `model.price_recursion(n)` returns
$(a,b,H)$. The first step is

$$
a(1) = -\alpha + e_1'c + \tfrac12 e_1'\Sigma e_1, \qquad
b(1) = -\xi + \Phi'e_1, \qquad
H(1) = -\Lambda,
$$

and the rest is a matrix Riccati.

!!! note "In words — Riccati, log-linearization"
    A **Riccati** recursion is a matrix iteration that contains a
    quadratic term in the previous matrix — here, $H(n)$ feeds
    $H(n+1)$ through $\Sigma$. Bond models use the same device
    whenever yields are quadratic in the state. If
    $\det(I-2\Sigma H(n))$ leaves the positive reals,
    `RecursionDivergedError` is raised: the quadratic term has blown
    up and the strip is no longer a well-defined expectation.

    A **log-linearization**
    ([Campbell and Shiller, 1988](../references.md#campbell-shiller-1988))
    is a different trick: replace a curved identity
    $\log(1+e^{x})\approx\text{constant}+\rho\,x$ by a first-order
    Taylor expansion around a typical price–dividend ratio. It is
    accurate near that typical ratio and drifts when prices or
    growth are far from typical. Here the relations are written in
    logs from the start, so the closed form is exact *inside the
    Gaussian-VAR class* — which is why it does not break for
    high-growth or extreme-multiple names the way a log-linear
    identity does. Exact inside the class is not exact in the world.

When $\Lambda=0$, $H(n)\equiv 0$ and the strip is exponential-affine:
a constant beta with a moving premium, or a moving beta with a constant
premium. Letting **both** move at once is what the $H(n)$ recursion is
for.

---

## 5. Putting the two sides together

The spot rate $\mu_t(n)$ is defined so that

$$
\frac{\mathbb{E}_t[C_{t+n}]}{C_t}\Big/\exp\!\bigl(n\,\mu_t(n)\bigr)
$$

is the contribution of horizon $n$ to the price–cash-flow ratio. The
left side is one term of the pricing sum — the expectation of a
product. The right side says: take the *expected* cash flow at horizon
$n$ and discount it at one horizon-specific rate $\mu_t(n)$. Summing
over $n$ recovers the full price. Each $\mu_t(n)$ internally contains
the covariance corrections of [The VAR](system.md); the two-step
workflow (forecast, then discount) survives, only the single WACC is
replaced by a curve.

In coefficients, $A(n) = (\bar a(n)-a(n))/n$, and likewise for $B$ and
$G$. The $a,b,H$ recursion is the priced counterpart of
$\bar a,\bar b$; their difference *is* the curve: the cash-flow
recursion ignores discounting, the priced recursion includes it, and
dividing by $n$ turns a cumulated object into a per-period spot rate.
Under stationarity, $\mu_t(n)\to\bar\mu$ as $n\to\infty$. The curve
can slope up, down, or be humped, and it moves with $X_t$.

`model.value(X, C)` is then

$$
V_t
  = \sum_{n=1}^{N}
      C_t\cdot
      \frac{\mathbb{E}_t[C_{t+n}]/C_t}{\exp\!\bigl(n\,\mu_t(n)\bigr)}
  + \text{tail at }\mu_t(N).
$$

Both the numerator and the denominator are functions of the **same** $X_t$
and the **same** $(\Phi, c, \Sigma)$. The covariance between growth and
discount rates is inside $\Phi$ and $\Sigma$, estimated once, and enters
**both** recursions. A valuation that conditions cash flows but not the
rate, or the rate but not cash flows, is a half-valuation.

| Call | Numerator | Denominator |
|---|---|---|
| `spot_rates(X, n)` | — | $\mu_t(1),\ldots,\mu_t(n)$ |
| `cashflow_expectation(X, n)` | $\mathbb{E}_t[C_{t+k}]/C_t$ | — |
| **`value(X, C)`** | $C$ times the recursion | the curve |
| `sum C_n e^{-n\mu_t(n)}` | a path you already have | the curve |
| `perpetuity(X)` | $1$ (unit-curve diagnostic) | the curve |
| `isolate_channels(..., on="cashflow")` | $\Phi[\texttt{cf},s]$ zeroed | unchanged |
| `isolate_channels(..., on="discount")` | unchanged | those names zeroed in $\Phi$ and $\Lambda$ except the cf row |

---

## 6. What replaces the terminal value

Gordon growth is Ang and Liu’s **special case 1**: constant expected
return and constant expected cash-flow growth. Then $b(n)=0$,
$H(n)=0$, $a(n)=n(g-\mu)$, and

$$
\frac{V_t}{C_t}
  = \sum_{n=1}^{\infty} e^{\,n(g-\mu)}
  = \frac{e^{g-\mu}}{1-e^{g-\mu}}
  \;\approx\; \frac{1+g}{\mu-g}.
$$

That case does **not** require $\Phi=\Sigma=0$. Other states may still
persist; they simply do not enter $g$ or $\mu$. Setting
$\Phi=\Sigma=0$ is a further degeneracy that delivers the same closed
form — zero persistence, zero volatility, zero correlation — but it is
not the statement of special case 1
([Ang and Liu, 2004](../references.md#ang-liu-2004)). Convergence in
the general case requires the eigenvalues of $\Phi$ inside the unit
circle *and* the priced strip eventually declining — the analogue of
$\mu>g$, but now a condition on the **dynamics** rather than on two
point estimates. The tail of `value` / `perpetuity` is a **geometric
remainder** at $\mu_t(N)$: once the spot rate has settled near its
long-run value, the leftover sum
$\sum_{k>N}e^{-k\mu_t(N)}$ is a Gordon-like closed form at that
terminal spot, not a hand-set $(r,g)$ bolted on at year ten.

---

## 7. When the growth forecast is not yet usable

If $\Phi[\texttt{cashflow},\texttt{cashflow}]$ is near one,
$\bar b(n)$ stacks a series that barely mean-reverts and
`cashflow_expectation` (hence `value`) is not a price. At the firm,
$\mathit{roe}=\log(\mathrm{NI}/\mathrm{BE}_{\mathrm{lag}})$ is a
*level* of profitability, not log dividend growth, and not
[Vuolteenaho’s](../references.md#vuolteenaho-2002)
$e_t=\log(1+X_t/B_{t-1})$. Treating it as growth in `value` is the
same mistake. Section 5 reports $\Phi_{\mathit{roe},\mathit{roe}}=0.46$
and reads $\mathbb{E}_t[\mathit{roe}_{t+n}]$ instead.

Two honest objects remain. `perpetuity` isolates the curve. The next
section discounts a cash-flow path you already have.

!!! warning "Inspect the own-lag before `value`"
    Print `fit.Phi[spec.cashflow_index(), spec.cashflow_index()]`.
    Near $1$, or when the cash-flow name is a *level*: do not call
    `value`. The curve is still defined. Discount a path you trust,
    or report `perpetuity`.

---

## 8. Discounting a path you already have

The two-step workflow
([Brennan, 1997](../references.md#brennan-1997);
[Ang and Liu, 2004](../references.md#ang-liu-2004)) is: forecast cash
flows however you forecast them, then discount at $\mu_t(n)$. The VAR
is required for the curve. It is not required for the numerator if you
already have $C_{t+1},\ldots,C_{t+N}$ — an analyst schedule, a
residual-income path, or an internal model.

!!! note "In words — residual income"
    **Residual income** (abnormal earnings) is
    $(\mathrm{ROE}_{t+j}-k_{t+j})B_{t+j-1}$: earnings minus a charge
    $k$ on beginning book $B$. Clean-surplus accounting then writes
    price as book plus the present value of those residual earnings
    ([Ohlson, 1995](../references.md#ohlson-1995);
    [Feltham and Ohlson, 1995](../references.md#feltham-ohlson-1995);
    [Ang and Liu, 2001](../references.md#ang-liu-2001)). That is a
    *numerator* you can bring to `spot_rates`. This library does not
    compute it. Section 5’s $\mathbb{E}_t[\mathit{roe}_{t+n}]$ is an
    AR path of $\log(\mathrm{NI}/\mathrm{BE})$, not residual income.

```python
import numpy as np

spots = model.spot_rates(X, n=len(cashflows))
user_pv = float(sum(
    C * np.exp(-(k + 1) * spots[k]) for k, C in enumerate(cashflows)
))
```

That sum is a present value of *those* cash flows under this curve. It
is not `value(X, C)`, which takes the numerator from the cash-flow
equation. Use it when `spec.cashflow` is a profitability level, when
the own-lag is not yet usable, or when the cash-flow model you trust
is not the VAR.

---

## 9. Freezing the numerator

Sometimes you want only the curve: “what is a dollar a year worth under
this $\mu_t(n)$?” Then set $\mathbb{E}_t[C_{t+n}] = 1$ and sum

$$
V_t^{\text{perp}}
  = \sum_{n=1}^{N} \exp\!\bigl(-n\,\mu_t(n)\bigr)
  + \text{geometric tail at }\mu_t(N).
$$

That is `model.perpetuity(X)`. It is a special case of `value` with the
cash-flow recursion switched off. Section 5 prints it as
`unit_curve_pv`: the present value of receiving $1$ at every horizon
under this curve, a denominator diagnostic. $24.70$ is that object
at permno 10026, not an equity value. It cannot tell you anything
about expected cash flows, because they do not enter.

---

## 10. The curve, in pictures

![Firm spot curves](../assets/figures/firm_spot_curves.png)
<p class="figure-caption"><strong>Figure 1</strong> (reprised). Term structure of $\mu_t(n)$ at three CRSP permnos, 30 September 2019. These curves are the denominator. Source: Section 5.</p>

---

## 11. Channel isolation

Isolation is a **counterfactual**, not news. You shut a named state on one
side, revalue with `value`, and compare.

```python
from varvaluation import isolate_channels

iso = isolate_channels(model, X, shut=("cay",), on="cashflow")
iso = isolate_channels(model, X, shut=("cay",), on="discount")
iso = isolate_channels(model, X, shut=("cay",), on="both")  # unmodified value
```

- `on="cashflow"` zeros $\Phi[\texttt{cashflow}, s]$ for each shut name.
  The state no longer forecasts growth. The discount curve is unchanged.
- `on="discount"` zeros those names in every *other* row of $\Phi$ and in
  $\Lambda$. Growth still loads on them; expected returns do not.
- `on="both"` is the original `value`.

News (`news_decomposition`) asks a different question: what moved last
period’s unexpected *return*? That page is [News](news.md).
