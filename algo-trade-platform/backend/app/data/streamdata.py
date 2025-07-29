import psycopg2
import threading
import time
import logging
import sys
import os
from psycopg2.pool import SimpleConnectionPool
from flask import Flask, jsonify
from datetime import datetime
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from urllib.parse import quote_plus

# Import Telegram notifier
from backend.app.services.telegram_notifier import (
    send_server_start_notification,
    send_server_stop_notification,
    send_first_entry_notification,
    send_last_entry_notification,
    send_connection_status
)

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import the FuturesRollManager
from backend.app.data.futures_roll import FuturesRollManager

# TWS Connection Configuration
TWS_HOST = '127.0.0.1'  # Change this to your TWS server IP
TWS_PORT = 7496  # Default TWS port (7496 for live, 7497 for paper trading)
TWS_CLIENT_ID = 123  # Unique client ID for this connection

# Remote database configuration
password = quote_plus("password")
DB_URI = f"postgresql://postgres:{password}@localhost:5432/theodb"
pool = SimpleConnectionPool(1, 5, DB_URI)  # Connection pool (min=1, max=5)

app = Flask(__name__)

# Initialize futures roll manager
futures_roll_manager = FuturesRollManager()

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.contract_details = {}  # symbol -> conId mapping
        self.reqId_map = {}  # reqId -> (symbol, conId) mapping
        self.connected = False
        self.connection_timeout = 10  # seconds to wait for connection
        self.first_entry_sent = False  # Track if first entry notification was sent
        self.last_entry_data = None  # Store last entry data for shutdown notification

    def connectAck(self):
        """Called when connection is acknowledged by TWS."""
        self.connected = True
        logging.info("✅ TWS Connection Acknowledged")
        # Send Telegram notification for connection established
        send_connection_status("connected")
        super().connectAck()

    def connectionClosed(self):
        """Called when connection is closed."""
        self.connected = False
        logging.warning("❌ TWS Connection Closed")
        # Send Telegram notification for connection lost
        send_connection_status("disconnected")
        super().connectionClosed()

    def wait_for_connection(self):
        """Wait for connection to be established."""
        start_time = time.time()
        while not self.connected and (time.time() - start_time) < self.connection_timeout:
            time.sleep(0.1)
        return self.connected

    def contractDetails(self, reqId, contractDetails):
        """Receive contract details from IBKR and store in database."""
        try:
            conn = pool.getconn()
            with conn.cursor() as cur:
                try:
                    # Check if we have a placeholder record (conId = 0) for this symbol
                    cur.execute("""
                        SELECT conid FROM ibkr_contracts 
                        WHERE symbol = %s AND exchange = %s AND conid = 0
                    """, (contractDetails.contract.symbol, contractDetails.contract.exchange))
                    
                    placeholder_exists = cur.fetchone()
                    
                    if placeholder_exists:
                        # Update the placeholder record with the real conId
                        cur.execute("""
                            UPDATE ibkr_contracts 
                            SET conid = %s, last_updated = CURRENT_TIMESTAMP
                            WHERE symbol = %s AND exchange = %s AND conid = 0
                        """, (
                            contractDetails.contract.conId,
                            contractDetails.contract.symbol,
                            contractDetails.contract.exchange
                        ))
                    else:
                        # Insert or update contract details
                        cur.execute("""
                            INSERT INTO ibkr_contracts (conid, symbol, sec_type, exchange, currency, last_updated)
                            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (conid) DO UPDATE SET
                                symbol = EXCLUDED.symbol,
                                sec_type = EXCLUDED.sec_type,
                                exchange = EXCLUDED.exchange,
                                currency = EXCLUDED.currency,
                                last_updated = CURRENT_TIMESTAMP;
                        """, (
                            contractDetails.contract.conId,
                            contractDetails.contract.symbol,
                            contractDetails.contract.secType,
                            contractDetails.contract.exchange,
                            contractDetails.contract.currency
                        ))
                    
                    conn.commit()
                    
                    # Update our mappings
                    symbol = contractDetails.contract.symbol
                    conId = contractDetails.contract.conId
                    self.contract_details[symbol] = conId
                    self.reqId_map[reqId] = (symbol, conId)
                    
                    logging.info(f"✅ Stored contract details for {symbol} (conId: {conId})")
                except Exception as e:
                    conn.rollback()
                    raise e
            pool.putconn(conn)
        except Exception as e:
            logging.error(f"❌ Error storing contract details: {e}")
            if conn:
                pool.putconn(conn)

    def get_active_contracts(self):
        """Fetch all active contracts from database."""
        conn = None
        try:
            conn = pool.getconn()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT conid, symbol, sec_type, exchange, currency 
                    FROM ibkr_contracts 
                    WHERE is_active = true
                    AND last_updated > NOW() - INTERVAL '24 hours'
                """)
                contracts = cur.fetchall()
            
            contract_list = []
            for conid, symbol, sec_type, exchange, currency in contracts:
                contract = Contract()
                contract.conId = conid
                contract.symbol = symbol
                contract.secType = sec_type
                contract.exchange = exchange
                contract.currency = currency
                
                # Handle futures contracts - add contract month
                if sec_type == 'FUT' and symbol == 'MES':
                    # For MES, we need to specify the contract month
                    # Using September 2025 as an example - this should be dynamic
                    contract.lastTradeDateOrContractMonth = "202509"
                
                contract_list.append(contract)
                
                # Update our mappings
                self.contract_details[symbol] = conid
                
            return contract_list
        except Exception as e:
            logging.error(f"❌ Error fetching active contracts: {e}")
            return []
        finally:
            if conn:
                pool.putconn(conn)

    def _get_contract_for_reqid(self, reqId):
        """Helper to get contract info from reqId."""
        return self.reqId_map.get(reqId)

    def _validate_tick_data(self, token, symbol, ts, price, volume):
        """Validate tick data before insertion."""
        try:
            # Basic validation
            if not token or not symbol or not ts:
                return False, "Missing required fields"
                
            # Price validation
            if price is not None:
                if not isinstance(price, (int, float)):
                    return False, "Invalid price type"
                if price <= 0:
                    return False, "Invalid price value"
                    
            # Volume validation
            if volume is not None and volume != -1:
                if not isinstance(volume, (int, float)):
                    return False, "Invalid volume type"
                if volume < 0:
                    return False, "Invalid volume value"
                    
            return True, None
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def tickPrice(self, reqId, tickType, price, attrib):
        """Process tick price data."""
        if tickType == 68:  # Last Price
            ts = datetime.utcnow().replace(microsecond=0)
            contract_info = self._get_contract_for_reqid(reqId)
            
            if contract_info:
                symbol, token = contract_info
                # Validate data
                is_valid, error_msg = self._validate_tick_data(token, symbol, ts, price, -1)
                if is_valid:
                    logging.info(f"📊 Tick Price: {ts}, Token: {token}, Symbol: {symbol}, Price: {price}")
                    
                    # Track first entry for Telegram notification
                    if not self.first_entry_sent:
                        send_first_entry_notification(symbol, price, 0)  # Volume will be updated when available
                        self.first_entry_sent = True
                    
                    # Store last entry data for shutdown notification
                    self.last_entry_data = {
                        'symbol': symbol,
                        'price': price,
                        'volume': 0,  # Will be updated when volume data arrives
                        'timestamp': ts
                    }
                    
                    # Store price in a temporary cache
                    self._cache_tick_data(token, symbol, ts, price=price)
                else:
                    logging.error(f"❌ Invalid tick price data: {error_msg}")
            else:
                logging.warning(f"⚠️ No contract found for reqId: {reqId}")

    def tickSize(self, reqId, tickType, size):
        """Process tick size/volume data."""
        if tickType == 8:  # Volume data
            ts = datetime.utcnow().replace(microsecond=0)
            contract_info = self._get_contract_for_reqid(reqId)
            
            if contract_info:
                symbol, token = contract_info
                # Validate data
                is_valid, error_msg = self._validate_tick_data(token, symbol, ts, None, size)
                if is_valid:
                    logging.info(f"📊 Tick Volume: {ts}, Token: {token}, Symbol: {symbol}, Volume: {size}")
                    
                    # Update last entry data with volume
                    if self.last_entry_data and self.last_entry_data['symbol'] == symbol:
                        self.last_entry_data['volume'] = size
                    
                    insert_tick(token, symbol, ts, None, size)
                else:
                    logging.error(f"❌ Invalid tick volume data: {error_msg}")
            else:
                logging.warning(f"⚠️ No contract found for reqId: {reqId}")

    def tickString(self, reqId, tickType, value):
        """Process tick string data."""
        if tickType == 88:  # Volume delivered as a string
            try:
                vol = float(value)
            except Exception as e:
                vol = -1
                
            ts = datetime.utcnow().replace(microsecond=0)
            contract_info = self._get_contract_for_reqid(reqId)
            
            if contract_info:
                symbol, token = contract_info
                logging.info(f"📊 Tick Volume (string): {ts}, Token: {token}, Symbol: {symbol}, Volume: {vol}")
                # Store volume in a temporary cache
                self._cache_tick_data(token, symbol, ts, volume=vol)
            else:
                logging.warning(f"⚠️ No contract found for reqId: {reqId}")

    def error(self, reqId, errorCode, errorString):
        """Handle IBKR API errors."""
        logging.error(f"⚠️ API Error {errorCode}: {errorString}")

    def _cache_tick_data(self, token, symbol, ts, price=None, volume=None):
        """Cache tick data and insert when both price and volume are available."""
        cache_key = f"{token}_{ts.isoformat()}"
        
        # Initialize cache if not exists
        if not hasattr(self, '_tick_cache'):
            self._tick_cache = {}
            
        # Get or create cache entry
        if cache_key not in self._tick_cache:
            self._tick_cache[cache_key] = {
                'token': token,
                'symbol': symbol,
                'ts': ts,
                'price': None,
                'volume': None
            }
            
        # Update cache with new data
        if price is not None:
            self._tick_cache[cache_key]['price'] = price
        if volume is not None:
            self._tick_cache[cache_key]['volume'] = volume
            
        # Check if we have both price and volume
        cache_entry = self._tick_cache[cache_key]
        if cache_entry['price'] is not None and cache_entry['volume'] is not None:
            # Insert complete data
            insert_tick(
                cache_entry['token'],
                cache_entry['symbol'],
                cache_entry['ts'],
                cache_entry['price'],
                cache_entry['volume']
            )
            # Remove from cache
            del self._tick_cache[cache_key]
            
        # Clean up old cache entries (older than 5 seconds)
        current_time = datetime.utcnow()
        for key in list(self._tick_cache.keys()):
            if (current_time - self._tick_cache[key]['ts']).total_seconds() > 5:
                del self._tick_cache[key]

def run_ibkr():
    """Start IBKR API loop in a separate thread."""
    app_ibkr = IBapi()
    
    # Send server start notification
    send_server_start_notification()
    
    # Start futures roll manager
    futures_roll_manager.start()
    
    # Attempt to connect to TWS
    try:
        logging.info(f"📡 Connecting to TWS at {TWS_HOST}:{TWS_PORT}...")
        app_ibkr.connect(TWS_HOST, TWS_PORT, TWS_CLIENT_ID)
        
        # Wait for connection to be established
        if not app_ibkr.wait_for_connection():
            error_msg = "Failed to connect to TWS within timeout period"
            logging.error(f"❌ {error_msg}")
            send_connection_status("error", error_msg)
            raise Exception(error_msg)
            
        api_thread = threading.Thread(target=app_ibkr.run, daemon=True)
        api_thread.start()
        time.sleep(1)  # Allow time for connection

        # Get active contracts from database
        contracts = app_ibkr.get_active_contracts()
        
        # If no contracts in database, add VIX as default
        if not contracts:
            logging.info("No contracts in database, adding VIX as default")
            vix_contract = Contract()
            vix_contract.symbol = 'VIX'
            vix_contract.secType = 'IND'
            vix_contract.exchange = 'CBOE'
            vix_contract.currency = 'USD'
            contracts = [vix_contract]

        # Request contract details and market data for each contract
        for i, contract in enumerate(contracts):
            # Request contract details to get/update conId
            app_ibkr.reqContractDetails(i+1, contract)
            time.sleep(0.1)  # Small delay between requests
            
            # Request market data
            app_ibkr.reqMarketDataType(3)  # 3 = Delayed Data
            app_ibkr.reqMktData(i+1, contract, "233", False, False, [])
            time.sleep(0.1)  # Small delay between requests

        logging.info("📌 IBKR Market Data Collection Running...")
        while True:
            if not app_ibkr.connected:
                logging.error("❌ Lost connection to TWS")
                break
            time.sleep(1)
            
    except Exception as e:
        logging.error(f"❌ Failed to connect to TWS: {e}")
        send_connection_status("error", str(e))
    finally:
        # Send last entry notification if we have data
        if app_ibkr.last_entry_data:
            send_last_entry_notification(
                app_ibkr.last_entry_data['symbol'],
                app_ibkr.last_entry_data['price'],
                app_ibkr.last_entry_data['volume']
            )
        
        # Send server stop notification
        send_server_stop_notification()
        
        # Stop futures roll manager
        futures_roll_manager.stop()
        if app_ibkr.isConnected():
            logging.warning("❌ Stopping IBKR...")
            app_ibkr.disconnect()

# Database Operations
def insert_tick(token, symbol, ts, price, volume):
    """
    Insert or update a tick in the database.
    The timestamp (ts) is provided by the caller (truncated to the second).
    If a row for the same token and ts exists, update price and/or volume accordingly.
    """
    try:
        conn = pool.getconn()
        with conn.cursor() as cur:
            # First check if a row exists for this timestamp
            cur.execute("""
                SELECT price, volume FROM stock_ticks 
                WHERE token = %s AND timestamp = %s
            """, (token, ts))
            existing = cur.fetchone()
            
            if existing:
                # Update existing row, preserving non-null values
                current_price, current_volume = existing
                new_price = price if price is not None else current_price
                new_volume = volume if volume != -1 else current_volume
                
                cur.execute("""
                    UPDATE stock_ticks 
                    SET price = %s, volume = %s
                    WHERE token = %s AND timestamp = %s
                """, (new_price, new_volume, token, ts))
            else:
                # Insert new row
                cur.execute("""
                    INSERT INTO stock_ticks (token, symbol, timestamp, price, volume) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (token, symbol, ts, price, volume))
            
            conn.commit()
        pool.putconn(conn)
        logging.info(f"✅ Inserted/Updated Tick - Token: {token}, Symbol: {symbol}, ts: {ts}, Price: {price}, Volume: {volume}")
    except psycopg2.Error as e:
        logging.error(f"❌ Database Insert Error: {e.pgcode} - {e.pgerror}")
    except Exception as e:
        logging.error(f"❌ Unexpected Error: {e}")

@app.route('/ohlc/<interval>/<token>')
def get_ohlc(interval, token):
    """Fetch OHLC data using token."""
    try:
        conn = pool.getconn()
        with conn.cursor() as cur:
            table = f"stock_ohlc_{interval}"
            query = f"""
                SELECT bucket, token, symbol, open, high, low, close
                FROM {table}
                WHERE token = %s
                ORDER BY bucket DESC
                LIMIT 10;
            """
            cur.execute(query, (token,))
            rows = cur.fetchall()
        pool.putconn(conn)
        return jsonify(rows)
    except Exception as e:
        logging.error(f"❌ OHLC Query Error: {e}")
        return jsonify({"error": "Failed to fetch OHLC data"}), 500

def run_flask():
    """Start Flask API server."""
    app.run(host='0.0.0.0', port=5005, threaded=True)

if __name__ == "__main__":
    threading.Thread(target=run_ibkr, daemon=True).start()
    threading.Thread(target=run_flask, daemon=True).start()
    while True:
        time.sleep(1)
