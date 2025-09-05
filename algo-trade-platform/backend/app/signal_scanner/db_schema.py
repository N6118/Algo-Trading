"""
Signal Scanner Database Schema

This module defines the database schema for the signal scanning framework,
including tables for signal configurations and generated signals.
"""

import os
import sys
import logging
from urllib.parse import quote_plus as urlquote
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Base class for SQLAlchemy models
Base = declarative_base()

# Signal Configuration Model
class SignalConfig(Base):
    """Configuration for a signal scanning strategy"""
    __tablename__ = 'signal_configs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Signal type and scheduling
    signal_type = Column(Enum('Intraday', 'Positional', name='signal_type_enum'), nullable=False)
    expiry = Column(Enum('Daily', 'Weekly', 'Monthly', name='expiry_enum'), nullable=False)
    trading_days = Column(String(50), default='Mon,Tue,Wed,Thu,Fri')  # Comma-separated days
    start_time = Column(String(8), default='09:30')  # Format: HH:MM in ET
    end_time = Column(String(8), default='16:00')  # Format: HH:MM in ET
    scan_interval_minutes = Column(Integer, default=15)  # How often to scan
    
    # Signal parameters
    max_signals_per_day = Column(Integer, default=5)
    signal_direction = Column(Enum('Long', 'Short', 'Both', name='direction_enum'), default='Both')
    instrument_type = Column(Enum('Stock', 'Option', 'Future', 'ETF', name='instrument_enum'), default='Stock')
    option_type = Column(Enum('CALL', 'PUT', 'Both', name='option_type_enum'), default='Both')
    option_category = Column(Enum('ITM', 'OTM', 'ATM', 'DITM', 'DOTM', 'Any', name='option_category_enum'), default='Any')
    
    # Execution mode
    mode = Column(Enum('Live', 'Virtual', 'Backtest', name='mode_enum'), default='Virtual')
    is_active = Column(Boolean, default=True)
    
    # Relationships
    symbols = relationship("SignalSymbol", back_populates="config", cascade="all, delete-orphan")
    entry_rules = relationship("SignalEntryRule", back_populates="config", cascade="all, delete-orphan")
    exit_rules = relationship("SignalExitRule", back_populates="config", cascade="all, delete-orphan")
    signals = relationship("GeneratedSignal", back_populates="config", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_signal_config_active', 'is_active'),
        Index('idx_signal_config_type', 'signal_type'),
    )
    
    def __repr__(self):
        return f"<SignalConfig(id={self.id}, name='{self.name}', type='{self.signal_type}')>"


class SignalSymbol(Base):
    """Symbols to be used in a signal configuration"""
    __tablename__ = 'signal_symbols'
    
    id = Column(Integer, primary_key=True)
    config_id = Column(Integer, ForeignKey('signal_configs.id'), nullable=False)
    symbol = Column(String(20), nullable=False)
    token = Column(Integer)  # Exchange token/ID for the symbol
    is_primary = Column(Boolean, default=False)  # Primary symbol for the strategy
    timeframe = Column(String(10), default='15min')  # Timeframe to use for this symbol
    weight = Column(Float, default=1.0)  # Weight for correlation calculation
    
    # Relationships
    config = relationship("SignalConfig", back_populates="symbols")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_signal_symbol_config', 'config_id'),
        Index('idx_signal_symbol_symbol', 'symbol'),
        Index('idx_signal_symbol_primary', 'is_primary'),
        UniqueConstraint('config_id', 'symbol', name='uq_signal_symbol_config_symbol'),
        CheckConstraint('weight >= 0 AND weight <= 1', name='chk_signal_symbol_weight')
    )
    
    def __repr__(self):
        return f"<SignalSymbol(symbol='{self.symbol}', is_primary={self.is_primary})>"


class SignalEntryRule(Base):
    """Entry rules for signal generation"""
    __tablename__ = 'signal_entry_rules'
    
    id = Column(Integer, primary_key=True)
    config_id = Column(Integer, ForeignKey('signal_configs.id'), nullable=False)
    rule_type = Column(Enum('PriceAbove', 'PriceBelow', 'CrossAbove', 'CrossBelow', 
                           'Correlation', 'RSI', 'MACD', 'Custom', name='rule_type_enum'), nullable=False)
    symbol = Column(String(20), nullable=False)
    parameter = Column(String(50), nullable=False)  # e.g., 'SH', 'SL', 'MA50', etc.
    value = Column(Float)  # Optional value for comparison
    comparison = Column(String(10))  # e.g., '>', '<', '==', etc.
    timeframe = Column(String(10), default='15min')
    is_required = Column(Boolean, default=True)  # If false, this is an optional condition
    
    # For correlation rules
    correlated_symbol = Column(String(20))  # Only used for correlation rules
    correlation_lookback = Column(Integer, default=10)  # Periods to look back for correlation
    correlation_threshold = Column(Float, default=0.7)  # Threshold for correlation
    correlation_enabled = Column(Boolean, default=True)  # Whether to use correlation in signal generation
    
    # Relationships
    config = relationship("SignalConfig", back_populates="entry_rules")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_entry_rule_config', 'config_id'),
        Index('idx_entry_rule_symbol', 'symbol'),
        Index('idx_entry_rule_type', 'rule_type'),
        CheckConstraint('correlation_threshold >= 0 AND correlation_threshold <= 1', name='chk_entry_rule_correlation_threshold'),
        CheckConstraint('correlation_lookback > 0', name='chk_entry_rule_correlation_lookback')
    )
    
    def __repr__(self):
        return f"<SignalEntryRule(rule_type='{self.rule_type}', symbol='{self.symbol}', parameter='{self.parameter}')>"


class SignalExitRule(Base):
    """Exit rules for signal generation"""
    __tablename__ = 'signal_exit_rules'
    
    id = Column(Integer, primary_key=True)
    config_id = Column(Integer, ForeignKey('signal_configs.id'), nullable=False)
    rule_type = Column(Enum('PriceAbove', 'PriceBelow', 'CrossAbove', 'CrossBelow', 
                           'Correlation', 'RSI', 'MACD', 'TimeElapsed', 'Custom', 
                           name='exit_rule_type_enum'), nullable=False)
    symbol = Column(String(20), nullable=False)
    parameter = Column(String(50), nullable=False)  # e.g., 'SH', 'SL', 'MA50', etc.
    value = Column(Float)  # Optional value for comparison
    comparison = Column(String(10))  # e.g., '>', '<', '==', etc.
    timeframe = Column(String(10), default='15min')
    priority = Column(Integer, default=1)  # Priority order for exit rules
    
    # For time-based exits
    minutes_elapsed = Column(Integer)  # For time-based exit rules
    
    # Relationships
    config = relationship("SignalConfig", back_populates="exit_rules")
    
    # Indexes
    __table_args__ = (
        Index('idx_exit_rule_config', 'config_id'),
        Index('idx_exit_rule_symbol', 'symbol'),
        Index('idx_exit_rule_type', 'rule_type'),
    )
    
    def __repr__(self):
        return f"<SignalExitRule(rule_type='{self.rule_type}', symbol='{self.symbol}', parameter='{self.parameter}')>"


class GeneratedSignal(Base):
    """Signals generated by the scanner"""
    __tablename__ = 'generated_signals'
    
    id = Column(Integer, primary_key=True)
    config_id = Column(Integer, ForeignKey('signal_configs.id'), nullable=False)
    symbol = Column(String(20), nullable=False)
    token = Column(Integer)
    signal_time = Column(DateTime, default=datetime.utcnow)
    direction = Column(Enum('Long', 'Short', name='signal_direction_enum'), nullable=False)
    price = Column(Float)  # Price at signal generation
    timeframe = Column(String(10))
    
    # Signal status
    status = Column(Enum('New', 'Executed', 'Rejected', 'Expired', name='signal_status_enum'), default='New')
    executed_time = Column(DateTime)
    rejection_reason = Column(String(200))
    
    # Trade parameters
    stop_loss = Column(Float)
    take_profit = Column(Float)
    risk_reward_ratio = Column(Float)
    
    # Relationships
    config = relationship("SignalConfig", back_populates="signals")
    conditions = relationship("SignalCondition", back_populates="signal", cascade="all, delete-orphan")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_generated_signal_config', 'config_id'),
        Index('idx_generated_signal_symbol', 'symbol'),
        Index('idx_generated_signal_time', 'signal_time'),
        Index('idx_generated_signal_status', 'status'),
        Index('idx_generated_signal_config_time', 'config_id', 'signal_time'),
        CheckConstraint('price > 0', name='chk_generated_signal_price'),
        CheckConstraint('stop_loss > 0', name='chk_generated_signal_stop_loss'),
        CheckConstraint('take_profit > 0', name='chk_generated_signal_take_profit'),
        CheckConstraint('risk_reward_ratio > 0', name='chk_generated_signal_risk_reward')
    )
    
    def __repr__(self):
        return f"<GeneratedSignal(id={self.id}, symbol='{self.symbol}', direction='{self.direction}', status='{self.status}')>"


class SignalCondition(Base):
    """Conditions that triggered a signal"""
    __tablename__ = 'signal_conditions'
    
    id = Column(Integer, primary_key=True)
    signal_id = Column(Integer, ForeignKey('generated_signals.id'), nullable=False)
    rule_type = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False)
    parameter = Column(String(50), nullable=False)
    value = Column(Float)
    comparison = Column(String(10))
    result = Column(Boolean, default=True)  # Whether the condition was met
    
    # Relationships
    signal = relationship("GeneratedSignal", back_populates="conditions")
    
    # Indexes
    __table_args__ = (
        Index('idx_signal_condition_signal', 'signal_id'),
        Index('idx_signal_condition_symbol', 'symbol'),
    )
    
    def __repr__(self):
        return f"<SignalCondition(rule_type='{self.rule_type}', symbol='{self.symbol}', parameter='{self.parameter}')>"


def init_db():
    """Initialize the database with the signal scanning tables"""
    try:
        # Get database connection string from environment or use default
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
        
        # Create engine and tables
        engine = create_engine(uri)
        Base.metadata.create_all(engine)
        
        logger.info("Signal scanning database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing signal scanning database: {str(e)}")
        return False


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize the database
    success = init_db()
    if success:
        print("Signal scanning database tables created successfully")
    else:
        print("Failed to create signal scanning database tables")
