# The two recursions

## Where this sits on the map

1. Value is $E[\text{product}]$.
2. The product carries a covariance term.
3. One VAR supplies the joint law.

Given that VAR,

$$
X_{t+1} = c + \Phi X_t + u_{t+1},
\qquad
u \sim N(0,\Sigma),
$$

and a one-period expected return

$$
\mu_t = \alpha + \xi'X_t + X_t'\Lambda X_t,
$$

[Ang and Liu (2004)](../references.md#ang-liu-2004) evaluate the product
in closed form. Two recursions; the spot curve $\mu_t(n)$ is their
ratio. The covariance estimated in $\Phi$ and $\Sigma$ enters **both**.

---

## 1. Cash-flow recursion

Let $e_g$ pick the growth coordinate ($g_t = e_g'X_t$). Cumulated
growth is Gaussian, and

$$
\frac{E_t[C_{t+n}]}{C_t}
  = \exp\!\bigl(\bar a(n) + \bar b(n)'X_t\bigr).
$$

Coefficients:

$$
\bar a(1) = e_g'c + \tfrac12 e_g'\Sigma e_g,
\qquad
\bar b(1) = \Phi'e_g,
$$

$$
\begin{aligned}
\bar a(n+1)
  &= \bar a(n) + e_g'c + \bar b(n)'c
   + \tfrac12(e_g+\bar b(n))'\Sigma(e_g+\bar b(n)), \\
\bar b(n+1)
  &= \Phi'(e_g + \bar b(n)).
\end{aligned}
$$

The $\tfrac12(\cdot)'\Sigma(\cdot)$ pieces *are* the variance of
cumulated growth shocks — the Jensen term from the product expansion.
No discounting enters here, so there is no $H(n)$.

```python
cf = model.cashflow_expectation(X, n=30)
```

---

## 2. Priced recursion

Each strip of the price–cash-flow ratio is
$E_t[\exp(\sum(g-\mu))]$. Under the quadratic-Gaussian law:

$$
\exp\!\bigl(a(n) + b(n)'X_t + X_t'H(n)X_t\bigr).
$$

First step:

$$
a(1) = -\alpha + e_g'c + \tfrac12 e_g'\Sigma e_g,
\qquad
b(1) = -\xi + \Phi'e_g,
\qquad
H(1) = -\Lambda.
$$

The rest is a matrix Riccati (Proposition I.1). $H(n)$ is present
because $\mu_t$ is quadratic when $\beta_t$ and $\lambda_t$ both move.
When $\Lambda=0$, $H(n)\equiv 0$ and the strip is exponential-affine.

The $-2\,\mathrm{Cov}(\sum g,\sum \mu)$ term from the mental map lives
here: it is folded into $(a,b,H)$ through $\Phi$ and $\Sigma$.

---

## 3. Spot discount rates $\mu_t(n)$

Define $\mu_t(n)$ so that dividing expected cash by
$\exp(n\,\mu_t(n))$ recovers the priced strip:

$$
\mu_t(n) = A(n) + B(n)'X_t + X_t'G(n)X_t.
$$

$A,B,G$ are the cash-flow recursion minus the priced recursion, scaled
by $1/n$ (Definition II.1). Under stationarity
$\mu_t(n)\to\bar\mu$ as $n\to\infty$.

```python
spots = model.spot_rates(X, n=30)   # μ_t(1), …, μ_t(30)
```

!!! note "The practical bridge"
    Forecast cash however you like; discount at $\mu_t(n)$. Each spot
    already contains the covariance correction. The two-step workflow
    survives; only the single WACC is replaced by a curve.

---

## 4. Present value = sum of strips

$$
\frac{V_t}{C_t}
  = \sum_{n=1}^{N}
      \frac{E_t[C_{t+n}]/C_t}{\exp\!\bigl(n\,\mu_t(n)\bigr)}
  + \text{tail at }\mu_t(N).
$$

Numerator and denominator share $(\Phi,c,\Sigma)$. The covariance is
estimated once and enters both sides.

```python
V = model.value(X, C0)   # sum of strips + tail
```

The tail is a geometric remainder at the terminal spot $\mu_t(N)$, not
a hand-set $(r,g)$.

| Call | Numerator | Denominator |
|---|---|---|
| `cashflow_expectation(X, n)` | cash-flow recursion | — |
| `spot_rates(X, n)` | — | $\mu_t(1),\ldots,\mu_t(n)$ |
| **`value(X, C)`** | both | both |
| external cash path | your forecast | `spot_rates` |

---

## 5. Gordon is special case 1

Constant expected return and constant expected growth: $b(n)=0$,
$H(n)=0$, $a(n)=n(g-\mu)$, and

$$
\frac{V_t}{C_t}
  = \sum_{n} e^{n(g-\mu)}
  \;\approx\; \frac{1+g}{\mu-g}.
$$

That is Ang and Liu’s special case 1 — zero contribution from the
covariance term, because there is no variation left to covary. The
general case requires eigenvalues of $\Phi$ inside the unit circle and
a declining priced strip.

---

## Side by side

| | Flat CAPM / WACC | Ang–Liu |
|---|---|---|
| Identity | ratio of expectations | $E[\text{product}]$ |
| Covariance | set to zero | inside $\Phi,\Sigma$, in both recursions |
| Discount rate | one $r$, all horizons | $\mu_t(n)$ from the joint system |
| Terminal value | hand-set Gordon | tail of the priced recursion |
