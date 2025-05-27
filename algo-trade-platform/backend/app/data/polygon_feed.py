import logging
import time
import threading
from datetime import datetime, timedelta
import requests
from urllib.parse import quote_plus
import psycopg2
from psycopg2.pool import SimpleConnectionPool

# Polygon.io Configuration
POLYGON_API_KEY = "YOUR_POLYGON_API_KEY"  # Replace with your API key
POLYGON_BASE_URL = "https://api.polygon.io"

# Database configuration
password = quote_plus("password")
DB_URI = f"postgresql://postgres:{password}@139.59.38.207:5432/theostock"
pool = SimpleConnectionPool(1, 5, DB_URI)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class PolygonFeed:
    def __init__(self):
        self.active = False
        self.symbols = set()
        self.last_timestamps = {}
        self.connection_errors = 0
        self.MAX_RETRIES = 5
        self.RETRY_DELAY = 5  # seconds

    def start(self):
        """Start the Polygon.io feed."""
        self.active = True
        self.feed_thread = threading.Thread(target=self._run_feed, daemon=True)
        self.feed_thread.start()
        logging.info("✅ Polygon.io feed started")

    def stop(self):
        """Stop the Polygon.io feed."""
        self.active = False
        if hasattr(self, 'feed_thread'):
            self.feed_thread.join()
        logging.info("✅ Polygon.io feed stopped")

    def add_symbol(self, symbol):
        """Add a symbol to track."""
        self.symbols.add(symbol)
        self.last_timestamps[symbol] = datetime.utcnow() - timedelta(minutes=1)
        logging.info(f"✅ Added symbol to Polygon feed: {symbol}")

    def remove_symbol(self, symbol):
        """Remove a symbol from tracking."""
        self.symbols.discard(symbol)
        self.last_timestamps.pop(symbol, None)
        logging.info(f"✅ Removed symbol from Polygon feed: {symbol}")

    def _run_feed(self):
        """Main feed loop."""
        while self.active:
            try:
                for symbol in list(self.symbols):
                    self._fetch_trades(symbol)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                logging.error(f"❌ Error in Polygon feed: {e}")
                self.connection_errors += 1
                if self.connection_errors >= self.MAX_RETRIES:
                    logging.error("❌ Max retries reached for Polygon feed")
                    self.active = False
                time.sleep(self.RETRY_DELAY)

    def _fetch_trades(self, symbol):
        """Fetch trades for a symbol."""
        try:
            # Calculate timestamp for last fetch
            last_timestamp = self.last_timestamps[symbol]
            current_time = datetime.utcnow()
            
            # Convert to milliseconds timestamp
            start_timestamp = int(last_timestamp.timestamp() * 1000)
            end_timestamp = int(current_time.timestamp() * 1000)
            
            # Make API request
            url = f"{POLYGON_BASE_URL}/v2/trades/{symbol}/range/1/minute/{start_timestamp}/{end_timestamp}"
            headers = {"Authorization": f"Bearer {POLYGON_API_KEY}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'success':
                self._process_trades(symbol, data.get('results', []))
                self.last_timestamps[symbol] = current_time
                
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Polygon API request failed for {symbol}: {e}")
            raise
        except Exception as e:
            logging.error(f"❌ Error processing trades for {symbol}: {e}")
            raise

    def _process_trades(self, symbol, trades):
        """Process and store trades."""
        if not trades:
            return

        conn = None
        try:
            conn = pool.getconn()
            with conn.cursor() as cur:
                for trade in trades:
                    # Extract trade data
                    price = float(trade.get('p', 0))  # price
                    size = float(trade.get('s', 0))   # size
                    timestamp = datetime.fromtimestamp(trade.get('t', 0) / 1000)
                    
                    # Insert into database
                    cur.execute("""
                        INSERT INTO stock_ticks (token, symbol, timestamp, price, volume)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (token, timestamp) DO UPDATE SET
                            price = EXCLUDED.price,
                            volume = EXCLUDED.volume;
                    """, (0, symbol, timestamp, price, size))
                
                conn.commit()
                logging.info(f"✅ Processed {len(trades)} trades for {symbol}")
                
        except Exception as e:
            if conn:
                conn.rollback()
            logging.error(f"❌ Database error processing trades: {e}")
            raise
        finally:
            if conn:
                pool.putconn(conn)

# Singleton instance
polygon_feed = PolygonFeed()

def start_polygon_feed():
    """Start the Polygon.io feed."""
    polygon_feed.start()

def stop_polygon_feed():
    """Stop the Polygon.io feed."""
    polygon_feed.stop()

def add_symbol_to_polygon(symbol):
    """Add a symbol to the Polygon.io feed."""
    polygon_feed.add_symbol(symbol)

def remove_symbol_from_polygon(symbol):
    """Remove a symbol from the Polygon.io feed."""
    polygon_feed.remove_symbol(symbol)

if __name__ == "__main__":
    # Test the feed
    start_polygon_feed()
    add_symbol_to_polygon("AAPL")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_polygon_feed() 