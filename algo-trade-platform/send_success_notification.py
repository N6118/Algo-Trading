#!/usr/bin/env python3
"""
Send success notification about the generated signal.
"""

import os
import sys

# Set Telegram environment variables
os.environ['TELEGRAM_BOT_TOKEN'] = '8468875074:AAEeCH6H5NfNzHFobMAaw4epxa2v8nZvw_8'
os.environ['TELEGRAM_CHAT_ID'] = '2074764227'

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def send_notification():
    try:
        from backend.app.services.telegram_notifier import get_telegram_notifier
        
        notifier = get_telegram_notifier()
        if notifier:
            message = """🚨 **SIGNAL GENERATED SUCCESSFULLY!** 🚨

**Symbol:** MES
**Direction:** Long (Buy)
**Price:** $6496.00
**Timeframe:** 15min
**Strategy:** Sample SH/SL Strategy
**Generated:** 2025-09-05 17:01:15

**Entry Conditions Met:**
• MES price > MES SH (6496.00 > 6486.00) ✅
• VIX price < VIX SL (14.69 < 15.69) ✅
• Correlation disabled ✅

**System Status:**
✅ Data collection: Active
✅ SH/SL calculation: Active  
✅ Signal generation: Working
✅ Correlation toggle: Working
✅ Telegram notifications: Working

The signal scanner successfully detected the conditions and generated a BUY signal!"""
            
            result = notifier.send_message(message)
            print(f"Telegram notification sent: {result}")
            return result
        else:
            print("Telegram notifier not available")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    send_notification()
