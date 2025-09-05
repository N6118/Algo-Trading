#!/usr/bin/env python3
"""
Create test data that meets signal conditions and will be picked up by the scanner.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus as urlquote
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def create_test_data_that_meets_conditions():
    """Create test data that meets signal conditions."""
    try:
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
        
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Get current SH/SL values
        query = text("""
            SELECT symbol, close, sh_price, sl_price, created
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
            symbol, created, close, sh_price, sl_price = row
            current_data[symbol] = {
                'created': created,
                'close': close,
                'sh_price': sh_price,
                'sl_price': sl_price
            }
        
        logger.info("📊 Current Data:")
        for symbol, data in current_data.items():
            logger.info(f"  {symbol}: Close={data['close']:.2f}, SH={data['sh_price']:.2f}, SL={data['sl_price']:.2f}")
        
        # Create test timestamp (next 15-minute interval)
        current_time = datetime.utcnow()
        # Round up to next 15-minute interval
        next_minute = ((current_time.minute // 15) + 1) * 15
        if next_minute >= 60:
            next_interval = current_time.replace(hour=current_time.hour + 1, minute=next_minute - 60, second=0, microsecond=0)
        else:
            next_interval = current_time.replace(minute=next_minute, second=0, microsecond=0)
        
        logger.info(f"📅 Creating test data for: {next_interval}")
        
        # Create BUY signal test data
        # MES price > MES SH AND VIX price < VIX SL
        mes_buy_price = current_data['MES']['sh_price'] + 5.0  # Well above SH
        vix_buy_price = current_data['VIX']['sl_price'] - 0.5  # Well below SL
        
        logger.info("🎯 BUY Test Data:")
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
        logger.info("✅ BUY test data inserted successfully")
        
        # Also create SELL test data for the next interval
        next_interval_sell = next_interval + timedelta(minutes=15)
        
        # Create SELL signal test data
        # MES price < MES SL AND VIX price > VIX SH
        mes_sell_price = current_data['MES']['sl_price'] - 5.0  # Well below SL
        vix_sell_price = current_data['VIX']['sh_price'] + 0.5  # Well above SH
        
        logger.info("🎯 SELL Test Data:")
        logger.info(f"  MES: {mes_sell_price:.2f} (<{current_data['MES']['sl_price']:.2f} SL)")
        logger.info(f"  VIX: {vix_sell_price:.2f} (>{current_data['VIX']['sh_price']:.2f} SH)")
        
        # Insert MES SELL test data
        session.execute(insert_query, {
            'created': next_interval_sell,
            'token': 756733,  # MES token
            'symbol': 'MES',
            'open': mes_sell_price + 2.0,
            'close': mes_sell_price,
            'high': mes_sell_price + 2.0,
            'low': mes_sell_price - 2.0,
            'volume': 1000,
            'sh_price': current_data['MES']['sh_price'],
            'sl_price': current_data['MES']['sl_price'],
            'sh_status': False,
            'sl_status': True
        })
        
        # Insert VIX SELL test data
        session.execute(insert_query, {
            'created': next_interval_sell,
            'token': 320227,  # VIX token
            'symbol': 'VIX',
            'open': vix_sell_price - 0.2,
            'close': vix_sell_price,
            'high': vix_sell_price + 0.2,
            'low': vix_sell_price - 0.2,
            'volume': 1000,
            'sh_price': current_data['VIX']['sh_price'],
            'sl_price': current_data['VIX']['sl_price'],
            'sh_status': True,
            'sl_status': False
        })
        
        session.commit()
        logger.info("✅ SELL test data inserted successfully")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"Error creating test data: {str(e)}")
        return False

def verify_test_data():
    """Verify the test data was inserted correctly."""
    try:
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
        
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check recent test data
        query = text("""
            SELECT symbol, created, close, sh_price, sl_price
            FROM tbl_ohlc_fifteen_output 
            WHERE created > NOW() - INTERVAL '1 hour'
            ORDER BY created DESC, symbol
            LIMIT 10
        """)
        
        result = session.execute(query)
        rows = result.fetchall()
        
        logger.info("📊 Recent Test Data:")
        for row in rows:
            symbol, created, close, sh_price, sl_price = row
            logger.info(f"  {symbol}: {created} - Close={close:.2f}, SH={sh_price:.2f}, SL={sl_price:.2f}")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"Error verifying test data: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Creating Test Data That Meets Signal Conditions")
    
    # Step 1: Create test data
    logger.info("📝 Step 1: Creating test data...")
    if create_test_data_that_meets_conditions():
        logger.info("✅ Test data created successfully")
    else:
        logger.error("❌ Failed to create test data")
        sys.exit(1)
    
    # Step 2: Verify test data
    logger.info("🔍 Step 2: Verifying test data...")
    verify_test_data()
    
    logger.info("🎯 Test data created! The signal scanner should pick this up in the next scan cycle.")
    logger.info("⏰ Next scan should happen within 15 minutes.")
    logger.info("🏁 Test data creation completed")
