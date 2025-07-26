from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ib_insync import IB, Stock, Option, util, BarData, Contract
import asyncio
from datetime import datetime, timezone, timedelta
import pytz
from functools import lru_cache
import time
from threading import Lock
from enum import Enum

class MarketDataQuality(Enum):
    REAL_TIME = "REAL_TIME"
    DELAYED = "DELAYED"
    FROZEN = "FROZEN"
    UNKNOWN = "UNKNOWN"

class MarketDataService:
    _instance = None
    _lock = Lock()
    _ib = None
    _last_connection_attempt = None
    _connection_retry_delay = 5  # seconds
    _max_retries = 3
    _max_subscriptions = 100  # Maximum number of concurrent market data subscriptions
    _subscription_timeout = 5  # seconds to wait for market data
    _subscription_retry_delay = 1  # seconds between subscription retries
    _max_subscription_retries = 3  # maximum number of subscription retries

    def __new__(cls, db: Session):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MarketDataService, cls).__new__(cls)
                cls._instance.db = db
                cls._instance._connect_ibkr()
                cls._instance._active_subscriptions = set()
            return cls._instance

    def _connect_ibkr(self):
        """Connect to IBKR API with retry mechanism"""
        if self._ib and self._ib.isConnected():
            return

        current_time = time.time()
        if (self._last_connection_attempt and 
            current_time - self._last_connection_attempt < self._connection_retry_delay):
            raise HTTPException(status_code=503, detail="Connection retry too soon")

        self._last_connection_attempt = current_time

        for attempt in range(self._max_retries):
            try:
                if not self._ib:
                    self._ib = IB()
                
                if not self._ib.isConnected():
                    self._ib.connect('127.0.0.1', 7497, clientId=1)
                    # Register error handler
                    self._ib.errorEvent += self._handle_error
                    return
            except Exception as e:
                if attempt == self._max_retries - 1:
                    raise HTTPException(status_code=500, detail=f"Failed to connect to IBKR after {self._max_retries} attempts: {str(e)}")
                time.sleep(self._connection_retry_delay)

    def _handle_error(self, reqId, errorCode, errorString, contract):
        """Handle IBKR API errors"""
        if errorCode in [502, 504]:  # Connection lost
            self._ib.disconnect()
            self._connect_ibkr()
        elif errorCode == 200:  # No security definition
            raise HTTPException(status_code=400, detail=f"No security definition: {errorString}")
        elif errorCode == 10197:  # Market data farm connection is OK
            pass  # This is a good message
        elif errorCode == 10168:  # Requested market data is not subscribed
            raise HTTPException(status_code=403, detail="Market data subscription required")
        elif errorCode == 10182:  # Market data subscription limit reached
            raise HTTPException(status_code=429, detail="Market data subscription limit reached")
        elif errorCode == 10183:  # Market data subscription delayed
            raise HTTPException(status_code=503, detail="Market data subscription delayed")
        elif errorCode == 10184:  # Market data subscription frozen
            raise HTTPException(status_code=503, detail="Market data subscription frozen")
        else:
            raise HTTPException(status_code=500, detail=f"IBKR error {errorCode}: {errorString}")

    def _check_subscription_limit(self):
        """Check if we've reached the market data subscription limit"""
        if len(self._active_subscriptions) >= self._max_subscriptions:
            raise HTTPException(status_code=429, detail="Market data subscription limit reached")

    def _subscribe_market_data(self, contract: Contract, include_pre_post: bool = False) -> None:
        """Subscribe to market data with retry mechanism"""
        self._check_subscription_limit()
        
        for attempt in range(self._max_subscription_retries):
            try:
                self._ib.reqMktData(contract, '', False, include_pre_post)
                self._active_subscriptions.add(contract.conId)
                return
            except Exception as e:
                if attempt == self._max_subscription_retries - 1:
                    raise HTTPException(status_code=500, detail=f"Failed to subscribe to market data: {str(e)}")
                time.sleep(self._subscription_retry_delay)

    def _unsubscribe_market_data(self, contract: Contract) -> None:
        """Unsubscribe from market data"""
        try:
            self._ib.cancelMktData(contract)
            self._active_subscriptions.discard(contract.conId)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to unsubscribe from market data: {str(e)}")

    def _get_market_data_quality(self, contract: Contract) -> MarketDataQuality:
        """Get the quality of market data for a contract"""
        try:
            # Request market data
            self._subscribe_market_data(contract)
            
            # Wait for data to arrive
            timeout = self._subscription_timeout
            start_time = datetime.now(timezone.utc)
            
            while (datetime.now(timezone.utc) - start_time).seconds < timeout:
                if contract.marketPrice():
                    if contract.marketPrice() == 0:
                        return MarketDataQuality.FROZEN
                    elif contract.marketPrice() == -1:
                        return MarketDataQuality.DELAYED
                    else:
                        return MarketDataQuality.REAL_TIME
                self._ib.sleep(0.1)
            
            return MarketDataQuality.UNKNOWN
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get market data quality: {str(e)}")
        finally:
            self._unsubscribe_market_data(contract)

    @lru_cache(maxsize=1000, ttl=300)  # Cache for 5 minutes
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol exists and is tradeable using IBKR"""
        try:
            # Create a Stock contract
            contract = Stock(symbol, 'SMART', 'USD')
            
            # Request contract details
            details = self._ib.reqContractDetails(contract)
            if not details:
                raise HTTPException(status_code=400, detail=f"No contract details found for {symbol}")
            
            # Check if the contract is tradeable
            if not details[0].tradeable:
                raise HTTPException(status_code=400, detail=f"Symbol {symbol} is not tradeable")
            
            # Check if the contract is active
            if not details[0].marketName:
                raise HTTPException(status_code=400, detail=f"Symbol {symbol} is not active")
            
            # Check market data subscription
            quality = self._get_market_data_quality(contract)
            if quality == MarketDataQuality.UNKNOWN:
                raise HTTPException(status_code=400, detail=f"Symbol {symbol} has no market data available")
            
            return True
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid symbol {symbol}: {str(e)}")

    def get_current_price(self, symbol: str, include_pre_post: bool = False) -> Optional[float]:
        """Get the current price for a symbol using IBKR"""
        contract = None
        try:
            # Create a Stock contract
            contract = Stock(symbol, 'SMART', 'USD')
            
            # Subscribe to market data
            self._subscribe_market_data(contract, include_pre_post)
            
            # Wait for data to arrive
            timeout = self._subscription_timeout
            start_time = datetime.now(timezone.utc)
            
            while (datetime.now(timezone.utc) - start_time).seconds < timeout:
                if contract.marketPrice():
                    return contract.marketPrice()
                self._ib.sleep(0.1)
            
            raise HTTPException(status_code=408, detail="Timeout waiting for market data")
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get price for {symbol}: {str(e)}")
        finally:
            # Unsubscribe from market data
            if contract:
                self._unsubscribe_market_data(contract)

    @lru_cache(maxsize=100, ttl=60)  # Cache for 1 minute
    def get_market_status(self, exchange: str, include_pre_post: bool = False) -> bool:
        """Check if the market is open for a given exchange using IBKR"""
        try:
            # Get market hours
            contract = Stock('SPY', exchange, 'USD')  # Using SPY as a reference
            trading_hours = self._ib.reqContractDetails(contract)[0].tradingHours
            
            # Parse trading hours
            # IBKR returns trading hours in format: "YYYYMMDD:HHMM-HHMM;YYYYMMDD:HHMM-HHMM"
            current_time = datetime.now(pytz.timezone('US/Eastern'))
            
            for session in trading_hours.split(';'):
                if not session:
                    continue
                    
                date_str, time_str = session.split(':')
                start_str, end_str = time_str.split('-')
                
                # Parse the date and times
                session_date = datetime.strptime(date_str, '%Y%m%d').date()
                start_time = datetime.strptime(start_str, '%H%M').time()
                end_time = datetime.strptime(end_str, '%H%M').time()
                
                # Check if current time is within this session
                if (session_date == current_time.date() and
                    start_time <= current_time.time() <= end_time):
                    return True
                
                # If pre/post market is requested, check those hours
                if include_pre_post:
                    # Pre-market: 4:00 AM - 9:30 AM ET
                    pre_market_start = datetime.strptime('0400', '%H%M').time()
                    pre_market_end = datetime.strptime('0930', '%H%M').time()
                    
                    # Post-market: 4:00 PM - 8:00 PM ET
                    post_market_start = datetime.strptime('1600', '%H%M').time()
                    post_market_end = datetime.strptime('2000', '%H%M').time()
                    
                    if (session_date == current_time.date() and
                        ((pre_market_start <= current_time.time() <= pre_market_end) or
                         (post_market_start <= current_time.time() <= post_market_end))):
                        return True
            
            return False
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get market status: {str(e)}")

    def get_historical_data(self, symbol: str, duration: str = '1 D', bar_size: str = '1 min') -> List[Dict[str, Any]]:
        """Get historical data for a symbol using IBKR"""
        try:
            # Create a Stock contract
            contract = Stock(symbol, 'SMART', 'USD')
            
            # Request historical data
            bars = self._ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )
            
            if not bars:
                raise HTTPException(status_code=404, detail=f"No historical data found for {symbol}")
            
            # Convert bars to dictionary format
            return [{
                'timestamp': bar.date,
                'open': bar.open,
                'high': bar.high,
                'low': bar.low,
                'close': bar.close,
                'volume': bar.volume,
                'average': bar.average,
                'bar_count': bar.barCount
            } for bar in bars]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get historical data: {str(e)}")

    def get_option_chain(self, symbol: str, expiry: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get option chain data for a symbol using IBKR"""
        try:
            # Create a Stock contract
            stock = Stock(symbol, 'SMART', 'USD')
            
            # Get option chain
            chains = self._ib.reqSecDefOptParams(
                stock.symbol,
                '',
                stock.secType,
                stock.conId
            )
            
            if not chains:
                raise HTTPException(status_code=404, detail=f"No option chain found for {symbol}")
            
            # Filter by expiry if provided
            if expiry:
                chains = [chain for chain in chains if chain.expirations and expiry in chain.expirations]
            
            # Get option contracts
            options = []
            for chain in chains:
                for strike in chain.strikes:
                    for right in ['C', 'P']:  # Call and Put
                        option = Option(
                            symbol,
                            chain.expirations[0] if chain.expirations else '',
                            strike,
                            right,
                            'SMART',
                            'USD'
                        )
                        details = self._ib.reqContractDetails(option)
                        if details:
                            options.append({
                                'symbol': details[0].contract.symbol,
                                'expiry': details[0].contract.lastTradeDateOrContractMonth,
                                'strike': details[0].contract.strike,
                                'right': details[0].contract.right,
                                'multiplier': details[0].contract.multiplier,
                                'trading_class': details[0].contract.tradingClass,
                                'market_name': details[0].marketName,
                                'min_tick': details[0].minTick,
                                'order_types': details[0].orderTypes,
                                'valid_exchanges': details[0].validExchanges,
                                'long_name': details[0].longName,
                                'contract_month': details[0].contractMonth,
                                'time_zone_id': details[0].timeZoneId,
                                'trading_hours': details[0].tradingHours,
                                'liquid_hours': details[0].liquidHours
                            })
            
            return options
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get option chain: {str(e)}")

    def get_market_data(self, symbol: str, include_pre_post: bool = False) -> Dict[str, Any]:
        """Get real-time market data for a symbol using IBKR"""
        contract = None
        try:
            # Create a Stock contract
            contract = Stock(symbol, 'SMART', 'USD')
            
            # Request market data
            self._ib.reqMktData(contract, '', False, include_pre_post)
            
            # Wait for data to arrive
            timeout = 5  # seconds
            start_time = datetime.now(timezone.utc)
            
            while (datetime.now(timezone.utc) - start_time).seconds < timeout:
                if contract.marketPrice():
                    return {
                        'symbol': symbol,
                        'price': contract.marketPrice(),
                        'bid': contract.bid,
                        'ask': contract.ask,
                        'last': contract.last,
                        'high': contract.high,
                        'low': contract.low,
                        'volume': contract.volume,
                        'close': contract.close,
                        'open': contract.open,
                        'bid_size': contract.bidSize,
                        'ask_size': contract.askSize,
                        'last_size': contract.lastSize,
                        'high_limit': contract.highLimit,
                        'low_limit': contract.lowLimit,
                        'vwap': contract.vwap,
                        'timestamp': datetime.now(timezone.utc)
                    }
                self._ib.sleep(0.1)
            
            raise HTTPException(status_code=408, detail="Timeout waiting for market data")
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get market data: {str(e)}")
        finally:
            # Cancel market data subscription
            if contract:
                self._ib.cancelMktData(contract)

    def get_market_depth(self, symbol: str, num_rows: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Get market depth data for a symbol using IBKR"""
        contract = None
        try:
            # Create a Stock contract
            contract = Stock(symbol, 'SMART', 'USD')
            
            # Request market depth
            self._ib.reqMktDepth(contract, num_rows)
            
            # Wait for data to arrive
            timeout = 5  # seconds
            start_time = datetime.now(timezone.utc)
            
            while (datetime.now(timezone.utc) - start_time).seconds < timeout:
                if contract.depthBids and contract.depthAsks:
                    return {
                        'bids': [{
                            'price': bid.price,
                            'size': bid.size,
                            'market_maker': bid.marketMaker
                        } for bid in contract.depthBids],
                        'asks': [{
                            'price': ask.price,
                            'size': ask.size,
                            'market_maker': ask.marketMaker
                        } for ask in contract.depthAsks]
                    }
                self._ib.sleep(0.1)
            
            raise HTTPException(status_code=408, detail="Timeout waiting for market depth")
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get market depth: {str(e)}")
        finally:
            # Cancel market depth subscription
            if contract:
                self._ib.cancelMktDepth(contract)

    def get_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """Get fundamental data for a symbol using IBKR"""
        try:
            # Create a Stock contract
            contract = Stock(symbol, 'SMART', 'USD')
            
            # Request fundamental data
            data = self._ib.reqFundamentalData(contract, 'ReportSnapshot')
            
            if not data:
                raise HTTPException(status_code=404, detail=f"No fundamental data found for {symbol}")
            
            # Parse XML data
            # Note: This is a simplified example. You might want to use a proper XML parser
            return {
                'symbol': symbol,
                'data': data
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get fundamental data: {str(e)}")

    def get_corporate_actions(self, symbol: str) -> List[Dict[str, Any]]:
        """Get corporate actions (dividends, splits) for a symbol using IBKR"""
        try:
            # Create a Stock contract
            contract = Stock(symbol, 'SMART', 'USD')
            
            # Request corporate actions
            actions = self._ib.reqContractDetails(contract)
            
            if not actions:
                raise HTTPException(status_code=404, detail=f"No corporate actions found for {symbol}")
            
            # Extract corporate actions
            corporate_actions = []
            for action in actions:
                if action.contractDetails:
                    if action.contractDetails.dividends:
                        corporate_actions.append({
                            'type': 'DIVIDEND',
                            'amount': action.contractDetails.dividends.amount,
                            'currency': action.contractDetails.dividends.currency,
                            'date': action.contractDetails.dividends.date
                        })
                    if action.contractDetails.splits:
                        corporate_actions.append({
                            'type': 'SPLIT',
                            'ratio': action.contractDetails.splits.ratio,
                            'date': action.contractDetails.splits.date
                        })
            
            return corporate_actions
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get corporate actions: {str(e)}")

    def get_account_equity(self) -> float:
        """Fetch the real account equity (NetLiquidation) from IBKR."""
        try:
            account = self._ib.accountSummary()
            net_liquidation = float(next((item.value for item in account if item.tag == 'NetLiquidation'), 0))
            if net_liquidation <= 0:
                raise HTTPException(status_code=400, detail="Account equity not available or zero.")
            return net_liquidation
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch account equity: {str(e)}")

    def __del__(self):
        """Cleanup IBKR connection and subscriptions"""
        if self._ib and self._ib.isConnected():
            # Unsubscribe from all market data
            for contract in self._ib.contracts():
                if contract.conId in self._active_subscriptions:
                    self._unsubscribe_market_data(contract)
            self._ib.disconnect() 