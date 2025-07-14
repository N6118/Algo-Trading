import logging
import time
import psycopg2
from psycopg2.extras import execute_values
from functools import lru_cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    def __init__(self, pool):
        self.pool = pool
        self.last_cleanup = time.time()
        self.cleanup_interval = 3600  # 1 hour
        
    def optimize_tick_insertion(self, token, symbol, ts, price, volume):
        """Optimized tick insertion with UPSERT"""
        try:
            conn = self.pool.getconn()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO stock_ticks (token, symbol, timestamp, price, volume) 
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (token, timestamp) 
                    DO UPDATE SET 
                        price = COALESCE(EXCLUDED.price, stock_ticks.price),
                        volume = COALESCE(EXCLUDED.volume, stock_ticks.volume)
                """, (token, symbol, ts, price, volume))
                conn.commit()
            self.pool.putconn(conn)
            return True
        except Exception as e:
            logger.error(f"❌ Database Insert Error: {str(e)}")
            if conn:
                self.pool.putconn(conn)
            return False
    
    @lru_cache(maxsize=1000)
    def get_ohlc(self, interval, token):
        """Optimized OHLC calculation with caching"""
        try:
            conn = self.pool.getconn()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        timestamp,
                        first_value(price) OVER w as open,
                        max(price) OVER w as high,
                        min(price) OVER w as low,
                        last_value(price) OVER w as close,
                        sum(volume) OVER w as volume
                    FROM stock_ticks
                    WHERE token = %s
                    WINDOW w AS (ORDER BY timestamp 
                                 ROWS BETWEEN %s PRECEDING AND CURRENT ROW)
                    ORDER BY timestamp DESC
                    LIMIT 100
                """, (token, interval))
                result = cur.fetchall()
            self.pool.putconn(conn)
            return result
        except Exception as e:
            logger.error(f"❌ OHLC Calculation Error: {str(e)}")
            return []
    
    def bulk_insert_ticks(self, ticks):
        """Bulk insert multiple ticks"""
        if not ticks:
            return True
        
        try:
            conn = self.pool.getconn()
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    INSERT INTO stock_ticks (token, symbol, timestamp, price, volume) 
                    VALUES %s
                    ON CONFLICT (token, timestamp) 
                    DO UPDATE SET 
                        price = COALESCE(EXCLUDED.price, stock_ticks.price),
                        volume = COALESCE(EXCLUDED.volume, stock_ticks.volume)
                    """,
                    ticks,
                    template="(%s, %s, %s, %s, %s)"
                )
                conn.commit()
            self.pool.putconn(conn)
            return True
        except Exception as e:
            logger.error(f"❌ Bulk Insert Error: {str(e)}")
            if conn:
                self.pool.putconn(conn)
            return False
    
    def cleanup_old_data(self):
        """Cleanup old tick data"""
        try:
            conn = self.pool.getconn()
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM stock_ticks
                    WHERE timestamp < NOW() - INTERVAL '7 days'
                """)
                conn.commit()
                logger.info("✅ Cleaned up old tick data")
            self.pool.putconn(conn)
            return True
        except Exception as e:
            logger.error(f"❌ Data Cleanup Error: {str(e)}")
            if conn:
                self.pool.putconn(conn)
            return False
    
    def log_metrics(self):
        """Log database metrics"""
        try:
            conn = self.pool.getconn()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        count(*) as total_ticks,
                        pg_size_pretty(pg_total_relation_size('stock_ticks')) as size,
                        extract(epoch from now() - max(timestamp)) as last_tick_age
                    FROM stock_ticks
                """)
                stats = cur.fetchone()
                logger.info(f"📊 Database Stats - Total Ticks: {stats[0]}, Size: {stats[1]}, Last Tick Age: {stats[2]}s")
            self.pool.putconn(conn)
        except Exception as e:
            logger.error(f"❌ Stats Collection Error: {str(e)}")

# Create optimizer instance
optimizer = DatabaseOptimizer(pool)

# Add cleanup scheduler
def cleanup_scheduler():
    while True:
        if time.time() - optimizer.last_cleanup > optimizer.cleanup_interval:
            optimizer.cleanup_old_data()
            optimizer.last_cleanup = time.time()
        time.sleep(300)  # Check every 5 minutes

# Start cleanup scheduler in a separate thread
cleanup_thread = threading.Thread(target=cleanup_scheduler, daemon=True)
cleanup_thread.start()
