#!/usr/bin/env python3
"""
Signal Scanner Setup Script

This script initializes the signal scanner database and creates sample configurations.
Run this before starting the signal scanner service.
"""

import os
import sys
import logging
from urllib.parse import quote_plus

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_signal_scanner():
    """Set up the signal scanner database and configurations"""
    try:
        # Import the initialization modules
        from backend.app.signal_scanner.init_db import init_db, create_sample_config
        
        logger.info("🚀 Setting up Signal Scanner...")
        
        # Initialize database tables
        logger.info("📊 Creating database tables...")
        engine = init_db()
        
        if not engine:
            logger.error("❌ Failed to initialize database")
            return False
        
        # Create sample configuration
        logger.info("⚙️ Creating sample signal configuration...")
        success = create_sample_config(engine)
        
        if success:
            logger.info("✅ Signal Scanner setup completed successfully!")
            logger.info("📋 Next steps:")
            logger.info("   1. Copy the service file to /etc/systemd/system/")
            logger.info("   2. Run: sudo systemctl daemon-reload")
            logger.info("   3. Run: sudo systemctl enable algo-trading-signal-scanner")
            logger.info("   4. Run: sudo systemctl start algo-trading-signal-scanner")
            return True
        else:
            logger.error("❌ Failed to create sample configuration")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error setting up signal scanner: {str(e)}")
        return False

if __name__ == "__main__":
    success = setup_signal_scanner()
    if success:
        print("✅ Signal Scanner setup completed successfully!")
    else:
        print("❌ Signal Scanner setup failed!")
        sys.exit(1) 