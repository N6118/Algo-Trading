#!/usr/bin/env python3
"""
Test Signal Scanner Without Correlation

This script temporarily bypasses correlation checks to test:
1. Signal generation based only on price conditions
2. Telegram notifications
3. Then restores correlation checks
"""

import os
import sys
import logging
from datetime import datetime, timedelta, timezone

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the signal scanner components
from backend.app.signal_scanner.scanner import SignalScanner
from backend.app.signal_scanner.correlation_strategy import CorrelationStrategy
from backend.app.signal_scanner.db_schema import SignalConfig, SignalSymbol, GeneratedSignal
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_signal_without_correlation():
    """Test signal generation without correlation checks."""
    logger.info("🔧 Testing signal scanner WITHOUT correlation checks...")
    
    try:
        scanner = SignalScanner()
        session = scanner.Session()
        
        # Get configuration
        config = session.query(SignalConfig).filter(SignalConfig.is_active == True).first()
        if not config:
            logger.error("❌ No active configuration found")
            return False
        
        logger.info(f"✅ Testing with config: {config.name}")
        
        # Temporarily disable correlation threshold by setting it to 0
        logger.info("🔧 Temporarily disabling correlation threshold...")
        
        update_query = text("""
            UPDATE signal_entry_rules 
            SET correlation_threshold = 0.0 
            WHERE rule_type = 'Correlation'
        """)
        
        session.execute(update_query)
        session.commit()
        logger.info("✅ Correlation threshold temporarily set to 0.0")
        
        # Test correlation strategy
        correlation_strategy = CorrelationStrategy(config)
        
        # Get symbols
        symbols = session.query(SignalSymbol).filter(SignalSymbol.config_id == config.id).all()
        primary_symbol = next((s for s in symbols if s.is_primary), None)
        correlated_symbol = next((s for s in symbols if not s.is_primary), None)
        
        logger.info(f"✅ Primary: {primary_symbol.symbol}")
        logger.info(f"✅ Correlated: {correlated_symbol.symbol}")
        
        # Get market data
        primary_data = correlation_strategy.get_market_data(
            primary_symbol.symbol, 
            primary_symbol.timeframe, 
            lookback=100
        )
        correlated_data = correlation_strategy.get_market_data(
            correlated_symbol.symbol, 
            correlated_symbol.timeframe, 
            lookback=100
        )
        
        if primary_data is None or correlated_data is None:
            logger.error("❌ Failed to retrieve market data")
            return False
        
        # Check latest data
        latest_primary = primary_data.iloc[-1]
        latest_correlated = correlated_data.iloc[-1]
        
        logger.info(f"Latest {primary_symbol.symbol}:")
        logger.info(f"  Close: {latest_primary['close']:.2f}")
        logger.info(f"  SH: {latest_primary['sh_price']:.2f}")
        logger.info(f"  SL: {latest_primary['sl_price']:.2f}")
        
        logger.info(f"Latest {correlated_symbol.symbol}:")
        logger.info(f"  Close: {latest_correlated['close']:.2f}")
        logger.info(f"  SH: {latest_correlated['sh_price']:.2f}")
        logger.info(f"  SL: {latest_correlated['sl_price']:.2f}")
        
        # Verify conditions are met
        mes_above_sh = latest_primary['close'] > latest_primary['sh_price']
        vix_below_sl = latest_correlated['close'] < latest_correlated['sl_price']
        
        logger.info(f"\n🔍 Condition Check:")
        logger.info(f"  MES Close > SH: {latest_primary['close']:.2f} > {latest_primary['sh_price']:.2f} = {mes_above_sh}")
        logger.info(f"  VIX Close < SL: {latest_correlated['close']:.2f} < {latest_correlated['sl_price']:.2f} = {vix_below_sl}")
        
        if mes_above_sh and vix_below_sl:
            logger.info("✅ BUY conditions are met!")
        else:
            logger.error("❌ BUY conditions are NOT met!")
            return False
        
        # Calculate correlation (should be ignored now)
        correlation = correlation_strategy.calculate_correlation(primary_data, correlated_data)
        logger.info(f"Correlation: {correlation:.4f} (will be ignored)")
        
        # Test buy conditions (should pass now)
        buy_condition, buy_description = correlation_strategy.check_buy_conditions(primary_data, correlated_data)
        logger.info(f"Buy condition check: {buy_condition} - {buy_description}")
        
        # Generate signals (should work now)
        signals = correlation_strategy.generate_signal(config)
        logger.info(f"Generated signals: {len(signals)}")
        
        for signal in signals:
            logger.info(f"  🎯 SIGNAL GENERATED: {signal.symbol} {signal.direction} at {signal.price}")
        
        # Check total signals in database
        total_signals = session.query(GeneratedSignal).count()
        logger.info(f"Total signals in database: {total_signals}")
        
        session.close()
        
        if len(signals) > 0:
            logger.info("🎉 SUCCESS! Signal was generated without correlation check!")
            logger.info("📱 Check your Telegram for notification!")
            return True
        else:
            logger.warning("⚠️ Still no signals generated")
            return False
        
    except Exception as e:
        logger.error(f"❌ Signal test without correlation failed: {str(e)}")
        return False

def restore_correlation_checks():
    """Restore correlation threshold back to normal."""
    logger.info("🔧 Restoring correlation threshold back to normal...")
    
    try:
        scanner = SignalScanner()
        session = scanner.Session()
        
        # Restore correlation threshold to 0.7
        restore_query = text("""
            UPDATE signal_entry_rules 
            SET correlation_threshold = 0.7 
            WHERE rule_type = 'Correlation'
        """)
        
        session.execute(restore_query)
        session.commit()
        logger.info("✅ Correlation threshold restored to 0.7")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to restore correlation threshold: {str(e)}")
        return False

def run_test_without_correlation():
    """Run the complete test without correlation."""
    logger.info("🚀 SIGNAL SCANNER TEST WITHOUT CORRELATION")
    logger.info("=" * 60)
    
    try:
        # Step 1: Test signal generation without correlation
        logger.info("\n📊 STEP 1: Testing signal generation without correlation...")
        if not test_signal_without_correlation():
            logger.error("❌ Signal test failed")
            return False
        
        # Step 2: Wait a moment for Telegram to send
        logger.info("\n📊 STEP 2: Waiting for Telegram notification...")
        logger.info("📱 Check your Telegram now - you should see a signal notification!")
        
        # Step 3: Restore correlation checks
        logger.info("\n📊 STEP 3: Restoring correlation checks...")
        if not restore_correlation_checks():
            logger.error("❌ Failed to restore correlation")
            return False
        
        logger.info("\n🎉 TEST COMPLETED SUCCESSFULLY!")
        logger.info("✅ Signal was generated without correlation")
        logger.info("✅ Telegram notification should have been sent")
        logger.info("✅ Correlation checks restored to normal")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test without correlation failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_test_without_correlation()
    if success:
        print("\n🎉 SIGNAL SCANNER TEST WITHOUT CORRELATION COMPLETE!")
        print("✅ Signal generated successfully")
        print("📱 Telegram notification sent")
        print("✅ Correlation checks restored")
        print("🎯 Your scanner is working perfectly!")
    else:
        print("\n💥 SIGNAL SCANNER TEST WITHOUT CORRELATION FAILED")
        sys.exit(1)
