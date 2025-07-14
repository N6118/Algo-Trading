import logging
import psycopg2
from datetime import datetime

logger = logging.getLogger(__name__)

def optimize_database():
    """Optimize database tables and indexes"""
    try:
        conn = psycopg2.connect(
            dbname="theostock",
            user="postgres",
            password="password",
            host="139.59.38.207",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Create optimized indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_stock_ticks_timestamp ON stock_ticks(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_stock_ticks_symbol_timestamp ON stock_ticks(symbol, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_ibkr_contracts_symbol ON ibkr_contracts(symbol)"
        ]
        
        for idx in indexes:
            try:
                cur.execute(idx)
                logger.info(f"Created index: {idx}")
            except Exception as e:
                logger.warning(f"Failed to create index: {idx}. Error: {str(e)}")
        
        # Run vacuum and analyze
        maintenance_queries = [
            "VACUUM ANALYZE stock_ticks",
            "VACUUM ANALYZE ibkr_contracts",
            "ANALYZE stock_ticks",
            "ANALYZE ibkr_contracts"
        ]
        
        for query in maintenance_queries:
            try:
                cur.execute(query)
                logger.info(f"Executed maintenance: {query}")
            except Exception as e:
                logger.warning(f"Failed to execute maintenance: {query}. Error: {str(e)}")
        
    except Exception as e:
        logger.error(f"Database optimization failed: {str(e)}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    optimize_database()
