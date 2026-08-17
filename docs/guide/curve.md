# The two recursions

Given the VAR

$$
X_{t+1} = c + \Phi X_t + u_{t+1},
\qquad
u \sim N(0,\Sigma)
$$

and a one-period expected return

$$
\mu_t = \alpha + \xi'X_t + X_t'\Lambda X_t,
$$

[Ang and Liu (2004)](../references.md#ang-liu-2004) give closed forms
for every horizon. There is no simulation and no hand-set terminal
$(r,g)$. Two recursions do the work; the spot curve $\mu_t(n)$ is their
ratio.

## 1. Cash-flow recursion

Let $e_g$ pick the cash-flow-growth coordinate of $X_t$
(so $g_t = e_g'X_t$). Cumulated growth $S_n = \sum_{i=1}^{n} g_{t+i}$
is Gaussian, and

$$
\frac{E_t[C_{t+n}]}{C_t}
  = \exp\!\bigl(\bar a(n) + \bar b(n)'X_t\bigr).
$$

No discounting enters this expectation, so there is no quadratic $H$
term. The coefficients start at

$$
\bar a(1) = e_g'c + \tfrac12 e_g'\Sigma e_g,
\qquad
\bar b(1) = \Phi'e_g
$$

and iterate

$$
\begin{aligned}
\bar a(n+1)
  &= \bar a(n) + e_g'c + \bar b(n)'c
   + \tfrac12(e_g+\bar b(n))'\Sigma(e_g+\bar b(n)), \\
\bar b(n+1)
  &= \Phi'(e_g + \bar b(n)).
\end{aligned}
$$

That is `cashflow_recursion` / `cashflow_expectation`.

- $\bar b(1)$ answers: how does **today’s entire state** forecast
  **next period’s** growth?
- $\bar b(n)$ accumulates those forecasts $n$ steps out.
- $\bar a(n)$ collects intercepts and Jensen terms
  ($\tfrac12\mathrm{Var}$ of cumulated growth shocks).

A state moves the numerator **only** if it loads on the growth
equation. If that entry of $\Phi$ is zero, the state can still move
the discount curve without moving expected cash flows.

## 2. Priced recursion

Each strip of the price–cash-flow ratio is the expectation of an
exponential of cumulated growth *minus* cumulated expected returns.
Under the quadratic-Gaussian law that expectation is

$$
\exp\!\bigl(a(n) + b(n)'X_t + X_t'H(n)X_t\bigr).
$$

$H(n)$ is there because $\mu_t$ is quadratic whenever $\beta_t$ and
$\lambda_t$ both move. The first step is

$$
a(1) = -\alpha + e_g'c + \tfrac12 e_g'\Sigma e_g,
\qquad
b(1) = -\xi + \Phi'e_g,
\qquad
H(1) = -\Lambda,
$$

and the rest is a matrix Riccati (Proposition I.1). That is
`price_recursion`.

When $\Lambda = 0$, $H(n)\equiv 0$ and the strip is
exponential-affine — constant beta with a moving premium, or a moving
beta with a constant premium. Letting **both** move at once is what
$H(n)$ is for.

## 3. Spot discount rates $\mu_t(n)$

Define $\mu_t(n)$ so that

$$
\frac{E_t[C_{t+n}]/C_t}{\exp\!\bigl(n\,\mu_t(n)\bigr)}
$$

is exactly the contribution of horizon $n$ to the price–cash-flow
ratio. In coefficients,

$$
\mu_t(n) = A(n) + B(n)'X_t + X_t'G(n)X_t,
$$

where $A,B,G$ are the cash-flow recursion minus the priced recursion,
scaled by $1/n$ (Definition II.1 / Proposition II.1). Under
stationarity, $\mu_t(n)\to\bar\mu$ as $n\to\infty$. The curve can
slope up, down, or be humped, and it moves with $X_t$.

```python
spots = model.spot_rates(X, n=30)     # μ_t(1), …, μ_t(30)
cf    = model.cashflow_expectation(X, n=30)
```

!!! note "The practical bridge"
    You can keep the usual two-step workflow: forecast cash flows
    however you forecast them, then discount at $\mu_t(n)$. The VAR is
    required for the curve. Each $\mu_t(n)$ already contains the
    covariance corrections; the practitioner never sees them, but they
    are priced in. That is Brennan (1997) made analytic, with moving
    betas allowed.

## 4. Present value is the sum of strips

$$
\frac{V_t}{C_t}
  = \sum_{n=1}^{N}
      \frac{E_t[C_{t+n}]/C_t}{\exp\!\bigl(n\,\mu_t(n)\bigr)}
  + \text{tail at }\mu_t(N).
$$

Both the numerator and the denominator are functions of the **same**
$X_t$ and the **same** $(\Phi,c,\Sigma)$. The covariance between growth
and discount rates sits inside $\Phi$ and $\Sigma$, estimated once,
and enters **both** recursions.

```python
V = model.value(X, C0)               # sum of strips + tail
```

The tail is a geometric remainder at the terminal spot $\mu_t(N)$ —
once the curve has settled near its long-run value — not a hand-set
$(r,g)$ bolted on at year ten.

| Call | Numerator | Denominator |
|---|---|---|
| `cashflow_expectation(X, n)` | $E_t[C_{t+k}]/C_t$ | — |
| `spot_rates(X, n)` | — | $\mu_t(1),\ldots,\mu_t(n)$ |
| **`value(X, C)`** | $C$ times the cash-flow recursion | the curve |
| path you already have | external forecast | `spot_rates` |

## 5. Gordon as a special case

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
$\Phi=\Sigma=0$ is a further degeneracy. Convergence in the general
case requires the eigenvalues of $\Phi$ inside the unit circle *and*
the priced strip eventually declining — the analogue of $\mu>g$, but
now a condition on the **dynamics**.

## 6. Side by side

| | Flat CAPM / WACC | Ang–Liu |
|---|---|---|
| Discount rate | One rate, all horizons | $\mu_t(n)$ from the joint VAR |
| Cash flows | Point forecast path | Cash-flow recursion (mean *and* variance) |
| Growth–rate interaction | None | Covariance enters the price level |
| Terminal value | Gordon, hand-set | Tail of the priced recursion |
| Beta | Single number | Horizon-specific loadings $b(n)$ |

## Optional: residual income as the numerator

Nothing above requires dividends. If cash flows are defined by clean
surplus — $C_{t+1} = B_t(e^{\mathrm{ROE}_{t+1}} - e^{g_{t+1}})$ — the
same two recursions apply to that map ([Ang and Liu, 2001](../references.md#ang-liu-2001);
[Feltham and Ohlson, 1995](../references.md#feltham-ohlson-1995)).
The package exposes that reading as `ResidualIncome` / `TermStructureModel`.
The discount-rate side is unchanged: still $\mu_t$ and $\mu_t(n)$ in
Ang–Liu notation.
