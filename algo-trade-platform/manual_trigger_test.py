#!/usr/bin/env python3
"""
Manually trigger the signal scanner to test if it picks up our test data.
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

def manual_trigger_scanner():
    """Manually trigger the signal scanner."""
    try:
        # Import the scanner
        sys.path.insert(0, '/home/anurag/Desktop/Algo-Trading/algo-trade-platform/backend/app/signal_scanner')
        from scanner import SignalScanner
        
        logger.info("🔍 Manually triggering signal scanner...")
        
        # Create scanner instance
        scanner = SignalScanner()
        
        # Get the config
        config = scanner.SignalConfig.query.filter_by(id=1).first()
        if not config:
            logger.error("No signal config found with ID 1")
            return False
        
        logger.info(f"📋 Using config: {config.name}")
        
        # Manually trigger the scan
        logger.info("🚀 Starting manual scan...")
        scanner.scan_for_signals(config)
        
        logger.info("✅ Manual scan completed")
        return True
        
    except Exception as e:
        logger.error(f"Error in manual trigger: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def check_generated_signals():
    """Check if any new signals were generated."""
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
        
        # Check recent signals
        query = text("""
            SELECT id, symbol, signal_time, direction, price, status, created_at
            FROM generated_signals 
            WHERE created_at > NOW() - INTERVAL '10 minutes'
            ORDER BY created_at DESC
        """)
        
        result = session.execute(query)
        signals = result.fetchall()
        
        if signals:
            logger.info("🎯 New signals generated:")
            for signal in signals:
                logger.info(f"  ID: {signal[0]}, {signal[1]} {signal[3]} at {signal[4]} - {signal[5]}")
        else:
            logger.info("❌ No new signals generated")
        
        session.close()
        return len(signals) > 0
        
    except Exception as e:
        logger.error(f"Error checking signals: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Manual Signal Scanner Test")
    
    # Step 1: Check current signals before
    logger.info("📊 Step 1: Checking current signals...")
    signals_before = check_generated_signals()
    
    # Step 2: Manually trigger scanner
    logger.info("🚀 Step 2: Manually triggering scanner...")
    if manual_trigger_scanner():
        logger.info("✅ Scanner triggered successfully")
    else:
        logger.error("❌ Failed to trigger scanner")
        sys.exit(1)
    
    # Step 3: Check for new signals
    logger.info("🔍 Step 3: Checking for new signals...")
    signals_after = check_generated_signals()
    
    if signals_after and not signals_before:
        logger.info("🎉 SUCCESS! New signals were generated!")
    elif signals_after:
        logger.info("ℹ️ Signals were already present")
    else:
        logger.info("❌ No signals were generated - need to investigate further")
    
    logger.info("🏁 Manual trigger test completed")
