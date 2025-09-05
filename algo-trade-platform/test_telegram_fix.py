#!/usr/bin/env python3
"""
Test Telegram notification with proper message format
"""

import os
import sys
import logging
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append('/Users/na61/Desktop/US stockmarket Algotrading /algo-trade-platform/backend')

from app.services.telegram_notifier import get_telegram_notifier

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_telegram_formats():
    """Test different message formats to find the working one"""
    
    # Set environment variables
    os.environ['TELEGRAM_BOT_TOKEN'] = '8468875074:AAEeCH6H5NfNzHFobMAaw4epxa2v8nZvw_8'
    os.environ['TELEGRAM_CHAT_ID'] = '2074764227'
    
    notifier = get_telegram_notifier()
    if not notifier:
        logger.error("❌ Telegram notifier not available")
        return False
    
    # Test 1: HTML format (current default)
    logger.info("🧪 Testing HTML format...")
    html_message = """
🚨 <b>SIGNAL GENERATED</b> 🚨

<b>Symbol:</b> MES
<b>Direction:</b> BUY
<b>Price:</b> $5,234.50
<b>Timeframe:</b> 15m
<b>Strategy:</b> Correlation Strategy
<b>Generated:</b> 2024-01-15 14:30:00

<b>Entry Rules:</b>
• Primary price 5234.50 > SH 5230.00
• Correlated price 12.45 < SL 12.50
    """.strip()
    
    success1 = notifier.send_message(html_message, parse_mode="HTML")
    logger.info(f"HTML format result: {'✅ Success' if success1 else '❌ Failed'}")
    
    # Test 2: Markdown format (what scanner is currently using)
    logger.info("🧪 Testing Markdown format...")
    markdown_message = """
🚨 **SIGNAL GENERATED** 🚨

**Symbol:** MES
**Direction:** BUY
**Price:** $5,234.50
**Timeframe:** 15m
**Strategy:** Correlation Strategy
**Generated:** 2024-01-15 14:30:00

**Entry Rules:**
• Primary price 5234.50 > SH 5230.00
• Correlated price 12.45 < SL 12.50
    """.strip()
    
    success2 = notifier.send_message(markdown_message, parse_mode="Markdown")
    logger.info(f"Markdown format result: {'✅ Success' if success2 else '❌ Failed'}")
    
    # Test 3: Plain text (no formatting)
    logger.info("🧪 Testing plain text format...")
    plain_message = """
🚨 SIGNAL GENERATED 🚨

Symbol: MES
Direction: BUY
Price: $5,234.50
Timeframe: 15m
Strategy: Correlation Strategy
Generated: 2024-01-15 14:30:00

Entry Rules:
• Primary price 5234.50 > SH 5230.00
• Correlated price 12.45 < SL 12.50
    """.strip()
    
    success3 = notifier.send_message(plain_message)
    logger.info(f"Plain text format result: {'✅ Success' if success3 else '❌ Failed'}")
    
    return success1 or success2 or success3

if __name__ == "__main__":
    logger.info("🔧 Testing Telegram notification formats...")
    success = test_telegram_formats()
    
    if success:
        logger.info("✅ At least one format worked!")
    else:
        logger.error("❌ All formats failed")
