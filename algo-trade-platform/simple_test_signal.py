#!/usr/bin/env python3
"""
Simple test to create data that meets signal conditions.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus as urlquote
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def create_simple_test_data():
    """Create simple test data that meets BUY conditions."""
    try:
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
        
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Get current data
        query = text("""
            SELECT symbol, close, sh_price, sl_price
            FROM tbl_ohlc_fifteen_output 
            WHERE symbol IN ('MES', 'VIX')
            AND created = (
                SELECT MAX(created) 
                FROM tbl_ohlc_fifteen_output 
                WHERE symbol = tbl_ohlc_fifteen_output.symbol
            )
            ORDER BY symbol
        """)
        
        result = session.execute(query)
        rows = result.fetchall()
        
        current_data = {}
        for row in rows:
            symbol, close, sh_price, sl_price = row
            current_data[symbol] = {
                'close': float(close),
                'sh_price': float(sh_price),
                'sl_price': float(sl_price)
            }
        
        logger.info("Current Data:")
        for symbol, data in current_data.items():
            logger.info(f"  {symbol}: Close={data['close']:.2f}, SH={data['sh_price']:.2f}, SL={data['sl_price']:.2f}")
        
        # Create test timestamp (next 15-minute interval)
        now = datetime.utcnow()
        next_interval = now.replace(minute=((now.minute // 15) + 1) * 15, second=0, microsecond=0)
        if next_interval.minute >= 60:
            next_interval = next_interval.replace(hour=next_interval.hour + 1, minute=0)
        
        logger.info(f"Creating test data for: {next_interval}")
        
        # Create BUY signal test data
        # MES price > MES SH AND VIX price < VIX SL
        mes_buy_price = current_data['MES']['sh_price'] + 10.0  # Well above SH
        vix_buy_price = current_data['VIX']['sl_price'] - 1.0   # Well below SL
        
        logger.info("BUY Test Data:")
        logger.info(f"  MES: {mes_buy_price:.2f} (>{current_data['MES']['sh_price']:.2f} SH)")
        logger.info(f"  VIX: {vix_buy_price:.2f} (<{current_data['VIX']['sl_price']:.2f} SL)")
        
        # Insert test data
        insert_query = text("""
            INSERT INTO tbl_ohlc_fifteen_output (
                created, token, symbol, open, close, high, low, volume,
                sh_price, sl_price, sh_status, sl_status
            ) VALUES (
                :created, :token, :symbol, :open, :close, :high, :low, :volume,
                :sh_price, :sl_price, :sh_status, :sl_status
            )
            ON CONFLICT ON CONSTRAINT tbl_ohlc_fifteen_output_created_token_n_key
            DO UPDATE SET
                close = EXCLUDED.close,
                high = EXCLUDED.high,
                low = EXCLUDED.low
        """)
        
        # Insert MES BUY test data
        session.execute(insert_query, {
            'created': next_interval,
            'token': 756733,  # MES token
            'symbol': 'MES',
            'open': mes_buy_price - 2.0,
            'close': mes_buy_price,
            'high': mes_buy_price + 2.0,
            'low': mes_buy_price - 2.0,
            'volume': 1000,
            'sh_price': current_data['MES']['sh_price'],
            'sl_price': current_data['MES']['sl_price'],
            'sh_status': True,
            'sl_status': False
        })
        
        # Insert VIX BUY test data
        session.execute(insert_query, {
            'created': next_interval,
            'token': 320227,  # VIX token
            'symbol': 'VIX',
            'open': vix_buy_price + 0.2,
            'close': vix_buy_price,
            'high': vix_buy_price + 0.2,
            'low': vix_buy_price - 0.2,
            'volume': 1000,
            'sh_price': current_data['VIX']['sh_price'],
            'sl_price': current_data['VIX']['sl_price'],
            'sh_status': False,
            'sl_status': True
        })
        
        session.commit()
        logger.info("BUY test data inserted successfully")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"Error creating test data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Creating Test Data That Meets BUY Conditions")
    
    if create_simple_test_data():
        logger.info("Test data created successfully!")
        logger.info("The signal scanner should pick this up in the next scan cycle.")
    else:
        logger.error("Failed to create test data")
        sys.exit(1)
