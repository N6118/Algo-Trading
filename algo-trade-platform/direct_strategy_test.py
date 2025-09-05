#!/usr/bin/env python3
"""
Directly test the correlation strategy with our test data.
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_strategy_directly():
    """Test the correlation strategy directly with our test data."""
    try:
        # Import the correlation strategy
        sys.path.insert(0, '/home/anurag/Desktop/Algo-Trading/algo-trade-platform/backend/app/signal_scanner')
        from correlation_strategy import CorrelationStrategy
        from db_schema import SignalConfig, SignalEntryRule
        
        logger.info("🧪 Testing Correlation Strategy with Test Data")
        
        # Create a mock config
        config = SignalConfig()
        config.id = 1
        config.name = "Test Strategy"
        config.entry_rules = []
        
        # Create correlation rule (disabled)
        correlation_rule = SignalEntryRule()
        correlation_rule.rule_type = 'Correlation'
        correlation_rule.correlation_enabled = False
        correlation_rule.correlation_threshold = 0.0
        config.entry_rules = [correlation_rule]
        
        # Create strategy instance
        strategy = CorrelationStrategy(config)
        
        # Get market data (should include our test data)
        mes_data = strategy.get_market_data('MES', '15min', lookback=25)
        vix_data = strategy.get_market_data('VIX', '15min', lookback=25)
        
        if mes_data is None or vix_data is None:
            logger.error("Could not get market data")
            return False
        
        logger.info(f"📊 Got {len(mes_data)} MES rows and {len(vix_data)} VIX rows")
        
        # Show latest data
        mes_latest = mes_data.iloc[-1]
        vix_latest = vix_data.iloc[-1]
        
        logger.info("📈 Latest Data from Strategy:")
        logger.info(f"  MES: Close={mes_latest['close']:.2f}, SH={mes_latest['sh_price']:.2f}, SL={mes_latest['sl_price']:.2f}")
        logger.info(f"  VIX: Close={vix_latest['close']:.2f}, SH={vix_latest['sh_price']:.2f}, SL={vix_latest['sl_price']:.2f}")
        
        # Check if our test data conditions are met
        mes_condition = mes_latest['close'] > mes_latest['sh_price']
        vix_condition = vix_latest['close'] < vix_latest['sl_price']
        
        logger.info("🎯 Condition Check:")
        logger.info(f"  MES: {mes_latest['close']:.2f} > {mes_latest['sh_price']:.2f} = {mes_condition}")
        logger.info(f"  VIX: {vix_latest['close']:.2f} < {vix_latest['sl_price']:.2f} = {vix_condition}")
        
        if mes_condition and vix_condition:
            logger.info("✅ BUY conditions are met!")
        else:
            logger.info("❌ BUY conditions not met")
        
        # Test buy conditions
        logger.info("🔍 Testing BUY conditions...")
        buy_result, buy_desc = strategy.check_buy_conditions(mes_data, vix_data)
        logger.info(f"BUY Result: {buy_result} - {buy_desc}")
        
        # Test sell conditions
        logger.info("🔍 Testing SELL conditions...")
        sell_result, sell_desc = strategy.check_sell_conditions(mes_data, vix_data)
        logger.info(f"SELL Result: {sell_result} - {sell_desc}")
        
        return buy_result or sell_result
        
    except Exception as e:
        logger.error(f"Error testing strategy: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def check_current_signals():
    """Check current signals in database."""
    try:
        from urllib.parse import quote_plus as urlquote
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
        
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check all signals
        query = text("""
            SELECT id, symbol, signal_time, direction, price, status
            FROM generated_signals 
            ORDER BY signal_time DESC
            LIMIT 5
        """)
        
        result = session.execute(query)
        signals = result.fetchall()
        
        if signals:
            logger.info("📊 Current signals in database:")
            for signal in signals:
                logger.info(f"  ID: {signal[0]}, {signal[1]} {signal[3]} at {signal[4]} - {signal[5]}")
        else:
            logger.info("❌ No signals in database")
        
        session.close()
        return len(signals)
        
    except Exception as e:
        logger.error(f"Error checking signals: {str(e)}")
        return 0

if __name__ == "__main__":
    logger.info("🧪 Direct Strategy Test with Test Data")
    
    # Step 1: Check current signals
    logger.info("📊 Step 1: Checking current signals...")
    signal_count = check_current_signals()
    
    # Step 2: Test strategy directly
    logger.info("🧪 Step 2: Testing strategy directly...")
    conditions_met = test_strategy_directly()
    
    if conditions_met:
        logger.info("✅ Strategy conditions are met - signals should be generated!")
        logger.info("💡 The issue might be in the scanner service or signal storage logic.")
    else:
        logger.info("❌ Strategy conditions not met - this explains why no signals are generated")
    
    logger.info("🏁 Direct strategy test completed")
