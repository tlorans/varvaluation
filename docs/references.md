# References

In-text citations use author–year and link here.

The recursions are those of Ang and Liu (2004, 2001). This library
implements the **quadratic-Gaussian** case: both $\beta_t$ and
$\lambda_t$ may move, so $\mu_t$ is quadratic in $X_t$ and the priced
strip carries an $H(n)$ recursion. When $\Lambda=0$ the same class
collapses to exponential-affine. Gordon growth is their special case 1
(constant expected return and constant expected growth).
$\Phi=\Sigma=0$ is a further degeneracy that delivers the same closed
form, not the statement of that case.

<div class="biblio" markdown="1">

## Recursions and news

- <span id="ang-liu-2004"></span>Ang, A. and J. Liu (2004), “How to Discount Cash Flows with Time-Varying Expected Returns,” *Journal of Finance* 59(6), 2745–2783. Definition II.1 and Proposition II.1 are the spot curve $\mu_t(n)=A(n)+B(n)'X_t+X_t'G(n)X_t$. Special case 1 nests Gordon.
- <span id="ang-liu-2001"></span>Ang, A. and J. Liu (2001), “A General Affine Earnings Valuation Model,” *Review of Accounting Studies* 6, 397–425. Residual-income companion. Corollary 2.2: a constant spread over the risk-free rate is not always available, even with constant interest rates.
- <span id="brennan-1997"></span>Brennan, M. J. (1997), “The Term Structure of Discount Rates,” *Financial Management* 26(1), 81–90. Maturity-specific discount rates; the two-step workflow the 2004 curve keeps.
- <span id="campbell-1991"></span>Campbell, J. Y. (1991), “A Variance Decomposition for Stock Returns,” *Economic Journal* 101, 157–179.
- <span id="chen-zhao-2009"></span>Chen, L. and X. Zhao (2009), “Return Decomposition,” *Review of Financial Studies* 22(12), 5213–5249. Residual cash-flow news absorbs misspecification of the discount-rate model.
- <span id="chen-da-zhao-2013"></span>Chen, L., Z. Da, and X. Zhao (2013), “What Drives Stock Price Movements?” *Review of Financial Studies* 26(4), 841–876. Cash-flow news must not be defined as the residual of a discount-rate model.
- <span id="chen-2009"></span>Chen, L. (2009), “On the Reversal of Return and Dividend Growth Predictability: A Tale of Two Periods,” *Journal of Financial Economics* 92(1), 128–151. Dividend growth is forecastable before the war; returns take over after.
- <span id="dhs-1999"></span>Dechow, P. M., A. P. Hutton, and R. G. Sloan (1999), “An Empirical Assessment of the Residual Income Valuation Model,” *Journal of Accounting and Economics* 26(1–3), 1–34. Ohlson dynamics get support; little gain over capitalizing short earnings forecasts.
- <span id="feltham-ohlson-1995"></span>Feltham, G. A. and J. A. Ohlson (1995), “Valuation and Clean Surplus Accounting for Operating and Financial Activities,” *Contemporary Accounting Research* 11(2), 689–731.
- <span id="hodrick-1992"></span>Hodrick, R. J. (1992), “Dividend Yields and Expected Stock Returns: Alternative Procedures for Inference and Measurement,” *Review of Financial Studies* 5(3), 357–386. Overlapping annual horizons; trailing-dividend construction.
- <span id="newey-west-1987"></span>Newey, W. K. and K. D. West (1987), “A Simple, Positive Semi-definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix,” *Econometrica* 55(3), 703–708.
- <span id="ohlson-1995"></span>Ohlson, J. A. (1995), “Earnings, Book Values, and Dividends in Equity Valuation,” *Contemporary Accounting Research* 11(2), 661–687. Residual income. Cited, not implemented.
- <span id="stambaugh-1999"></span>Stambaugh, R. F. (1999), “Predictive Regressions,” *Journal of Financial Economics* 54(3), 375–421.
- <span id="vuolteenaho-2002"></span>Vuolteenaho, T. (2002), “What Drives Firm-Level Stock Returns?” *Journal of Finance* 57(1), 233–264. Uses $e_t=\log(1+X_t/B_{t-1})$, not $\log(\mathrm{NI}/\mathrm{BE}_{\mathrm{lag}})$. Section 5 does not confirm the finding.

## What sits in $X_t$

- <span id="bansal-yaron-2004"></span>Bansal, R. and A. Yaron (2004), “Risks for the Long Run: A Potential Resolution of Asset Pricing Puzzles,” *Journal of Finance* 59(4), 1481–1509.
- <span id="campbell-shiller-1988"></span>Campbell, J. Y. and R. J. Shiller (1988), “The Dividend-Price Ratio and Expectations of Future Dividends and Discount Factors,” *Review of Financial Studies* 1(3), 195–228.
- <span id="cochrane-2008"></span>Cochrane, J. H. (2008), “The Dog That Did Not Bark: A Defense of Return Predictability,” *Review of Financial Studies* 21(4), 1533–1575. The present-value identity can imply return predictability even when the dividend yield is a weak return forecast.
- <span id="cochrane-2011"></span>Cochrane, J. H. (2011), “Presidential Address: Discount Rates,” *Journal of Finance* 66(4), 1047–1108.
- <span id="croce-2014"></span>Croce, M. M. (2014), “Long-Run Productivity Risk: A New Hope for Production-Based Asset Pricing?” *Journal of Monetary Economics* 66, 68–85.
- <span id="ff-1997"></span>Fama, E. F. and K. R. French (1997), “Industry Costs of Equity,” *Journal of Financial Economics* 43(2), 153–193.
- <span id="ff-2000"></span>Fama, E. F. and K. R. French (2000), “Forecasting Profitability and Earnings,” *Journal of Business* 73(2), 161–175.
- <span id="ff-2006"></span>Fama, E. F. and K. R. French (2006), “Profitability, Investment and Average Returns,” *Journal of Financial Economics* 82(3), 491–518. Expected profitability and investment enter the dividend-discount *level*; they also line up average returns.
- <span id="hxz-2015"></span>Hou, K., C. Xue, and L. Zhang (2015), “Digesting Anomalies: An Investment Approach,” *Review of Financial Studies* 28(3), 650–705. A \(q\)-factor model: investment and profitability as return characteristics, motivated by present-value \(q\).
- <span id="kvn-2011"></span>Koijen, R. S. J. and S. Van Nieuwerburgh (2011), “Predictability of Returns and Cash Flows,” *Annual Review of Financial Economics* 3, 467–491. Survey: which side of the present-value identity is forecastable depends on sample and on how dividends are measured.
- <span id="lettau-ludvigson-2005"></span>Lettau, M. and S. C. Ludvigson (2005), “Expected Returns and Expected Dividend Growth,” *Journal of Financial Economics* 76(3), 583–626. Expected dividend growth varies and moves with expected returns.
- <span id="fama-schwert-1977"></span>Fama, E. F. and G. W. Schwert (1977), “Asset Returns and Inflation,” *Journal of Financial Economics* 5(2), 115–146.
- <span id="goyal-welch-2003"></span>Goyal, A. and I. Welch (2003), “Predicting the Equity Premium with Dividend Ratios,” *Management Science* 49(5), 639–654.
- <span id="goyal-welch-2008"></span>Goyal, A. and I. Welch (2008), “A Comprehensive Look at the Empirical Performance of Equity Premium Prediction,” *Review of Financial Studies* 21(4), 1455–1508. In-sample predictors, including $\mathit{cay}$, fail or weaken out of sample.
- <span id="lettau-ludvigson-2001"></span>Lettau, M. and S. Ludvigson (2001), “Consumption, Aggregate Wealth, and Expected Stock Returns,” *Journal of Finance* 56(3), 815–849. Strong in-sample quarterly predictor. The FRED reconstruction in Section 5 is not their cointegrating residual.
- <span id="lewellen-nagel-2006"></span>Lewellen, J. and S. Nagel (2006), “The Conditional CAPM Does Not Explain Asset-Pricing Anomalies,” *Journal of Financial Economics* 82(2), 289–314. Short-window betas are noisy.
- <span id="nissim-penman-2001"></span>Nissim, D. and S. H. Penman (2001), “Ratio Analysis and Equity Valuation: From Research to Practice,” *Review of Accounting Studies* 6, 109–154. ROE decomposition and fade; not a rates-to-profitability regression.
- <span id="vbk-2010"></span>van Binsbergen, J. H. and R. S. J. Koijen (2010), “Predictive Regressions: A Present-Value Approach,” *Journal of Finance* 65(4), 1439–1471.
- <span id="vbbk-2012"></span>van Binsbergen, J., M. Brandt, and R. Koijen (2012), “On the Timing and Pricing of Dividends,” *American Economic Review* 102(4), 1596–1618. Prices of traded dividend strips.
- <span id="vbk-2017"></span>van Binsbergen, J. H. and R. S. J. Koijen (2017), “The Term Structure of Returns: Facts and Theory,” *Journal of Financial Economics* 124(1), 1–21. Returns on traded dividend claims; not a direct test of a fitted $\mu_t(n)$.

</div>
