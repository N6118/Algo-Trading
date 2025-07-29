#!/usr/bin/env python3
"""
Wrapper script to start the IBKR streamdata service with Telegram notifications.
This script sets the required environment variables and starts the streamdata service.
"""

import os
import sys
import subprocess
from pathlib import Path

# Set Telegram environment variables
os.environ['TELEGRAM_BOT_TOKEN'] = '8468875074:AAEeCH6H5NfNzHFobMAaw4epxa2v8nZvw_8'
os.environ['TELEGRAM_CHAT_ID'] = '2074764227'

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import and run the streamdata service
from backend.app.data.streamdata import run_ibkr

if __name__ == "__main__":
    print("🚀 Starting IBKR Streamdata Service with Telegram notifications...")
    print(f"📱 Telegram Bot Token: {os.environ.get('TELEGRAM_BOT_TOKEN', 'Not set')[:20]}...")
    print(f"💬 Telegram Chat ID: {os.environ.get('TELEGRAM_CHAT_ID', 'Not set')}")
    
    try:
        run_ibkr()
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
    except Exception as e:
        print(f"❌ Service error: {e}")
        sys.exit(1) 