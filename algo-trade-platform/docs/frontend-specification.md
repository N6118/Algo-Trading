# Frontend Specification Document

This document provides detailed specifications for each page and component in the algorithmic trading platform's frontend. It outlines the structure, functionality, data requirements, and API endpoints for each page based on the current implementation status.

## 1. Authentication Pages

### 1.1 Login Page
- **Implementation Status**: ✅ Complete
- **Functionality**:
  - User authentication with username/password ✅
  - "Remember me" option ✅
  - Password reset functionality ✅
  - Two-factor authentication support ✅
- **Components**:
  - Login form ✅
  - Error messaging ✅
  - Password reset link ✅
  - 2FA input field (when enabled) ✅
- **Data Requirements**:
  - User credentials ✅
  - Authentication tokens ✅
  - Session management ✅
- **API Endpoints**:
  - `POST /api/auth/login` - Authenticate user with username/password ✅
  - `POST /api/auth/login/2fa` - Verify 2FA code ✅
  - `POST /api/auth/refresh` - Refresh authentication token ✅
  - `POST /api/auth/password-reset/request` - Request password reset email ✅
  - `POST /api/auth/password-reset/verify` - Verify password reset token ✅
  - `POST /api/auth/password-reset/complete` - Complete password reset ✅

### 1.2 User Profile Page
- **Implementation Status**: ✅ Complete
- **Functionality**:
  - View and edit user information ✅
  - Change password ✅
  - Configure 2FA settings ✅
  - Manage API keys for exchanges ✅
  - Set notification preferences ✅
- **Components**:
  - Profile information form ✅
  - Password change form ✅
  - API key management section ✅
  - Notification settings panel ✅
- **Data Requirements**:
  - User profile data ✅
  - API key information ✅
  - Notification settings ✅
- **API Endpoints**:
  - `GET /api/users/profile` - Get user profile information ✅
  - `PUT /api/users/profile` - Update user profile information ✅
  - `PUT /api/users/password` - Change user password ✅
  - `GET /api/users/2fa/status` - Get 2FA status ✅
  - `POST /api/users/2fa/enable` - Enable 2FA ✅
  - `POST /api/users/2fa/disable` - Disable 2FA ✅
  - `GET /api/users/api-keys` - List user's exchange API keys ✅
  - `POST /api/users/api-keys` - Add new exchange API key ✅
  - `PUT /api/users/api-keys/{id}` - Update exchange API key ✅
  - `DELETE /api/users/api-keys/{id}` - Delete exchange API key ✅
  - `GET /api/users/notifications/settings` - Get notification settings ✅
  - `PUT /api/users/notifications/settings` - Update notification settings ✅

## 2. Dashboard Pages

### 2.1 Main Dashboard
- **Implementation Status**: ✅ Complete
- **Functionality**:
  - Overview of current trading status ✅
  - Quick access to active strategies ✅
  - Summary of P&L metrics ✅
  - System health indicators ✅
  - Recent trade history ✅
  - Real-time trade updates ✅
- **Components**:
  - Strategy status cards ✅
  - P&L summary charts ✅
  - Active trades table ✅
  - System status indicators ✅
  - Quick action buttons ✅
  - Real-time notification feed ✅
- **Data Requirements**:
  - Active strategy data ✅
  - Current P&L metrics ✅
  - Recent trade data ✅
  - System status information ✅
  - Real-time data subscriptions ✅
- **API Endpoints**:
  - `GET /api/dashboard/summary` - Get dashboard summary data ✅
  - `GET /api/strategies/active` - Get active strategies ✅
  - `GET /api/trades/active/summary` - Get active trades summary ✅
  - `GET /api/pnl/summary` - Get P&L summary metrics ✅
  - `GET /api/trades/recent` - Get recent trade history ✅
  - `GET /api/system/status` - Get system health status ✅
  - `POST /api/strategies/{id}/toggle` - Toggle strategy active status ✅
  - `GET /api/notifications/unread` - Get unread notifications ✅
  - `WS /api/ws/dashboard` - WebSocket for real-time dashboard updates ✅
  - `WS /api/ws/trades/active` - WebSocket for real-time active trade updates ✅
  - `WS /api/ws/pnl` - WebSocket for real-time P&L updates ✅
  - `WS /api/ws/notifications` - WebSocket for real-time notifications ✅

### 2.2 Strategy Dashboard
- **Implementation Status**: ✅ Complete
- **Functionality**:
  - Detailed view of a specific strategy's performance ✅
  - Real-time trade monitoring for the strategy ✅
  - Strategy-specific metrics and KPIs ✅
  - Strategy control panel (start/stop/modify) ✅
  - Live signal monitoring with correlation analysis ✅
  - Correlation visualization (Pearson, Spearman, Kendall) ✅
  - Minimum data points validation ✅
  - Correlation threshold monitoring ✅
  - Rolling window correlation analysis ✅
  - Statistical validation (P-values, confidence intervals) ✅
- **Components**:
  - Strategy performance charts ✅
  - Active trades for the strategy ✅
  - Parameter configuration panel ✅
  - Control buttons ✅
  - Real-time signal feed ✅
  - Live performance indicators ✅
  - Correlation matrix visualization ⚠️
  - Data quality indicators ⚠️
- **Data Requirements**:
  - Strategy configuration data ✅
  - Strategy performance metrics ✅
  - Active trades for the strategy ✅
  - Historical performance data ✅
  - Real-time trade and signal data ✅
- **API Endpoints**:
  - `GET /api/strategies/{id}` - Get strategy details ✅
  - `GET /api/strategies/{id}/performance` - Get strategy performance metrics ✅
  - `GET /api/strategies/{id}/trades/active` - Get active trades for strategy ✅
  - `GET /api/strategies/{id}/trades/history` - Get historical trades for strategy ✅
  - `GET /api/strategies/{id}/metrics` - Get strategy KPIs ✅
  - `POST /api/strategies/{id}/start` - Start strategy ✅
  - `POST /api/strategies/{id}/stop` - Stop strategy ✅
  - `GET /api/strategies/{id}/parameters` - Get strategy parameters ✅
  - `PUT /api/strategies/{id}/parameters` - Update strategy parameters ✅
  - `GET /api/strategies/{id}/signals` - Get recent signals for strategy ✅
  - `GET /api/market/data/{symbol}` - Get market data for symbol ✅
  - `WS /api/ws/strategies/{id}` - WebSocket for real-time strategy updates ✅
  - `WS /api/ws/strategies/{id}/trades` - WebSocket for strategy's trade updates ✅
  - `WS /api/ws/strategies/{id}/signals` - WebSocket for real-time strategy signals ✅
  - `WS /api/ws/strategies/{id}/performance` - WebSocket for real-time performance updates ✅

## 3. Strategy Management Pages

### 3.1 Strategy List Page
- **Implementation Status**: ✅ Complete
- **Functionality**:
  - View all configured strategies ✅
  - Filter and search strategies ✅
  - Enable/disable strategies ✅
  - Clone existing strategies ✅
  - Create new strategies ✅
- **Components**:
  - Strategy list table with filters ✅
  - Status indicators ✅
  - Action buttons (edit, clone, delete) ✅
  - "Create New" button ✅
- **Data Requirements**:
  - List of all strategies ✅
  - Status information for each strategy ✅
  - Performance summary for each strategy ✅
- **API Endpoints**:
  - `GET /api/strategies` - Get all strategies with pagination and filtering ✅
  - `GET /api/strategies/types` - Get available strategy types ✅
  - `POST /api/strategies/{id}/clone` - Clone an existing strategy ✅
  - `DELETE /api/strategies/{id}` - Delete a strategy ✅
  - `POST /api/strategies/{id}/enable` - Enable a strategy ✅
  - `POST /api/strategies/{id}/disable` - Disable a strategy ✅
  - `GET /api/strategies/performance/summary` - Get performance summary for all strategies ✅

### 3.2 Strategy Creation/Edit Page
- **Implementation Status**: ✅ Complete
- **Functionality**:
  - Configure all strategy parameters ✅
  - Set signal scanning parameters ✅
  - Configure signal generation rules ✅
  - Set risk management parameters ✅
  - Test strategy with historical data ✅
  - Configure correlation thresholds ✅
  - Set minimum data points requirements ✅
  - Configure multiple correlation methods (Pearson, Spearman, Kendall) ✅
  - Configure rolling correlation windows ✅
  - Statistical validation (P-values, confidence intervals) ✅
  - Method-specific correlation thresholds ✅
- **Components**:
  - Strategy name and description fields ✅
  - Parameter configuration forms ✅
  - Signal scanning configuration ✅
    - Name ✅
    - Expiry settings (Weekly, Monthly) ✅
    - SS-Type (Intraday, Positional) ✅
    - Trading days selection ✅
    - Time settings (Start Time, End Time, with U.S. market hours defaults) ✅
    - Signal type configuration (Long, Short) ✅
    - Instrument selection (FUT, OPTION, ETF, Cash Equity) ✅
    - Option type selection (CALL, PUT) ✅
    - Option category selection (ITM, OTM, FUT, DOTM, DITM with U.S. tick structure) ✅
    - Mode selection (Live, Virtual) ✅
  - Signal generation configuration ✅
    - Exchange selection (NYSE, NASDAQ, CBOE, SMART, ISLAND, ARCA, MEMX, IEX) ✅
    - Order type selection (Stop, Stop Limit, Market, Limit) ✅
    - Product type selection (Margin, Cash) ✅
    - Base value configuration (contract size/lot size) ✅
  - Entry rule builder ✅
  - Exit rule builder ✅
  - Risk management settings ✅
  - Backtesting panel ✅
  - PDT rule compliance monitor ✅
  - Margin utilization display ✅
- **Data Requirements**:
  - Strategy configuration templates ⚠️ (Basic templates only)
  - Available symbols and instruments ⚠️ (Limited implementation)
  - Historical data for backtesting ❌ (Not implemented)
  - Risk parameter options ✅
  - U.S. market calendar (regular, half days, holidays) ❌ (Not implemented)
- **API Endpoints**:
  - `POST /api/strategies` - Create a new strategy ✅
  - `PUT /api/strategies/{id}` - Update an existing strategy
  - `GET /api/strategies/templates` - Get strategy templates
  - `GET /api/symbols` - Get available symbols
  - `GET /api/correlation/methods` - Get available correlation methods
  - `POST /api/strategies/{id}/correlation` - Test correlation configuration
  - `GET /api/market-data/stats` - Get market data statistics
  - `GET /api/instruments` - Get available instruments
  - `GET /api/exchanges` - Get available exchanges
  - `GET /api/order-types` - Get available order types
  - `GET /api/product-types` - Get available product types
  - `GET /api/option-types` - Get available option types
  - `GET /api/option-categories` - Get available option categories
  - `POST /api/strategies/backtest` - Run strategy backtest
  - `GET /api/strategies/backtest/{id}` - Get backtest results
  - `GET /api/strategies/rules/entry/templates` - Get entry rule templates
  - `GET /api/strategies/rules/exit/templates` - Get exit rule templates
  - `GET /api/risk/parameters` - Get risk parameter options
  - `GET /api/market/calendar` - Get U.S. market calendar

### 3.3 Correlation Strategy Configuration Page
- **Implementation Status**: ⚠️ Partially Implemented
- **Functionality**:
  - Specialized interface for multi-symbol correlation strategies ✅
  - Configure correlation parameters ✅
  - Set timeframes for technical indicator calculations ✅
  - Configure signal conditions ⚠️ (Predefined conditions only, no custom conditions)
- **Components**:
  - Primary and correlated symbol selection ✅
  - Timeframe selection (configurable) ✅
  - Signal condition configuration ⚠️ (Limited implementation)
    - Buy conditions (primary symbol price > SH of primary symbol, correlated symbol price < SL of correlated symbol) ✅
    - Sell conditions (primary symbol price < SL of primary symbol, correlated symbol price > SH of correlated symbol) ✅
    - Custom condition builder ❌ (Not implemented)
  - Backtesting results visualization ⚠️ (Basic metrics only, no detailed visualization)
- **Data Requirements**:
  - Historical data for selected symbols ⚠️ (Limited implementation)
  - Technical indicator calculation parameters ⚠️ (Basic parameters only)
  - Correlation metrics ✅
- **API Endpoints**:
  - `GET /api/strategies/templates/correlation` - Get correlation strategy template ⚠️ (Partially implemented)
  - `POST /api/strategies/correlation` - Create new correlation strategy ⚠️ (Partially implemented)
  - `PUT /api/strategies/correlation/{id}` - Update correlation strategy ❌ (Not implemented)
  - `GET /api/market/data/{symbol}` - Get symbol historical data ⚠️ (Partially implemented)
  - `GET /api/indicators/parameters` - Get indicator calculation parameters ❌ (Not implemented)
  - `POST /api/indicators/calculate` - Calculate indicators for given data ❌ (Not implemented)
  - `GET /api/correlation/metrics` - Get correlation metrics between symbols ⚠️ (Partially implemented)
  - `POST /api/strategies/correlation/backtest` - Run backtest for correlation strategy ❌ (Not implemented)
  - `GET /api/strategies/correlation/backtest/{id}` - Get correlation strategy backtest results ❌ (Not implemented)

## 4. Trade Management Pages

### 4.1 Active Trades Page
- **Implementation Status**: ✅ Complete
- **Functionality**:
  - View all active trades ✅
  - Filter trades by strategy, symbol, etc. ✅
  - Monitor trade status in real-time ✅
  - Advanced order management (MARKET, LIMIT, STOP, STOP_LIMIT, TRAILING_STOP) ✅
  - Time-in-Force options (DAY, GTC, IOC, FOK) ✅
  - Complex order structures (SIMPLE, BRACKET, OCO) ✅
  - Bracket order configuration ✅
  - OCO order setup ✅
  - Trailing stop configuration ✅
- **Components**:
  - Trades table with filtering ✅
  - Trade status indicators ✅
  - P&L charts ✅
  - Position size controls ✅
  - Stop-loss and take-profit settings ✅
- **Data Requirements**:
  - Active trade data ✅
  - Real-time price updates ✅
  - Position information ✅
  - P&L calculations ✅
- **API Endpoints**:
  - `GET /api/trades/active` - Get all active trades with filtering ✅
  - `GET /api/trades/active/count` - Get count of active trades ✅
  - `GET /api/trades/active/summary` - Get summary of active trades ✅
  - `POST /api/trades/{id}/close` - Close a trade manually ✅
  - `PUT /api/trades/{id}/size` - Adjust position size ✅
  - `PUT /api/trades/{id}/stop-loss` - Set stop-loss level ✅
  - `PUT /api/trades/{id}/take-profit` - Set take-profit level ✅
  - `WS /api/ws/trades/active` - WebSocket for real-time trade updates ✅
  - `WS /api/ws/trades/price` - WebSocket for real-time price updates ✅
  - `WS /api/ws/trades/pnl` - WebSocket for real-time P&L updates ✅

### 4.2 Trade Detail Page
- **Implementation Status**: ⚠️ Partially Implemented
- **Functionality**:
  - View detailed trade information ✅
  - Monitor real-time trade status ✅
  - View price charts ✅
  - Add trade notes ✅
  - Modify trade parameters ✅
- **Components**:
  - Trade overview card ✅
  - Price chart ✅
  - Trade notes section ✅
  - Parameter modification form ✅
  - Trade status indicators ✅
- **Data Requirements**:
  - Trade details data ✅
  - Real-time price data ✅
  - Trade notes storage ✅
  - Parameter modification rules ✅
- **API Endpoints**:
  - `GET /api/trades/{id}` - Get trade details ✅
  - `GET /api/trades/{id}/price-history` - Get price history ✅
  - `POST /api/trades/{id}/notes` - Add trade notes ✅
  - `PUT /api/trades/{id}/parameters` - Modify trade parameters ✅
  - `WS /api/ws/trades/{id}` - WebSocket for real-time trade updates ✅
  - `WS /api/ws/trades/{id}/price` - WebSocket for real-time price updates ✅
  - `DELETE /api/trades/{id}/notes/{noteId}` - Delete note from trade ❌ (Not implemented)
  - `GET /api/market/data/{symbol}/range` - Get market data for symbol in date range ⚠️ (Partially implemented)
  - `GET /api/trades/{id}/executions` - Get execution details for trade ❌ (Not implemented)
  - `WS /api/ws/trades/{id}` - WebSocket for real-time trade updates ⚠️ (Partially implemented)
  - `WS /api/ws/market/data/{symbol}` - WebSocket for symbol's real-time market data ⚠️ (Partially implemented)
  - `WS /api/ws/trades/{id}/pnl` - WebSocket for real-time trade P&L updates ⚠️ (Partially implemented)
  - `WS /api/ws/trades/{id}/executions` - WebSocket for trade execution updates ❌ (Not implemented)

### 4.3 Pre-Trade Analysis Page
- **Implementation Status**: ✅ Implemented
- **Functionality**:
  - Review pre-trade checks and calculations ✅
  - View risk assessment for potential trades ✅
  - Adjust trade parameters before execution ✅
- **Components**:
  - Pre-trade checklist ✅
  - Risk calculation display ✅
  - Parameter adjustment controls ✅
  - Trade preview panel ✅
- **Data Requirements**:
  - Account risk parameters ✅
  - Active trade count ✅
  - Daily trade count ✅
  - Risk calculation metrics ✅
- **API Endpoints**:
  - `POST /api/trades/analyze` - Analyze potential trade ✅
  - `GET /api/trades/active/count` - Get active trade count ✅
  - `GET /api/trades/daily/count` - Get daily trade count ✅
  - `GET /api/risk/parameters/current` - Get current risk parameters ✅
  - `POST /api/risk/calculate` - Calculate risk for potential trade ✅
  - `GET /api/account/balance` - Get account balance information ✅
  - `POST /api/trades/preview` - Generate trade preview with parameters ✅

## 5. Risk Management Pages

### 5.1 Risk Dashboard
- **Implementation Status**: ✅ Complete
- **Functionality**:
  - Overview of current risk exposure ✅
  - Monitor risk parameters across all trades ✅
  - View risk alerts and warnings ✅
  - Access risk management settings ✅
  - Monitor PDT rule compliance status ✅
  - Track Reg-T margin utilization ✅
  - Real-time risk metrics updates ✅
  - RR-Trigger mechanism for profitable trades ✅
  - Configurable R-multiple thresholds ✅
  - Automatic risk reduction ✅
  - Breakeven management ✅ 
- **Components**:
  - Risk exposure charts 
  - Risk parameter displays 
  - Alert indicators 
  - Quick action buttons 
  - PDT rule status panel (day trades count, equity requirements) 
  - Margin utilization display 
  - Settlement date tracker (T+2 for U.S. equities) 
  - Regulatory compliance indicators 
  - Real-time risk threshold monitor
- **Data Requirements**:
  - Current risk metrics 
  - Risk parameter settings 
  - Alert configuration 
  - Day trade count (rolling 5 business days) 
  - Account equity status 
  - Margin utilization metrics 
  - Real-time position data 
  - Market volatility indicators
- **API Endpoints**:
  - `GET /api/risk/dashboard` - Get risk dashboard data ✅
  - `GET /api/risk/exposure` - Get current risk exposure metrics ✅
  - `GET /api/risk/parameters` - Get risk parameter settings ✅
  - `GET /api/risk/alerts` - Get active risk alerts ✅
  - `POST /api/risk/alerts/acknowledge/{id}` - Acknowledge risk alert ✅
  - `GET /api/risk/limits/status` - Get status of risk limits ✅
  - `GET /api/risk/historical` - Get historical risk metrics ✅
  - `GET /api/risk/exposure/breakdown` - Get breakdown of risk exposure by strategy/symbol
  - `GET /api/risk/pdt/status` - Get PDT rule compliance status
  - `GET /api/risk/pdt/day-trades` - Get day trades count in rolling window
  - `GET /api/risk/margin/utilization` - Get Reg-T margin utilization metrics
  - `GET /api/risk/settlement/dates` - Get settlement dates for open positions
  - `WS /api/ws/risk/dashboard` - WebSocket for real-time risk dashboard updates
  - `WS /api/ws/risk/exposure` - WebSocket for real-time risk exposure updates

## 6. WebSocket Integration

### 6.1 Real-time Updates
- **Implementation Status**: ✅ Complete
- **Functionality**:
  - Custom WebSocket hook implementation ✅
  - Auto-reconnection with exponential backoff ✅
  - Multiple concurrent WebSocket connections ✅
  - Robust error handling and monitoring ✅
  - Connection status indicators ✅
- **Components**:
  - Connection status indicators ✅
  - Reconnection progress UI ✅
  - Error notification system ✅
  - Connection health monitoring ✅
- **Data Requirements**:
  - WebSocket connection state ✅
  - Reconnection attempts count ✅
  - Error history ✅
  - Connection latency metrics ✅
- **API Endpoints**:
  - `WS /api/ws/dashboard` - Real-time dashboard metrics ✅
  - `WS /api/ws/trades` - Live trade status and P&L ✅
  - `WS /api/ws/signals` - Real-time strategy signals ✅
  - `WS /api/ws/performance` - Live performance metrics ✅
  - `WS /api/ws/market` - Real-time price and volume updates ✅

## 7. Performance and UX Enhancements

### 7.1 Performance Optimization
- **Implementation Status**: ✅ Complete
- **Functionality**:
  - Efficient data processing and updates ✅
  - Memory optimization ✅
  - WebSocket connection pooling ✅
  - Error recovery mechanisms ✅
  - Graceful degradation ✅
- **Components**:
  - Optimized data structures ✅
  - Efficient update mechanisms ✅
  - Resource monitoring ✅
  - Performance metrics dashboard ✅
- **Data Requirements**:
  - Performance metrics ✅
  - Resource usage data ✅
  - Error logs ✅
  - Connection statistics ✅

### 5.1 Risk Dashboard
- **Implementation Status**: ✅ Complete
- **Functionality**:
  - Overview of current risk exposure ✅
  - Monitor risk parameters across all trades ✅
  - View risk alerts and warnings ✅
  - Access risk management settings ✅
  - Monitor PDT rule compliance status ✅
  - Track Reg-T margin utilization ✅
  - Real-time risk metrics updates ✅
  - RR-Trigger mechanism for profitable trades ✅
  - Configurable R-multiple thresholds ✅
  - Automatic risk reduction ✅
  - Breakeven management ✅ 
- **Components**:
  - Risk exposure charts 
  - Risk parameter displays 
  - Alert indicators 
  - Quick action buttons 
  - PDT rule status panel (day trades count, equity requirements) 
  - Margin utilization display 
  - Settlement date tracker (T+2 for U.S. equities) 
  - Regulatory compliance indicators 
  - Real-time risk threshold monitor 
- **Data Requirements**:
  - Current risk metrics 
  - Risk parameter settings 
  - Alert configuration 
  - Day trade count (rolling 5 business days) 
  - Account equity status 
  - Margin utilization metrics 
  - Real-time position data 
  - Market volatility indicators 
- **API Endpoints**:
  - `GET /api/risk/dashboard` - Get risk dashboard data ✅
  - `GET /api/risk/exposure` - Get current risk exposure metrics ✅
  - `GET /api/risk/parameters` - Get risk parameter settings ✅
  - `GET /api/risk/alerts` - Get active risk alerts ⚠️ (Partially implemented)
  - `POST /api/risk/alerts/acknowledge/{id}` - Acknowledge risk alert ❌ (Not implemented)
  - `GET /api/risk/limits/status` - Get status of risk limits ⚠️ (Partially implemented)
  - `GET /api/risk/historical` - Get historical risk metrics ✅
  - `GET /api/risk/exposure/breakdown` - Get breakdown of risk exposure by strategy/symbol
  - `GET /api/risk/pdt/status` - Get PDT rule compliance status
  - `GET /api/risk/pdt/day-trades` - Get day trades count in rolling window
  - `GET /api/risk/margin/utilization` - Get Reg-T margin utilization metrics
  - `GET /api/risk/settlement/dates` - Get settlement dates for open positions
  - `WS /api/ws/risk/dashboard` - WebSocket for real-time risk dashboard updates
  - `WS /api/ws/risk/exposure` - WebSocket for real-time risk exposure updates
  - `WS /api/ws/risk/alerts` - WebSocket for real-time risk alerts
  - `WS /api/ws/risk/pdt` - WebSocket for PDT rule status updates
  - `WS /api/ws/risk/margin` - WebSocket for margin utilization updates

### 5.2 Risk Settings Page
- **Implementation Status**: ✅ Implemented
- **Functionality**:
  - Configure risk management parameters ✅
  - Set maximum stop loss per trade ✅
  - Set maximum stop loss across all trades ✅
  - Configure risk reduction rules ✅
- **Components**:
  - Risk parameter configuration forms ✅
  - Risk visualization tools ⚠️ (Limited implementation)
- **Data Requirements**:
  - Risk parameter settings ✅
  - Account position limits ✅
  - Stop loss parameters ✅
  - Correlation settings ✅
- **API Endpoints**:
  - `GET /api/risk/settings` - Get risk settings ✅
  - `PUT /api/risk/settings` - Update risk settings ⚠️ (UI exists but functionality not fully implemented)
  - `GET /api/risk/limits` - Get risk limits ✅
  - `PUT /api/risk/limits` - Update risk limits ⚠️ (UI exists but functionality not fully implemented)
  - Historical risk analysis
  - Save/reset buttons
- **Data Requirements**:
  - Risk parameter options
  - Historical risk data
  - Account information
- **API Endpoints**:
  - `GET /api/risk/settings` - Get risk management settings
  - `PUT /api/risk/settings` - Update risk management settings
  - `GET /api/risk/settings/templates` - Get risk setting templates
  - `POST /api/risk/settings/apply-template/{id}` - Apply risk setting template
  - `GET /api/risk/max-stoploss/trade` - Get maximum stop loss per trade
  - `PUT /api/risk/max-stoploss/trade` - Update maximum stop loss per trade
  - `GET /api/risk/max-stoploss/all` - Get maximum stop loss across all trades
  - `PUT /api/risk/max-stoploss/all` - Update maximum stop loss across all trades
  - `GET /api/risk/historical/analysis` - Get historical risk analysis data
  - `GET /api/account/info` - Get account information for risk calculations

### 5.3 Risk Reduction Rules Page
- **Implementation Status**: ✅ Implemented
- **Functionality**:
  - Configure rules for automatic risk reduction ✅
  - Set triggers for risk reduction actions ✅
  - Configure quantity sell parameters ✅
- **Components**:
  - Rule configuration forms ✅
  - Trigger setup controls ✅
  - Quantity calculation settings ✅
  - Rule testing panel ✅
- **Data Requirements**:
  - Current trade data ✅
  - Risk reduction templates ⚠️ (Basic templates only)
  - Historical risk reduction data ⚠️ (Limited implementation)
- **API Endpoints**:
  - `GET /api/risk/reduction/rules` - Get risk reduction rules ✅
  - `POST /api/risk/reduction/rules` - Create new risk reduction rule ✅
  - `PUT /api/risk/reduction/rules/{id}` - Update risk reduction rule ⚠️ (Partially implemented)
  - `DELETE /api/risk/reduction/rules/{id}` - Delete risk reduction rule ✅
  - `GET /api/risk/reduction/triggers` - Get available trigger types ✅
  - `GET /api/risk/reduction/actions` - Get available action types ✅
  - `POST /api/risk/reduction/test` - Test risk reduction rule ✅
  - `GET /api/risk/reduction/history` - Get history of risk reduction actions ❌ (Not implemented)
  - `GET /api/risk/reduction/templates` - Get risk reduction rule templates ⚠️ (Partially implemented)
  - `POST /api/risk/reduction/quantity/calculate` - Calculate sell quantity based on parameters ⚠️ (Partially implemented)

## 6. Reporting Pages

### 6.1 Deals Report Page
- **Implementation Status**: ⚠️ Partially Implemented
- **Functionality**:
  - View comprehensive trade history ✅
  - Filter and search past trades ⚠️ (Basic filtering only)
  - Export trade data ⚠️ (UI exists but functionality not implemented)
  - Analyze trade performance ⚠️ (Limited implementation)
- **Components**:
  - Deals table with advanced filtering ⚠️ (Basic filtering only)
  - Performance metrics ⚠️ (Limited implementation)
  - Export controls ⚠️ (UI only, functionality not implemented)
  - Visualization tools ❌ (Not implemented)
- **Data Requirements**:
  - Complete trade history ⚠️ (Mock data only)
  - Performance metrics ⚠️ (Basic metrics only)
  - Trade details including: ✅
    - Strategy Name ✅
    - SS-Type ✅
    - SS-signal-Type ✅
    - Symbol name ✅
    - Quantity (Entry Qty, Exit Qty) ✅
    - Price (Entry Price, Exit Price) ✅
    - P&L ✅
    - Charges ✅
    - Net P&L ✅
    - Net P&L% ✅
    - Date (Entry Date, Exit Date) ✅
    - Status
    - Comments
- **API Endpoints**:
  - `GET /api/trades/history` - Get trade history with pagination and filtering
  - `GET /api/trades/history/export` - Export trade history in various formats
  - `GET /api/trades/history/summary` - Get summary of trade history
  - `GET /api/trades/performance/metrics` - Get performance metrics for trades
  - `GET /api/trades/filters` - Get available trade filters
  - `GET /api/trades/history/{id}` - Get detailed information for a specific trade
  - `POST /api/trades/history/search` - Advanced search for trade history

### 6.2 Performance Analytics Page
- **Implementation Status**: ⚠️ Partially Implemented
- **Functionality**:
  - Analyze trading performance over time ⚠️ (Basic implementation with static data)
  - View performance by strategy, symbol, etc. ⚠️ (Limited implementation)
  - Compare strategies and time periods ❌ (Not implemented)
  - Identify strengths and weaknesses ⚠️ (Basic metrics only)
- **Components**:
  - Performance charts and graphs ⚠️ (Basic line chart implemented)
  - Comparison tools ❌ (Not implemented)
  - Metric selection controls ❌ (Not implemented)
  - Time period selectors ❌ (Not implemented)
- **Data Requirements**:
  - Historical performance data ⚠️ (Mock data only)
  - Strategy metrics ⚠️ (Basic metrics with static data)
  - Benchmark data ❌ (Not implemented)
- **API Endpoints**:
  - `GET /api/performance/summary` ❌ (Not implemented, using mock data)
  - `GET /api/performance/strategies` ❌ (Not implemented, using mock data)
  - `GET /api/performance/symbols` ❌ (Not implemented)
  - `GET /api/performance/time-series` ❌ (Not implemented, using mock data)
  - `GET /api/performance/comparison` ❌ (Not implemented)
  - `GET /api/performance/metrics` ❌ (Not implemented)
  - `GET /api/performance/benchmarks` ❌ (Not implemented)
  - `POST /api/performance/custom-report` ❌ (Not implemented)

### 6.3 P&L Reporting Page
- **Implementation Status**: ❌ Not Implemented
- **Functionality**:
  - Detailed P&L analysis 
  - View P&L by day, week, month, year 
  - Break down P&L by strategy, symbol, etc. 
  - Export P&L reports 
- **Components**:
  - P&L summary charts 
  - Detailed P&L tables 
  - Filtering and grouping controls 
  - Export buttons 
- **Data Requirements**:
  - P&L data at various time granularities 
  - Strategy and symbol P&L breakdowns 
  - Fee and commission data 
- **API Endpoints**:
  - `GET /api/pnl/summary` ❌ (Not implemented)
  - `GET /api/pnl/daily` ❌ (Not implemented)
  - `GET /api/pnl/weekly` ❌ (Not implemented)
  - `GET /api/pnl/monthly` ❌ (Not implemented)
  - `GET /api/pnl/yearly` ❌ (Not implemented)
  - `GET /api/pnl/strategies` ❌ (Not implemented)
  - `GET /api/pnl/symbols` ❌ (Not implemented)
  - `GET /api/pnl/fees` ❌ (Not implemented)
  - `GET /api/pnl/export/{format}` ❌ (Not implemented)
  - `POST /api/pnl/custom-report` ❌ (Not implemented)

## 7. System Configuration Pages

### 7.1 Universal Settings Page
- **Implementation Status**: ❌ Not Implemented
- **Functionality**:
  - Configure platform-wide settings ❌ (Not implemented)
  - Set U.S. trading hours (regular, pre-market, post-market) ❌ (Not implemented)
  - Configure NYSE/NASDAQ holiday calendar ❌ (Not implemented)
  - Set capital allocation ❌ (Not implemented)
  - Configure option category splits ❌ (Not implemented)
  - Manage regulatory compliance settings ❌ (Not implemented)
- **Components**:
  - Settings configuration forms ❌ (Not implemented)
  - Capital input fields ❌ (Not implemented)
- **Data Requirements**:
  - Current universal settings 
  - NYSE/NASDAQ holiday calendar data 
  - Capital information 
  - Regulatory threshold values 
- **API Endpoints**:
  - `GET /api/settings/universal` - Get universal settings
  - `PUT /api/settings/universal` - Update universal settings
  - `GET /api/settings/trading-hours` - Get trading hours
  - `PUT /api/settings/trading-hours` - Update trading hours
  - `GET /api/market/holiday-calendar` - Get holiday calendar
  - `GET /api/settings/option-categories` - Get option categories
  - `PUT /api/settings/option-categories` - Update option categories
  - `GET /api/settings/regulatory` - Get regulatory settings
  - `PUT /api/settings/regulatory` - Update regulatory settings
  - `GET /api/settings/data-archiving` - Get data archiving settings
  - `PUT /api/settings/data-archiving` - Update data archiving settings

### 7.2 API Connections Page
- **Implementation Status**: 
- **Functionality**:
  - Manage connections to exchange APIs 
  - Monitor API connection status 
  - Configure API parameters 
  - Test API connections 
- **Components**:
  - API connection status indicators 
  - Configuration forms 
  - Test connection buttons 
  - Connection logs 
- **Data Requirements**:
  - API connection status 
  - API configuration parameters 
  - Connection logs 
- **API Endpoints**:
  - `GET /api/connections` - Get API connections
  - `GET /api/connections/{id}` - Get API connection details
  - `POST /api/connections` - Create new API connection
  - `PUT /api/connections/{id}` - Update API connection
  - `DELETE /api/connections/{id}` - Delete API connection
  - `GET /api/connections/{id}/status` - Get API connection status
  - `POST /api/connections/{id}/test` - Test API connection
  - `GET /api/connections/{id}/logs` - Get API connection logs
  - `GET /api/connections/providers` - Get available API providers
  - `GET /api/connections/latency` - Get API connection latency
  - `GET /api/connections/websocket` - Get WebSocket connection status
  - `POST /api/connections/websocket` - Establish WebSocket connection

### 7.3 System Monitoring Page
- **Implementation Status**: 
- **Functionality**:
  - Monitor system health 
  - View system logs 
  - Real-time performance metrics 
  - Resource usage monitoring 
  - Error tracking and alerts 
  - WebSocket connection status 
  - Market data feed health 
  - Order execution latency monitoring 
- **Components**:
  - System health dashboard 
  - Log viewer 
  - Performance metrics charts 
  - Resource usage graphs 
  - Alert panel 
  - WebSocket status indicators 
  - Data feed monitors 
- **Data Requirements**:
  - System health metrics 
  - Log data 
  - Database performance metrics 
  - Alert configuration 
- **API Endpoints**:
  - `GET /api/system/health` - Get system health
  - `GET /api/system/metrics` - Get system metrics
  - `GET /api/system/logs` - Get system logs
  - `GET /api/system/database/performance` - Get database performance
  - `GET /api/system/alerts` - Get system alerts
  - `POST /api/system/alerts` - Create new system alert
  - `PUT /api/system/alerts/{id}` - Update system alert
  - `DELETE /api/system/alerts/{id}` - Delete system alert
  - `GET /api/system/resources` - Get system resources
  - `GET /api/system/services/status` - Get system service status

## 8. Mobile Responsive Views

### 8.1 Mobile Dashboard
- **Implementation Status**: 
- **Functionality**:
  - View key trading metrics on mobile 
  - Quick access to active trades 
  - Monitor strategy performance 
  - Receive notifications 
  - Basic trade management 
- **Components**:
  - Mobile-friendly dashboard layout 
  - Trade status cards 
  - Strategy performance indicators 
  - Mobile notification center 
  - Quick action buttons 
- **Data Requirements**:
  - Mobile-optimized data endpoints 
  - Push notification configuration 
  - Mobile-specific UI components 
- **API Endpoints**:
  - `GET /api/mobile/dashboard` - Get mobile-optimized dashboard data 
  - `GET /api/mobile/trades/active` - Get active trades for mobile 
  - `GET /api/mobile/notifications` - Get mobile notifications 
  - `POST /api/mobile/trades/{id}/close` - Close trade from mobile 
  - `POST /api/mobile/notifications/read` - Mark notifications as read 

### 8.2 Mobile Trade Management
- **Implementation Status**: 
- **Functionality**:
  - View trade details on mobile 
  - Close trades 
  - Adjust position size 
  - Set stop-loss/take-profit 
  - View trade history 
- **Components**:
  - Mobile trade detail view 
  - Mobile trade action buttons 
  - Mobile trade history list 
  - Mobile position controls 
  - Mobile stop-loss/take-profit settings 
- **Data Requirements**:
  - Mobile-optimized trade data 
  - Mobile-specific position controls 
  - Mobile trade history format 
  - P&L data ⚠️ (Same as desktop view)
- **API Endpoints**:
  - `GET /api/trades/monitor/mobile` ❌ (Not implemented, using desktop endpoints)
  - `GET /api/trades/{id}/mobile` ❌ (Not implemented, using desktop endpoints)
  - `POST /api/trades/{id}/close/mobile` ❌ (Not implemented, using desktop endpoints)
  - `PUT /api/trades/{id}/stoploss/mobile` ❌ (Not implemented, using desktop endpoints)
  - `PUT /api/trades/{id}/target/mobile` ❌ (Not implemented, using desktop endpoints)
  - `GET /api/pnl/summary/mobile` ❌ (Not implemented, using desktop endpoints)
  - `GET /api/alerts/trade/mobile` ❌ (Not implemented)

## 9. Design System

### 9.1 Component Library
- **Implementation Status**: ⚠️ Partially Implemented
- Typography system ⚠️ (Basic implementation)
- Color palette (dark and light themes) ✅ (Implemented with Tailwind CSS)
- Form components ⚠️ (Basic implementation)
- Button styles ⚠️ (Basic implementation)
- Card and panel designs ✅ (Implemented with DashboardCard and other components)
- Table designs ⚠️ (Basic implementation)
- Chart and visualization components ⚠️ (Limited implementation)
- Navigation components ⚠️ (Basic implementation)
- Alert and notification designs ⚠️ (Limited implementation)
- Real-time data components ❌ (Not implemented)

### 9.2 Layout Templates
- **Implementation Status**: ⚠️ Partially Implemented
- Dashboard layouts ✅ (Implemented with Navbar and Sidebar components)
- Form page layouts ⚠️ (Basic implementation)
- Report page layouts ⚠️ (Basic implementation)
- Detail page layouts ⚠️ (Basic implementation)
- Mobile layouts ⚠️ (Limited responsive design only)
- Real-time monitoring layouts ❌ (Not implemented)

### 9.3 Interaction Patterns
- **Implementation Status**: ⚠️ Partially Implemented
- Form validation ⚠️ (Basic implementation)
- Data loading states ⚠️ (Basic implementation)
- Error handling ⚠️ (Basic implementation)
- Confirmation dialogs ⚠️ (Limited implementation)
- Tooltips and help systems ⚠️ (Limited implementation)
- Drag and drop interfaces ❌ (Not implemented)
- Real-time data updates ❌ (Not implemented)
- WebSocket connection management ❌ (Not implemented)

### 9.4 Component Integration Guide
- **Implementation Status**: ⚠️ Partially Implemented

- **Component Integration with WebSockets**:
  - **Implementation Status**: ❌ Not Implemented
  - Guidelines for connecting components to WebSocket data sources ❌ (Not implemented)
  - Patterns for handling real-time data updates ❌ (Not implemented)
  - State management for WebSocket data ❌ (Not implemented)
  - Error handling and reconnection strategies ❌ (Not implemented)
  - Performance optimization techniques ❌ (Not implemented)

- **Data Visualization Integration**:
  - **Implementation Status**: ⚠️ Partially Implemented
  - TradingView chart integration ⚠️ (Limited implementation)
  - D3.js visualization patterns ⚠️ (Basic implementation)
  - Real-time chart update patterns ❌ (Not implemented)
  - Large dataset handling ❌ (Not implemented)

- **U.S. Market-Specific Components**:
  - **Implementation Status**: ⚠️ Partially Implemented
  - Market hours indicators ⚠️ (Basic implementation)
  - PDT rule compliance widgets ❌ (Not implemented)
  - Settlement date trackers ❌ (Not implemented)
  - Options chain visualizers with U.S. tick structure ❌ (Not implemented)
  - Regulatory compliance indicators ❌ (Not implemented)

## 10. Implementation Status Summary

### 10.1 Overall Implementation Progress

| Category | Fully Implemented | Partially Implemented | Not Implemented | Total |
|----------|-------------------|----------------------|-----------------|-------|
| Authentication Pages | 0 | 2 | 0 | 2 |
| Dashboard Pages | 1 | 1 | 0 | 2 |
| Strategy Management Pages | 1 | 2 | 0 | 3 |
| Trade Management Pages | 1 | 2 | 0 | 3 |
| Risk Management Pages | 2 | 1 | 0 | 3 |
| Reporting Pages | 0 | 2 | 1 | 3 |
| System Configuration Pages | 0 | 0 | 3 | 3 |
| Mobile Responsive Views | 0 | 2 | 0 | 2 |
| Design System | 0 | 4 | 0 | 4 |
| **Total** | **5** | **16** | **4** | **25** |

### 10.2 Priority Areas for Development

1. **High Priority**:
   - Complete the partially implemented authentication features (API key management, password changes)
   - Implement missing Strategy Dashboard features (control panels, live signal monitoring)
   - Complete Trade Detail Page functionality (trade modification, advanced analytics)
   - Implement WebSocket connections for real-time data updates

2. **Medium Priority**:
   - Complete the Reporting Pages section (P&L Reporting, advanced filtering in Deals Report)
   - Enhance mobile responsiveness with dedicated mobile views
   - Implement remaining Risk Dashboard features (real-time alerts, PDT rule compliance)

3. **Lower Priority**:
   - Implement System Configuration Pages
   - Implement API Connections management
   - Complete advanced visualization components

### 10.3 Implementation Notes

- Most core trading functionality is at least partially implemented
- The application has a consistent design system using Tailwind CSS
- Real-time data functionality is largely missing and should be prioritized
- Mobile support is limited to basic responsive design rather than dedicated mobile views
- System configuration and API connection management are completely missing
