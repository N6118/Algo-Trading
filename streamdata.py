import psycopg2
import threading
import time
import logging
from psycopg2.pool import SimpleConnectionPool
from flask import Flask, jsonify
from datetime import datetime
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

# ✅ Database Configuration
DB_URI = "postgresql://postgres:password@localhost:5432/theostock"
pool = SimpleConnectionPool(1, 5, DB_URI)  # ✅ Connection pool (min=1, max=5)

app = Flask(__name__)

# ✅ Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ====================== IBKR CLIENT SETUP ======================

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.contract_details = {}  # symbol -> conId mapping
        self.reqId_map = {}  # reqId -> (symbol, conId) mapping
        self.last_heartbeat = datetime.utcnow()
        self.reconnect_count = 0
        self.MAX_RECONNECTS = 5

    def contractDetails(self, reqId, contractDetails):
        """Receive contract details from IBKR and store in database."""
        try:
            conn = pool.getconn()
            with conn.cursor() as cur:
                try:
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

    def _check_heartbeat(self):
        """Check if we're still receiving data."""
        if (datetime.utcnow() - self.last_heartbeat).seconds > 30:  # No data for 30 seconds
            logging.warning("❌ No data received for 30 seconds, attempting reconnection...")
            self.handle_connection_error()
        
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
                    insert_tick(token, symbol, ts, price, -1)
                    self.last_heartbeat = datetime.utcnow()  # Update heartbeat
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
                    insert_tick(token, symbol, ts, None, size)
                    self.last_heartbeat = datetime.utcnow()  # Update heartbeat
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
                insert_tick(token, symbol, ts, None, vol)
            else:
                logging.warning(f"⚠️ No contract found for reqId: {reqId}")

    def error(self, reqId, errorCode, errorString):
        """Handle IBKR API errors."""
        logging.error(f"⚠️ API Error {errorCode}: {errorString}")
        
        # Handle connection-related errors
        if errorCode in [1100, 1101, 1102]:  # Connection-related errors
            self.handle_connection_error()
        
    def handle_connection_error(self):
        """Handle connection errors with reconnection logic."""
        if self.reconnect_count < self.MAX_RECONNECTS:
            self.reconnect_count += 1
            logging.warning(f"📡 Attempting reconnection {self.reconnect_count}/{self.MAX_RECONNECTS}")
            
            # Disconnect if still connected
            if self.isConnected():
                self.disconnect()
            
            time.sleep(5)  # Wait before reconnecting
            
            try:
                self.connect('127.0.0.1', 7496, 123)
                self.reqPositions()  # Test the connection
                self.reconnect_count = 0  # Reset counter on successful reconnection
                logging.info("✅ Successfully reconnected to IBKR")
                
                # Resubscribe to market data
                self._resubscribe_market_data()
            except Exception as e:
                logging.error(f"❌ Reconnection failed: {e}")
        else:
            logging.error("❌ Max reconnection attempts reached. Manual intervention required.")

    def _resubscribe_market_data(self):
        """Resubscribe to market data for all active contracts."""
        try:
            # Clear existing mappings
            self.reqId_map.clear()
            
            # Get active contracts and resubscribe
            contracts = self.get_active_contracts()
            for i, contract in enumerate(contracts):
                reqId = i + 1
                self.reqId_map[reqId] = (contract.symbol, contract.conId)
                self.reqMarketDataType(3)
                self.reqMktData(reqId, contract, "233", False, False, [])
                time.sleep(0.1)
        except Exception as e:
            logging.error(f"❌ Error resubscribing to market data: {e}")

def run_ibkr():
    """Start IBKR API loop in a separate thread."""
    app_ibkr = IBapi()
    app_ibkr.connect('127.0.0.1', 7496, 123)
    api_thread = threading.Thread(target=app_ibkr.run, daemon=True)
    api_thread.start()
    time.sleep(1)  # Allow time for connection

    # Get active contracts from database
    contracts = app_ibkr.get_active_contracts()
    
    # If no contracts in database, add VIX as default
    if not contracts:
        print("No contracts in database, adding VIX as default")
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
    try:
        while True:
            app_ibkr._check_heartbeat()  # Check for data freshness
            time.sleep(1)
    except KeyboardInterrupt:
        logging.warning("❌ Stopping IBKR...")
        app_ibkr.disconnect()

# ====================== DATABASE OPERATIONS ======================

def insert_tick(token, symbol, ts, price, volume):
    """
    Insert or update a tick in the database.
    The timestamp (ts) is provided by the caller (truncated to the second).
    If a row for the same token and ts exists, update price and/or volume accordingly.
    """
    try:
        conn = pool.getconn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO stock_ticks (token, symbol, timestamp, price, volume) 
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (token, timestamp) DO UPDATE SET
                    price = CASE WHEN EXCLUDED.price IS NOT NULL THEN EXCLUDED.price ELSE stock_ticks.price END,
                    volume = CASE WHEN EXCLUDED.volume != -1 THEN EXCLUDED.volume ELSE stock_ticks.volume END;
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
