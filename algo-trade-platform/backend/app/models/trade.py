from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base
from app.models.signal_generation import ExchangeType, OrderSide

class TradeStatus(enum.Enum):
    RUNNING = "RUNNING"
    CLOSED = "CLOSED"
    WAITING = "WAITING"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    signal_id = Column(Integer, ForeignKey("signal_generation.id"), nullable=True, index=True)
    symbol = Column(String, nullable=False)
    exchange = Column(Enum(ExchangeType), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    status = Column(Enum(TradeStatus), nullable=False, default=TradeStatus.RUNNING)
    pnl = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    risk_reduced = Column(Boolean, default=False)
    risk_reduction_qty = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")
    signal = relationship("SignalGeneration", back_populates="trades")

    __table_args__ = (
        UniqueConstraint('user_id', 'strategy_id', 'symbol', 'created_at', name='uq_trade'),
        CheckConstraint('quantity > 0', name='check_trade_quantity_positive'),
        CheckConstraint('entry_price > 0', name='check_trade_entry_price_positive'),
        CheckConstraint('(exit_price IS NULL) OR (exit_price > 0)', name='check_trade_exit_price_positive'),
        CheckConstraint('(stop_loss IS NULL) OR (stop_loss > 0)', name='check_trade_stop_loss_positive'),
        CheckConstraint('(take_profit IS NULL) OR (take_profit > 0)', name='check_trade_take_profit_positive'),
    )

    class Config:
        orm_mode = True 