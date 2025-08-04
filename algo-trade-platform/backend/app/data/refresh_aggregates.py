#!/usr/bin/env python3
"""
Refresh TimescaleDB Continuous Aggregates
This script periodically refreshes the stock_ohlc_15min continuous aggregate
to ensure fresh data is available for SL/TP calculations.
"""

import psycopg2
import logging
import time
import os
from datetime import datetime, timedelta
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Database configuration
DB_PASSWORD = "password"
DB_URI = f"postgresql://postgres:{quote_plus(DB_PASSWORD)}@localhost:5432/theodb"

class AggregateRefresher:
    def __init__(self):
        self.connection = None
        
    def connect_db(self):
        """Connect to the database"""
        try:
            self.connection = psycopg2.connect(DB_URI)
            logger.info("✅ Database connection established")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def refresh_aggregates(self):
        """Refresh the stock_ohlc_15min continuous aggregate"""
        try:
            # Refresh the last 24 hours of data
            refresh_query = """
                CALL refresh_continuous_aggregate('stock_ohlc_15min', NOW() - INTERVAL '24 hours', NOW());
            """
            
            with self.connection.cursor() as cur:
                cur.execute("COMMIT")  # End any existing transaction
                cur.execute(refresh_query)
                self.connection.commit()
            
            logger.info("✅ Refreshed stock_ohlc_15min continuous aggregate")
            
            # Check how many rows we have now
            count_query = "SELECT COUNT(*) FROM stock_ohlc_15min WHERE created >= NOW() - INTERVAL '24 hours'"
            with self.connection.cursor() as cur:
                cur.execute(count_query)
                count = cur.fetchone()[0]
            
            logger.info(f"📊 Found {count} rows in the last 24 hours")
            
        except Exception as e:
            logger.error(f"❌ Error refreshing aggregates: {e}")
            if self.connection:
                self.connection.rollback()
    
    def run(self):
        """Main loop to refresh aggregates every 5 minutes"""
        if not self.connect_db():
            return
        
        logger.info("🚀 Starting aggregate refresher service")
        
        while True:
            try:
                self.refresh_aggregates()
                logger.info("💤 Sleeping for 5 minutes...")
                time.sleep(300)  # Sleep for 5 minutes
                
            except KeyboardInterrupt:
                logger.info("🛑 Stopping aggregate refresher service")
                break
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
        
        if self.connection:
            self.connection.close()

if __name__ == "__main__":
    refresher = AggregateRefresher()
    refresher.run() 