#!/usr/bin/env python3
"""
Direct test of the correlation strategy with test data.
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote_plus as urlquote
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the correlation strategy
sys.path.insert(0, '/home/anurag/Desktop/Algo-Trading/algo-trade-platform/backend/app/signal_scanner')
from correlation_strategy import CorrelationStrategy
from db_schema import SignalConfig, SignalSymbol, SignalEntryRule

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_correlation_strategy():
    """Test the correlation strategy directly."""
    try:
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
        
        # Get current data
        mes_data = strategy.get_market_data('MES', '15min', lookback=25)
        vix_data = strategy.get_market_data('VIX', '15min', lookback=25)
        
        if mes_data is None or vix_data is None:
            logger.error("Could not get market data")
            return False
        
        logger.info(f"📊 Got {len(mes_data)} MES rows and {len(vix_data)} VIX rows")
        
        # Test buy conditions
        logger.info("🔍 Testing BUY conditions...")
        buy_result, buy_desc = strategy.check_buy_conditions(mes_data, vix_data)
        logger.info(f"BUY Result: {buy_result} - {buy_desc}")
        
        # Test sell conditions
        logger.info("🔍 Testing SELL conditions...")
        sell_result, sell_desc = strategy.check_sell_conditions(mes_data, vix_data)
        logger.info(f"SELL Result: {sell_result} - {sell_desc}")
        
        # Show latest data
        mes_latest = mes_data.iloc[-1]
        vix_latest = vix_data.iloc[-1]
        
        logger.info("📈 Latest Data:")
        logger.info(f"  MES: Close={mes_latest['close']:.2f}, SH={mes_latest['sh_price']:.2f}, SL={mes_latest['sl_price']:.2f}")
        logger.info(f"  VIX: Close={vix_latest['close']:.2f}, SH={vix_latest['sh_price']:.2f}, SL={vix_latest['sl_price']:.2f}")
        
        # Check conditions manually
        mes_price = mes_latest['close']
        vix_price = vix_latest['close']
        mes_sh = mes_latest['sh_price']
        mes_sl = mes_latest['sl_price']
        vix_sh = vix_latest['sh_price']
        vix_sl = vix_latest['sl_price']
        
        buy_condition = mes_price > mes_sh and vix_price < vix_sl
        sell_condition = mes_price < mes_sl and vix_price > vix_sh
        
        logger.info("🎯 Manual Condition Check:")
        logger.info(f"  BUY: MES {mes_price:.2f} > {mes_sh:.2f} = {mes_price > mes_sh}, VIX {vix_price:.2f} < {vix_sl:.2f} = {vix_price < vix_sl}")
        logger.info(f"  SELL: MES {mes_price:.2f} < {mes_sl:.2f} = {mes_price < mes_sl}, VIX {vix_price:.2f} > {vix_sh:.2f} = {vix_price > vix_sh}")
        logger.info(f"  BUY Condition Met: {buy_condition}")
        logger.info(f"  SELL Condition Met: {sell_condition}")
        
        return buy_result or sell_result
        
    except Exception as e:
        logger.error(f"Error testing correlation strategy: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("🧪 Testing Correlation Strategy Directly")
    
    if test_correlation_strategy():
        logger.info("✅ Strategy test completed - conditions were met!")
    else:
        logger.info("❌ Strategy test completed - no conditions met")
    
    logger.info("🏁 Test completed")
