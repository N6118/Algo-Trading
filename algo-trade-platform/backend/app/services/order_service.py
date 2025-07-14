from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ib_insync import IB, Stock, MarketOrder, LimitOrder, StopOrder, StopLimitOrder, BracketOrder, TrailingStopOrder, OCOOrder
from datetime import datetime, timedelta
import time
from threading import Lock
from enum import Enum
from collections import deque

from app.models.signal_generation import ExchangeType, OrderType, ProductType, OrderSide

class TimeInForce(Enum):
    DAY = "DAY"
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill

class OrderRouting(Enum):
    SMART = "SMART"
    DIRECT = "DIRECT"
    ARCA = "ARCA"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    CBOE = "CBOE"

class OrderAllocation(Enum):
    FIFO = "FIFO"  # First In, First Out
    LIFO = "LIFO"  # Last In, First Out
    PRO_RATA = "PRO_RATA"  # Proportional allocation

class OrderService:
    _instance = None
    _lock = Lock()
    _ib = None
    _last_connection_attempt = None
    _connection_retry_delay = 5  # seconds
    _max_retries = 3
    _pdt_threshold = 25000  # $25,000 PDT threshold
    _pdt_window = 5  # 5 business days
    _reg_t_margin_requirement = 0.5  # 50% Reg-T margin requirement
    
    # Order limits
    _min_order_size = 1  # Minimum order size
    _max_order_size = 1000000  # Maximum order size
    _min_order_price = 0.01  # Minimum order price
    _max_order_price = 1000000  # Maximum order price
    _max_orders_per_minute = 50  # Maximum orders per minute
    _order_timeout = 30  # seconds to wait for order completion
    
    # Order tracking
    _order_history = deque(maxlen=1000)  # Track last 1000 orders
    _order_timestamps = deque(maxlen=_max_orders_per_minute)  # Track order timestamps for rate limiting

    def __new__(cls, db: Session):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(OrderService, cls).__new__(cls)
                cls._instance.db = db
                cls._instance._connect_ibkr()
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
                    self._ib.connect('127.0.0.1', 7497, clientId=2)  # Different clientId than market data
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
        elif errorCode == 10182:  # Order rejected
            raise HTTPException(status_code=400, detail=f"Order rejected: {errorString}")
        elif errorCode == 10183:  # Order rejected - PDT rule violation
            raise HTTPException(status_code=400, detail="Order rejected: Pattern Day Trader rule violation")
        elif errorCode == 10184:  # Order rejected - Reg-T margin violation
            raise HTTPException(status_code=400, detail="Order rejected: Reg-T margin requirement violation")
        elif errorCode == 10185:  # Order rejected - Order size limit
            raise HTTPException(status_code=400, detail="Order rejected: Order size limit exceeded")
        elif errorCode == 10186:  # Order rejected - Order price limit
            raise HTTPException(status_code=400, detail="Order rejected: Order price limit exceeded")
        elif errorCode == 10187:  # Order rejected - Order frequency limit
            raise HTTPException(status_code=429, detail="Order rejected: Order frequency limit exceeded")
        else:
            raise HTTPException(status_code=500, detail=f"IBKR error {errorCode}: {errorString}")

    def _check_order_limits(self, quantity: int, price: float = None) -> None:
        """Check if order limits are violated"""
        # Check order size
        if quantity < self._min_order_size:
            raise HTTPException(status_code=400, detail=f"Order size {quantity} is below minimum {self._min_order_size}")
        if quantity > self._max_order_size:
            raise HTTPException(status_code=400, detail=f"Order size {quantity} exceeds maximum {self._max_order_size}")
        
        # Check order price if provided
        if price is not None:
            if price < self._min_order_price:
                raise HTTPException(status_code=400, detail=f"Order price {price} is below minimum {self._min_order_price}")
            if price > self._max_order_price:
                raise HTTPException(status_code=400, detail=f"Order price {price} exceeds maximum {self._max_order_price}")
        
        # Check order frequency
        current_time = time.time()
        # Remove timestamps older than 1 minute
        while self._order_timestamps and current_time - self._order_timestamps[0] > 60:
            self._order_timestamps.popleft()
        
        if len(self._order_timestamps) >= self._max_orders_per_minute:
            raise HTTPException(status_code=429, detail=f"Order frequency limit of {self._max_orders_per_minute} orders per minute exceeded")
        
        # Add current timestamp
        self._order_timestamps.append(current_time)

    def _check_pdt_rules(self) -> bool:
        """Check if PDT rules are violated"""
        try:
            # Get account summary
            account = self._ib.accountSummary()
            
            # Get net liquidation value
            net_liquidation = float(next((item.value for item in account if item.tag == 'NetLiquidation'), 0))
            
            # Get day trades in last 5 business days
            day_trades = self._ib.reqCompletedOrders(False)
            recent_trades = [trade for trade in day_trades 
                           if trade.orderStatus.status == 'Filled' 
                           and (datetime.now() - trade.orderStatus.completedTime).days <= self._pdt_window]
            
            # Count day trades (buy and sell on same day)
            day_trade_count = len(set(trade.order.orderId for trade in recent_trades))
            
            # Check PDT rules
            if net_liquidation < self._pdt_threshold and day_trade_count >= 4:
                return False
            
            return True
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to check PDT rules: {str(e)}")

    def _check_reg_t_margin(self, order_value: float) -> bool:
        """Check if Reg-T margin requirements are met"""
        try:
            # Get account summary
            account = self._ib.accountSummary()
            
            # Get available funds
            available_funds = float(next((item.value for item in account if item.tag == 'AvailableFunds'), 0))
            
            # Check if we have enough margin
            required_margin = order_value * self._reg_t_margin_requirement
            return available_funds >= required_margin
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to check Reg-T margin: {str(e)}")

    def _create_ibkr_order(self, order_type: OrderType, side: OrderSide, quantity: int, 
                          price: float = None, stop_price: float = None, 
                          trailing_percent: float = None, time_in_force: TimeInForce = TimeInForce.DAY,
                          routing: OrderRouting = OrderRouting.SMART) -> Any:
        """Create an IBKR order object based on order type"""
        # Check order limits
        self._check_order_limits(quantity, price)
        
        action = "BUY" if side == OrderSide.BUY else "SELL"
        
        if order_type == OrderType.MARKET:
            order = MarketOrder(action, quantity)
        elif order_type == OrderType.LIMIT:
            if not price:
                raise HTTPException(status_code=400, detail="Limit price required for LIMIT orders")
            order = LimitOrder(action, quantity, price)
        elif order_type == OrderType.STOP:
            if not stop_price:
                raise HTTPException(status_code=400, detail="Stop price required for STOP orders")
            order = StopOrder(action, quantity, stop_price)
        elif order_type == OrderType.STOP_LIMIT:
            if not price or not stop_price:
                raise HTTPException(status_code=400, detail="Both limit price and stop price required for STOP_LIMIT orders")
            order = StopLimitOrder(action, quantity, price, stop_price)
        elif order_type == OrderType.TRAILING_STOP:
            if not trailing_percent:
                raise HTTPException(status_code=400, detail="Trailing percent required for TRAILING_STOP orders")
            order = TrailingStopOrder(action, quantity, trailing_percent)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported order type: {order_type}")
        
        # Set time in force
        order.tif = time_in_force.value
        
        # Set routing
        order.exchange = routing.value
        
        return order

    def _wait_for_order_completion(self, trade, timeout: int = None) -> None:
        """Wait for order completion with timeout"""
        if timeout is None:
            timeout = self._order_timeout
            
        start_time = time.time()
        while not trade.isDone():
            if time.time() - start_time > timeout:
                raise HTTPException(status_code=408, detail=f"Order completion timeout after {timeout} seconds")
            self._ib.sleep(0.1)

    def create_bracket_order(self, order_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a bracket order (entry + stop loss + take profit) using IBKR"""
        try:
            # Create the contract
            contract = Stock(
                order_params['symbol'],
                order_params['exchange'].value,
                'USD'
            )

            # Calculate order value
            order_value = order_params['quantity'] * order_params['entry_price']

            # Check PDT rules
            if not self._check_pdt_rules():
                raise HTTPException(status_code=400, detail="Pattern Day Trader rule violation")

            # Check Reg-T margin
            if not self._check_reg_t_margin(order_value):
                raise HTTPException(status_code=400, detail="Insufficient margin for order")

            # Create the bracket order
            bracket = BracketOrder(
                parent=self._create_ibkr_order(
                    order_type=order_params['order_type'],
                    side=order_params['side'],
                    quantity=order_params['quantity'],
                    price=order_params.get('entry_price'),
                    time_in_force=order_params.get('time_in_force', TimeInForce.DAY),
                    routing=order_params.get('routing', OrderRouting.SMART)
                ),
                takeProfit=LimitOrder(
                    "SELL" if order_params['side'] == OrderSide.BUY else "BUY",
                    order_params['quantity'],
                    order_params['take_profit'],
                    tif=order_params.get('time_in_force', TimeInForce.GTC).value,
                    exchange=order_params.get('routing', OrderRouting.SMART).value
                ),
                stopLoss=StopOrder(
                    "SELL" if order_params['side'] == OrderSide.BUY else "BUY",
                    order_params['quantity'],
                    order_params['stop_loss'],
                    tif=order_params.get('time_in_force', TimeInForce.GTC).value,
                    exchange=order_params.get('routing', OrderRouting.SMART).value
                )
            )

            # Place the bracket order
            trades = self._ib.placeOrder(contract, bracket)
            
            # Wait for orders to be submitted
            for trade in trades:
                self._wait_for_order_completion(trade)

            # Add to order history
            self._order_history.append({
                'id': trades[0].order.orderId,
                'type': 'BRACKET',
                'symbol': order_params['symbol'],
                'quantity': order_params['quantity'],
                'created_at': datetime.utcnow()
            })

            # Return order details
            return {
                "id": trades[0].order.orderId,
                "status": trades[0].orderStatus.status,
                "symbol": order_params['symbol'],
                "quantity": order_params['quantity'],
                "entry_price": order_params.get('entry_price'),
                "stop_loss": order_params['stop_loss'],
                "take_profit": order_params['take_profit'],
                "order_type": order_params['order_type'].value,
                "side": order_params['side'].value,
                "exchange": order_params['exchange'].value,
                "time_in_force": order_params.get('time_in_force', TimeInForce.DAY).value,
                "routing": order_params.get('routing', OrderRouting.SMART).value,
                "created_at": datetime.utcnow()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create bracket order: {str(e)}")

    def create_oco_order(self, order_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create an OCO (One Cancels Other) order using IBKR"""
        try:
            # Create the contract
            contract = Stock(
                order_params['symbol'],
                order_params['exchange'].value,
                'USD'
            )

            # Calculate order value
            order_value = order_params['quantity'] * order_params['entry_price']

            # Check PDT rules
            if not self._check_pdt_rules():
                raise HTTPException(status_code=400, detail="Pattern Day Trader rule violation")

            # Check Reg-T margin
            if not self._check_reg_t_margin(order_params['quantity'] * order_params['take_profit']):
                raise HTTPException(status_code=400, detail="Insufficient margin for order")

            # Create the OCO order
            oco = OCOOrder(
                self._create_ibkr_order(
                    order_type=OrderType.LIMIT,
                    side=order_params['side'],
                    quantity=order_params['quantity'],
                    price=order_params['take_profit'],
                    time_in_force=order_params.get('time_in_force', TimeInForce.GTC),
                    routing=order_params.get('routing', OrderRouting.SMART)
                ),
                self._create_ibkr_order(
                    order_type=OrderType.STOP,
                    side=order_params['side'],
                    quantity=order_params['quantity'],
                    stop_price=order_params['stop_loss'],
                    time_in_force=order_params.get('time_in_force', TimeInForce.GTC),
                    routing=order_params.get('routing', OrderRouting.SMART)
                )
            )

            # Place the OCO order
            trades = self._ib.placeOrder(contract, oco)
            
            # Wait for orders to be submitted
            for trade in trades:
                while not trade.isDone():
                    self._ib.sleep(0.1)

            # Return order details
            return {
                "id": trades[0].order.orderId,
                "status": trades[0].orderStatus.status,
                "symbol": order_params['symbol'],
                "quantity": order_params['quantity'],
                "take_profit": order_params['take_profit'],
                "stop_loss": order_params['stop_loss'],
                "order_type": "OCO",
                "side": order_params['side'].value,
                "exchange": order_params['exchange'].value,
                "time_in_force": order_params.get('time_in_force', TimeInForce.GTC).value,
                "routing": order_params.get('routing', OrderRouting.SMART).value,
                "created_at": datetime.utcnow()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create OCO order: {str(e)}")

    def create_order(self, order_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new order using IBKR"""
        try:
            # Create the contract
            contract = Stock(
                order_params['symbol'],
                order_params['exchange'].value,
                'USD'
            )

            # Calculate order value
            order_value = order_params['quantity'] * (order_params.get('price', 0) or order_params.get('stop_price', 0))

            # Check PDT rules
            if not self._check_pdt_rules():
                raise HTTPException(status_code=400, detail="Pattern Day Trader rule violation")

            # Check Reg-T margin
            if not self._check_reg_t_margin(order_value):
                raise HTTPException(status_code=400, detail="Insufficient margin for order")

            # Create the order
            order = self._create_ibkr_order(
                order_type=order_params['order_type'],
                side=order_params['side'],
                quantity=order_params['quantity'],
                price=order_params.get('price'),
                stop_price=order_params.get('stop_price'),
                trailing_percent=order_params.get('trailing_percent'),
                time_in_force=order_params.get('time_in_force', TimeInForce.DAY),
                routing=order_params.get('routing', OrderRouting.SMART)
            )

            # Place the order
            trade = self._ib.placeOrder(contract, order)
            
            # Wait for order to be submitted
            while not trade.isDone():
                self._ib.sleep(0.1)

            # Return order details
            return {
                "id": trade.order.orderId,
                "status": trade.orderStatus.status,
                "symbol": order_params['symbol'],
                "quantity": order_params['quantity'],
                "price": order_params.get('price'),
                "stop_price": order_params.get('stop_price'),
                "trailing_percent": order_params.get('trailing_percent'),
                "order_type": order_params['order_type'].value,
                "side": order_params['side'].value,
                "exchange": order_params['exchange'].value,
                "time_in_force": order_params.get('time_in_force', TimeInForce.DAY).value,
                "routing": order_params.get('routing', OrderRouting.SMART).value,
                "created_at": datetime.utcnow()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")

    def modify_order(self, order_id: int, order_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Modify an existing order using IBKR"""
        try:
            # Get the order
            trade = self._ib.trades()[order_id]
            if not trade:
                raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

            # Update order parameters
            if 'quantity' in order_params:
                trade.order.totalQuantity = order_params['quantity']
            if 'price' in order_params:
                trade.order.lmtPrice = order_params['price']
            if 'stop_price' in order_params:
                trade.order.auxPrice = order_params['stop_price']
            if 'trailing_percent' in order_params:
                trade.order.trailingPercent = order_params['trailing_percent']
            if 'time_in_force' in order_params:
                trade.order.tif = order_params['time_in_force'].value
            if 'routing' in order_params:
                trade.order.exchange = order_params['routing'].value

            # Modify the order
            self._ib.placeOrder(trade.contract, trade.order)
            
            # Wait for order to be modified
            while not trade.isDone():
                self._ib.sleep(0.1)

            # Return updated order details
            return {
                "id": trade.order.orderId,
                "status": trade.orderStatus.status,
                "symbol": trade.contract.symbol,
                "quantity": trade.order.totalQuantity,
                "price": trade.order.lmtPrice,
                "stop_price": trade.order.auxPrice,
                "trailing_percent": trade.order.trailingPercent,
                "order_type": trade.order.orderType,
                "side": trade.order.action,
                "exchange": trade.contract.exchange,
                "time_in_force": trade.order.tif,
                "routing": trade.order.exchange,
                "updated_at": datetime.utcnow()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to modify order: {str(e)}")

    def cancel_order(self, order_id: int) -> bool:
        """Cancel an existing order using IBKR"""
        try:
            # Get the order
            trade = self._ib.trades()[order_id]
            if not trade:
                raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

            # Cancel the order
            self._ib.cancelOrder(trade.order)
            
            # Wait for order to be cancelled
            while not trade.isDone():
                self._ib.sleep(0.1)

            return True
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to cancel order: {str(e)}")

    def get_order_status(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get the status of an order using IBKR"""
        try:
            # Get the order
            trade = self._ib.trades()[order_id]
            if not trade:
                raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

            # Return order status
            return {
                "id": trade.order.orderId,
                "status": trade.orderStatus.status,
                "filled": trade.orderStatus.filled,
                "remaining": trade.orderStatus.remaining,
                "avg_fill_price": trade.orderStatus.avgFillPrice,
                "last_fill_price": trade.orderStatus.lastFillPrice,
                "why_held": trade.orderStatus.whyHeld,
                "created_at": trade.orderStatus.submitTime,
                "updated_at": trade.orderStatus.updateTime
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get order status: {str(e)}")

    def __del__(self):
        """Cleanup IBKR connection"""
        if self._ib and self._ib.isConnected():
            self._ib.disconnect() 