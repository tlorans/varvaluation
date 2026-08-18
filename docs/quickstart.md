# Offline check

No downloads. A synthetic state, one VAR, the two recursions, and the spot curve $\mu_t(n)$.

```text
python examples/quickstart.py
```

## What you get

```text
Mental map
  1. Product     value = E[discount path × cash flow]
  2. Covariance  Cov(∑g, ∑μ) enters the *price level*
  3. One VAR     both forecasts share (Φ, c, Σ)

Step 1. Estimate one joint VAR
  spectral radius : 0.409  (< 1 ⇒ stationary)
  Φ:
     ret  +0.295  +0.124
       g  +0.006  +0.402

Step 3. Cash-flow recursion
     n      E[C]/C
     1       0.999
     5       1.008
    10       1.021
    15       1.034

Step 4. Spot curve μ_t(n)
  identity check: μ_t(1) = 2.3709% = α+ξ'X+X'ΛX  ✓
     n    μ_t(n) %
     1        2.37
     5        3.78
    10        4.09
    15        4.19

Step 5. Present value
  strip-sum value (C=1, n=40) : 24.07
  flat PV vs curve            : +12.8%
```

Check that $\mu_t(1)$ equals the one-period $\mu_t$. That is the definition of the spot curve.

The course walks the same path:

- [The problem](guide/problem.md): flat-versus-curve gap
- [One system](guide/system.md): simulate, estimate, read $\Phi$ and $\Sigma$
- [The two recursions](guide/curve.md): cash-flow recursion, spot curve, present value
