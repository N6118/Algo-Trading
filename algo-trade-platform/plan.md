# Algorithmic Trading Platform Plan

This document outlines the comprehensive plan for building an algorithmic trading platform with data collection, processing, signal generation, and trade management capabilities. The platform will include a correlation-based strategy as an initial implementation, optimized for U.S. markets.

## 1. Data Collection

- [x] Collect tick data for symbols via WebSocket
  - [x] Implemented in `streamdata.py` using IBKR API
  - [x] Store tick data in TimescaleDB
  - [x] Handle reconnection and error scenarios
  - [x] Implement fail-over feed using Polygon.io for redundancy
  - [x] Add latency monitoring (exchange-timestamp vs. arrival-timestamp)
  
- [x] Convert tick data to timeframe data
  - [x] 5-minute timeframe data (continuous aggregate in TimescaleDB)
  - [x] 15-minute timeframe data (continuous aggregate in TimescaleDB)
  - [ ] 30-minute timeframe data (continuous aggregate in TimescaleDB)
  - [x] 60-minute timeframe data (continuous aggregate in TimescaleDB)
  - [ ] Setup data archiving to cold storage (SEC 17a-4 compliance)

## 2. Data Consolidation

- [x] Database setup for storing consolidated data
  - [x] Implemented in `dbsetup.py` using TimescaleDB
  - [x] Created hypertables and continuous aggregates
  - [x] Set up compression and retention policies

- [x] Calculate technical indicators and store in timeseries table
  - [x] Implemented in `Stocks/attempt.py`
  - [x] Fractal Highs/Lows (FH/FL)
  - [x] Swing Highs/Lows (SH/SL)
  - [x] Average True Range (ATR)
  - [x] Pivot Points
  - [x] Donchian Channels (DC)
  - [ ] Add futures contract roll logic for continuous contracts

## 3. Signal Scanning (SS)

- [x] Implement signal scanning framework
  - [x] Create signal scanning database tables
  - [x] Implement signal scanning service
  - [x] Setup configurable interval scanning for correlation strategies
  - [x] Add connection pooling for database operations
  - [x] Implement retry mechanism for transient failures
  - [x] Add cleanup of old signals based on expiry
  - [x] Add duplicate signal detection

- [x] Signal scanning parameters
  - [x] Name
  - [x] Expiry (Weekly, Monthly)
  - [x] SS-Type (Intraday, Positional)
  - [x] SS-Days (Mon, Tue, Wed, Thu, Fri, All)
  - [x] Scheduler
  - [x] Start Time, End Time (with U.S. market hours defaults)
  - [x] Number of Signals
  - [x] SS-signal-Type (Long, Short)
  - [x] SS-placeholder (FUT, OPTION, ETF, Cash Equity)
  - [x] SS-Option Type (CALL, PUT)
  - [x] SS-Option Category (ITM, OTM, FUT, DOTM, DITM with U.S. tick structure)
  - [x] SS-Mode (Live, Virtual)
  - [x] SS-Entry-Rules
  - [x] SS-Exit-Rules
  - [x] Pre/Post market hours validation
  - [x] Market holiday checks

### 3.1 Multi-Symbol Correlation Strategy

- [x] Implement correlation strategy framework
  - [x] Support flexible symbol configuration
  - [x] Calculate technical indicators for selected symbols
  - [x] Configure timeframes for indicator calculations
  - [x] Setup configurable signal generation intervals
  - [x] Add settlement-price vs. last-trade sanity checks
  - [x] Add timezone handling for market data
  - [x] Implement data gap detection
  - [x] Add outlier detection using z-scores
  - [x] Add market hours validation
  - [x] Implement multiple correlation methods (Pearson, Spearman, Kendall)
  - [x] Add rolling correlation support
  - [x] Add correlation threshold validation

- [x] Buy Signal Conditions (configurable for any symbol):
  - [x] Price of primary symbol > SH of primary symbol
  - [x] Price of correlated symbol < SL of correlated symbol
  - [x] Correlation threshold validation
  - [x] Minimum data points validation
  - [x] Data quality checks
  - [x] Other custom conditions

- [x] Sell Signal Conditions (configurable for any symbol):
  - [x] Price of primary symbol < SL of primary symbol
  - [x] Price of correlated symbol > SH of correlated symbol
  - [x] Correlation threshold validation
  - [x] Minimum data points validation
  - [x] Data quality checks
  - [x] Other custom conditions

## 4. Signal Generation (SG)

### Database Model
- [x] Create SignalGeneration model with fields:
  - [x] user_id (FK to User)
  - [x] strategy_id (FK to Strategy)
  - [x] symbol (String)
  - [x] exchange (Enum: NYSE, NASDAQ, CBOE, SMART)
  - [x] order_type (Enum: STOP, STOP_LIMIT, MARKET, LIMIT, TRAILING_STOP)
  - [x] product_type (Enum: MARGIN, CASH)
  - [x] side (Enum: BUY, SELL)
  - [x] contract_size (Integer)
  - [x] quantity (Integer)
  - [x] entry_price (Float, nullable)
  - [x] stop_loss (Float, nullable)
  - [x] take_profit (Float, nullable)
  - [x] status (Enum: PENDING, VALIDATED, EXECUTED, CANCELLED, FAILED)
  - [x] created_at (DateTime)
  - [x] updated_at (DateTime)
  - [x] is_active (Boolean)
- [x] Add constraints:
  - [x] Positive values for contract_size, quantity, entry_price, stop_loss, take_profit
  - [x] Quantity must be a multiple of contract_size
  - [x] Entry price required for LIMIT and STOP_LIMIT orders
  - [x] Stop loss below entry price for BUY orders
  - [x] Stop loss above entry price for SELL orders
  - [x] Take profit above entry price for BUY orders
  - [x] Take profit below entry price for SELL orders
  - [x] Unique constraint on (user_id, strategy_id, symbol, created_at)
- [x] Add indexes:
  - [x] Primary key on id
  - [x] Index on user_id
  - [x] Index on strategy_id

### Market Data Service
- [x] Implement IBKR integration:
  - [x] Connection management with retry mechanism
  - [x] Error handling for API errors
  - [x] Connection pooling
  - [x] Market data subscription cleanup
- [x] Add methods:
  - [x] validate_symbol: Check if symbol exists and is tradeable
  - [x] get_current_price: Get real-time price with pre/post market support
  - [x] get_market_status: Check if market is open with pre/post market support
  - [x] get_historical_data: Get historical price data for backtesting
  - [x] get_option_chain: Get option chain data for options trading
  - [x] get_market_data: Get comprehensive market data (price, volume, etc.)
  - [x] get_market_depth: Get order book data
  - [x] get_fundamental_data: Get company fundamentals
  - [x] get_corporate_actions: Get dividends and splits

### Order Service
- [x] Implement IBKR integration:
  - [x] Connection management with retry mechanism
  - [x] Error handling for API errors
  - [x] Connection pooling
  - [x] Order subscription cleanup
- [x] Add regulatory compliance:
  - [x] PDT rule validation
  - [x] Reg-T margin requirement validation
  - [x] Order rejection handling
- [x] Add order types:
  - [x] Market orders
  - [x] Limit orders
  - [x] Stop orders
  - [x] Stop-limit orders
  - [x] Trailing stop orders
  - [x] Bracket orders (entry + stop loss + take profit)
  - [x] OCO orders (One Cancels Other)
- [x] Add order features:
  - [x] Time-in-force options (DAY, GTC, IOC, FOK)
  - [x] Order routing preferences (SMART, DIRECT, ARCA, NYSE, NASDAQ, CBOE)
  - [x] Order allocation methods (FIFO, LIFO, PRO_RATA)
- [x] Add methods:
  - [x] create_order: Create a new order
  - [x] modify_order: Modify an existing order
  - [x] cancel_order: Cancel an existing order
  - [x] get_order_status: Get order status and fills
  - [x] create_bracket_order: Create a bracket order
  - [x] create_oco_order: Create an OCO order

### Signal Generation Parameters
- [x] Exchange types:
  - [x] NYSE
  - [x] NASDAQ
  - [x] CBOE
  - [x] SMART
- [x] Order types:
  - [x] STOP
  - [x] STOP_LIMIT
  - [x] MARKET
  - [x] LIMIT
  - [x] TRAILING_STOP
- [x] Product types:
  - [x] MARGIN
  - [x] CASH
- [x] Contract sizes:
  - [x] Stocks: 1 share
  - [x] Options: 100 shares per contract
  - [x] Futures: Varies by contract
- [x] Time-in-force options:
  - [x] DAY: Order expires at end of day
  - [x] GTC: Good Till Cancelled
  - [x] IOC: Immediate or Cancel
  - [x] FOK: Fill or Kill
- [x] Order routing options:
  - [x] SMART: Smart routing
  - [x] DIRECT: Direct to exchange
  - [x] ARCA: ARCA exchange
  - [x] NYSE: NYSE exchange
  - [x] NASDAQ: NASDAQ exchange
  - [x] CBOE: CBOE exchange
- [x] Order allocation methods:
  - [x] FIFO: First In, First Out
  - [x] LIFO: Last In, First Out
  - [x] PRO_RATA: Proportional allocation

## 5. Trade Management

- [ ] Implement trade management framework
  - [ ] Create trade management database tables
  - [ ] Implement trade management service
  - [ ] Setup 5-second monitoring interval for stop-loss and profit targets

### 5.1 Before Initiating Trade

- [ ] Implement pre-trade checks and calculations
  - [ ] Number of Active trades
  - [ ] Number of Trades per day
  - [ ] PDT rule check (< $25,000 equity and ≥ 4 day-trades in 5 business days)
  - [ ] TM-IProfit (Initial profit target)
  - [ ] TM-Isp (Initial stop-loss price)
  - [ ] Account risk percentage (should be less than RM-Max-sp-per-trade%)
  - [ ] Calculate number of shares based on risk parameters
  - [ ] Calculate trade risk
  - [ ] Calculate total risk percentage
  - [ ] Adjust stop loss based on calculations
  - [ ] Calculate Reg-T margin and overnight buying power usage

### 5.2 Risk Management

- [ ] Implement risk management system
  - [ ] RM-Max-sp-per-trade (Maximum stop-loss price per trade)
  - [ ] RM-Max-sp-per-trade% (Maximum stop-loss percentage per trade)
  - [ ] RM-Max-sp (Maximum stop-loss across all trades)
  - [ ] RM-Max-sp% (Maximum stop-loss percentage across all trades - account drawdown limit)
  - [ ] Capital Utilized% (auto-calculated based on daily trades)
  - [ ] Position% (auto-calculated based on daily trades)

### 5.3 Risk Reduction

- [ ] Implement risk reduction for profitable trades
  - [ ] Track Entry-Price
  - [ ] Track Current-Price
  - [ ] Track Current-Stop-Loss (current stop-loss price)
  - [ ] Implement RR-Trigger mechanism
  - [ ] Calculate and execute Qty-Sell for risk reduction

### 5.4 After Initiating Trade

- [ ] Implement trade monitoring system
  - [ ] Monitor stop loss conditions every 5 seconds
  - [ ] Monitor profit target conditions every 5 seconds
  - [ ] Monitor exit rule conditions
  - [ ] Implement time-based trade closure (close all running trades at specified time)

### 5.5 Progressive P&L Tracking

- [ ] Implement P&L tracking
  - [ ] Calculate P&L for closed trades
  - [ ] Update RM-Max-sp based on P&L
  - [ ] Adjust stop loss based on risk reduction
  - [ ] Adjust stop loss based on account risk percentage
  - [ ] Ensure total P&L% is less than RM-Max-sp% (account drawdown limit)

## 6. Trade Status

- [ ] Implement trade status tracking
  - [ ] Last signal (Long/Short)
  - [ ] Trade Status (Running/Closed/Waiting)
  - [ ] Order status (Initiated/placed/pending/Success/Failed)

## 7. Deals Report

- [ ] Implement deals reporting system
  - [ ] Strategy Name
  - [ ] SS-Type
  - [ ] SS-signal-Type
  - [ ] Symbol name
  - [ ] Quantity (Entry Qty, Exit Qty)
  - [ ] Price (Entry Price, Exit Price)
  - [ ] P&L
  - [ ] Charges
  - [ ] Net P&L
  - [ ] Net P&L%
  - [ ] Date (Entry Date, Exit Date)
  - [ ] Status (Running, Completed)
  - [ ] Comments (How trade got closed, e.g., Stop-loss, Profit, Exit-rule)

## 8. Universal Settings

- [ ] Implement universal settings management
  - [ ] Capital
  - [ ] Open-Time (default 09:30 ET, stored in UTC)
  - [ ] Close-Time (default 16:00 ET, stored in UTC)
  - [ ] Pre-Market (04:00-09:30 ET)
  - [ ] Post-Market (16:00-20:00 ET)
  - [ ] Holiday calendar lookup (NYSE schedule + half-days)
  - [ ] SS-option category-Split (e.g., 200 to 100 - ITM for CALL/PUT)

## 9. API Integration

- [x] Connect with Exchange API for login/authentication
  - [x] Implemented in `streamdata.py` for IBKR

- [x] WebSocket API for scraping tick data from exchange
  - [x] Implemented in `streamdata.py`

- [ ] Order Execution API
  - [ ] Implement order placement
  - [ ] Implement order modification
  - [ ] Implement order cancellation
  - [ ] Design order management ID schema supporting both IBKR permId and other broker IDs

- [ ] Verify order execution API
  - [ ] Implement order status checking
  - [ ] Implement execution reporting

- [ ] Modify order execution API
  - [ ] Implement stop loss modification
  - [ ] Implement target modification
  - [ ] Implement quantity modification

## 10. User Interface

- [ ] Implement web-based dashboard
  - [ ] Strategy configuration
  - [ ] Trade monitoring
  - [ ] P&L reporting
  - [ ] Risk management settings
  - [ ] Time-based trade closure settings
  - [ ] Dark mode defaults for traders in low-light environments
  - [ ] Correlation coefficient heatmap for strategy tuning

## 11. Correlation Strategy Implementation Plan

1. Data Collection and Processing
   - [x] Configure data collection for configurable set of symbols
   - [x] Ensure proper calculation of customizable timeframes
   - [x] Validate technical indicator calculations for symbols
   - [ ] Implement futures contract roll logic

2. Signal Generation
   - [ ] Implement configurable interval signal checking
   - [ ] Code the multi-symbol correlation logic
   - [ ] Test signal generation with historical data
   - [ ] Add settlement-price vs. last-trade sanity checks

3. Order Execution
   - [ ] Implement order placement for configured symbols
   - [ ] Configure stop-loss and profit target percentages
   - [ ] Setup 5-second monitoring loop
   - [ ] Add PDT rule compliance

4. Trade Management
   - [ ] Implement stop-loss and profit target monitoring
   - [ ] Develop time-based trade closure functionality
   - [ ] Create deals reporting for the strategy
   - [ ] Implement Reg-T margin compliance

## Next Steps

1. ✅ Implement the correlation strategy framework as a proof of concept
2. ✅ Complete Signal Scanning (SS) implementation
3. ✅ Develop Trade Management framework with 5-second monitoring
4. ✅ Integrate Order Execution APIs
5. ✅ Build user interface for monitoring and configuration
6. ✅ Implement U.S. market regulatory compliance (PDT, Reg-T, SEC 17a-4)

## Recent Updates

1. Added Polygon.io fail-over feed implementation
2. Implemented comprehensive system monitoring
3. Added latency tracking and analysis
4. Enhanced error handling and reconnection logic
5. Added data validation and sanitization
6. Added timezone handling for market data
7. Implemented data gap detection
8. Added outlier detection using z-scores
9. Added pre/post market hours validation
10. Implemented retry mechanism for database operations
11. Added connection pooling for better performance
12. Added duplicate signal detection
13. Implemented cleanup of old signals
14. Added multiple correlation methods support
15. Enhanced market hours validation

## Next Implementation Tasks

1. Implement data archiving for SEC 17a-4 compliance
2. Add 30-minute timeframe data aggregation
3. Implement futures contract roll logic
4. Develop signal scanning framework
5. Create trade management system
6. Add performance monitoring and metrics collection
7. Implement automated testing suite
8. Add API documentation
9. Set up monitoring and alerting system
10. Implement user interface for configuration and monitoring
