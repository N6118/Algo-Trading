#!/usr/bin/env python3
"""
Utility script to refresh contract timestamps in the database.
This prevents contracts from being filtered out due to stale timestamps.
"""

import psycopg2
from urllib.parse import quote_plus
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database configuration
password = quote_plus("password")
DB_URI = f"postgresql://postgres:{password}@localhost:5432/theodb"

def refresh_contract_timestamps():
    """Update timestamps for all active contracts."""
    conn = None
    try:
        conn = psycopg2.connect(DB_URI)
        with conn.cursor() as cur:
            # Get count of active contracts
            cur.execute("SELECT COUNT(*) FROM ibkr_contracts WHERE is_active = true")
            count = cur.fetchone()[0]
            
            if count == 0:
                logging.warning("No active contracts found in database")
                return
            
            # Update timestamps for all active contracts
            cur.execute("""
                UPDATE ibkr_contracts 
                SET last_updated = NOW() 
                WHERE is_active = true
            """)
            conn.commit()
            
            logging.info(f"✅ Updated timestamps for {count} active contracts")
            
            # Show the updated contracts
            cur.execute("""
                SELECT symbol, sec_type, exchange, last_updated 
                FROM ibkr_contracts 
                WHERE is_active = true 
                ORDER BY symbol
            """)
            contracts = cur.fetchall()
            
            logging.info("📊 Active contracts:")
            for symbol, sec_type, exchange, last_updated in contracts:
                logging.info(f"  - {symbol} ({sec_type}) on {exchange} - Updated: {last_updated}")
                
    except Exception as e:
        logging.error(f"❌ Error refreshing contract timestamps: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.info("🔄 Refreshing contract timestamps...")
    refresh_contract_timestamps()
    logging.info("✅ Contract timestamp refresh completed") 