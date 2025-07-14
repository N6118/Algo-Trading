from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, time
import pytz
from fastapi import HTTPException

from app.models.signal_generation import SignalGeneration, ExchangeType, OrderType, ProductType
from app.schemas.signal_generation import SignalGenerationCreate, SignalGenerationUpdate
from app.services.market_data_service import MarketDataService
from app.services.order_service import OrderService

class SignalGenerationService:
    def __init__(self, db: Session):
        self.db = db
        self.market_data_service = MarketDataService(db)
        self.order_service = OrderService(db)

    def create_signal(self, signal_data: SignalGenerationCreate) -> SignalGeneration:
        """Create a new signal generation entry"""
        db_signal = SignalGeneration(
            user_id=signal_data.user_id,
            strategy_id=signal_data.strategy_id,
            symbol=signal_data.symbol,
            exchange=signal_data.exchange,
            order_type=signal_data.order_type,
            product_type=signal_data.product_type,
            contract_size=signal_data.contract_size,
            quantity=signal_data.quantity,
            entry_price=signal_data.entry_price,
            stop_loss=signal_data.stop_loss,
            take_profit=signal_data.take_profit,
            status="PENDING"
        )
        self.db.add(db_signal)
        self.db.commit()
        self.db.refresh(db_signal)
        return db_signal

    def get_signal(self, signal_id: int) -> Optional[SignalGeneration]:
        """Get a signal by ID"""
        return self.db.query(SignalGeneration).filter(SignalGeneration.id == signal_id).first()

    def get_user_signals(self, user_id: int, skip: int = 0, limit: int = 100) -> List[SignalGeneration]:
        """Get all signals for a specific user"""
        return self.db.query(SignalGeneration)\
            .filter(SignalGeneration.user_id == user_id)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_active_signals(self) -> List[SignalGeneration]:
        """Get all active signals"""
        return self.db.query(SignalGeneration)\
            .filter(SignalGeneration.is_active == True)\
            .all()

    def update_signal(self, signal_id: int, signal_data: SignalGenerationUpdate) -> Optional[SignalGeneration]:
        """Update a signal"""
        db_signal = self.get_signal(signal_id)
        if not db_signal:
            return None

        update_data = signal_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_signal, key, value)

        db_signal.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_signal)
        return db_signal

    def deactivate_signal(self, signal_id: int) -> Optional[SignalGeneration]:
        """Deactivate a signal"""
        db_signal = self.get_signal(signal_id)
        if not db_signal:
            return None

        db_signal.is_active = False
        db_signal.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_signal)
        return db_signal

    def validate_signal(self, signal: SignalGeneration) -> bool:
        """Validate signal parameters"""
        try:
            # Check if symbol exists and is valid
            if not self.market_data_service.validate_symbol(signal.symbol):
                raise HTTPException(status_code=400, detail=f"Invalid symbol: {signal.symbol}")

            # Validate trading hours
            if not self._is_within_trading_hours(signal.exchange):
                raise HTTPException(status_code=400, detail="Outside trading hours")

            # Validate price ranges
            current_price = self.market_data_service.get_current_price(signal.symbol)
            if not current_price:
                raise HTTPException(status_code=400, detail="Unable to get current price")

            # Validate stop loss and take profit levels
            if signal.stop_loss and signal.stop_loss >= current_price:
                raise HTTPException(status_code=400, detail="Stop loss must be below current price")
            if signal.take_profit and signal.take_profit <= current_price:
                raise HTTPException(status_code=400, detail="Take profit must be above current price")

            # Validate order type against exchange
            if not self._is_valid_order_type_for_exchange(signal.order_type, signal.exchange):
                raise HTTPException(status_code=400, detail=f"Order type {signal.order_type} not supported for {signal.exchange}")

            # Validate contract size
            if signal.contract_size <= 0:
                raise HTTPException(status_code=400, detail="Contract size must be positive")

            # Validate quantity
            if signal.quantity <= 0:
                raise HTTPException(status_code=400, detail="Quantity must be positive")

            return True

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

    def process_signal(self, signal_id: int) -> bool:
        """Process a signal and generate orders"""
        try:
            signal = self.get_signal(signal_id)
            if not signal or not signal.is_active:
                return False

            if not self.validate_signal(signal):
                return False

            # Get current market data
            current_price = self.market_data_service.get_current_price(signal.symbol)
            if not current_price:
                raise HTTPException(status_code=400, detail="Unable to get current price")

            # Create main order
            order_params = {
                "symbol": signal.symbol,
                "exchange": signal.exchange,
                "order_type": signal.order_type,
                "quantity": signal.quantity,
                "price": current_price,
                "product_type": signal.product_type,
                "contract_size": signal.contract_size
            }

            # Place main order
            main_order = self.order_service.create_order(order_params)
            if not main_order:
                raise HTTPException(status_code=400, detail="Failed to create main order")

            # Create stop loss order if specified
            if signal.stop_loss:
                stop_loss_params = {
                    **order_params,
                    "order_type": OrderType.STOP,
                    "price": signal.stop_loss,
                    "parent_order_id": main_order.id
                }
                self.order_service.create_order(stop_loss_params)

            # Create take profit order if specified
            if signal.take_profit:
                take_profit_params = {
                    **order_params,
                    "order_type": OrderType.LIMIT,
                    "price": signal.take_profit,
                    "parent_order_id": main_order.id
                }
                self.order_service.create_order(take_profit_params)

            # Update signal status
            signal.status = "EXECUTED"
            signal.entry_price = current_price
            self.db.commit()

            return True

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

    def _is_within_trading_hours(self, exchange: ExchangeType) -> bool:
        """Check if current time is within trading hours for the exchange"""
        et = pytz.timezone('US/Eastern')
        current_time = datetime.now(et).time()
        
        # Regular market hours (9:30 AM - 4:00 PM ET)
        market_open = time(9, 30)
        market_close = time(16, 0)
        
        # Pre-market hours (4:00 AM - 9:30 AM ET)
        pre_market_open = time(4, 0)
        pre_market_close = time(9, 30)
        
        # Post-market hours (4:00 PM - 8:00 PM ET)
        post_market_open = time(16, 0)
        post_market_close = time(20, 0)

        return (market_open <= current_time <= market_close or
                pre_market_open <= current_time <= pre_market_close or
                post_market_open <= current_time <= post_market_close)

    def _is_valid_order_type_for_exchange(self, order_type: OrderType, exchange: ExchangeType) -> bool:
        """Validate if order type is supported by the exchange"""
        exchange_order_types = {
            ExchangeType.NYSE: [OrderType.MARKET, OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT],
            ExchangeType.NASDAQ: [OrderType.MARKET, OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT],
            ExchangeType.CBOE: [OrderType.MARKET, OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT],
            ExchangeType.SMART: [OrderType.MARKET, OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT]
        }
        return order_type in exchange_order_types.get(exchange, []) 