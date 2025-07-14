import logging
import psycopg2
import threading
import time
from datetime import datetime, timedelta
from psycopg2.pool import SimpleConnectionPool
from urllib.parse import quote_plus

# Database configuration
password = quote_plus("password")
DB_URI = f"postgresql://postgres:{password}@100.121.186.86:5432/theodb"
pool = SimpleConnectionPool(1, 5, DB_URI)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class FuturesRollManager:
    def __init__(self):
        self.active = False
        self.roll_thread = None
        self.check_interval = 3600  # Check every hour

    def start(self):
        """Start the futures roll management service."""
        self.active = True
        self.roll_thread = threading.Thread(target=self._roll_check_loop, daemon=True)
        self.roll_thread.start()
        logging.info("✅ Futures roll management started")

    def stop(self):
        """Stop the futures roll management service."""
        self.active = False
        if self.roll_thread:
            self.roll_thread.join()
        logging.info("✅ Futures roll management stopped")

    def _roll_check_loop(self):
        """Main loop for checking and managing futures rolls."""
        while self.active:
            try:
                self._check_pending_rolls()
                time.sleep(self.check_interval)
            except Exception as e:
                logging.error(f"❌ Error in roll check loop: {e}")

    def _check_pending_rolls(self):
        """Check for futures contracts that need to be rolled."""
        conn = None
        try:
            conn = pool.getconn()
            with conn.cursor() as cur:
                # Get all active futures contracts that need rolling
                cur.execute("""
                    SELECT 
                        fcr.id,
                        fcr.base_symbol,
                        fcr.front_month_conid,
                        fcr.back_month_conid,
                        fcr.roll_date,
                        fcr.roll_type,
                        fcr.roll_offset,
                        ic1.symbol as front_month_symbol,
                        ic2.symbol as back_month_symbol
                    FROM futures_contract_rolls fcr
                    JOIN ibkr_contracts ic1 ON fcr.front_month_conid = ic1.conid
                    JOIN ibkr_contracts ic2 ON fcr.back_month_conid = ic2.conid
                    WHERE fcr.is_active = true
                    AND fcr.roll_date <= CURRENT_DATE + INTERVAL '1 day'
                    ORDER BY fcr.roll_date ASC;
                """)
                pending_rolls = cur.fetchall()

                for roll in pending_rolls:
                    self._process_roll(cur, roll)

        except Exception as e:
            logging.error(f"❌ Error checking pending rolls: {e}")
        finally:
            if conn:
                pool.putconn(conn)

    def _process_roll(self, cur, roll):
        """Process a single futures contract roll."""
        try:
            roll_id, base_symbol, front_month_conid, back_month_conid, roll_date, roll_type, roll_offset, front_symbol, back_symbol = roll
            
            # Update the continuous contract data
            cur.execute("""
                WITH roll_data AS (
                    SELECT 
                        timestamp,
                        CASE 
                            WHEN timestamp < %s THEN price
                            ELSE price * (SELECT price FROM stock_ticks 
                                        WHERE token = %s AND timestamp = %s) /
                                     (SELECT price FROM stock_ticks 
                                      WHERE token = %s AND timestamp = %s)
                        END as adjusted_price,
                        volume
                    FROM stock_ticks
                    WHERE token = %s
                )
                INSERT INTO stock_ticks (token, symbol, timestamp, price, volume)
                SELECT 
                    %s,  -- Use the back month conid
                    %s,  -- Use the base symbol
                    timestamp,
                    adjusted_price,
                    volume
                FROM roll_data
                ON CONFLICT (token, timestamp) DO UPDATE SET
                    price = EXCLUDED.price,
                    volume = EXCLUDED.volume;
            """, (
                roll_date,
                back_month_conid, roll_date,
                front_month_conid, roll_date,
                front_month_conid,
                back_month_conid,
                base_symbol
            ))

            # Mark the roll as processed
            cur.execute("""
                UPDATE futures_contract_rolls
                SET is_active = false,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s;
            """, (roll_id,))

            logging.info(f"✅ Processed roll for {base_symbol} from {front_symbol} to {back_symbol}")

        except Exception as e:
            logging.error(f"❌ Error processing roll {roll_id}: {e}")
            raise

    def add_roll_schedule(self, base_symbol, front_month_conid, back_month_conid, roll_date, roll_type='EXPIRY', roll_offset=5):
        """Add a new futures contract roll schedule."""
        conn = None
        try:
            conn = pool.getconn()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO futures_contract_rolls 
                    (base_symbol, front_month_conid, back_month_conid, roll_date, roll_type, roll_offset)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (base_symbol, front_month_conid, back_month_conid, roll_date)
                    DO UPDATE SET
                        roll_type = EXCLUDED.roll_type,
                        roll_offset = EXCLUDED.roll_offset,
                        updated_at = CURRENT_TIMESTAMP;
                """, (base_symbol, front_month_conid, back_month_conid, roll_date, roll_type, roll_offset))
                conn.commit()
                logging.info(f"✅ Added roll schedule for {base_symbol}")
        except Exception as e:
            logging.error(f"❌ Error adding roll schedule: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                pool.putconn(conn)

    def get_active_rolls(self, base_symbol=None):
        """Get all active futures contract rolls."""
        conn = None
        try:
            conn = pool.getconn()
            with conn.cursor() as cur:
                if base_symbol:
                    cur.execute("""
                        SELECT 
                            fcr.*,
                            ic1.symbol as front_month_symbol,
                            ic2.symbol as back_month_symbol
                        FROM futures_contract_rolls fcr
                        JOIN ibkr_contracts ic1 ON fcr.front_month_conid = ic1.conid
                        JOIN ibkr_contracts ic2 ON fcr.back_month_conid = ic2.conid
                        WHERE fcr.is_active = true
                        AND fcr.base_symbol = %s
                        ORDER BY fcr.roll_date ASC;
                    """, (base_symbol,))
                else:
                    cur.execute("""
                        SELECT 
                            fcr.*,
                            ic1.symbol as front_month_symbol,
                            ic2.symbol as back_month_symbol
                        FROM futures_contract_rolls fcr
                        JOIN ibkr_contracts ic1 ON fcr.front_month_conid = ic1.conid
                        JOIN ibkr_contracts ic2 ON fcr.back_month_conid = ic2.conid
                        WHERE fcr.is_active = true
                        ORDER BY fcr.roll_date ASC;
                    """)
                return cur.fetchall()
        except Exception as e:
            logging.error(f"❌ Error getting active rolls: {e}")
            return []
        finally:
            if conn:
                pool.putconn(conn) 