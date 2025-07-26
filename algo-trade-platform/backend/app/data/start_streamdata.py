#!/usr/bin/env python3
"""
Wrapper script to start the IBKR streamdata service with Telegram notifications.
This script is designed to be called by the systemd service.
"""

import os
import sys
import signal
import logging
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.data.streamdata import run_ibkr, run_flask
from backend.app.services.telegram_notifier import (
    send_server_start_notification,
    send_server_stop_notification,
    send_connection_status
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/ibkr-streamdata.log')
    ]
)

logger = logging.getLogger(__name__)

# Global flag to track shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True

def main():
    """Main function to start the IBKR streamdata service."""
    global shutdown_requested
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Send initial server start notification
    logger.info("🚀 Starting IBKR Streamdata Service...")
    send_server_start_notification()
    
    try:
        # Start the IBKR data collection in a separate thread
        import threading
        ibkr_thread = threading.Thread(target=run_ibkr, daemon=True)
        ibkr_thread.start()
        
        # Start the Flask API server in a separate thread
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        logger.info("✅ IBKR Streamdata Service started successfully")
        
        # Main loop - keep the service running
        while not shutdown_requested:
            time.sleep(1)
            
            # Check if threads are still alive
            if not ibkr_thread.is_alive():
                logger.error("❌ IBKR thread died unexpectedly")
                break
                
            if not flask_thread.is_alive():
                logger.error("❌ Flask thread died unexpectedly")
                break
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"❌ Unexpected error in main loop: {e}")
        send_connection_status("error", str(e))
    finally:
        # Send server stop notification
        logger.info("🛑 Shutting down IBKR Streamdata Service...")
        send_server_stop_notification()
        logger.info("✅ IBKR Streamdata Service shutdown complete")

if __name__ == "__main__":
    main() 