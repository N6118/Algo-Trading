# Algo-Trading Platform Backend Agent Documentation

## 🚨 CRITICAL DEVELOPMENT MODEL WARNING

**⚠️ ATTENTION: This platform operates on a SERVER-BASED DEVELOPMENT MODEL**

- **ALL services run on the remote server** (100.121.186.86)
- **ALL databases are on the server** (PostgreSQL 17)
- **Local development is for CODE EDITING ONLY**
- **EVERY code change requires: PUSH → PULL → RESTART**
- **NEVER run services locally** - they won't connect to server databases

### Required Workflow for ANY Changes:
1. Edit code locally
2. `git add . && git commit -m "message" && git push origin main`
3. SSH to server: `ssh anurag@100.121.186.86`
4. Pull changes: `git pull origin main`
5. Restart services: `sudo systemctl restart algo-trading-*`

---

## Overview
This document provides comprehensive information about the backend architecture, services, and components of the algorithmic trading platform. It serves as a guide for AI agents, developers, and system administrators working with the platform.

## Architecture Overview

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   IBKR/TWS      │    │   PostgreSQL    │    │   FastAPI       │
│   Gateway       │◄──►│   + TimescaleDB │◄──►│   Backend       │
│   (Port 7496)   │    │   (Port 5432)   │    │   (Port 8000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data          │    │   Signal        │    │   Strategy      │
│   Collection    │    │   Scanner       │    │   Engine        │
│   Service       │    │   Service       │    │   (attempt.py)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components
1. **Data Collection**: Real-time market data from IBKR
2. **Database**: PostgreSQL 17 with TimescaleDB extension
3. **Signal Generation**: Correlation-based signal scanner
4. **Strategy Execution**: SH/SL calculation and trade management
5. **API Layer**: FastAPI backend for frontend integration

## Database Schema

### Core Tables

#### Market Data Tables
```sql
-- Raw tick data from IBKR
stock_ticks (
    token INT NOT NULL,           -- IBKR conId
    symbol TEXT NOT NULL,         -- Symbol (MES, VIX, etc.)
    timestamp TIMESTAMPTZ NOT NULL,
    price DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    PRIMARY KEY (token, timestamp)
);

-- 15-minute OHLC aggregates (TimescaleDB continuous aggregate)
stock_ohlc_15min (
    created TIMESTAMPTZ,
    token INT,
    symbol TEXT,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION
);

-- Processed data with SH/SL calculations
tbl_ohlc_fifteen_output (
    id SERIAL,
    token INT NOT NULL,
    symbol TEXT,
    created TIMESTAMPTZ NOT NULL,
    close DOUBLE PRECISION,
    sh_price DOUBLE PRECISION,    -- Swing High
    sl_price DOUBLE PRECISION,    -- Swing Low
    sh_status BOOLEAN,
    sl_status BOOLEAN,
    -- Additional technical indicators...
);
```

#### Signal Management Tables
```sql
-- Signal configurations
signal_configs (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    signal_type ENUM('Intraday', 'Positional'),
    is_active BOOLEAN DEFAULT true,
    scan_interval_minutes INTEGER DEFAULT 15
);

-- Symbols for each configuration
signal_symbols (
    id SERIAL PRIMARY KEY,
    config_id INTEGER REFERENCES signal_configs(id),
    symbol TEXT NOT NULL,
    token INTEGER,
    is_primary BOOLEAN DEFAULT false,
    timeframe TEXT DEFAULT '15min'
);

-- Entry rules for signal generation
signal_entry_rules (
    id SERIAL PRIMARY KEY,
    config_id INTEGER REFERENCES signal_configs(id),
    rule_type TEXT,               -- 'PriceAbove', 'PriceBelow', 'Correlation'
    symbol TEXT,
    parameter TEXT,               -- 'SH', 'SL'
    correlation_threshold FLOAT DEFAULT 0.7
);

-- Generated signals
generated_signals (
    id SERIAL PRIMARY KEY,
    config_id INTEGER REFERENCES signal_configs(id),
    symbol TEXT NOT NULL,
    token INTEGER,
    signal_time TIMESTAMP,
    direction ENUM('Long', 'Short'),
    price DOUBLE PRECISION,
    timeframe TEXT,
    status ENUM('New', 'Executed', 'Rejected') DEFAULT 'New'
);
```

## Services and Processes

### 1. Data Collection Service (`streamdata.py`)
**Purpose**: Collects real-time market data from IBKR
**Location**: `backend/app/data/streamdata.py`
**Status**: ✅ Running (PID: 3040288)

**Key Features**:
- Connects to IBKR TWS/Gateway on port 7496
- Collects tick data for configured symbols
- Stores data in `stock_ticks` table
- Sends Telegram notifications for connection status

**Configuration**:
```python
TWS_HOST = '127.0.0.1'
TWS_PORT = 7496
TWS_CLIENT_ID = 456
DB_URI = "postgresql://postgres:password@localhost:5432/theodb"
```

### 2. SH/SL Calculator Service (`sl_tp_calculator.py`)
**Purpose**: Calculates Swing High/Swing Low values
**Location**: `backend/app/services/sl_tp_calculator.py`
**Status**: ✅ Running (PID: 3649354)

**Key Features**:
- Processes 15-minute OHLC data
- Calculates ATR, Donchian Channels, Swing High/Low
- Updates `tbl_ohlc_fifteen_output` table
- Sends Telegram notifications for new values

**Calculation Logic**:
- ATR-based trailing stop loss
- Donchian Channel support/resistance levels
- Fractal-based swing high/low detection

### 3. Signal Scanner Service (`scanner.py`)
**Purpose**: Generates trading signals based on correlation strategy
**Location**: `backend/app/signal_scanner/scanner.py`
**Status**: ✅ Running (PID: 3040973)

**Key Features**:
- Monitors MES (primary) and VIX (correlated) symbols
- Uses correlation-based strategy
- Generates buy/sell signals based on SH/SL conditions
- Stores signals in `generated_signals` table

**Signal Conditions**:
```python
# Buy Signal
if (MES_close > MES_SH) and (VIX_close < VIX_SL) and (correlation > 0.7):
    generate_buy_signal()

# Sell Signal  
if (MES_close < MES_SL) and (VIX_close > VIX_SH) and (correlation > 0.7):
    generate_sell_signal()
```

### 4. Strategy Engine (`attempt.py`)
**Purpose**: Main strategy execution and trade management
**Location**: `backend/app/strategies/Stocks/attempt.py`
**Status**: 🔄 Available for execution

**Key Features**:
- Advanced technical analysis
- Risk management
- Position sizing
- Trade execution logic

## Configuration Files

### Database Configuration
```json
// scanner_config.json
{
    "database": {
        "host": "100.121.186.86",
        "port": 5432,
        "user": "postgres",
        "password": "password",
        "database": "theodb"
    },
    "scanning": {
        "interval_minutes": 1,
        "max_signals_per_day": 10
    }
}
```

### Telegram Configuration
```json
// telegram_config.json
{
    "bot_token": "8468875074:AAEeCH6H5NfNzHFobMAaw4epxa2v8nZvw_8",
    "chat_id": "2074764227",
    "notifications": {
        "server_start": true,
        "server_stop": true,
        "first_entry": true,
        "last_entry": true,
        "connection_status": true
    }
}
```

## API Endpoints

### FastAPI Backend (`main.py`)
**Location**: `backend/app/main.py`
**Port**: 8000

**Key Endpoints**:
```python
GET /                    # Health check
GET /health             # Service status
GET /api/market-data/*  # Market data endpoints
GET /api/strategies/*   # Strategy management
GET /api/trades/*       # Trade management
GET /api/settings/*     # System settings
```

## Service Management

### Systemd Services
All services are managed via systemd on the remote server:

```bash
# Check service status
sudo systemctl status algo-trading-streamdata.service
sudo systemctl status algo-trading-signal-scanner.service
sudo systemctl status algo-trading-sl-tp-calculator.service

# Restart services
sudo systemctl restart algo-trading-streamdata.service
sudo systemctl restart algo-trading-signal-scanner.service

# View logs
sudo journalctl -u algo-trading-streamdata.service -f
sudo journalctl -u algo-trading-signal-scanner.service -f
```

### Manual Service Control
```bash
# Start data collection
cd /home/anurag/Desktop/Algo-Trading/algo-trade-platform
source backend/app/data/venv/bin/activate
python backend/app/data/streamdata.py

# Start signal scanner
python backend/app/signal_scanner/scanner.py

# Start SH/SL calculator
python backend/app/services/sl_tp_calculator.py
```

## Database Operations

### Common Queries

**Check Latest Data**:
```sql
-- Latest tick data
SELECT symbol, timestamp, price, volume 
FROM stock_ticks 
ORDER BY timestamp DESC LIMIT 10;

-- Latest 15-minute aggregates
SELECT symbol, created, open, high, low, close 
FROM stock_ohlc_15min 
ORDER BY created DESC LIMIT 10;

-- Latest SH/SL values
SELECT symbol, created, close, sh_price, sl_price, sh_status, sl_status 
FROM tbl_ohlc_fifteen_output 
WHERE symbol IN ('MES', 'VIX') 
ORDER BY created DESC LIMIT 5;
```

**Check Generated Signals**:
```sql
-- Recent signals
SELECT id, symbol, signal_time, direction, price, status 
FROM generated_signals 
ORDER BY signal_time DESC LIMIT 10;

-- Active signals
SELECT * FROM generated_signals 
WHERE status = 'New' 
ORDER BY signal_time DESC;
```

**Refresh TimescaleDB Aggregates**:
```sql
-- Refresh 15-minute aggregates
CALL refresh_continuous_aggregate('stock_ohlc_15min', NOW() - INTERVAL '24 hours', NOW());
```

## Troubleshooting

### Common Issues

1. **No Data Collection**
   - Check IBKR TWS/Gateway is running on port 7496
   - Verify streamdata service is running
   - Check database connection

2. **No SH/SL Calculations**
   - Ensure 15-minute aggregates are being refreshed
   - Check SH/SL calculator service is running
   - Verify sufficient historical data exists

3. **No Signal Generation**
   - Check correlation threshold (default 0.7)
   - Verify entry rules are configured correctly
   - Ensure signal scanner service is running

### Debug Commands
```bash
# Check if TWS is listening
netstat -tlnp | grep 7496

# Check Python processes
ps aux | grep python | grep -v grep

# Check database size
SELECT pg_size_pretty(pg_database_size('theodb'));

# Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Development Workflow

### ⚠️ CRITICAL: Server-Based Development Model

**IMPORTANT**: This platform uses a **server-based development model**. All services, databases, and execution happen on the remote server. Local development is for code editing only.

### Development Process

#### 1. Local Development (Code Editing Only)
```bash
# Clone repository locally for code editing
git clone <repository-url>
cd algo-trade-platform

# Install dependencies locally (for development tools only)
pip install -r backend/requirements.txt

# Edit code locally
# Make changes to Python files, configurations, etc.
```

#### 2. Push Changes to Server
```bash
# Commit your changes
git add .
git commit -m "Description of changes"

# Push to remote repository
git push origin main

# SSH to server and pull changes
ssh anurag@100.121.186.86
cd /home/anurag/Desktop/Algo-Trading/algo-trade-platform
git pull origin main
```

#### 3. Restart Services on Server
```bash
# After pulling changes, restart affected services
sudo systemctl restart algo-trading-streamdata.service
sudo systemctl restart algo-trading-signal-scanner.service
sudo systemctl restart algo-trading-sl-tp-calculator.service

# Or restart all services
sudo systemctl restart algo-trading-*
```

### Development Rules

1. **NEVER run services locally** - They won't connect to the server database
2. **ALWAYS push changes** before testing - Server has the latest code
3. **ALWAYS pull on server** after pushing - Ensure server has latest changes
4. **ALWAYS restart services** after code changes - Services need to reload new code
5. **Test on server only** - Local testing won't reflect server environment

### Quick Development Cycle
```bash
# 1. Edit code locally
vim backend/app/signal_scanner/scanner.py

# 2. Push to server
git add .
git commit -m "Updated signal scanner logic"
git push origin main

# 3. Pull on server
ssh anurag@100.121.186.86
cd /home/anurag/Desktop/Algo-Trading/algo-trade-platform
git pull origin main

# 4. Restart service
sudo systemctl restart algo-trading-signal-scanner.service

# 5. Check logs
sudo journalctl -u algo-trading-signal-scanner.service -f
```

### Testing (Server-Based Only)
```bash
# ⚠️ ALL testing must be done on the server

# Test signal scanner manually (on server)
ssh anurag@100.121.186.86
cd /home/anurag/Desktop/Algo-Trading/algo-trade-platform
python test_signal_scanner.py

# Test database connection (on server)
PGPASSWORD=password psql -h localhost -U postgres -d theodb -c "SELECT 1;"

# Test SH/SL calculation (on server)
python -c "from backend.app.services.sl_tp_calculator import SLTPCalculator; calc = SLTPCalculator(); calc.connect_db(); calc.process_symbol('MES');"

# Check service logs (on server)
sudo journalctl -u algo-trading-signal-scanner.service -f
sudo journalctl -u algo-trading-streamdata.service -f
```

## Security Considerations

1. **Database Access**: Use strong passwords and limit access
2. **API Security**: Implement authentication for FastAPI endpoints
3. **Telegram Bot**: Keep bot token secure
4. **IBKR Connection**: Ensure TWS is properly configured for API access

## Performance Monitoring

### Key Metrics
- Data collection latency
- Signal generation frequency
- Database query performance
- Service uptime and reliability

### Monitoring Commands
```bash
# Check service uptime
systemctl status algo-trading-*

# Monitor database performance
SELECT * FROM pg_stat_activity WHERE state = 'active';

# Check TimescaleDB performance
SELECT * FROM timescaledb_information.hypertables;
SELECT * FROM timescaledb_information.continuous_aggregates;
```

## Future Enhancements

1. **Additional Strategies**: Implement more correlation strategies
2. **Risk Management**: Add position sizing and risk controls
3. **Backtesting**: Implement historical strategy testing
4. **Machine Learning**: Add ML-based signal generation
5. **Real-time Alerts**: Enhanced notification system
6. **Web Interface**: Full web-based management interface

---

**Last Updated**: August 28, 2025
**Version**: 1.0.0
**Maintainer**: System Administrator
