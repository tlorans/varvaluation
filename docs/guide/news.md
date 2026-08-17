# News

Campbell (1991): unexpected return $= N_{\mathrm{CF}} - N_{\mathrm{DR}}$.

The usual implementation estimates $N_{\mathrm{DR}}$ from the VAR and sets $N_{\mathrm{CF}}$ to the residual. Chen, Da, Zhao (2013) show that residual absorbs every misspecification (Treasury test: known cash flows, residual still nonzero).

This library never uses the residual as the definition of cash-flow news.

## Formula

Let $u_{t+1}$ be the VAR residual at the estimation horizon, $e_{\mathrm{cf}}$ the unit vector for `spec.cashflow`, and $\rho\in(0,1)$ the linearization parameter (default $0.96$).

$$
N_{\mathrm{DR},t+1} = \lambda'\,\rho\Phi(I-\rho\Phi)^{-1}u_{t+1}
$$

$$
N_{\mathrm{CF},t+1}^{\mathrm{direct}} = e_{\mathrm{cf}}'(I-\rho\Phi)^{-1}u_{t+1}
$$

$\lambda$ is chosen in exactly one of two ways:

1. **Expected-return gradient** (default for Ang–Liu). Pass `xi` and `Lambda`. Then $\lambda = \xi + 2\Lambda\bar X$ with $\bar X$ the unconditional mean. The Ang–Liu state has no equity-return equation; this is the intended path.
2. **Named return equation** (Campbell–Shiller). Pass `return_state` as a name in `spec.names`. Then $\lambda = e_{\mathrm{return}}$.

Passing both, or neither, raises `StateSpecError`.

```python
news = news_decomposition(fit, returns, xi=xi, Lambda=Lambda)
# news.frame: date, cf, dr, unexpected, residual
# news.shares: var_cf, var_dr, cov, var_unexpected, residual_share
```

`residual = unexpected - (cf - dr)` is always present as a diagnostic.

The returns frame must be simple returns in $(-1, 5)$. Use compounded twelve-month simple returns, not a raw sum of log returns.

## Treasury test

```python
from varvaluation import treasury_test

news = treasury_test(nobs=800)
assert news.shares.var_cf < 1e-6
```

On a synthetic series whose cash-flow equation is identically zero, direct CF news is approximately 0. Whatever the discount-rate model missed sits in `residual`.
