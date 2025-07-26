from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, CheckConstraint, and_, or_, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base

class ExchangeType(enum.Enum):
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    CBOE = "CBOE"
    SMART = "SMART"

class OrderType(enum.Enum):
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    TRAILING_STOP = "TRAILING_STOP"

class ProductType(enum.Enum):
    MARGIN = "MARGIN"
    CASH = "CASH"

class OrderSide(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class SignalStatus(enum.Enum):
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

class MarketSession(enum.Enum):
    REGULAR = "REGULAR"
    PRE_MARKET = "PRE_MARKET"
    POST_MARKET = "POST_MARKET"

class SignalGeneration(Base):
    __tablename__ = "signal_generation"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    symbol = Column(String, nullable=False)
    exchange = Column(Enum(ExchangeType), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    product_type = Column(Enum(ProductType), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    contract_size = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    status = Column(Enum(SignalStatus), nullable=False, default=SignalStatus.PENDING)
    market_session = Column(Enum(MarketSession), nullable=False, default=MarketSession.REGULAR)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="signal_generations")
    strategy = relationship("Strategy", back_populates="signal_generations")
    trades = relationship("Trade", back_populates="signal")

    # Constants
    MIN_QUANTITY = 1  # Minimum order quantity
    MAX_QUANTITY = 1000000  # Maximum order quantity
    TICK_SIZE = 0.01  # Minimum price increment

    # Constraints
    __table_args__ = (
        # Unique constraint to prevent duplicate signals
        UniqueConstraint(
            'user_id', 'strategy_id', 'symbol', 'created_at',
            name='uq_signal_generation'
        ),
        
        # Basic positive value constraints
        CheckConstraint('contract_size > 0', name='check_contract_size_positive'),
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        
        # Quantity must be a multiple of contract size
        CheckConstraint(
            'MOD(quantity, contract_size) = 0',
            name='check_quantity_multiple_of_contract_size'
        ),
        
        # Minimum and maximum quantity constraints
        CheckConstraint(
            f'quantity >= {MIN_QUANTITY}',
            name='check_min_quantity'
        ),
        CheckConstraint(
            f'quantity <= {MAX_QUANTITY}',
            name='check_max_quantity'
        ),
        
        # Price constraints that only apply when values are not null
        CheckConstraint(
            '(entry_price IS NULL) OR (entry_price > 0)',
            name='check_entry_price_positive'
        ),
        CheckConstraint(
            '(stop_loss IS NULL) OR (stop_loss > 0)',
            name='check_stop_loss_positive'
        ),
        CheckConstraint(
            '(take_profit IS NULL) OR (take_profit > 0)',
            name='check_take_profit_positive'
        ),
        
        # Price must be a multiple of tick size
        CheckConstraint(
            f'(entry_price IS NULL) OR (MOD(entry_price, {TICK_SIZE}) = 0)',
            name='check_entry_price_tick_size'
        ),
        CheckConstraint(
            f'(stop_loss IS NULL) OR (MOD(stop_loss, {TICK_SIZE}) = 0)',
            name='check_stop_loss_tick_size'
        ),
        CheckConstraint(
            f'(take_profit IS NULL) OR (MOD(take_profit, {TICK_SIZE}) = 0)',
            name='check_take_profit_tick_size'
        ),
        
        # Entry price required for LIMIT and STOP_LIMIT orders
        CheckConstraint(
            '(order_type NOT IN (\'LIMIT\', \'STOP_LIMIT\')) OR (entry_price IS NOT NULL)',
            name='check_entry_price_required'
        ),
        
        # Price relationship constraints for BUY orders
        CheckConstraint(
            '(side != \'BUY\') OR (entry_price IS NULL) OR (stop_loss IS NULL) OR (stop_loss < entry_price)',
            name='check_buy_stop_loss_below_entry'
        ),
        CheckConstraint(
            '(side != \'BUY\') OR (entry_price IS NULL) OR (take_profit IS NULL) OR (take_profit > entry_price)',
            name='check_buy_take_profit_above_entry'
        ),
        
        # Price relationship constraints for SELL orders
        CheckConstraint(
            '(side != \'SELL\') OR (entry_price IS NULL) OR (stop_loss IS NULL) OR (stop_loss > entry_price)',
            name='check_sell_stop_loss_above_entry'
        ),
        CheckConstraint(
            '(side != \'SELL\') OR (entry_price IS NULL) OR (take_profit IS NULL) OR (take_profit < entry_price)',
            name='check_sell_take_profit_below_entry'
        ),
        
        # Pre/post market validation
        CheckConstraint(
            '(market_session != \'PRE_MARKET\') OR (exchange IN (\'NASDAQ\', \'NYSE\'))',
            name='check_pre_market_exchange'
        ),
        CheckConstraint(
            '(market_session != \'POST_MARKET\') OR (exchange IN (\'NASDAQ\', \'NYSE\'))',
            name='check_post_market_exchange'
        ),
    )

    class Config:
        orm_mode = True 