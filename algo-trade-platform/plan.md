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

- [ ] Implement signal scanning framework
  - [ ] Create signal scanning database tables
  - [ ] Implement signal scanning service
  - [ ] Setup configurable interval scanning for correlation strategies

- [ ] Signal scanning parameters
  - [ ] Name
  - [ ] Expiry (Weekly, Monthly)
  - [ ] SS-Type (Intraday, Positional)
  - [ ] SS-Days (Mon, Tue, Wed, Thu, Fri, All)
  - [ ] Scheduler
  - [ ] Start Time, End Time (with U.S. market hours defaults)
  - [ ] Number of Signals
  - [ ] SS-signal-Type (Long, Short)
  - [ ] SS-placeholder (FUT, OPTION, ETF, Cash Equity)
  - [ ] SS-Option Type (CALL, PUT)
  - [ ] SS-Option Category (ITM, OTM, FUT, DOTM, DITM with U.S. tick structure)
  - [ ] SS-Mode (Live, Virtual)
  - [ ] SS-Entry-Rules
  - [ ] SS-Exit-Rules

### 3.1 Multi-Symbol Correlation Strategy

- [ ] Implement correlation strategy framework
  - [ ] Support flexible symbol configuration
  - [ ] Calculate technical indicators for selected symbols
  - [ ] Configure timeframes for indicator calculations
  - [ ] Setup configurable signal generation intervals
  - [ ] Add settlement-price vs. last-trade sanity checks

- [ ] Buy Signal Conditions (configurable for any symbol):
  - [ ] Price of primary symbol > SH of primary symbol
  - [ ] Price of correlated symbol < SL of correlated symbol
  - [ ] Other custom conditions

- [ ] Sell Signal Conditions (configurable for any symbol):
  - [ ] Price of primary symbol < SL of primary symbol
  - [ ] Price of correlated symbol > SH of correlated symbol
  - [ ] Other custom conditions

## 4. Signal Generation (SG)

- [ ] Implement signal generation per strategy for each user
  - [ ] Create signal generation database tables
  - [ ] Implement signal generation service

- [ ] Signal generation parameters
  - [ ] SG-exchange (NYSE, NASDAQ, CBOE, SMART routing)
  - [ ] SG-order-type (Stop, Stop Limit, Market, Limit)
  - [ ] SG-PRODUCT (Margin, Cash)
  - [ ] SG-Base (contract size/lot size)

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

## Next Implementation Tasks

1. Implement data archiving for SEC 17a-4 compliance
2. Add 30-minute timeframe data aggregation
3. Implement futures contract roll logic
4. Develop signal scanning framework
5. Create trade management system
