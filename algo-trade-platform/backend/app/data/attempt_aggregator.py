#!/usr/bin/env python3
"""
Attempt Aggregator Service
Calls the attempt.py /update endpoint to process 15-minute data
"""

import requests
import logging
import time
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration
ATTEMPT_URL = "http://localhost:5001/update"
CHECK_INTERVAL = 300  # 5 minutes

def call_attempt_update():
    """Call the attempt.py update endpoint"""
    try:
        logger.info("🔄 Calling attempt.py update endpoint...")
        response = requests.get(ATTEMPT_URL, timeout=60)
        
        if response.status_code == 200:
            logger.info("✅ Successfully called attempt.py update endpoint")
            return True
        else:
            logger.error(f"❌ Attempt.py update failed with status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ Could not connect to attempt.py service (port 5001)")
        return False
    except requests.exceptions.Timeout:
        logger.error("❌ Attempt.py update request timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Error calling attempt.py update: {e}")
        return False

def main():
    """Main loop - call attempt.py update every 5 minutes"""
    logger.info("🚀 Starting Attempt Aggregator Service")
    
    while True:
        try:
            current_time = datetime.now()
            logger.info(f"⏰ Checking for updates at {current_time}")
            
            success = call_attempt_update()
            
            if success:
                logger.info("✅ Update completed successfully")
            else:
                logger.warning("⚠️ Update failed, will retry in next cycle")
            
            logger.info(f"💤 Sleeping for {CHECK_INTERVAL} seconds...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal, shutting down...")
            break
        except Exception as e:
            logger.error(f"❌ Unexpected error in main loop: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main() 