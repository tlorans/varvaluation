# The VAR dynamics

All the variables in \(X_t\) evolve according to one simple linear system:

$$
X_{t+1} = c + \Phi X_t + u_{t+1}
$$

where

- \(c\) is a vector of constants (intercepts),
- \(\Phi\) is a matrix of slopes (how much each variable today helps predict every variable tomorrow — own persistence on the diagonal, cross-effects off the diagonal),
- \(u_{t+1}\) are random shocks that can be correlated with each other (their covariance matrix is called \(\Sigma\)).

This is just a collection of ordinary linear regressions estimated *jointly*. Because everything is driven by the same \(X_t\) and the same shocks, the covariance between cash-flow surprises and discount-rate surprises is automatically present. That covariance is exactly what a product of separate expectations would miss.

Compactly:

$$
X_{t+1} = c + \Phi X_t + u_{t+1},\qquad u_{t+1}\sim N(0,\Sigma).
$$

The package estimates \(\Phi\), \(c\) and \(\Sigma\) for you (`estimate_var` or the panel version `estimate_var_panel`).

If every eigenvalue of \(\Phi\) has absolute value less than one (the *spectral radius* of \(\Phi\) is less than one), the system is stationary: rates and growth glide back to their long-run means. The package refuses to build a valuation model when the spectral radius is \(\ge 1\).

The off-diagonal cells of \(\Phi\) are the cross-forecast channels. The off-diagonal cells of \(\Sigma\) are the contemporaneous shock correlations. Together they are the statistical home of the covariance term that enters the price level.

```python
from varvaluation import estimate_var, simulate_state

state, spec = simulate_state(nobs=400, seed=7)
fit = estimate_var(state, spec)

print("Φ:\n", fit.Phi.round(3))
print("spectral radius:", round(fit.spectral_radius, 3))
```
