#!/usr/bin/env python3
"""
Test Telegram notification with a real signal from the database
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append('/Users/na61/Desktop/US stockmarket Algotrading /algo-trade-platform/backend')

from app.services.telegram_notifier import get_telegram_notifier
from app.signal_scanner.db_schema import get_db_session, GeneratedSignal, SignalConfig

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_telegram_with_real_signal():
    """Test Telegram notification with a real signal from the database"""
    
    # Set environment variables
    os.environ['TELEGRAM_BOT_TOKEN'] = '8468875074:AAEeCH6H5NfNzHFobMAaw4epxa2v8nZvw_8'
    os.environ['TELEGRAM_CHAT_ID'] = '2074764227'
    
    notifier = get_telegram_notifier()
    if not notifier:
        logger.error("❌ Telegram notifier not available")
        return False
    
    # Get the latest signal from the database
    session = get_db_session()
    try:
        latest_signal = session.query(GeneratedSignal).order_by(GeneratedSignal.id.desc()).first()
        if not latest_signal:
            logger.error("❌ No signals found in database")
            return False
        
        logger.info(f"📊 Found signal ID {latest_signal.id}: {latest_signal.symbol} {latest_signal.direction}")
        
        # Get the config for this signal
        config = session.query(SignalConfig).filter(SignalConfig.id == latest_signal.config_id).first()
        config_name = config.name if config else "Unknown Strategy"
        
        # Create the message in the same format as the scanner
        message = f"🚨 **SIGNAL GENERATED** 🚨\n\n"
        message += f"**Symbol:** {latest_signal.symbol}\n"
        message += f"**Direction:** {latest_signal.direction}\n"
        message += f"**Price:** ${latest_signal.price:.2f}\n"
        message += f"**Timeframe:** {latest_signal.timeframe}\n"
        message += f"**Strategy:** {config_name}\n"
        message += f"**Generated:** {latest_signal.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        message += f"**Entry Rules:**\n"
        for rule in latest_signal.entry_rules:
            message += f"• {rule.condition}\n"
        
        logger.info("📤 Sending Telegram notification...")
        logger.info(f"Message preview: {message[:100]}...")
        
        # Send the message with Markdown format
        success = notifier.send_message(message, parse_mode="Markdown")
        
        if success:
            logger.info("✅ Telegram notification sent successfully!")
            return True
        else:
            logger.error("❌ Failed to send Telegram notification")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing Telegram notification: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    logger.info("🧪 Testing Telegram notification with real signal...")
    success = test_telegram_with_real_signal()
    
    if success:
        logger.info("🎉 Telegram notifications are working!")
    else:
        logger.error("💥 Telegram notifications are still broken")
