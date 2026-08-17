# Valuation

**Both** sides of every strip come from the same state $X_t$. This page
derives the two recursions and then shows the special case that freezes
the numerator.

Given a fitted VAR and a one-period expected return

$$
\mu_t = \alpha + \xi' X_t + X_t' \Lambda X_t,
$$

every object below is exact. The cash-flow basis vector is
`spec.cashflow`, not “whatever happens to sit in column 0.”

```python
from varvaluation import ValuationModel

model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=alpha)
rates = model.spot_rates(X, n=30)            # μ_t(1), …, μ_t(30)
cf    = model.cashflow_expectation(X, n=30)  # E_t[C_{t+n}] / C_t
value = model.value(X, C=1.0, n=80)          # both from X
```

`from_var` refuses a companion with spectral radius $\ge 1$
(`NonStationaryVARError`). Negative *short* rates are allowed. A
non-positive *terminal* rate raises `PerpetuityDivergesError`.

If $\Lambda = 0$, the quadratic term is off, $H(n)\equiv 0$, and the
solution is exponential-affine — the scalar playground on the
[course](https://github.com/tlorans/var_valuation). Same class. No second
solver.

---

## 1. Two sides of every strip

A present value is a sum of strips. Each strip has a **numerator** (what you
expect to receive $n$ years from now) and a **denominator** (how hard you
discount that receipt).

A constant-rate DCF writes the denominator as $(1+r)^n$ with one $r$ for
all $n$, and takes the numerator from a spreadsheet. Here both objects are
forecasts from the VAR of $X_t$. `value` multiplies them.

!!! note "Value versus a frozen numerator"
    `value(X, C)` takes expected cash flows *and* the discount curve from
    $X_t$. `perpetuity(X)` freezes the numerator at $1$ so only the curve
    can move. Use that when you want to isolate the denominator.

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

## 4. Putting the two sides together

The spot rate $\mu_t(n)$ is defined so that

$$
\frac{\mathbb{E}_t[C_{t+n}]}{C_t}\Big/\exp\!\bigl(n\,\mu_t(n)\bigr)
$$

is the contribution of horizon $n$ to the price–cash-flow ratio. In
coefficients, $A(n) = (\bar a(n)-a(n))/n$, and likewise for $B$ and $G$.
The $a,b,H$ recursion is the **priced** (discounted) counterpart of
$\bar a,\bar b$; their difference *is* the curve.

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
| `perpetuity(X)` | $1$ (diagnostic) | the curve |
| `isolate_channels(..., on="cashflow")` | $\Phi[\texttt{cf},s]$ zeroed | unchanged |
| `isolate_channels(..., on="discount")` | unchanged | those names zeroed in $\Phi$ and $\Lambda$ except the cf row |

---

## 5. When the growth forecast is not yet usable

On some Ken French **value** portfolios, $\Phi_{g,g}$ is near one. Then
$\bar b(n)$ keeps stacking growth that barely mean-reverts,
$\mathbb{E}_t[C_{t+n}]/C_t$ grows without bound, and `value` is not a
price you should publish. That is not a bug in the recursion. It is the
recursion telling you the $g$ equation is not a usable cash-flow model at
that aggregation.

Check $\Phi[\texttt{cashflow},\texttt{cashflow}]$ first. If the own-lag is
near a unit root, either improve the cash-flow specification (firm-level
ROE mean-reverts more reliably) or use `perpetuity` as a
**denominator-only** diagnostic until the numerator is trustworthy.

!!! warning "Inspect the own-lag"
    Before you report a full PV, print
    `fit.Phi[spec.cashflow_index(), spec.cashflow_index()]`.
    Near $1$: do not trust `value` yet. Comfortably inside the unit
    circle: `value` is the object you came for.

---

## 6. Freezing the numerator (optional)

Sometimes you want only the curve: “what is a dollar a year worth under
this $\mu_t(n)$?” Then set $\mathbb{E}_t[C_{t+n}] = 1$ and sum

$$
V_t^{\text{perp}}
  = \sum_{n=1}^{N} \exp\!\bigl(-n\,\mu_t(n)\bigr)
  + \text{geometric tail at }\mu_t(N).
$$

That is `model.perpetuity(X)`. It is a special case of `value` with the
cash-flow recursion switched off. It cannot tell you anything about
expected cash flows, because they do not enter.

---

## 7. The curve, in pictures

![Spot discount curves](../assets/figures/spot_curves.png)
<p class="figure-caption">Term structure of $\mu_t(n)$ for growth (D1), mid (D6), and value (D10) at the last state in the 1965–2024 sample. These curves are the denominator. The present value multiplies each strip by $\mathbb{E}_t[C_{t+n}]/C_t$.</p>

![Variance decomposition, D10](../assets/figures/variance_decomp_d10.png)
<p class="figure-caption">Share of <em>spot-rate</em> variance by state, value decile. $\mathit{cay}$ and $\beta$ dominate the <em>discount curve</em>. That $g$ is negligible here does <em>not</em> mean cash flows do not matter for prices — it means they do not drive $\mu_t(n)$. They drive the numerator, which this figure does not show.</p>

---

## 8. Channel isolation

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
