import logging
import time
import threading
from datetime import datetime, timedelta
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from urllib.parse import quote_plus

# Database configuration
password = quote_plus("password")
DB_URI = f"postgresql://postgres:{password}@139.59.38.207:5432/theostock"
pool = SimpleConnectionPool(1, 5, DB_URI)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class SystemMonitor:
    def __init__(self):
        self.active = False
        self.monitoring_thread = None
        self.last_check = {}
        self.latency_threshold = 1000  # milliseconds
        self.health_check_interval = 60  # seconds

    def start(self):
        """Start the monitoring service."""
        self.active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitoring_thread.start()
        logging.info("✅ System monitoring started")

    def stop(self):
        """Stop the monitoring service."""
        self.active = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logging.info("✅ System monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.active:
            try:
                self._check_system_health()
                self._check_data_latency()
                time.sleep(self.health_check_interval)
            except Exception as e:
                logging.error(f"❌ Error in monitoring loop: {e}")

    def _check_system_health(self):
        """Check overall system health."""
        try:
            conn = pool.getconn()
            with conn.cursor() as cur:
                # Check database connection
                cur.execute("SELECT 1")
                
                # Check table sizes
                cur.execute("""
                    SELECT relname, n_live_tup 
                    FROM pg_stat_user_tables 
                    WHERE relname IN ('stock_ticks', 'ibkr_contracts')
                """)
                table_stats = cur.fetchall()
                
                # Log table statistics
                for table, rows in table_stats:
                    logging.info(f"📊 Table {table}: {rows:,} rows")
                
                # Check for any errors in the last hour
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM stock_ticks 
                    WHERE timestamp > NOW() - INTERVAL '1 hour'
                """)
                recent_ticks = cur.fetchone()[0]
                
                if recent_ticks == 0:
                    logging.warning("⚠️ No ticks received in the last hour")
                
            pool.putconn(conn)
            
        except Exception as e:
            logging.error(f"❌ System health check failed: {e}")
            if conn:
                pool.putconn(conn)

    def _check_data_latency(self):
        """Check data latency for each symbol."""
        try:
            conn = pool.getconn()
            with conn.cursor() as cur:
                # Get latest tick for each symbol
                cur.execute("""
                    SELECT symbol, MAX(timestamp) as last_tick
                    FROM stock_ticks
                    WHERE timestamp > NOW() - INTERVAL '1 hour'
                    GROUP BY symbol
                """)
                
                current_time = datetime.utcnow()
                for symbol, last_tick in cur.fetchall():
                    if last_tick:
                        latency = (current_time - last_tick).total_seconds() * 1000
                        if latency > self.latency_threshold:
                            logging.warning(f"⚠️ High latency for {symbol}: {latency:.2f}ms")
                        else:
                            logging.info(f"✅ Normal latency for {symbol}: {latency:.2f}ms")
                    else:
                        logging.warning(f"⚠️ No recent data for {symbol}")
            
            pool.putconn(conn)
            
        except Exception as e:
            logging.error(f"❌ Data latency check failed: {e}")
            if conn:
                pool.putconn(conn)

    def record_tick_latency(self, symbol, exchange_timestamp, received_timestamp):
        """Record tick latency for analysis."""
        try:
            latency = (received_timestamp - exchange_timestamp).total_seconds() * 1000
            
            conn = pool.getconn()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO tick_latency (symbol, exchange_timestamp, received_timestamp, latency_ms)
                    VALUES (%s, %s, %s, %s)
                """, (symbol, exchange_timestamp, received_timestamp, latency))
                conn.commit()
            
            pool.putconn(conn)
            
            if latency > self.latency_threshold:
                logging.warning(f"⚠️ High tick latency for {symbol}: {latency:.2f}ms")
            
        except Exception as e:
            logging.error(f"❌ Failed to record tick latency: {e}")
            if conn:
                pool.putconn(conn)

# Create database table for latency tracking
def setup_latency_table():
    """Create the tick_latency table if it doesn't exist."""
    try:
        conn = pool.getconn()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tick_latency (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    exchange_timestamp TIMESTAMPTZ NOT NULL,
                    received_timestamp TIMESTAMPTZ NOT NULL,
                    latency_ms DOUBLE PRECISION NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_tick_latency_symbol 
                ON tick_latency (symbol, exchange_timestamp DESC);
                
                CREATE INDEX IF NOT EXISTS idx_tick_latency_created 
                ON tick_latency (created_at DESC);
            """)
            conn.commit()
        pool.putconn(conn)
        logging.info("✅ Tick latency table setup complete")
    except Exception as e:
        logging.error(f"❌ Failed to setup tick latency table: {e}")
        if conn:
            pool.putconn(conn)

# Singleton instance
system_monitor = SystemMonitor()

def start_monitoring():
    """Start the system monitoring service."""
    setup_latency_table()
    system_monitor.start()

def stop_monitoring():
    """Stop the system monitoring service."""
    system_monitor.stop()

def record_latency(symbol, exchange_timestamp, received_timestamp):
    """Record tick latency."""
    system_monitor.record_tick_latency(symbol, exchange_timestamp, received_timestamp)

if __name__ == "__main__":
    # Test the monitoring service
    start_monitoring()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_monitoring() 