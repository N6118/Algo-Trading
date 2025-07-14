# Algorithmic Trading Platform Documentation

## Overview
This documentation provides a detailed overview of the implemented components of the algorithmic trading platform. The platform is built with a focus on U.S. markets and includes data collection, processing, signal generation, and trade management capabilities.

## 1. Data Collection Layer

### 1.1 Tick Data Collection (`streamdata.py`)
- **Implementation**: Uses IBKR API for real-time data collection
- **Features**:
  - WebSocket-based tick data streaming
  - TimescaleDB integration for data storage
  - Automatic reconnection handling
  - Error scenario management
  - Polygon.io fail-over feed for redundancy
  - Latency monitoring (exchange vs. arrival timestamps)

### 1.2 Timeframe Data Conversion
- **Implementation**: Continuous aggregates in TimescaleDB
- **Supported Timeframes**:
  - 5-minute (implemented)
  - 15-minute (implemented)
  - 60-minute (implemented)
  - 30-minute (pending)
- **Storage**: TimescaleDB hypertables with compression

## 2. Data Consolidation Layer

### 2.1 Database Setup (`dbsetup.py`)
- **Implementation**: TimescaleDB configuration
- **Features**:
  - Hypertable creation
  - Continuous aggregates setup
  - Compression policies
  - Retention policies

### 2.2 Technical Indicators (`Stocks/attempt.py`)
- **Implemented Indicators**:
  - Fractal Highs/Lows (FH/FL)
  - Swing Highs/Lows (SH/SL)
  - Average True Range (ATR)
  - Pivot Points
  - Donchian Channels (DC)
- **Pending**: Futures contract roll logic

## 3. Signal Scanning (SS)

### 3.1 Framework Implementation
- **Database Structure**:
  - Signal scanning tables
  - Connection pooling
  - Retry mechanism
  - Signal cleanup system
  - Duplicate detection

### 3.2 Signal Parameters
- **Configuration Options**:
  - Name and expiry (Weekly/Monthly)
  - SS-Type (Intraday/Positional)
  - Trading days selection
  - Scheduler configuration
  - Market hours (with defaults)
  - Signal quantity limits
  - Signal types (Long/Short)
  - Product types (FUT/OPTION/ETF/Cash Equity)
  - Option configurations
  - Market session validation
  - Holiday calendar integration

### 3.3 Multi-Symbol Correlation Strategy
- **Features**:
  - Flexible symbol configuration
  - Technical indicator calculation
  - Configurable timeframes
  - Signal generation intervals
  - Price validation
  - Timezone handling
  - Data gap detection
  - Outlier detection (z-scores)
  - Market hours validation
  - Multiple correlation methods:
    - Pearson
    - Spearman
    - Kendall
  - Rolling correlation support
  - Correlation threshold validation

## 4. Signal Generation (SG)

### 4.1 Database Model (`signal_generation.py`)
- **Core Fields**:
  ```python
  - user_id (FK to User)
  - strategy_id (FK to Strategy)
  - symbol (String)
  - exchange (Enum)
  - order_type (Enum)
  - product_type (Enum)
  - side (Enum)
  - contract_size (Integer)
  - quantity (Integer)
  - entry_price (Float)
  - stop_loss (Float)
  - take_profit (Float)
  - status (Enum)
  - market_session (Enum)
  - timestamps
  - is_active (Boolean)
  ```

- **Constraints**:
  - Positive value validation
  - Contract size multiple validation
  - Price relationship validation
  - Market session validation
  - Unique signal constraints

### 4.2 Market Data Service (`market_data_service.py`)
- **IBKR Integration**:
  - Connection management
  - Error handling
  - Connection pooling
  - Subscription management

- **Core Methods**:
  ```python
  - validate_symbol()
  - get_current_price()
  - get_market_status()
  - get_historical_data()
  - get_option_chain()
  - get_market_data()
  - get_market_depth()
  - get_fundamental_data()
  - get_corporate_actions()
  ```

### 4.3 Order Service (`order_service.py`)
- **IBKR Integration**:
  - Connection management
  - Error handling
  - Order subscription management

- **Regulatory Compliance**:
  - PDT rule validation
  - Reg-T margin validation
  - Order rejection handling

- **Order Types**:
  ```python
  - Market orders
  - Limit orders
  - Stop orders
  - Stop-limit orders
  - Trailing stop orders
  - Bracket orders
  - OCO orders
  ```

- **Order Features**:
  ```python
  - Time-in-force options (DAY, GTC, IOC, FOK)
  - Order routing preferences
  - Order allocation methods
  ```

- **Core Methods**:
  ```python
  - create_order()
  - modify_order()
  - cancel_order()
  - get_order_status()
  - create_bracket_order()
  - create_oco_order()
  ```

## 5. Configuration Parameters

### 5.1 Exchange Types
- NYSE
- NASDAQ
- CBOE
- SMART

### 5.2 Order Types
- STOP
- STOP_LIMIT
- MARKET
- LIMIT
- TRAILING_STOP

### 5.3 Product Types
- MARGIN
- CASH

### 5.4 Contract Sizes
- Stocks: 1 share
- Options: 100 shares per contract
- Futures: Variable by contract

### 5.5 Time-in-Force Options
- DAY
- GTC (Good Till Cancelled)
- IOC (Immediate or Cancel)
- FOK (Fill or Kill)

### 5.6 Order Routing
- SMART
- DIRECT
- ARCA
- NYSE
- NASDAQ
- CBOE

### 5.7 Order Allocation
- FIFO (First In, First Out)
- LIFO (Last In, First Out)
- PRO_RATA (Proportional allocation)

## 6. Error Handling

### 6.1 Market Data Errors
- Connection lost (502, 504)
- No security definition (200)
- Subscription limits (10182)
- Subscription delays (10183)
- Subscription frozen (10184)

### 6.2 Order Errors
- Order rejection (10182)
- PDT rule violation (10183)
- Reg-T margin violation (10184)
- Order size limit (10185)
- Order price limit (10186)
- Order frequency limit (10187)

## 7. Next Steps

### 7.1 Pending Implementations
1. 30-minute timeframe data aggregation
2. Data archiving for SEC 17a-4 compliance
3. Futures contract roll logic
4. Trade management system
5. Performance monitoring
6. Automated testing suite
7. API documentation
8. Monitoring and alerting system
9. User interface implementation

### 7.2 Priority Tasks
1. Complete trade management framework
2. Implement risk management system
3. Add position tracking
4. Develop deals reporting system
5. Create universal settings management
6. Build order execution API
7. Implement web-based dashboard

## 8. Best Practices

### 8.1 Code Organization
- Services are implemented as singletons
- Connection pooling for database operations
- Retry mechanisms for transient failures
- Comprehensive error handling
- Thread-safe operations using locks

### 8.2 Data Management
- TimescaleDB for time-series data
- Continuous aggregates for timeframe data
- Compression and retention policies
- Data validation and sanitization

### 8.3 Trading Compliance
- PDT rule enforcement
- Reg-T margin requirements
- Market hours validation
- Holiday calendar integration
- Pre/post market handling

## 9. Dependencies

### 9.1 External Services
- IBKR API
- Polygon.io (fail-over)
- TimescaleDB

### 9.2 Python Packages
- ib_insync
- sqlalchemy
- fastapi
- pytz
- datetime
- threading
- collections
- enum 