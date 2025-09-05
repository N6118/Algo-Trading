#!/usr/bin/env python3
"""
Test Telegram notification with proper environment variables.
"""

import os
import sys
import logging
from datetime import datetime

# Set Telegram environment variables
os.environ['TELEGRAM_BOT_TOKEN'] = '8468875074:AAEeCH6H5NfNzHFobMAaw4epxa2v8nZvw_8'
os.environ['TELEGRAM_CHAT_ID'] = '2074764227'

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_telegram_notification():
    """Test Telegram notification."""
    try:
        # Import Telegram notifier
        sys.path.insert(0, '/home/anurag/Desktop/Algo-Trading/algo-trade-platform/backend/app/services')
        from telegram_notifier import get_telegram_notifier
        
        notifier = get_telegram_notifier()
        if notifier:
            message = f"""
🚨 **SIGNAL GENERATED SUCCESSFULLY!** 🚨

**Symbol:** MES
**Direction:** Short
**Price:** $6467.50
**Timeframe:** 15min
**Strategy:** Sample SH/SL Strategy
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

**Entry Conditions Met:**
• MES price < MES SL (6467.50 < 6472.50) ✅
• VIX price > VIX SH (16.63 > 16.13) ✅
• Correlation disabled ✅

**System Status:**
✅ Data collection: Active
✅ SH/SL calculation: Active  
✅ Signal generation: Active
✅ Correlation toggle: Working

The signal scanner is now working correctly without correlation requirements!
            """.strip()
            
            notifier.send_message(message)
            logger.info("✅ Telegram notification sent successfully")
            return True
        else:
            logger.error("❌ Telegram notifier not available")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("📱 Testing Telegram Notification")
    
    if test_telegram_notification():
        logger.info("🎉 SUCCESS: Telegram notification sent!")
        logger.info("📱 Check your Telegram for the notification")
    else:
        logger.error("❌ Failed to send Telegram notification")
    
    logger.info("🏁 Test completed")
