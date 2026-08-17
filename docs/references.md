# References

In-text citations use author–year and link here.

The recursions are those of Ang and Liu (2004, 2001). This library
implements the **quadratic-Gaussian** case: both $\beta_t$ and
$\lambda_t$ may move, so $\mu_t$ is quadratic in $X_t$ and the priced
strip carries an $H(n)$ recursion. When $\Lambda=0$ the same class
collapses to exponential-affine. Gordon growth is
$\Phi=\Sigma=0$.

<div class="biblio" markdown="1">

## Recursions and news

- <span id="ang-liu-2004"></span>Ang, A. and J. Liu (2004), “How to Discount Cash Flows with Time-Varying Expected Returns,” *Journal of Finance* 59(6), 2745–2783. Definition II.1 and Proposition II.1 are the spot curve $\mu_t(n)=A(n)+B(n)'X_t+X_t'G(n)X_t$.
- <span id="ang-liu-2001"></span>Ang, A. and J. Liu (2001), “A General Affine Earnings Valuation Model,” *Review of Accounting Studies* 6, 397–425. Residual-income companion. Corollary 2.2: a constant spread over the risk-free rate is not always available, even with constant interest rates.
- <span id="campbell-1991"></span>Campbell, J. Y. (1991), “A Variance Decomposition for Stock Returns,” *Economic Journal* 101, 157–179.
- <span id="chen-da-zhao-2013"></span>Chen, L., Z. Da, and X. Zhao (2013), “What Drives Stock Price Movements?” *Review of Financial Studies* 26(4), 841–876. Cash-flow news must not be defined as the residual of a discount-rate model.
- <span id="newey-west-1987"></span>Newey, W. K. and K. D. West (1987), “A Simple, Positive Semi-definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix,” *Econometrica* 55(3), 703–708.
- <span id="stambaugh-1999"></span>Stambaugh, R. F. (1999), “Predictive Regressions,” *Journal of Financial Economics* 54(3), 375–421.

## What sits in $X_t$

- <span id="bansal-yaron-2004"></span>Bansal, R. and A. Yaron (2004), “Risks for the Long Run: A Potential Resolution of Asset Pricing Puzzles,” *Journal of Finance* 59(4), 1481–1509.
- <span id="campbell-shiller-1988"></span>Campbell, J. Y. and R. J. Shiller (1988), “The Dividend-Price Ratio and Expectations of Future Dividends and Discount Factors,” *Review of Financial Studies* 1(3), 195–228.
- <span id="cochrane-2011"></span>Cochrane, J. H. (2011), “Presidential Address: Discount Rates,” *Journal of Finance* 66(4), 1047–1108.
- <span id="croce-2014"></span>Croce, M. M. (2014), “Long-Run Productivity Risk: A New Hope for Production-Based Asset Pricing?” *Journal of Monetary Economics* 66, 68–85.
- <span id="ff-1997"></span>Fama, E. F. and K. R. French (1997), “Industry Costs of Equity,” *Journal of Financial Economics* 43(2), 153–193.
- <span id="ff-2000"></span>Fama, E. F. and K. R. French (2000), “Forecasting Profitability and Earnings,” *Journal of Business* 73(2), 161–175.
- <span id="fama-schwert-1977"></span>Fama, E. F. and G. W. Schwert (1977), “Asset Returns and Inflation,” *Journal of Financial Economics* 5(2), 115–146.
- <span id="goyal-welch-2003"></span>Goyal, A. and I. Welch (2003), “Predicting the Equity Premium with Dividend Ratios,” *Management Science* 49(5), 639–654.
- <span id="lettau-ludvigson-2001"></span>Lettau, M. and S. Ludvigson (2001), “Consumption, Aggregate Wealth, and Expected Stock Returns,” *Journal of Finance* 56(3), 815–849.
- <span id="nissim-penman-2001"></span>Nissim, D. and S. H. Penman (2001), “Ratio Analysis and Equity Valuation: From Research to Practice,” *Review of Accounting Studies* 6, 109–154. ROE decomposition and fade; not a rates-to-profitability regression.
- <span id="vbk-2017"></span>van Binsbergen, J. H. and R. S. J. Koijen (2017), “The Term Structure of Returns: Facts and Theory,” *Journal of Financial Economics* 124(1), 1–21. Returns on traded dividend claims; not a direct test of a fitted $\mu_t(n)$.
- <span id="vuolteenaho-2002"></span>Vuolteenaho, T. (2002), “What Drives Firm-Level Stock Returns?” *Journal of Finance* 57(1), 233–264. For a typical stock, cash-flow-news variance is more than twice expected-return-news variance.

</div>
