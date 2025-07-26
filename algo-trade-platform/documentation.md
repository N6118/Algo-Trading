# Backend File Documentation

## 1. Application Entry Point

### `main.py`
- **Description:** Main FastAPI application entry point. Sets up the API, CORS, logging, and background services (market data collection, signal scanning, trade monitoring). Registers all routers and exposes root and health check endpoints.

---

## 2. Data Collection & Processing (`data/`)

- **`streamdata.py`**: Collects real-time tick data from IBKR and Polygon.io, handles reconnections, and stores data in TimescaleDB.
- **`polygon_feed.py`**: Manages data feed integration with Polygon.io for redundancy and failover.
- **`monitoring.py`**: Monitors data feed health, latency, and system status.
- **`futures_roll.py`**: Handles futures contract roll logic for continuous contract data.
- **`optimizations.py`**: Contains data processing and optimization routines.
- **`db_maintenance.py`**: Scripts for database maintenance and cleanup.
- **`maintenance_cron.sh`**: Shell script for scheduled maintenance tasks.

---

## 3. Signal Scanning (`signal_scanner/`)

- **`api.py`**: Main API for the signal scanner, orchestrates scanning logic and exposes scanner-related functions for use by other services or scripts.
- **`scanner.py`**: Core scanning logic for signals, including scheduling, execution, and management of scanning jobs.
- **`correlation_strategy.py`**: Implements multi-symbol correlation-based signal strategies, including calculation of correlation coefficients and signal conditions.
- **`db_schema.py`**: Defines the database schema for signal scanning, including table definitions and relationships.
- **`init_db.py`**: Initializes the signal scanner database, creating necessary tables and seeding initial data if required.
- **`test_correlation.py`**: Unit tests for correlation strategy logic, ensuring correctness of correlation calculations and signal generation.

---

## 4. Signal Generation (`services/`, `models/`, `schemas/`)

### Services
- **`signal_generation_service.py`**: Contains business logic for creating, updating, retrieving, and processing trading signals. Handles validation, status updates, and interaction with the database for signal lifecycle management.

### Models
- **`signal_generation.py`**: SQLAlchemy model defining the structure of signal generation entries in the database, including fields for user, strategy, symbol, order details, and status.

### Schemas
- **`signal_generation.py`**: Pydantic schemas for request and response validation in the signal generation API, ensuring data integrity and type safety for all signal-related endpoints.

---

## 5. Trade Management (`services/`, `models/`)

### Services
- **`trade_service.py`**: Handles trade creation, modification, and status tracking. Implements business logic for trade lifecycle, including validation, compliance checks, and database operations.
- **`trade_management_service.py`**: Monitors active trades, enforces stop-loss and profit target rules, manages trade closure, and oversees the entire trade lifecycle in real time.
- **`order_service.py`**: Integrates with IBKR for order placement, modification, and cancellation. Manages order types, routing, and compliance with trading regulations.
- **`signal_promotion_service.py`**: Promotes eligible signals to trades based on strategy logic and risk management rules.

### Models
- **`trade.py`**: SQLAlchemy model defining the structure of trade records in the database, including fields for user, strategy, signal, order details, status, and timestamps.

---

## 6. Market Data (`services/`)

- **`market_data_service.py`**: Fetches and validates market data, manages real-time and historical data subscriptions, provides price, volume, option chain, and order book data. Handles integration with IBKR and Polygon.io, including error handling and connection pooling.

---

## 7. Risk Management (`models/`)

- **`risk_settings.py`**: SQLAlchemy model for user, strategy, and account risk settings. Defines configurable risk parameters such as max trades, max risk percentage, and other compliance-related settings.

---

## 8. Database Setup (`models/`)

- **`dbsetup.py`**: Sets up TimescaleDB tables, hypertables, and continuous aggregates for all time-series and trading data. Manages database schema migrations, compression, and retention policies.

---

## 9. Pipeline Management (`pipeline/`)

- **`pipeline_manager.py`**: Orchestrates data and signal processing pipelines, managing the flow of data from collection through processing to signal generation and trade execution.

---

## 10. Strategies (`strategies/Stocks/`)

- **`attempt.py`**: Main implementation of stock trading strategies, including technical indicators, signal logic, and backtesting routines.
- **`original.py`**: Original or baseline version of stock trading strategies for comparison and validation.
- **`config/config.json`**: Configuration file for strategy parameters, such as symbols, thresholds, and timeframes.
- **`logs/`**: Log files for strategy runs, useful for debugging and performance analysis.
- **`requirements.txt`**: Python dependencies required for running strategy code.

---

## 11. API Layer (`api/`)

- **`endpoints/signal_generation.py`**: FastAPI endpoints for signal generation CRUD operations and processing, exposing the signal generation service to the API layer.
- **`endpoints/trade.py`**: FastAPI endpoints for trade creation and management, exposing the trade service to the API layer.
- **`api.py`**: Registers API routers for the application, connecting endpoint modules to the FastAPI app.

---

## 12. Schemas (`schemas/`)

- **`signal_generation.py`**: Pydantic models for signal generation API requests and responses, ensuring type safety and validation for all signal-related endpoints.

---

## 13. Utilities (`utils/`)

- *(No files listed, but typically contains helper functions and shared utilities used across the backend.)*

---
