# Algorithmic Trading Platform Plan

This document outlines the comprehensive plan for building an algorithmic trading platform with data collection, processing, signal generation, and trade management capabilities. The platform will include a correlation-based strategy as an initial implementation, optimized for U.S. markets.

## 🏗️ System Architecture & Deployment Model

### Development Environment
- **Local Development**: macOS development machine with local code editing
- **Remote Deployment**: All services run on a remote Linux server
- **Database**: PostgreSQL 17 + TimescaleDB extension on remote server
- **Deployment Method**: Git push/pull workflow (local → remote server)
- **Services**: Managed via systemd on remote server

### Key Infrastructure Components
- **Database**: `theodb` (PostgreSQL 17 + TimescaleDB)
- **Data Source**: IBKR TWS/Gateway (port 7496)
- **Backend**: FastAPI (Python)
- **Frontend**: React + TypeScript + Vite
- **Notifications**: Telegram Bot API
- **Monitoring**: Custom logging + Telegram notifications

### Critical Services (systemd)
- `algo-trading-streamdata.service` - Data collection from IBKR
- `algo-trading-signal-scanner.service` - Signal generation
- `algo-trading-attempt.service` - Strategy execution
- `algo-trading-attempt-aggregator.service` - Data aggregation
- `postgres-monitor.service` - Database monitoring

## 📊 Current System Status

### ✅ Fully Operational Components
- **Data Streaming**: IBKR tick data collection via `streamdata.py`
- **Data Aggregation**: TimescaleDB continuous aggregates (5min, 15min, 60min)
- **SH/SL Calculator**: Swing High/Low calculations with Telegram notifications
- **Signal Scanner**: Correlation-based signal generation
- **Telegram Notifications**: Real-time alerts for system events
- **Database**: PostgreSQL 17 + TimescaleDB with proper hypertables

### 🔧 Recently Fixed Issues
- **TimescaleDB Auto-refresh**: Enabled continuous aggregate refresh policies
- **Duplicate Notifications**: Implemented timestamp tracking in SH/SL calculator
- **Signal Scanner**: Fixed duplicate signal detection and cleanup
- **Database Schema**: Corrected enum constraints and table structures

### 📁 Critical Files & Their Purposes
- `backend/app/data/streamdata.py` - Core data collection from IBKR
- `backend/app/services/sl_tp_calculator.py` - SH/SL calculations & notifications
- `backend/app/signal_scanner/scanner.py` - Main signal scanning logic
- `backend/app/signal_scanner/correlation_strategy.py` - Correlation strategy implementation
- `backend/app/services/telegram_notifier.py` - Telegram notification service
- `backend/app/models/dbsetup.py` - Database schema and TimescaleDB setup
- `config/telegram_config.json` - Telegram bot configuration
- `config/scanner_config.json` - Signal scanner settings
- `server/*.service` - systemd service definitions

## 🚨 Troubleshooting Guide

### Common Issues & Solutions
1. **"relation does not exist" errors**: Check if PostgreSQL 17 is running and TimescaleDB is enabled
2. **Duplicate Telegram messages**: Check `last_processed_timestamps` in SH/SL calculator
3. **Stale data in SH/SL**: Verify TimescaleDB continuous aggregate refresh policies are enabled
4. **Signal scanner errors**: Check enum constraints in database schema
5. **Connection issues**: Verify IBKR TWS/Gateway is running on port 7496

### Database Verification Commands
```sql
-- Check TimescaleDB extension
SELECT * FROM pg_extension WHERE extname = 'timescaledb';

-- Check continuous aggregates
SELECT * FROM timescaledb_information.jobs WHERE proc_name = 'policy_refresh_continuous_aggregate';

-- Check hypertables
SELECT * FROM timescaledb_information.hypertables;

-- Check recent data
SELECT COUNT(*) FROM stock_ticks WHERE created > NOW() - INTERVAL '1 hour';
```

### Service Management Commands
```bash
# Check service status
sudo systemctl status algo-trading-*

# Restart services
sudo systemctl restart algo-trading-streamdata.service
sudo systemctl restart algo-trading-signal-scanner.service

# View logs
sudo journalctl -u algo-trading-streamdata.service -f
sudo journalctl -u algo-trading-signal-scanner.service -f
```

## 🔐 Configuration & Credentials

### Database Configuration
- **Host**: localhost (on remote server)
- **Port**: 5432
- **Database**: theodb
- **User**: postgres
- **Password**: password (stored in systemd service files)

### Telegram Configuration
- **Bot Token**: 8468875074:AAEeCH6H5NfNzHFobMAaw4epxa2v8nZvw_8
- **Bot Username**: @algo_trading_notifications_bot
- **Current Chat ID**: Configured in `config/telegram_config.json`
- **Multi-user Support**: Ready for boss's user ID addition

### IBKR Configuration
- **TWS/Gateway Port**: 7496
- **Connection Type**: WebSocket
- **Symbols**: MES, VIX (configurable)
- **Market Hours**: 09:30-16:00 ET (configurable)

## 📈 Data Flow Architecture

```
IBKR TWS/Gateway → streamdata.py → stock_ticks (TimescaleDB)
                                      ↓
                              Continuous Aggregates
                              (5min, 15min, 60min)
                                      ↓
                              sl_tp_calculator.py
                              (SH/SL calculations)
                                      ↓
                              scanner.py + correlation_strategy.py
                              (Signal generation)
                                      ↓
                              Telegram notifications
                              (Real-time alerts)
```

## 🔄 Development Workflow

### Code Changes
1. **Local Development**: Edit code on macOS machine
2. **Git Push**: `git add . && git commit -m "message" && git push`
3. **Remote Pull**: SSH to server and run `git pull`
4. **Service Restart**: Restart affected systemd services
5. **Verification**: Check logs and Telegram notifications

### Testing New Features
1. **Local Testing**: Use test scripts in project root
2. **Remote Testing**: SSH to server and run Python scripts directly
3. **Production Testing**: Monitor via Telegram notifications and logs
4. **Rollback**: Git revert if issues arise

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

- [x] Create trade management database tables
  - [x] Implement trade management service
  - [x] Setup 5-second monitoring interval for stop-loss and profit targets

### 5.1 Before Initiating Trade

- [x] Implement pre-trade checks and calculations for trade management: (1) Number of active trades, (2) Number of trades per day, (3) PDT rule check, (4) Initial profit target, (5) Initial stop-loss price, (6) Account risk percentage, (7) Calculate number of shares based on risk, (8) Calculate trade risk, (9) Calculate total risk percentage, (10) Adjust stop loss, (11) Calculate Reg-T margin and overnight buying power usage.
- [x] Implement logic to enforce pre-trade checks before any trade is placed, integrating with the order/trade creation flow.
- [x] Integrate order placement (via OrderService) into trade creation flow; only persist trade if order is successfully placed.
- [x] Use explicit DB transactions for trade creation and order placement to ensure atomicity.
- [x] Refactor error handling in TradeService to use custom exception classes for risk, compliance, and technical errors.
- [x] Enhance TradeManagementService monitoring: add time-based trade closure, exit rule monitoring, and dynamic stop-loss adjustment (trailing stops, risk reduction).

### 5.2 Risk Management

- [x] Make risk parameters (max trades, max risk %, etc.) configurable per user/account/strategy, not hardcoded.

### 5.3 Risk Reduction

- [x] Implement risk reduction for profitable trades
  - [x] Track Entry-Price
  - [x] Track Current-Price
  - [x] Track Current-Stop-Loss (current stop-loss price)
  - [x] Implement RR-Trigger mechanism
  - [x] Calculate and execute Qty-Sell for risk reduction

### 5.4 After Initiating Trade

- [x] Implement trade monitoring system
  - [x] Monitor stop loss conditions every 5 seconds
  - [x] Monitor profit target conditions every 5 seconds
  - [x] Monitor exit rule conditions
  - [x] Implement time-based trade closure (close all running trades at specified time)

### 5.5 Progressive P&L Tracking

- [x] Implement P&L tracking
  - [x] Calculate P&L for closed trades
  - [x] Update RM-Max-sp based on P&L
  - [x] Adjust stop loss based on risk reduction
  - [x] Adjust stop loss based on account risk percentage
  - [x] Ensure total P&L% is less than RM-Max-sp% (account drawdown limit)

## 6. Trade Status

- [x] Implement trade status tracking
  - [x] Last signal (Long/Short)
  - [x] Trade Status (Running/Closed/Waiting)
  - [x] Order status (Initiated/placed/pending/Success/Failed)

## 7. Deals Report

- [x] Implement deals reporting system
  - [x] Strategy Name
  - [x] SS-Type
  - [x] SS-signal-Type
  - [x] Symbol name
  - [x] Quantity (Entry Qty, Exit Qty)
  - [x] Price (Entry Price, Exit Price)
  - [x] P&L
  - [x] Charges
  - [x] Net P&L
  - [x] Net P&L%
  - [x] Date (Entry Date, Exit Date)
  - [x] Status (Running, Completed)
  - [x] Comments (How trade got closed, e.g., Stop-loss, Profit, Exit-rule)

## 8. Universal Settings

- [x] Implement universal settings management
  - [x] Capital
  - [x] Open-Time (default 09:30 ET, stored in UTC)
  - [x] Close-Time (default 16:00 ET, stored in UTC)
  - [x] Pre-Market (04:00-09:30 ET)
  - [x] Post-Market (16:00-20:00 ET)
  - [x] Holiday calendar lookup (NYSE schedule + half-days)
  - [x] SS-option category-Split (e.g., 200 to 100 - ITM for CALL/PUT)

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
   - [x] Implement configurable interval signal checking
   - [x] Code the multi-symbol correlation logic
   - [x] Test signal generation with historical data
   - [x] Add settlement-price vs. last-trade sanity checks

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

## 12. Monitoring & Alerting

### Telegram Notifications
- [x] **System Status**: Connection status, service health
- [x] **Data Collection**: First/last tick data entries
- [x] **SH/SL Calculations**: New Swing High/Low values
- [x] **Signal Generation**: New trading signals
- [x] **Error Alerts**: System failures and exceptions
- [x] **Multi-user Support**: Ready for boss notifications

### Logging Strategy
- [x] **Structured Logging**: JSON format for easy parsing
- [x] **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- [x] **Log Rotation**: Automatic log file management
- [x] **Remote Logging**: Centralized log collection
- [x] **Performance Metrics**: Latency, throughput tracking

### Health Checks
- [x] **Database Connectivity**: Connection pool monitoring
- [x] **IBKR Connection**: TWS/Gateway status
- [x] **Data Freshness**: Recent tick data validation
- [x] **Service Status**: systemd service health
- [x] **Memory Usage**: Process resource monitoring

## 9. Security & Compliance

### Data Security
- [x] **Encrypted Connections**: SSL/TLS for database and API
- [x] **Credential Management**: Environment variables for secrets
- [x] **Access Control**: Database user permissions
- [x] **Audit Logging**: Track all system access

### Regulatory Compliance
- [x] **SEC 17a-4**: Data retention requirements
- [x] **PDT Rules**: Pattern Day Trader compliance
- [x] **Reg-T Margin**: Margin requirement validation
- [x] **Order Management**: Proper order routing and execution

### Risk Management
- [x] **Position Limits**: Maximum position sizes
- [x] **Loss Limits**: Maximum daily loss thresholds
- [x] **Exposure Limits**: Maximum market exposure
- [x] **Circuit Breakers**: Automatic trading halts

## 14. Performance Optimization

### Database Optimization
- [x] **TimescaleDB Hypertables**: Time-series data optimization
- [x] **Continuous Aggregates**: Pre-computed OHLC data
- [x] **Compression Policies**: Automatic data compression
- [x] **Retention Policies**: Automatic data cleanup
- [x] **Index Optimization**: Proper indexing for queries

### Application Performance
- [x] **Connection Pooling**: Database connection management
- [x] **Async Processing**: Non-blocking operations
- [x] **Caching**: Redis for frequently accessed data
- [x] **Load Balancing**: Multiple service instances
- [x] **Resource Monitoring**: CPU, memory, disk usage

### Latency Optimization
- [x] **Co-location**: Services near exchange
- [x] **Network Optimization**: Low-latency connections
- [x] **Memory Management**: Efficient data structures
- [x] **Parallel Processing**: Multi-threaded operations

## 15. Disaster Recovery & Backup

### Backup Strategy
- [x] **Database Backups**: Daily automated backups
- [x] **Configuration Backups**: Service configuration files
- [x] **Code Backups**: Git repository with remote backup
- [x] **Log Backups**: Centralized log storage

### Recovery Procedures
- [x] **Service Recovery**: Automated service restart
- [x] **Database Recovery**: Point-in-time recovery
- [x] **Configuration Recovery**: Automated config restoration
- [x] **Data Validation**: Post-recovery data integrity checks

### High Availability
- [x] **Service Redundancy**: Multiple service instances
- [x] **Database Replication**: Read replicas for scaling
- [x] **Failover Procedures**: Automatic failover mechanisms
- [x] **Health Monitoring**: Continuous availability monitoring

## 🎯 Current Priorities & Next Steps

### Immediate Tasks (Next 1-2 Days)
1. **Multi-user Telegram Notifications**: Add boss's user ID to notification system
2. **Order Execution Integration**: Connect signal generation to actual order placement
3. **Trade Management**: Implement real-time trade monitoring and management
4. **Frontend Dashboard**: Complete React dashboard for monitoring and control

### Short-term Goals (Next 1-2 Weeks)
1. **Strategy Backtesting**: Implement historical data backtesting for correlation strategy
2. **Risk Management**: Add comprehensive risk controls and position sizing
3. **Performance Optimization**: Optimize database queries and service performance
4. **Documentation**: Complete API documentation and user guides

### Medium-term Goals (Next 1-2 Months)
1. **Additional Strategies**: Implement momentum, mean reversion, and other strategies
2. **Advanced Analytics**: Add machine learning models for signal improvement
3. **Multi-asset Support**: Extend to options, futures, and other instruments
4. **Enterprise Features**: Add multi-user support, role-based access, and audit trails

## 📋 Quick Start Guide for New Developers

### Prerequisites
- Python 3.11+, PostgreSQL 17, TimescaleDB extension
- IBKR TWS/Gateway running on port 7496
- Telegram bot token and chat ID
- SSH access to remote server

### First Steps
1. **Clone Repository**: `git clone <repo-url>`
2. **Install Dependencies**: `pip install -r backend/requirements.txt`
3. **Setup Database**: Run `backend/app/models/dbsetup.py`
4. **Configure Services**: Update config files with your credentials
5. **Deploy to Server**: Push code and restart services
6. **Verify Operation**: Check Telegram notifications and logs

### Common Commands
```bash
# Check system status
ssh server "sudo systemctl status algo-trading-*"

# View recent logs
ssh server "sudo journalctl -u algo-trading-streamdata.service -n 50"

# Restart services
ssh server "sudo systemctl restart algo-trading-streamdata.service"

# Check database
ssh server "psql -d theodb -c 'SELECT COUNT(*) FROM stock_ticks WHERE created > NOW() - INTERVAL \"1 hour\";'"
```

### Key Files to Understand
- `backend/app/data/streamdata.py` - Data collection logic
- `backend/app/services/sl_tp_calculator.py` - SH/SL calculations
- `backend/app/signal_scanner/scanner.py` - Signal generation
- `config/*.json` - Configuration files
- `server/*.service` - systemd service definitions

