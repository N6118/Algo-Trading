"""
Initialize Signal Scanner Database

This script initializes the database tables for the signal scanner and creates a sample signal configuration.
"""

import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus as urlquote

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import database models
from backend.app.signal_scanner.db_schema import (
    Base, SignalConfig, SignalSymbol, SignalEntryRule, SignalExitRule
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database with the signal scanning tables"""
    try:
        # Get database connection string from environment or use default
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@139.59.38.207:5432/theostock")
        
        # Create engine and tables
        engine = create_engine(uri)
        Base.metadata.create_all(engine)
        
        logger.info("Signal scanning database tables created successfully")
        return engine
    except Exception as e:
        logger.error(f"Error initializing signal scanning database: {str(e)}")
        return None

def create_sample_config(engine):
    """Create a sample signal configuration"""
    if not engine:
        logger.error("Engine not available, cannot create sample configuration")
        return False
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if sample config already exists
        existing = session.query(SignalConfig).filter(SignalConfig.name == "Sample SH/SL Strategy").first()
        if existing:
            logger.info("Sample configuration already exists")
            return True
        
        # Create sample config
        config = SignalConfig(
            name="Sample SH/SL Strategy",
            description="A sample strategy that generates signals based on Swing High/Low breakouts",
            signal_type="Intraday",
            expiry="Daily",
            trading_days="Mon,Tue,Wed,Thu,Fri",
            start_time="09:30",
            end_time="16:00",
            scan_interval_minutes=15,
            max_signals_per_day=5,
            signal_direction="Both",
            instrument_type="Stock",
            mode="Virtual",
            is_active=True
        )
        
        session.add(config)
        session.flush()  # Get the config ID
        
        # Add symbols
        symbols = [
            # Primary symbol
            SignalSymbol(
                config_id=config.id,
                symbol="SPY",
                token=756733,
                is_primary=True,
                timeframe="15min",
                weight=1.0
            ),
            # Correlated symbol
            SignalSymbol(
                config_id=config.id,
                symbol="QQQ",
                token=320227,
                is_primary=False,
                timeframe="15min",
                weight=0.7
            )
        ]
        
        for symbol in symbols:
            session.add(symbol)
        
        # Add entry rules
        entry_rules = [
            # Long entry: Price breaks above Swing High
            SignalEntryRule(
                config_id=config.id,
                rule_type="PriceAbove",
                symbol="SPY",
                parameter="SH",
                timeframe="15min",
                is_required=True
            ),
            # Long entry: Correlated symbol is above its Swing Low
            SignalEntryRule(
                config_id=config.id,
                rule_type="PriceAbove",
                symbol="QQQ",
                parameter="SL",
                timeframe="15min",
                is_required=True
            ),
            # Short entry: Price breaks below Swing Low
            SignalEntryRule(
                config_id=config.id,
                rule_type="PriceBelow",
                symbol="SPY",
                parameter="SL",
                timeframe="15min",
                is_required=True
            ),
            # Short entry: Correlated symbol is below its Swing High
            SignalEntryRule(
                config_id=config.id,
                rule_type="PriceBelow",
                symbol="QQQ",
                parameter="SH",
                timeframe="15min",
                is_required=True
            )
        ]
        
        for rule in entry_rules:
            session.add(rule)
        
        # Add exit rules
        exit_rules = [
            # Long exit: Price breaks below Swing Low
            SignalExitRule(
                config_id=config.id,
                rule_type="PriceBelow",
                symbol="SPY",
                parameter="SL",
                timeframe="15min",
                priority=1
            ),
            # Short exit: Price breaks above Swing High
            SignalExitRule(
                config_id=config.id,
                rule_type="PriceAbove",
                symbol="SPY",
                parameter="SH",
                timeframe="15min",
                priority=1
            ),
            # Time-based exit: After 120 minutes
            SignalExitRule(
                config_id=config.id,
                rule_type="TimeElapsed",
                symbol="SPY",
                parameter="Minutes",
                timeframe="15min",
                priority=2,
                minutes_elapsed=120
            )
        ]
        
        for rule in exit_rules:
            session.add(rule)
        
        session.commit()
        logger.info("Sample signal configuration created successfully")
        return True
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating sample configuration: {str(e)}")
        return False
    
    finally:
        session.close()

if __name__ == "__main__":
    # Initialize database
    engine = init_db()
    
    # Create sample configuration
    if engine:
        success = create_sample_config(engine)
        if success:
            print("Sample signal configuration created successfully")
        else:
            print("Failed to create sample signal configuration")
    else:
        print("Failed to initialize database")
