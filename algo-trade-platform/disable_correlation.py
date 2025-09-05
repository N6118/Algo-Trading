#!/usr/bin/env python3
"""
Script to disable correlation checking for signal generation.
This allows the system to generate signals based on SH/SL breakouts only,
without requiring correlation between symbols.
"""

import os
import sys
import logging
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

def disable_correlation():
    """Disable correlation checking for the signal configuration."""
    try:
        # Database connection
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
        
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Update the correlation rule to disable correlation
        update_query = text("""
            UPDATE signal_entry_rules 
            SET correlation_enabled = false,
                correlation_threshold = -1
            WHERE rule_type = 'Correlation' 
            AND config_id = 1
        """)
        
        result = session.execute(update_query)
        session.commit()
        
        logger.info(f"✅ Disabled correlation for {result.rowcount} correlation rules")
        
        # Verify the update
        verify_query = text("""
            SELECT id, rule_type, correlation_enabled, correlation_threshold 
            FROM signal_entry_rules 
            WHERE rule_type = 'Correlation' 
            AND config_id = 1
        """)
        
        result = session.execute(verify_query)
        rules = result.fetchall()
        
        logger.info("📊 Current correlation rule status:")
        for rule in rules:
            logger.info(f"  Rule ID {rule[0]}: correlation_enabled={rule[2]}, threshold={rule[3]}")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error disabling correlation: {str(e)}")
        return False

def enable_correlation():
    """Re-enable correlation checking for the signal configuration."""
    try:
        # Database connection
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
        
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Update the correlation rule to enable correlation
        update_query = text("""
            UPDATE signal_entry_rules 
            SET correlation_enabled = true,
                correlation_threshold = 0.7
            WHERE rule_type = 'Correlation' 
            AND config_id = 1
        """)
        
        result = session.execute(update_query)
        session.commit()
        
        logger.info(f"✅ Enabled correlation for {result.rowcount} correlation rules")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enabling correlation: {str(e)}")
        return False

def show_status():
    """Show current correlation status."""
    try:
        # Database connection
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
        
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Get current status
        query = text("""
            SELECT id, rule_type, correlation_enabled, correlation_threshold 
            FROM signal_entry_rules 
            WHERE rule_type = 'Correlation' 
            AND config_id = 1
        """)
        
        result = session.execute(query)
        rules = result.fetchall()
        
        if rules:
            logger.info("📊 Current correlation rule status:")
            for rule in rules:
                status = "ENABLED" if rule[2] else "DISABLED"
                logger.info(f"  Rule ID {rule[0]}: {status} (threshold={rule[3]})")
        else:
            logger.info("❌ No correlation rules found")
        
        session.close()
        
    except Exception as e:
        logger.error(f"❌ Error checking status: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Toggle correlation checking for signal generation")
    parser.add_argument("action", choices=["disable", "enable", "status"], 
                       help="Action to perform: disable, enable, or show status")
    
    args = parser.parse_args()
    
    if args.action == "disable":
        logger.info("🔄 Disabling correlation checking...")
        success = disable_correlation()
        if success:
            logger.info("✅ Correlation disabled successfully!")
            logger.info("📈 Signals will now be generated based on SH/SL breakouts only")
        else:
            logger.error("❌ Failed to disable correlation")
    
    elif args.action == "enable":
        logger.info("🔄 Enabling correlation checking...")
        success = enable_correlation()
        if success:
            logger.info("✅ Correlation enabled successfully!")
            logger.info("📊 Signals will now require correlation > 0.7")
        else:
            logger.error("❌ Failed to enable correlation")
    
    elif args.action == "status":
        show_status()
