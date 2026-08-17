# References

The closed-form recursions implemented here are those of Ang and Liu
(2004, 2001). This library uses the **quadratic-Gaussian** case: both
$\beta_t$ and $\lambda_t$ may move, so $\mu_t$ is quadratic in $X_t$
and the priced strip carries an $H(n)$ recursion. When $\Lambda=0$
(constant beta or constant premium) the same class collapses to
exponential-affine. Gordon growth is the further collapse
$\Phi=\Sigma=0$. The news identity and the residual critique are
Campbell (1991) and Chen, Da, and Zhao (2013). This page is the only
place the docs name those two valuation papers.

## Recursions and news

- Ang, A. and J. Liu (2004), “How to Discount Cash Flows with Time-Varying Expected Returns,” *Journal of Finance* 59(6), 2745–2783.
- Ang, A. and J. Liu (2001), “A General Affine Earnings Valuation Model,” *Review of Accounting Studies* 6, 397–425.
- Campbell, J. Y. (1991), “A Variance Decomposition for Stock Returns,” *Economic Journal* 101, 157–179.
- Chen, L., Z. Da, and X. Zhao (2013), “What Drives Stock Price Movements?” *Review of Financial Studies* 26(4), 841–876.

The 2004 paper’s Definition II.1 / Proposition II.1 is the spot curve
$\mu_t(n)=A(n)+B(n)'X_t+X_t'G(n)X_t$. The 2001 companion is the
residual-income version of the same idea (Corollary 2.2: a constant
spread over the risk-free rate is not always available, even with
constant interest rates).

## What sits in $X_t$

- Bansal, R. and A. Yaron (2004), “Risks for the Long Run,” *Journal of Finance* 59(4), 1481–1509.
- Campbell, J. Y. and R. J. Shiller (1988), “The Dividend-Price Ratio and Expectations of Future Dividends and Discount Factors,” *Review of Financial Studies* 1(3), 195–228.
- Cochrane, J. H. (2011), “Presidential Address: Discount Rates,” *Journal of Finance* 66(4), 1047–1108.
- Croce, M. M. (2014), “Long-Run Productivity Risk,” *Journal of Monetary Economics* 66, 68–85.
- Fama, E. F. and K. R. French (1997), “Industry Costs of Equity,” *Journal of Financial Economics* 43(2), 153–193.
- Fama, E. F. and K. R. French (2000), “Forecasting Profitability and Earnings,” *Journal of Business* 73(2), 161–175.
- Fama, E. F. and G. W. Schwert (1977), “Asset Returns and Inflation,” *Journal of Financial Economics* 5(2), 115–146.
- Goyal, A. and I. Welch (2003), “Predicting the Equity Premium with Dividend Ratios,” *Management Science* 49(5), 639–654.
- Lettau, M. and S. Ludvigson (2001), “Consumption, Aggregate Wealth, and Expected Stock Returns,” *Journal of Finance* 56(3), 815–849.
- Nissim, D. and S. H. Penman (2001), “Ratio Analysis and Equity Valuation,” *Review of Accounting Studies* 6, 109–154.
- van Binsbergen, J. H. and R. S. J. Koijen (2017), “The Term Structure of Returns,” *Journal of Financial Economics* 124(1), 1–21.
- Vuolteenaho, T. (2002), “What Drives Firm-Level Stock Returns?” *Journal of Finance* 57(1), 233–264.

Nissim and Penman (2001) is the ROE decomposition and fade, not a
rates-to-profitability regression. Vuolteenaho (2002): for a typical
stock the variance of cash-flow news is more than twice that of
expected-return news. van Binsbergen and Koijen (2017) measure returns
on traded dividend claims; they are not a direct test of a fitted
$\mu_t(n)$ curve.
