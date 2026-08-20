# Putting it together

The present value is literally

$$
V_t = \sum_n \mathbb{E}_t\Bigl[
  \underbrace{\text{discount path of length }n}_{\text{from the }\mu\text{'s}}
  \times
  \underbrace{\text{cash flow at }n}_{\text{from the }g\text{'s}}
\Bigr].
$$

Because both the discount path and the cash-flow path are functions of the *same* VAR, the covariance between them is automatically inside the expectation. Separate models would miss that term and would therefore mis-price the claim.

In short:

- \(X_t\) is the common driver.
- The VAR (\(c, \Phi, \Sigma\)) is the single dynamics that governs every variable in \(X\).
- Cash-flow growth is one coordinate of that dynamics → the cash-flow recursion (the numerator).
- Expected returns are a (possibly quadratic) function of that same dynamics → the priced recursion that gives the discount curve (the denominator).
- Value is the product of the two, evaluated under the joint law.

That is exactly what the library implements in closed form (no simulation needed once the VAR is estimated).

```python
from varvaluation import ValuationModel

model = ValuationModel.from_var(fit, xi=xi, Lambda=Lambda, alpha=0.04)
X = fit.X_lag[-1]

curve = model.spot_curve(X, n=15)          # the discount curve
value = model.value(X, C=1.0, n=40)        # present value of a unit claim
```

You can also bring your own cash-flow path and discount it at the model’s spot rates, or freeze the numerator at 1 and look only at the pure discount curve (`perpetuity`).

The key modelling discipline is never to mix a cash-flow forecast from one system with a discount curve from another. Both sides must read from the same \((\Phi, c, \Sigma)\).
