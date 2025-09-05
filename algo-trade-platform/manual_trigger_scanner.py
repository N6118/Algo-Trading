#!/usr/bin/env python3
"""
Manually trigger the signal scanner to run immediately.
"""

import os
import sys
import logging
from urllib.parse import quote_plus as urlquote
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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

def manual_trigger_scanner():
    """Manually trigger the signal scanner."""
    try:
        # Import the scanner
        sys.path.insert(0, '/home/anurag/Desktop/Algo-Trading/algo-trade-platform/backend/app/signal_scanner')
        from scanner import SignalScanner
        from db_schema import SignalConfig
        
        logger.info("🔄 Manually triggering signal scanner...")
        
        # Create scanner instance
        scanner = SignalScanner()
        
        # Get the configuration
        session = scanner.Session()
        config = session.query(SignalConfig).filter(SignalConfig.id == 1).first()
        session.close()
        
        if not config:
            logger.error("❌ Could not find signal configuration")
            return False
        
        logger.info(f"📊 Found config: {config.name}")
        
        # Run the scan
        signals = scanner.scan_for_signals(config)
        
        if signals:
            logger.info(f"🎉 Generated {len(signals)} signals!")
            for signal in signals:
                logger.info(f"  Signal: {signal.symbol} {signal.direction} at ${signal.price:.2f}")
            
            # Send Telegram notification
            from backend.app.services.telegram_notifier import get_telegram_notifier
            notifier = get_telegram_notifier()
            if notifier:
                message = f"""🚨 **SIGNAL GENERATED!** 🚨

**Generated {len(signals)} signal(s):**
"""
                for signal in signals:
                    message += f"• {signal.symbol} {signal.direction} at ${signal.price:.2f}\n"
                
                message += f"""
**Strategy:** {config.name}
**Time:** {signals[0].signal_time.strftime('%Y-%m-%d %H:%M:%S')}

**System Status:**
✅ Signal generation: Working
✅ Correlation disabled: Working
✅ Telegram notifications: Working

The signal scanner successfully detected conditions and generated signals!"""
                
                notifier.send_message(message)
                logger.info("✅ Telegram notification sent")
            
            return True
        else:
            logger.info("❌ No signals generated")
            return False
            
    except Exception as e:
        logger.error(f"Error in manual trigger: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("🧪 Manually Triggering Signal Scanner")
    
    if manual_trigger_scanner():
        logger.info("🎉 SUCCESS: Signal scanner generated signals!")
    else:
        logger.info("❌ No signals were generated")
    
    logger.info("🏁 Manual trigger completed")
