# Expected returns and the link to \(X_t\)

The one-period expected return \(\mu_t\) (the discount rate you require for the next period) is allowed to be a flexible function of the *same* state:

$$
\mu_t = \alpha + \xi' X_t + X_t' \Lambda X_t.
$$

- If \(\Lambda = 0\) the formula is linear (affine) in \(X_t\).
- If both beta and the market premium move with the state, \(\Lambda\) is non-zero and \(\mu_t\) becomes quadratic in \(X_t\).

Because \(\mu_t\) is a function of \(X_t\), and \(X\) itself follows the VAR, the whole future path of expected returns is also completely determined by today’s \(X_t\).

The package turns this into a **priced recursion** (a matrix Riccati recursion) that produces the term structure of discount rates \(\mu_t(n)\) — the equity analogue of a bond yield curve. Each \(\mu_t(n)\) is the single rate that correctly discounts an \(n\)-period cash-flow strip, already incorporating all the covariance corrections that live inside \(\Phi\) and \(\Sigma\).

In practice you supply the loadings via `ExpectedReturnSpec`:

```python
from varvaluation import ExpectedReturnSpec

xi, Lambda = ExpectedReturnSpec(
    rate="rf", beta="beta", premium=("cay",)
).xi_lambda(spec, loadings)
```

The one-period identity must hold by construction:

$$
\mu_t(1) = \alpha + \xi' X_t + X_t' \Lambda X_t.
$$

Under stationarity the curve converges to a long-run rate as maturity grows. The shape of the curve (upward, downward, or humped) is driven by how far today’s \(X_t\) sits from its unconditional mean and by the speed of mean reversion in \(\Phi\).
