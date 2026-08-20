# Cash-flow dynamics and the link to \(X_t\)

Cash flows themselves are written in growth form. If \(g\) is the cash-flow growth coordinate of \(X\), then

$$
C_{t+n} = C_t \times \exp\bigl(g_{t+1} + g_{t+2} + \dots + g_{t+n}\bigr).
$$

Because \(g\) is one piece of the VAR, the whole future path of growth is completely determined by today’s \(X_t\):

- The expected path of growth is obtained by iterating the VAR forward (using the relevant row of \(\Phi\)).
- Because shocks are Gaussian, the expectation of the *exponential* of the sum of future growth rates has a closed-form expression that also includes a variance (Jensen) term coming from \(\Sigma\).

The package computes this with a simple recursion called the **cash-flow recursion**. The result is an affine function of today’s state:

$$
\frac{\mathbb{E}_t[C_{t+n}]}{C_t}
  = \exp\bigl(\bar a(n) + \bar b(n)' X_t\bigr).
$$

So the link is direct: **today’s entire vector \(X_t\) tells you (via \(\Phi\) and \(\Sigma\)) what cash-flow growth is expected to do at every future horizon, and how uncertain that path is.**

No discounting enters this recursion. It only produces the numerator of each strip. The coefficients start at

$$
\bar a(1) = e_g'c + \tfrac12 e_g'\Sigma e_g,\qquad
\bar b(1) = \Phi'e_g
$$

and then iterate. Here \(e_g\) is the selector that picks the cash-flow row of the state.

A state variable moves expected cash flows only if it appears in the cash-flow equation of the VAR (i.e., the corresponding entry of \(\Phi\) is non-zero). It can still affect the discount curve without affecting the numerator.
