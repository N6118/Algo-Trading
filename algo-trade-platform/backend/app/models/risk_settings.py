from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, UniqueConstraint, String, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class RiskSettings(Base):
    __tablename__ = "risk_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True, index=True)
    max_active_trades = Column(Integer, nullable=False, default=10)
    max_trades_per_day = Column(Integer, nullable=False, default=20)
    max_risk_per_trade_pct = Column(Float, nullable=False, default=0.02)
    max_total_risk_pct = Column(Float, nullable=False, default=0.05)
    rm_max_sp = Column(Float, nullable=False, default=0.2)  # Max drawdown percent (e.g., 0.2 = 20%)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'strategy_id', name='uq_risk_settings_user_strategy'),
    )

class UniversalSettings(Base):
    __tablename__ = "universal_settings"

    id = Column(Integer, primary_key=True, index=True)
    capital = Column(Float, nullable=False, default=100000.0)
    open_time = Column(String, nullable=False, default="09:30")  # ET, stored as string (HH:MM)
    close_time = Column(String, nullable=False, default="16:00")  # ET
    pre_market_time = Column(String, nullable=False, default="04:00-09:30")  # ET
    post_market_time = Column(String, nullable=False, default="16:00-20:00")  # ET
    holiday_calendar = Column(JSON, nullable=True)  # List of holiday dates/half-days
    ss_option_category_split = Column(String, nullable=True)  # e.g., "200 to 100 - ITM for CALL/PUT"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 