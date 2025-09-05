#!/usr/bin/env python3
"""
Generate a test signal directly in the database to test the full flow.
"""

import os
import sys
import logging
from datetime import datetime
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

def generate_test_signal():
    """Generate a test signal directly in the database."""
    try:
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
        
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Insert a test signal
        signal_query = text("""
            INSERT INTO generated_signals (
                config_id, symbol, token, signal_time, direction, price, timeframe, status
            ) VALUES (
                :config_id, :symbol, :token, :signal_time, :direction, :price, :timeframe, :status
            )
        """)
        
        # Generate a SELL signal (since our test data met SELL conditions)
        session.execute(signal_query, {
            'config_id': 1,
            'symbol': 'MES',
            'token': 756733,
            'signal_time': datetime.utcnow(),
            'direction': 'Short',
            'price': 6467.50,
            'timeframe': '15min',
            'status': 'New'
        })
        
        session.commit()
        logger.info("✅ Generated test SELL signal for MES at $6467.50")
        
        # Check if signal was created
        check_query = text("""
            SELECT id, symbol, signal_time, direction, price, status
            FROM generated_signals
            WHERE signal_time > NOW() - INTERVAL '1 minute'
            ORDER BY signal_time DESC
        """)
        
        result = session.execute(check_query)
        signals = result.fetchall()
        
        if signals:
            logger.info("🎉 SIGNAL CREATED SUCCESSFULLY!")
            for signal in signals:
                logger.info(f"  Signal ID {signal[0]}: {signal[1]} {signal[3]} at ${signal[4]:.2f} ({signal[5]})")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"Error generating test signal: {str(e)}")
        return False

def test_telegram_notification():
    """Test if Telegram notifications work."""
    try:
        # Import Telegram notifier
        sys.path.insert(0, '/home/anurag/Desktop/Algo-Trading/algo-trade-platform/backend/app/services')
        from telegram_notifier import get_telegram_notifier
        
        notifier = get_telegram_notifier()
        if notifier:
            message = """
🚨 **TEST SIGNAL GENERATED** 🚨

**Symbol:** MES
**Direction:** Short
**Price:** $6467.50
**Timeframe:** 15min
**Strategy:** Test Signal
**Generated:** """ + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + """

**Entry Rules:**
• MES price < MES SL (6467.50 < 6472.50) ✅
• VIX price > VIX SH (16.63 > 16.13) ✅
• Correlation disabled ✅

This is a test signal to verify the system is working correctly.
            """.strip()
            
            notifier.send_message(message)
            logger.info("✅ Test Telegram notification sent")
            return True
        else:
            logger.error("❌ Telegram notifier not available")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Generating Test Signal and Testing Telegram")
    
    # Step 1: Generate test signal
    logger.info("📝 Step 1: Generating test signal...")
    if generate_test_signal():
        logger.info("✅ Test signal generated successfully")
    else:
        logger.error("❌ Failed to generate test signal")
        sys.exit(1)
    
    # Step 2: Test Telegram notification
    logger.info("📱 Step 2: Testing Telegram notification...")
    if test_telegram_notification():
        logger.info("✅ Telegram notification sent successfully")
    else:
        logger.error("❌ Failed to send Telegram notification")
    
    logger.info("🏁 Test completed - Check your Telegram for the notification!")
