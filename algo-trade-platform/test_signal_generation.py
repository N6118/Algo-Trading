#!/usr/bin/env python3
"""
Test script to insert data that meets signal generation conditions
and verify that the signal scanner picks it up and generates signals.
"""

import os
import sys
import logging
import pandas as pd
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

def get_current_sh_sl_values():
    """Get current SH/SL values for MES and VIX."""
    try:
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
        
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Get latest SH/SL values
        query = text("""
            SELECT symbol, close, sh_price, sl_price, created
            FROM tbl_ohlc_fifteen_output 
            WHERE symbol IN ('MES', 'VIX')
            ORDER BY created DESC, symbol
            LIMIT 2
        """)
        
        result = session.execute(query)
        rows = result.fetchall()
        
        session.close()
        
        values = {}
        for row in rows:
            values[row[0]] = {
                'close': row[1],
                'sh_price': row[2],
                'sl_price': row[3],
                'created': row[4]
            }
        
        return values
        
    except Exception as e:
        logger.error(f"Error getting SH/SL values: {str(e)}")
        return {}

def insert_test_data():
    """Insert test data that meets signal generation conditions."""
    try:
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
        
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Get current SH/SL values
        current_values = get_current_sh_sl_values()
        
        if not current_values:
            logger.error("Could not get current SH/SL values")
            return False
        
        # Create test timestamp (current time)
        test_time = datetime.utcnow().replace(second=0, microsecond=0)
        
        # Test data that meets BUY conditions:
        # MES price > MES SH AND VIX price < VIX SL
        mes_buy_price = current_values['MES']['sh_price'] + 5.0  # Above SH
        vix_buy_price = current_values['VIX']['sl_price'] - 0.5  # Below SL
        
        # Test data that meets SELL conditions:
        # MES price < MES SL AND VIX price > VIX SH
        mes_sell_price = current_values['MES']['sl_price'] - 5.0  # Below SL
        vix_sell_price = current_values['VIX']['sh_price'] + 0.5  # Above SH
        
        logger.info("📊 Current SH/SL Values:")
        logger.info(f"  MES: Close={current_values['MES']['close']:.2f}, SH={current_values['MES']['sh_price']:.2f}, SL={current_values['MES']['sl_price']:.2f}")
        logger.info(f"  VIX: Close={current_values['VIX']['close']:.2f}, SH={current_values['VIX']['sh_price']:.2f}, SL={current_values['VIX']['sl_price']:.2f}")
        
        logger.info("🎯 Test Data:")
        logger.info(f"  BUY Test: MES={mes_buy_price:.2f} (>{current_values['MES']['sh_price']:.2f}), VIX={vix_buy_price:.2f} (<{current_values['VIX']['sl_price']:.2f})")
        logger.info(f"  SELL Test: MES={mes_sell_price:.2f} (<{current_values['MES']['sl_price']:.2f}), VIX={vix_sell_price:.2f} (>{current_values['VIX']['sh_price']:.2f})")
        
        # Insert test data for BUY signal
        buy_query = text("""
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
        session.execute(buy_query, {
            'created': test_time,
            'token': 756733,  # MES token
            'symbol': 'MES',
            'open': mes_buy_price - 1.0,
            'close': mes_buy_price,
            'high': mes_buy_price + 1.0,
            'low': mes_buy_price - 1.0,
            'volume': 1000,
            'sh_price': current_values['MES']['sh_price'],
            'sl_price': current_values['MES']['sl_price'],
            'sh_status': True,
            'sl_status': False
        })
        
        # Insert VIX BUY test data
        session.execute(buy_query, {
            'created': test_time,
            'token': 320227,  # VIX token
            'symbol': 'VIX',
            'open': vix_buy_price + 0.1,
            'close': vix_buy_price,
            'high': vix_buy_price + 0.1,
            'low': vix_buy_price - 0.1,
            'volume': 1000,
            'sh_price': current_values['VIX']['sh_price'],
            'sl_price': current_values['VIX']['sl_price'],
            'sh_status': False,
            'sl_status': True
        })
        
        session.commit()
        logger.info("✅ Inserted BUY test data successfully")
        
        # Wait a moment, then insert SELL test data
        import time
        time.sleep(2)
        
        test_time_sell = test_time + timedelta(minutes=1)
        
        # Insert MES SELL test data
        session.execute(buy_query, {
            'created': test_time_sell,
            'token': 756733,  # MES token
            'symbol': 'MES',
            'open': mes_sell_price + 1.0,
            'close': mes_sell_price,
            'high': mes_sell_price + 1.0,
            'low': mes_sell_price - 1.0,
            'volume': 1000,
            'sh_price': current_values['MES']['sh_price'],
            'sl_price': current_values['MES']['sl_price'],
            'sh_status': False,
            'sl_status': True
        })
        
        # Insert VIX SELL test data
        session.execute(buy_query, {
            'created': test_time_sell,
            'token': 320227,  # VIX token
            'symbol': 'VIX',
            'open': vix_sell_price - 0.1,
            'close': vix_sell_price,
            'high': vix_sell_price + 0.1,
            'low': vix_sell_price - 0.1,
            'volume': 1000,
            'sh_price': current_values['VIX']['sh_price'],
            'sl_price': current_values['VIX']['sl_price'],
            'sh_status': True,
            'sl_status': False
        })
        
        session.commit()
        logger.info("✅ Inserted SELL test data successfully")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"Error inserting test data: {str(e)}")
        return False

def check_generated_signals():
    """Check if any signals were generated."""
    try:
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
        
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check for recent signals
        query = text("""
            SELECT id, symbol, signal_time, direction, price, status
            FROM generated_signals
            WHERE signal_time > NOW() - INTERVAL '10 minutes'
            ORDER BY signal_time DESC
        """)
        
        result = session.execute(query)
        signals = result.fetchall()
        
        session.close()
        
        if signals:
            logger.info("🎉 SIGNALS GENERATED!")
            for signal in signals:
                logger.info(f"  Signal ID {signal[0]}: {signal[1]} {signal[3]} at ${signal[4]:.2f} ({signal[5]})")
            return True
        else:
            logger.info("❌ No signals generated yet")
            return False
            
    except Exception as e:
        logger.error(f"Error checking signals: {str(e)}")
        return False

def trigger_manual_scan():
    """Trigger a manual signal scan."""
    try:
        # Import and run the scanner manually
        sys.path.insert(0, '/home/anurag/Desktop/Algo-Trading/algo-trade-platform/backend/app/signal_scanner')
        
        from scanner import SignalScanner
        
        logger.info("🔄 Triggering manual signal scan...")
        scanner = SignalScanner()
        
        # Get the config and run scan
        session = scanner.Session()
        config = session.query(scanner.SignalConfig).filter(scanner.SignalConfig.id == 1).first()
        session.close()
        
        if config:
            signals = scanner.scan_for_signals(config)
            if signals:
                logger.info(f"✅ Manual scan generated {len(signals)} signals")
                return True
            else:
                logger.info("❌ Manual scan generated no signals")
                return False
        else:
            logger.error("❌ Could not find signal configuration")
            return False
            
    except Exception as e:
        logger.error(f"Error in manual scan: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Starting Signal Generation Test")
    
    # Step 1: Insert test data
    logger.info("📝 Step 1: Inserting test data...")
    if insert_test_data():
        logger.info("✅ Test data inserted successfully")
    else:
        logger.error("❌ Failed to insert test data")
        sys.exit(1)
    
    # Step 2: Trigger manual scan
    logger.info("🔍 Step 2: Triggering manual signal scan...")
    if trigger_manual_scan():
        logger.info("✅ Manual scan completed")
    else:
        logger.info("⚠️ Manual scan completed but no signals generated")
    
    # Step 3: Check for generated signals
    logger.info("📊 Step 3: Checking for generated signals...")
    if check_generated_signals():
        logger.info("🎉 SUCCESS: Signals were generated!")
    else:
        logger.info("❌ No signals found - checking scanner logs...")
    
    logger.info("🏁 Test completed")
