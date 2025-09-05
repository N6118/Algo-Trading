#!/usr/bin/env python3
"""
Debug the signal scanner to understand why it's not picking up conditions.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus as urlquote
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def analyze_current_data():
    """Analyze current data and conditions."""
    try:
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
        
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Get latest data for both symbols
        query = text("""
            SELECT symbol, created, close, sh_price, sl_price
            FROM tbl_ohlc_fifteen_output 
            WHERE symbol IN ('MES', 'VIX')
            AND created = (
                SELECT MAX(created) 
                FROM tbl_ohlc_fifteen_output 
                WHERE symbol = tbl_ohlc_fifteen_output.symbol
            )
            ORDER BY symbol
        """)
        
        result = session.execute(query)
        rows = result.fetchall()
        
        logger.info("📊 Current Latest Data:")
        current_data = {}
        for row in rows:
            symbol, created, close, sh_price, sl_price = row
            current_data[symbol] = {
                'created': created,
                'close': close,
                'sh_price': sh_price,
                'sl_price': sl_price
            }
            logger.info(f"  {symbol}: Close={close:.2f}, SH={sh_price:.2f}, SL={sl_price:.2f}")
        
        # Check conditions
        if 'MES' in current_data and 'VIX' in current_data:
            mes = current_data['MES']
            vix = current_data['VIX']
            
            buy_condition = mes['close'] > mes['sh_price'] and vix['close'] < vix['sl_price']
            sell_condition = mes['close'] < mes['sl_price'] and vix['close'] > vix['sh_price']
            
            logger.info("🎯 Condition Analysis:")
            logger.info(f"  BUY: MES {mes['close']:.2f} > {mes['sh_price']:.2f} = {mes['close'] > mes['sh_price']}, VIX {vix['close']:.2f} < {vix['sl_price']:.2f} = {vix['close'] < vix['sl_price']}")
            logger.info(f"  SELL: MES {mes['close']:.2f} < {mes['sl_price']:.2f} = {mes['close'] < mes['sl_price']}, VIX {vix['close']:.2f} > {vix['sh_price']:.2f} = {vix['close'] > vix['sh_price']}")
            logger.info(f"  BUY Condition Met: {buy_condition}")
            logger.info(f"  SELL Condition Met: {sell_condition}")
            
            if not buy_condition and not sell_condition:
                logger.info("❌ No conditions met - this is why no signals are generated")
                
                # Suggest what data would trigger signals
                logger.info("💡 To trigger BUY signal, we need:")
                logger.info(f"    MES > {mes['sh_price']:.2f} (currently {mes['close']:.2f})")
                logger.info(f"    VIX < {vix['sl_price']:.2f} (currently {vix['close']:.2f})")
                
                logger.info("💡 To trigger SELL signal, we need:")
                logger.info(f"    MES < {mes['sl_price']:.2f} (currently {mes['close']:.2f})")
                logger.info(f"    VIX > {vix['sh_price']:.2f} (currently {vix['close']:.2f})")
        
        session.close()
        return current_data
        
    except Exception as e:
        logger.error(f"Error analyzing data: {str(e)}")
        return {}

def test_correlation_strategy_directly():
    """Test the correlation strategy directly with current data."""
    try:
        # Import the correlation strategy
        sys.path.insert(0, '/home/anurag/Desktop/Algo-Trading/algo-trade-platform/backend/app/signal_scanner')
        from correlation_strategy import CorrelationStrategy
        from db_schema import SignalConfig, SignalEntryRule
        
        logger.info("🧪 Testing Correlation Strategy Directly")
        
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
        
        # Show latest data
        mes_latest = mes_data.iloc[-1]
        vix_latest = vix_data.iloc[-1]
        
        logger.info("📈 Latest Data from Strategy:")
        logger.info(f"  MES: Close={mes_latest['close']:.2f}, SH={mes_latest['sh_price']:.2f}, SL={mes_latest['sl_price']:.2f}")
        logger.info(f"  VIX: Close={vix_latest['close']:.2f}, SH={vix_latest['sh_price']:.2f}, SL={vix_latest['sl_price']:.2f}")
        
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
        logger.error(f"Error testing correlation strategy: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def check_signal_scanner_config():
    """Check the signal scanner configuration."""
    try:
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
        
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check signal config
        config_query = text("SELECT * FROM signal_configs WHERE id = 1")
        config_result = session.execute(config_query)
        config = config_result.fetchone()
        
        if config:
            logger.info("📋 Signal Configuration:")
            logger.info(f"  ID: {config[0]}")
            logger.info(f"  Name: {config[1]}")
            logger.info(f"  Active: {config[16]}")
            logger.info(f"  Scan Interval: {config[8]} minutes")
        
        # Check signal symbols
        symbols_query = text("SELECT * FROM signal_symbols WHERE config_id = 1")
        symbols_result = session.execute(symbols_query)
        symbols = symbols_result.fetchall()
        
        logger.info("📊 Signal Symbols:")
        for symbol in symbols:
            logger.info(f"  {symbol[2]} (Primary: {symbol[4]}, Timeframe: {symbol[5]})")
        
        # Check entry rules
        rules_query = text("SELECT * FROM signal_entry_rules WHERE config_id = 1")
        rules_result = session.execute(rules_query)
        rules = rules_result.fetchall()
        
        logger.info("📝 Entry Rules:")
        for rule in rules:
            logger.info(f"  {rule[2]}: {rule[3]} {rule[4]} (Correlation: {rule[11] if len(rule) > 11 else 'N/A'})")
        
        session.close()
        
    except Exception as e:
        logger.error(f"Error checking config: {str(e)}")

if __name__ == "__main__":
    logger.info("🔍 Debugging Signal Scanner")
    
    # Step 1: Analyze current data
    logger.info("📊 Step 1: Analyzing current data...")
    current_data = analyze_current_data()
    
    # Step 2: Check configuration
    logger.info("📋 Step 2: Checking signal scanner configuration...")
    check_signal_scanner_config()
    
    # Step 3: Test strategy directly
    logger.info("🧪 Step 3: Testing correlation strategy directly...")
    conditions_met = test_correlation_strategy_directly()
    
    if conditions_met:
        logger.info("✅ Conditions are met - signals should be generated")
    else:
        logger.info("❌ No conditions met - this explains why no signals are generated")
    
    logger.info("🏁 Debug completed")
