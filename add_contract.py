import psycopg2
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import time
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database configuration
DB_URI = "postgresql://postgres:password@localhost:5432/theostock"

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.contract_details = {}
        self.reqId_map = {}
        self.contract_found = False
        self.contract_data = None

    def contractDetails(self, reqId, contractDetails):
        """Store contract details when received."""
        self.contract_found = True
        self.contract_data = {
            'conid': contractDetails.contract.conId,
            'symbol': contractDetails.contract.symbol,
            'sec_type': contractDetails.contract.secType,
            'exchange': contractDetails.contract.exchange,
            'currency': contractDetails.contract.currency
        }
        logging.info(f"Contract details received for {contractDetails.contract.symbol}")
        logging.info(f"conId: {contractDetails.contract.conId}")
        logging.info(f"secType: {contractDetails.contract.secType}")
        logging.info(f"exchange: {contractDetails.contract.exchange}")
        logging.info(f"currency: {contractDetails.contract.currency}")

    def error(self, reqId, errorCode, errorString):
        """Handle API errors."""
        logging.error(f"Error {errorCode}: {errorString}")
        if errorCode == 354:  # Requested market data is not subscribed
            logging.error("Market data subscription required")
        elif errorCode == 200:  # No security definition found
            logging.error("No contract details found for the given symbol")

def add_contract_to_db(contract_data):
    """Add contract to database."""
    try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        
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
            contract_data['conid'],
            contract_data['symbol'],
            contract_data['sec_type'],
            contract_data['exchange'],
            contract_data['currency']
        ))
        
        conn.commit()
        logging.info(f"Successfully added/updated contract for {contract_data['symbol']}")
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_contract_details(symbol):
    """Get contract details from IBKR and add to database."""
    app = IBapi()
    
    try:
        # Connect to TWS/Gateway
        app.connect('127.0.0.1', 4001, 456)  # Try a different client ID
        logging.info("Connected to IBKR TWS/Gateway")
        
        # Create contract object
        contract = Contract()
        contract.symbol = symbol
        contract.secType = 'STK'  # For stocks
        contract.exchange = 'SMART'  # Smart routing
        contract.currency = 'USD'
        
        # Request contract details
        app.reqContractDetails(1, contract)
        
        # Run the client for a maximum of 10 seconds
        start_time = time.time()
        while not app.contract_found and time.time() - start_time < 10:
            app.run()
            time.sleep(0.1)
        
        if app.contract_found and app.contract_data:
            add_contract_to_db(app.contract_data)
            return True
        else:
            logging.error(f"No contract details found for symbol: {symbol}")
            return False
            
    except Exception as e:
        logging.error(f"Error: {e}")
        return False
    finally:
        app.disconnect()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_contract.py <symbol>")
        print("Example: python add_contract.py AAPL")
        sys.exit(1)
        
    symbol = sys.argv[1].upper()
    success = get_contract_details(symbol)
    
    if success:
        print(f"Successfully added contract for {symbol}")
    else:
        print(f"Failed to add contract for {symbol}") 