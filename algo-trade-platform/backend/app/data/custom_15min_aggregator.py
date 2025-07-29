#!/usr/bin/env python3
"""
Custom 15-Minute Aggregator
Replaces the unreliable TimescaleDB automatic refresh with a custom solution
"""

import psycopg2
import pandas as pd
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

class Custom15MinAggregator:
    def __init__(self):
        self.connection = None
        self.last_processed_bucket = None
        
    def connect_db(self):
        """Connect to the database"""
        try:
            self.connection = psycopg2.connect(DB_URI)
            logger.info("✅ Database connection established")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def get_unprocessed_buckets(self):
        """Get 15-minute buckets that need to be processed"""
        try:
            query = """
                WITH raw_buckets AS (
                    SELECT 
                        time_bucket('15 minutes', timestamp) as bucket,
                        token,
                        symbol,
                        COUNT(*) as tick_count,
                        MIN(timestamp) as min_time,
                        MAX(timestamp) as max_time
                    FROM stock_ticks 
                    WHERE timestamp >= NOW() - INTERVAL '24 hours'
                    GROUP BY time_bucket('15 minutes', timestamp), token, symbol
                    HAVING COUNT(*) >= 10  -- At least 10 ticks to consider bucket complete
                ),
                existing_buckets AS (
                    SELECT DISTINCT created, token, symbol
                    FROM stock_ohlc_15min 
                    WHERE created >= NOW() - INTERVAL '24 hours'
                )
                SELECT 
                    rb.bucket,
                    rb.token,
                    rb.symbol,
                    rb.tick_count,
                    rb.min_time,
                    rb.max_time
                FROM raw_buckets rb
                LEFT JOIN existing_buckets eb ON rb.bucket = eb.created AND rb.token = eb.token AND rb.symbol = eb.symbol
                WHERE eb.created IS NULL
                ORDER BY rb.bucket, rb.token, rb.symbol
            """
            
            df = pd.read_sql_query(query, self.connection)
            return df
        except Exception as e:
            logger.error(f"❌ Error getting unprocessed buckets: {e}")
            return pd.DataFrame()
    
    def aggregate_bucket(self, bucket, token, symbol):
        """Aggregate a single 15-minute bucket"""
        try:
            query = """
                SELECT 
                    time_bucket('15 minutes', timestamp) as bucket,
                    token,
                    symbol,
                    first(price, timestamp) as open,
                    max(price) as high,
                    min(price) as low,
                    last(price, timestamp) as close,
                    sum(volume) as volume
                FROM stock_ticks 
                WHERE time_bucket('15 minutes', timestamp) = %s 
                AND token = %s 
                AND symbol = %s
                GROUP BY time_bucket('15 minutes', timestamp), token, symbol
            """
            
            df = pd.read_sql_query(query, self.connection, params=(bucket, token, symbol))
            
            if not df.empty:
                # Insert into continuous aggregate
                insert_query = """
                    INSERT INTO stock_ohlc_15min (created, token, symbol, open, high, low, close, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT ON CONSTRAINT stock_ohlc_15min_created_token_symbol_key
                    DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume
                """
                
                row = df.iloc[0]
                with self.connection.cursor() as cur:
                    cur.execute(insert_query, (
                        row['bucket'], row['token'], row['symbol'],
                        row['open'], row['high'], row['low'], row['close'], row['volume']
                    ))
                    self.connection.commit()
                
                logger.info(f"✅ Aggregated bucket {bucket} for {symbol} ({row['tick_count']} ticks)")
                return True
            else:
                logger.warning(f"⚠️ No data found for bucket {bucket} {token} {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error aggregating bucket {bucket} for {symbol}: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def process_all_buckets(self):
        """Process all unprocessed 15-minute buckets"""
        try:
            df = self.get_unprocessed_buckets()
            
            if df.empty:
                logger.info("✅ No unprocessed buckets found")
                return
            
            logger.info(f"🔄 Found {len(df)} unprocessed buckets")
            
            success_count = 0
            for _, row in df.iterrows():
                if self.aggregate_bucket(row['bucket'], row['token'], row['symbol']):
                    success_count += 1
            
            logger.info(f"✅ Successfully processed {success_count}/{len(df)} buckets")
            
        except Exception as e:
            logger.error(f"❌ Error processing buckets: {e}")
    
    def run(self):
        """Main run loop - check every 5 minutes"""
        logger.info("🚀 Starting Custom 15-Minute Aggregator")
        
        if not self.connect_db():
            return
        
        try:
            while True:
                current_time = datetime.now()
                logger.info(f"⏰ Checking for unprocessed buckets at {current_time}")
                
                self.process_all_buckets()
                
                # Wait 5 minutes before next check
                logger.info("💤 Sleeping for 5 minutes...")
                time.sleep(300)
                
        except KeyboardInterrupt:
            logger.info("🛑 Custom 15-Minute Aggregator stopped by user")
        except Exception as e:
            logger.error(f"❌ Custom 15-Minute Aggregator error: {e}")
        finally:
            if self.connection:
                self.connection.close()

if __name__ == "__main__":
    aggregator = Custom15MinAggregator()
    aggregator.run() 