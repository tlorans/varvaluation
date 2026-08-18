# Going further

You now have the three-step map, the two recursions, and the follow-along numbers on the synthetic state. This page is optional orientation: where the literature stands on *state-variable choices* and on *applications beyond equity portfolios*.

The map — product, covariance, one VAR — is asset-class agnostic. What changes across papers is which coordinates enter $X_t$, and which claim is being priced.

---

## State variables

Value is $E[\text{discount path}\times\text{cash flow}]$. The state therefore needs at least a cash-flow coordinate — growth $g_t=\log(C_t/C_{t-1})$, or an accounting object that maps into growth, such as ROE or residual income — and coordinates that move expected returns: the short rate, a market premium $\lambda_t$, conditional beta $\beta_t$, or other predictors.

If both $\beta_t$ and $\lambda_t$ move, $\mu_t=\alpha+\xi'X_t+X_t'\Lambda X_t$ is *quadratic* and the priced recursion carries an $H(n)$ matrix ([Ang and Liu, 2004](../references.md#ang-liu-2004)). If either is constant, $\Lambda=0$ and the strip is exponential-affine.

A few facts about the equity state are settled.

Profitability is forecastable and mean-reverts ([Fama and French, 2000](../references.md#ff-2000)). ROE or a related profitability measure belongs as a *level*, not only as a growth rate.

The dividend yield is a weak out-of-sample return predictor ([Goyal and Welch, 2003, 2008](../references.md#goyal-welch-2008)). Do not treat it as a free lunch. Test no-look-ahead vintages.

The present-value identity still requires *something* to be predictable ([Campbell and Shiller, 1988](../references.md#campbell-shiller-1988); [Cochrane, 2008, 2011](../references.md#cochrane-2011)). Either cash-flow growth or discount rates, or both, must move with valuation ratios.

The short rate is a classical predictor ([Fama and Schwert, 1977](../references.md#fama-schwert-1977)), and a natural coordinate when the risk-free rate sits inside the VAR.

Consumption–wealth residual $\mathit{cay}$ is strong *in sample* ([Lettau and Ludvigson, 2001](../references.md#lettau-ludvigson-2001)). It is a useful instrument, disputed out of sample and on look-ahead.

Long-run growth risk can drive both sides of the product ([Bansal and Yaron, 2004](../references.md#bansal-yaron-2004)). That is a structural rationale for a shared state. It is not estimated here.

A standard empirical system is six-dimensional: growth, beta, and instruments for the premium and the short rate. The package lets you name any subset and mark which row is cash-flow growth (`StateSpec.cashflow`).

A few specification choices matter more than the rest.

A VAR(1) is the workhorse because closed forms for $E[e^{\cdot}]$ are analytic under Gaussian shocks. The spectral radius of $\Phi$ must be less than one; otherwise the unconditional mean does not exist and the library refuses to build the model.

Quadratic $\mu_t$ is required when beta and the premium *both* move. Setting $\Lambda=0$ is a deliberate restriction, not the default of the theory.

A full Treasury curve can be kept *outside* $X_t$ and supplied as data when forming spot rates. That is common in applications that already have a fitted yield curve.

A single companion on stacked lag pairs is not the same object as firm-level companions. Cross-firm lagging is a specification error the panel estimator is designed to avoid.

[Building the state](state.md) turns these choices into named coordinates. [One system](system.md) is where $\Phi$ and $\Sigma$ enter the map.

---

## Other asset classes

The product identity does not care whether $C$ is a dividend, a coupon, a rent, or a convenience-adjusted commodity payoff. The literature has developed parallel term structures of discount rates for several claims.

Affine term-structure models are the fixed-income sibling of the equity construction. A low-dimensional state drives the entire yield curve under no-arbitrage ([Duffie and Kan, 1996](../references.md#duffie-kan-1996); [Dai and Singleton, 2000](../references.md#dai-singleton-2000); [Ang and Piazzesi, 2003](../references.md#ang-piazzesi-2003)). Spot rates $\mu_t(n)$ play the same practical role that yields play for bonds: one number per horizon, read from a joint state. The difference is institutional. Bond cash flows are contractual; equity cash flows are discretionary. The map — product, covariance, one system — is the same.

Sovereign curves add credit, political, and currency risk to the usual rate factors. Joint VARs of domestic yields, spreads, and macro variables are common. The discount-rate object remains a maturity-specific spot rate implied by a joint law of motion. Cross-country panels often share global factors while keeping local state coordinates for the cash-flow (coupon) side.

In real estate, rents replace dividends and the rent–price ratio is the valuation ratio ([Plazzi, Torous, and Valkanov, 2010](../references.md#plazzi-2010)). Expected rent growth and expected returns on property, or on REIT equity, must again share a state if the covariance term is to enter the price. Empirical work finds that discount-rate variation is a large driver of real-estate price movements, consistent with the equity evidence that a flat cap rate misprices when expected returns move.

For commodity futures the cash-and-carry identity links spot, futures, and the convenience yield. Convenience yield, or inventory, is the natural cash-flow-like state. The futures basis and risk premia play the role of discount-rate coordinates. VARs of spot, convenience yield, and basis are standard. Time-varying discount rates matter, though cash-flow (convenience-yield) news often plays a larger relative role than in equities. The same product logic applies once a claim to future commodity payoffs is written down.

What stays fixed is the map. Equities use $g$ or ROE as the cash-flow coordinate and $\beta$, $\lambda$, and $r_f$ as discount-rate coordinates. Bonds use the coupon, or the risk-free payoff, and the usual level-slope-curvature factors. Real estate uses rent growth and a cap rate or expected return. Commodities use convenience yield or inventory, and the basis or risk premium. In every case the joint law is a VAR, or an affine state, for $X_t$, and the practical output is a maturity-specific discount rate.

The package implements the equity, and portfolio, case. Extending it to another asset class is a change of *state names and data*, not a change of the mental map or the two recursions.

The package’s own check of the 2004 tables is [Ang and Liu (2004)](angliu.md). The full bibliography is [References](../references.md).
