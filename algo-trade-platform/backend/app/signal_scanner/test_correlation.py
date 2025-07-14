"""
Test Correlation Strategy

This script tests the correlation strategy implementation by creating a sample
configuration and running it against market data.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus as urlquote

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import database models and correlation strategy
from backend.app.signal_scanner.db_schema import (
    SignalConfig, SignalSymbol, SignalEntryRule, SignalExitRule,
    GeneratedSignal, SignalCondition, Base
)
from backend.app.signal_scanner.correlation_strategy import CorrelationStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_config(session):
    """Create a test configuration for correlation strategy."""
    try:
        # Create signal configuration
        config = SignalConfig(
            name="Test Correlation Strategy",
            description="Test configuration for correlation-based trading strategy",
            signal_type="Intraday",
            expiry="Daily",
            trading_days="Monday,Tuesday,Wednesday,Thursday,Friday",
            start_time="09:30",
            end_time="16:00",
            scan_interval_minutes=15,
            max_signals_per_day=5,
            signal_direction="Both",
            instrument_type="Stock",
            is_active=True
        )
        session.add(config)
        session.flush()
        
        # Add primary symbol (e.g., SPY)
        primary_symbol = SignalSymbol(
            config_id=config.id,
            symbol="SPY",
            is_primary=True,
            timeframe="15min",
            weight=1.0
        )
        session.add(primary_symbol)
        
        # Add correlated symbol (e.g., QQQ)
        correlated_symbol = SignalSymbol(
            config_id=config.id,
            symbol="QQQ",
            is_primary=False,
            timeframe="15min",
            weight=1.0
        )
        session.add(correlated_symbol)
        
        # Add entry rules
        entry_rules = [
            SignalEntryRule(
                config_id=config.id,
                rule_type="PriceAbove",
                symbol="SPY",
                parameter="sh_price",
                is_required=True
            ),
            SignalEntryRule(
                config_id=config.id,
                rule_type="PriceBelow",
                symbol="QQQ",
                parameter="sl_price",
                is_required=True
            )
        ]
        session.add_all(entry_rules)
        
        # Add exit rules
        exit_rules = [
            SignalExitRule(
                config_id=config.id,
                rule_type="PriceBelow",
                symbol="SPY",
                parameter="sl_price",
                is_required=True
            ),
            SignalExitRule(
                config_id=config.id,
                rule_type="PriceAbove",
                symbol="QQQ",
                parameter="sh_price",
                is_required=True
            )
        ]
        session.add_all(exit_rules)
        
        session.commit()
        logger.info("Test configuration created successfully")
        return config
        
    except Exception as e:
        logger.error(f"Error creating test configuration: {str(e)}")
        session.rollback()
        return None

def test_correlation_strategy():
    """Test the correlation strategy with sample data."""
    try:
        # Set up database connection
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@139.59.38.207:5432/theostock")
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        
        # Create test configuration
        session = Session()
        config = create_test_config(session)
        session.close()
        
        if not config:
            logger.error("Failed to create test configuration")
            return
        
        # Initialize correlation strategy
        strategy = CorrelationStrategy()
        
        # Generate signals
        signals = strategy.generate_signal(config)
        
        if signals:
            logger.info(f"Generated {len(signals)} signals:")
            for signal in signals:
                logger.info(f"Signal: {signal.symbol} {signal.direction} at {signal.price}")
                logger.info(f"Stop Loss: {signal.stop_loss}")
                logger.info(f"Take Profit: {signal.take_profit}")
                logger.info(f"Risk/Reward: {signal.risk_reward_ratio}")
        else:
            logger.info("No signals generated")
        
    except Exception as e:
        logger.error(f"Error testing correlation strategy: {str(e)}")

if __name__ == "__main__":
    test_correlation_strategy() 