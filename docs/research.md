# Data and research decisions

Reviewed 22 November 2026. Free access and permission to redistribute are separate questions. Only synthetic examples ship with this project.

## Market data

| Candidate | Access and coverage | Decision |
| --- | --- | --- |
| Alpaca Basic | An eligible paper account can request historical US stock and ETF bars. Basic has IEX coverage and history since 2016. IEX volume and some OHLC values can differ materially from consolidated US data. | Implemented for the four US symbols. Use privately under the applicable subscriber agreement. Review account permissions for storage and non-display research before import or changing the intended use. |
| Alpha Vantage | Free compact raw daily history provides up to 100 bars. Full daily history requires premium access. Its terms govern use. | Possible short-window cross-check. Raw prices need a compatible split basis for comparisons. |
| Botswana Stock Exchange | The BSE offers historical data and ETF information by request. Educational fee waivers are discretionary. STX500-ETF and STXWDM-ETF are listed counters. | Obtain a data specification, licence and quote from productdev@bse.co.bw. Confirm price units, corporate actions, zero-trade days and quote age before integrating. |
| VWRA | The selected US stock endpoint covers US instruments. | Confirm the intended listing, trading currency, session calendar and data entitlement before adding it. |

Provider references: [Alpaca plans](https://docs.alpaca.markets/us/v1.1/docs/about-market-data-api), [historical bars contract](https://docs.alpaca.markets/us/reference/stockbars), [agreements](https://alpaca.markets/disclosures), [Alpha Vantage daily API](https://www.alphavantage.co/documentation/#daily), [Alpha Vantage terms](https://www.alphavantage.co/terms_of_service/), [BSE data products](https://www.bse.co.bw/data-products-2/), [BSE ETFs](https://www.bse.co.bw/exchange-traded-fund/).

### Data contract and limitations

The adapter requests `1Day`, `feed=iex`, `adjustment=split` for all four symbols from Alpaca's historical bars endpoint. Provider split adjustment applies to prices and volume. Dividends are excluded. VOO close-to-close performance would therefore omit distributions. A total-return study requires a separate distribution series and consistent handling of dividends for the strategy and benchmarks. Adjusted history can be revised. A snapshot fetched today cannot establish which adjustments were available on a past decision date.

Normalize provider bar timestamps to New York session dates. Use XNYS as the common scheduled US equity session calendar for these instruments. Reject missing sessions, unexpected symbols, duplicates, nonfinite values, invalid price ranges and fractional or negative volume. Never fill a missing price with yesterday's close. A halt or a missing IEX session may legitimately block an import. Inspect the affected range before reuse. The snapshot model stores normalized data, feed, price basis, interval and UTC retrieval time, but does not archive raw HTTP replies or prove historical point-in-time availability. Daily bars omit bid/ask spreads, queue depth and intraday execution order. Provider rate or network errors stop the import; retry the same command after recovery.

## Evidence and evaluation design

Lo, Mamaysky and Wang found that some technical patterns added information about historical conditional return distributions. Their analysis motivates testing features, and supplies no measured result for this watchlist's RSI or MACD rules. Gu, Kelly and Xiu studied a broad equity cross-section and found predictive value from nonlinear interactions. Four selected liquid US instruments, daily horizons and a USD 100 account pose a different empirical question. [Technical analysis study](https://www.mit.edu/~alo/Papers/techanal.html) · [Machine learning study](https://www.nber.org/papers/w25398)

For the next milestone, predefine the short-term target as whether a long trade opened at the next session's open and closed at a fixed later open earns a positive return after costs. Pin the holding horizon, investable universe, data vintage and date cutoffs before fitting. Use the same calendar boundaries across all symbols. Purge training labels whose outcome windows overlap validation or test. Fit scalers, imputation, thresholds and probability calibration only inside earlier development folds. Use an expanding training window, a subsequent validation window and an untouched final date block. Reserve a later forward paper log for independent confirmation.

Compare logistic regression, Random Forest and XGBoost with a training-only base rate. Assess calibration with reliability bins, Brier score and log loss. A model output of 0.70 is a score until held-out observations near 0.70 show the corresponding event frequency, with uncertainty. Check stability across trailing volatility regimes defined from training data. The short watchlist introduces selection bias and correlated exposures.

Start the simulator at USD 100 cash. Track available cash, minimum commissions, spread, slippage, FX costs, fractional-share eligibility, residual cash and turnover. Apply the same rules to buy-and-hold VOO and a predeclared simple moving-average strategy. Specify how each benchmark receives contributions and dividends. Compare net ending wealth, maximum drawdown, exposure and risk-adjusted return. Show sensitivity to costs, the number of trades and uncertainty. At USD 100, a hypothetical USD 1 round-trip cost absorbs 1% of starting capital. That example is arithmetic, independent of any particular broker's fee schedule.

For a long-term ETF study, use total returns, funding frequency, exchange-rate exposure and cash drag. Keep the short-horizon stock experiment in a separate paper ledger so frequent trades cannot quietly consume the long-term allocation.

## Botswana and connectivity

IBKR includes Botswana on its available-country list. TWS API and Web API support paper accounts. Paper fills use a simulator with limited fill realism. Account eligibility, FX/funding costs and fractional-share availability for the exact instrument and account require verification before modeling executable positions. No broker integration exists in this milestone. [Country list](https://www.interactivebrokers.com/en/accounts/open-account-country-list.php) · [Paper API](https://www.interactivebrokers.com/support/faq/content/use-ibkrs-apis-paper-account-629299048) · [Simulator limitations](https://www.interactivebrokers.com/support/faq/content/limitations-paper-trading-account-35807733)

For the Botswana route, the BSE publishes ETF trading fees and brokerage commission bands. For ETF trades below P50,000 its published table lists P9.60 BSE and P6.40 CSD per side before VAT, with brokerage listed separately. Obtain a local broker's all-in written quote and minimum trade size before a BWP simulation. Recheck prevailing prices and fees at evaluation time. [BSE fees](https://www.bse.co.bw/fees/) · [BSE investor FAQ](https://www.bse.co.bw/investors-faq/)
