# A numerical walkthrough

The six-variable state in [Ang and Liu (2004)](angliu.md) is the right object for a market curve. It is the wrong object to compute by hand. This page is the same two recursions on two numbers — cash-flow growth and the premium — with every \(n=1\) and \(n=2\) term written out in numpy. A later section adds a moving beta.

Run the numbers:

```text
uv run python examples/numerical_toy.py
```

The numbers are made up. Nothing is estimated from returns.

---

## A simple claim

You are valuing a claim that pays cash once a year. Two numbers describe it: how fast the cash is growing, \(g_t\), and the equity premium, \(\lambda_t\). The risk-free rate is 3% and does not move. Beta is 1, so the return you require this year is just the risk-free rate plus the premium,

$$
\mu_t = 0.03 + \lambda_t.
$$

In a typical year growth is 2% and the premium is 6%. Today growth is still 2%, but the premium is 3%.

Tomorrow’s pair is a linear function of today’s, plus a shock. The premium is sticky. Growth fades. A high premium this year goes with lower growth next year. Growth this year does not forecast the premium.

```python
import numpy as np

Phi = np.array([
    [ 0.40, -0.50],
    [ 0.00,  0.50],
])
X_bar = np.array([0.02, 0.06])          # typical year: g=2%, λ=6%
c     = (np.eye(2) - Phi) @ X_bar       # intercept consistent with that mean
Sigma = np.array([
    [ 0.0040, -0.0010],
    [-0.0010,  0.0025],
])
alpha = 0.03
xi    = np.array([0.0, 1.0])            # μ = 0.03 + λ
Lambda = np.zeros((2, 2))               # no βλ product
e_g   = np.array([1.0, 0.0])            # picks growth out of the pair
X     = np.array([0.02, 0.03])          # today: growth typical, premium cheap
```

\(\Phi\) is the map from today to tomorrow, \(c\) the intercept, \(\Sigma\) the shock covariance.

| | \(g_t\) | \(\lambda_t\) |
|---|---:|---:|
| \(g_{t+1}\) | \(0.40\) | \(-0.50\) |
| \(\lambda_{t+1}\) | \(0\) | \(0.50\) |

---

## Cash-flow recursion, \(n=1\)

The numerator of a one-year strip is \(E_t[C_{t+1}]/C_t=\exp(\bar a(1)+\bar b(1)'X_t)\).

```python
bar_a1 = e_g @ c + 0.5 * e_g @ Sigma @ e_g
bar_b1 = Phi.T @ e_g
```

| Term | Value | What it is |
|---|---:|---|
| \(e_g'c\) | \(0.042\) | intercept contribution to next-year growth |
| \(\tfrac12 e_g'\Sigma e_g\) | \(0.002\) | Jensen: \(E[e^u]=e^{\mathrm{Var}(u)/2}\) |
| \(\bar a(1)\) | \(0.044\) | |
| \(\bar b(1)=\Phi'e_g\) | \((0.40,\,-0.50)\) | today's \((g,\lambda)\) map into \(E[g_{t+1}]\) |

```python
cf1 = np.exp(bar_a1 + bar_b1 @ X)      # 1.0377
```

Next year's expected cash flow is 3.77% above today. The same number as iterating the VAR and adding Jensen:

```python
E_g = e_g @ (c + Phi @ X)              # 0.035
np.exp(E_g + 0.5 * Sigma[0, 0])        # 1.0377
```

High \(\lambda\) today *lowers* expected growth (\(\bar b_\lambda=-0.50\)). That is \(\Phi_{g,\lambda}\) entering the numerator.

---

## Priced recursion, \(n=1\)

The priced strip is \(E_t[\exp(g_{t+1}-\mu_t)]=\exp(a(1)+b(1)'X_t+X_t'H(1)X_t)\). Subtract the expected-return side:

```python
a1 = -alpha + e_g @ c + 0.5 * e_g @ Sigma @ e_g    # 0.014
b1 = -xi + Phi.T @ e_g                             # (0.40, -1.50)
H1 = -Lambda                                       # 0
strip1 = np.exp(a1 + b1 @ X)                       # 0.9773
```

\(a(1)\) is \(\bar a(1)-\alpha\). \(b(1)\) is \(\bar b(1)-\xi\). \(H(1)\) is \(-\Lambda\), zero because \(\mu_t\) is affine. At one year the discount factor \(e^{-\mu_t}\) is *known today*, so the strip is just the cash-flow ratio times \(e^{-\mu_t}\):

```python
np.exp(-(alpha + X[1])) * cf1          # 0.9773, same as strip1
```

The product covariance is not visible yet. It starts at \(n=2\), when tomorrow's \(\mu_{t+1}\) is random.

---

## The one-period identity

The spot rate \(\mu_t(n)\) is defined so that dividing expected cash by \(\exp(n\,\mu_t(n))\) recovers the priced strip.

```python
mu1 = (bar_a1 - a1) + (bar_b1 - b1) @ X    # 0.0600
alpha + xi @ X                             # 0.0600
```

\(\mu_t(1)=6\%=\mu_t\). This is the identity the library asserts to machine precision. It is not a test of the data. It is a test that the two recursions were started consistently.

---

## One more year

From \(n\) to \(n+1\) the cash-flow coefficients accumulate mean growth, the intercept, and Jensen:

```python
eb = e_g + bar_b1                          # (1.40, -0.50)
bar_a2 = bar_a1 + e_g @ c + bar_b1 @ c + 0.5 * eb @ Sigma @ eb
bar_b2 = Phi.T @ eb
cf2 = np.exp(bar_a2 + bar_b2 @ X)          # 1.0784
```

| Term | Value |
|---|---:|
| \(e_g'c\) | \(0.0420\) |
| \(\bar b(1)'c\) | \(0.0018\) |
| \(\tfrac12(e_g+\bar b)'\Sigma(e_g+\bar b)\) | \(0.00493\) |
| \(\bar a(2)\) | \(0.09273\) |
| \(\bar b(2)\) | \((0.56,\,-0.95)\) |

Because \(\Lambda=0\), \(H(n)\) stays zero and the priced update is the same shape with \(-\alpha\) and \(-\xi\) subtracted:

```python
D = e_g + b1                               # (1.40, -1.50)
a2 = a1 - alpha + (e_g + b1) @ c + 0.5 * D @ Sigma @ D
b2 = -xi + Phi.T @ (e_g + b1)              # (0.56, -2.45)
strip2 = np.exp(a2 + b2 @ X)               # 0.9459
mu2 = (bar_a2 - a2) / 2 + (bar_b2 - b2) @ X / 2   # 0.06555
```

Check: \(E[C]/C \big/ e^{2\mu_t(2)} = 0.9459\), the strip.

\(\mu_t(2)=6.555\%\). That is **not** the average of today's \(6\%\) and \(E_t[\mu_{t+1}]=7.5\%\). The average of the one-period path would be \(6.75\%\). The extra \(20\) bp is the product: variance of \(\mu\) and \(\mathrm{Cov}(\sum g,\sum\mu)\) sit inside the strip, so the rate that prices it is not the expected path of \(\mu\).

---

## The curve

Iterate the same two updates.

| \(n\) | \(\mu_t(n)\) | \(E_t[C_{t+n}]/C_t\) | strip |
|---:|---:|---:|---:|
| 1 | 6.000% | 1.038 | 0.977 |
| 2 | 6.555% | 1.078 | 0.946 |
| 5 | 7.057% | 1.198 | 0.842 |
| 10 | 7.202% | 1.407 | 0.685 |

The curve slopes **up**. \(\lambda_t\) is 3% against a 6% mean. Under stationarity the state mean-reverts, so a long strip is not priced at today's cheap one-period rate. That is the paper's December 2000 picture, with two coordinates instead of six.

The curve does not climb to the unconditional \(E[\mu]=9\%\). The long-run *spot* — the rate that prices a distant strip after Jensen and the covariance have been taken — is about \(7.3\%\). Using \(E[\mu]\) as a Gordon rate would be a third, different number.

A 15-year unit annuity on this curve is 8.89. The same annuity locked at \(\mu_t(1)=6\%\) is 9.60, **+8.0%**. A flat rate at a cheap-premium date overvalues the claim, because the curve is already on its way up.

---

## \(E[\text{product}]\) is not \(E[\text{discount}]\,E[\text{cash flow}]\)

At \(n=2\) the discount path \(e^{-(\mu_t+\mu_{t+1})}\) and the cash-flow path \(e^{g_{t+1}+g_{t+2}}\) are both random (only \(\mu_t\) is known). Draw the two shocks from \(\Sigma\) and compare the joint expectation to the product of the two margins.

```python
rng = np.random.default_rng(0)
N = 200_000
L = np.linalg.cholesky(Sigma)
U1 = L @ rng.standard_normal((2, N))
U2 = L @ rng.standard_normal((2, N))
X1 = c[:, None] + Phi @ X[:, None] + U1
X2 = c[:, None] + Phi @ X1 + U2

product   = np.exp(-(alpha + X[1]) - (alpha + X1[1]) + X1[0] + X2[0])
cf_path   = np.exp(X1[0] + X2[0])
disc_path = np.exp(-(alpha + X[1]) - (alpha + X1[1]))
```

| Object | Value |
|---|---:|
| Monte Carlo \(E[\text{product}]\) | 0.9461 |
| Closed-form strip | 0.9459 |
| \(E[\text{discount}]\,\times\,E[\text{cash flow}]\) | 0.9436 |
| \(E[\text{product}]\big/\bigl(E[D]\,E[C]\bigr)\) | 1.0027 |
| \(\mathrm{Cov}(g_{t+1}+g_{t+2},\,\mu_t+\mu_{t+1})\) | \(-0.0027\) |

For jointly normal logs,

$$
E[e^{g-\mu}] = E[e^{g}]\,E[e^{-\mu}]\,\exp\bigl(-\mathrm{Cov}(g,\mu)\bigr).
$$

\(\mathrm{Cov}(g,\mu)<0\) here because \(\Phi_{g,\lambda}=-0.50\) and \(\Sigma_{g,\lambda}<0\): a high premium comes with low growth. The extra factor is therefore greater than one. Two separate forecasts miss that factor. The recursion never computes it by hand — it is already inside \((a,b,H)\) because those coefficients were built from the same \((\Phi,c,\Sigma)\).

The Monte Carlo is a check, not a method. Once the VAR is Gaussian, the closed form *is* the expectation of the product.

---

## Why \(H(n)\) exists: \(\mu_t=\alpha+\beta_t\lambda_t\)

A valuator’s CAPM is \(\mu_t=\alpha+r_t+\beta_t\lambda_t\). The last term is a *product* of two numbers. Three cases:

| What moves | \(\mu_t\) as a function of \(X_t\) | \(H(n)\) |
|---|---|---|
| only \(\lambda\), \(\beta\) fixed | affine (the 2×2 toy: \(\beta=1\)) | \(0\) |
| only \(\beta\), \(\lambda\) fixed | affine | \(0\) |
| **both** \(\beta_t\) and \(\lambda_t\) | quadratic: \(X_t'\Lambda X_t=\beta_t\lambda_t\) | a real matrix |

The third case is the paper. Add a beta coordinate so the state is three-dimensional.

```python
# X = (g, β, λ),   μ = α + β λ
Lambda = np.zeros((3, 3))
Lambda[1, 2] = Lambda[2, 1] = 0.5      # X'ΛX = βλ
xi = np.zeros(3)
X  = np.array([0.02, 1.20, 0.03])      # high-ish beta, compressed premium
# μ_t = 0.03 + 1.20 × 0.03 = 0.066
```

The priced strip — one horizon’s contribution to \(V_t/C_t\) — is always of the form

$$
\exp\bigl(a(n)+b(n)'X_t+X_t'H(n)X_t\bigr).
$$

\(a(n)\) is a scalar. \(b(n)\) is a vector (the linear loading). \(H(n)\) is the \(K\times K\) **quadratic matrix**: it multiplies the products of today’s coordinates. At one year you just subtract today’s \(\beta\lambda\), so

$$
H(1)=-\Lambda,
\qquad
X_t'H(1)X_t = -\beta_t\lambda_t = -0.036.
$$

The one-period identity still holds: \(\mu_t(1)=6.60\%=\alpha+\beta_t\lambda_t\). At \(n=2\), tomorrow’s \(\beta_{t+1}\lambda_{t+1}\) is random and a function of today’s \(X_t\) through \(\Phi\). Folding that future product back onto today updates the matrix: \(H(2)\ne-\Lambda\) (the Riccati step in [Ang and Liu, 2004](../references.md#ang-liu-2004), Proposition I.1). That is the only algebraic reason the strip is exponential-quadratic rather than exponential-affine. When \(\Lambda=0\), \(H(n)\equiv 0\) and the first toy is the special case.

---

## The same toy through the library

```python
from varvaluation import StateSpec, ValuationModel

spec  = StateSpec(names=("g", "lam"), cashflow="g")
model = ValuationModel(spec, Phi, c, Sigma, xi, Lambda, alpha)
rates = model.spot_rates(X, n=15)      # 6.000%, 6.555%, … 7.246%
value = model.value(X, C=1.0, n=40)    # 22.38
```

`spot_rates` is the curve in the table. `value` sums the strips plus a geometric tail at \(\mu_t(40)\). The numpy in the first seven steps *is* that call, with every matrix written out.

This toy is not the paper. There is no \(\mathit{cay}\), no inflation, no rolling CAPM beta, no Newey–West VAR. What it is: the product identity, the two recursions, the one-period identity, the covariance that two separate forecasts miss, and the \(H(n)\) matrix that appears when \(\beta\) and \(\lambda\) both move. The six-variable curve on [Ang and Liu (2004)](angliu.md) is the same objects with more rows.
