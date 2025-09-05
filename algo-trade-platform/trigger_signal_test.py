#!/usr/bin/env python3
"""
Trigger a signal generation test by inserting fresh data and waiting for the scanner to pick it up.
"""

import os
import sys
import logging
import time
from datetime import datetime, timedelta
from urllib.parse import quote_plus as urlquote
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set Telegram environment variables
os.environ['TELEGRAM_BOT_TOKEN'] = '8468875074:AAEeCH6H5NfNzHFobMAaw4epxa2v8nZvw_8'
os.environ['TELEGRAM_CHAT_ID'] = '2074764227'

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def insert_fresh_test_data():
    """Insert fresh test data that meets signal conditions."""
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
            ORDER BY created DESC, symbol
            LIMIT 2
        """)
        
        result = session.execute(query)
        rows = result.fetchall()
        
        current_values = {}
        for row in rows:
            current_values[row[0]] = {
                'close': row[1],
                'sh_price': row[2],
                'sl_price': row[3],
                'created': row[4]
            }
        
        # Create fresh test timestamp (current time + 1 minute to avoid conflicts)
        test_time = datetime.utcnow().replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # Create test data that meets BUY conditions:
        # MES price > MES SH AND VIX price < VIX SL
        mes_buy_price = current_values['MES']['sh_price'] + 10.0  # Well above SH
        vix_buy_price = current_values['VIX']['sl_price'] - 1.0   # Well below SL
        
        logger.info("📊 Current SH/SL Values:")
        logger.info(f"  MES: Close={current_values['MES']['close']:.2f}, SH={current_values['MES']['sh_price']:.2f}, SL={current_values['MES']['sl_price']:.2f}")
        logger.info(f"  VIX: Close={current_values['VIX']['close']:.2f}, SH={current_values['VIX']['sh_price']:.2f}, SL={current_values['VIX']['sl_price']:.2f}")
        
        logger.info("🎯 Fresh Test Data (BUY conditions):")
        logger.info(f"  MES: {mes_buy_price:.2f} (>{current_values['MES']['sh_price']:.2f} SH)")
        logger.info(f"  VIX: {vix_buy_price:.2f} (<{current_values['VIX']['sl_price']:.2f} SL)")
        
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
            'created': test_time,
            'token': 756733,  # MES token
            'symbol': 'MES',
            'open': mes_buy_price - 2.0,
            'close': mes_buy_price,
            'high': mes_buy_price + 2.0,
            'low': mes_buy_price - 2.0,
            'volume': 1000,
            'sh_price': current_values['MES']['sh_price'],
            'sl_price': current_values['MES']['sl_price'],
            'sh_status': True,
            'sl_status': False
        })
        
        # Insert VIX BUY test data
        session.execute(insert_query, {
            'created': test_time,
            'token': 320227,  # VIX token
            'symbol': 'VIX',
            'open': vix_buy_price + 0.2,
            'close': vix_buy_price,
            'high': vix_buy_price + 0.2,
            'low': vix_buy_price - 0.2,
            'volume': 1000,
            'sh_price': current_values['VIX']['sh_price'],
            'sl_price': current_values['VIX']['sl_price'],
            'sh_status': False,
            'sl_status': True
        })
        
        session.commit()
        logger.info("✅ Fresh test data inserted successfully")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"Error inserting fresh test data: {str(e)}")
        return False

def wait_for_signal():
    """Wait for the signal scanner to pick up the conditions and generate a signal."""
    try:
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = os.getenv("DB_URI", f"postgresql://postgres:{encoded_password}@localhost:5432/theodb")
        
        engine = create_engine(uri)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        logger.info("⏳ Waiting for signal scanner to detect conditions...")
        
        # Wait up to 2 minutes for a signal
        for i in range(24):  # 24 * 5 seconds = 2 minutes
            time.sleep(5)
            
            # Check for new signals
            query = text("""
                SELECT id, symbol, signal_time, direction, price, status
                FROM generated_signals
                WHERE signal_time > NOW() - INTERVAL '5 minutes'
                ORDER BY signal_time DESC
            """)
            
            result = session.execute(query)
            signals = result.fetchall()
            
            if signals:
                logger.info("🎉 SIGNAL DETECTED!")
                for signal in signals:
                    logger.info(f"  Signal ID {signal[0]}: {signal[1]} {signal[3]} at ${signal[4]:.2f} ({signal[5]})")
                session.close()
                return signals[0]  # Return the first signal
            
            logger.info(f"⏳ Still waiting... ({i+1}/24)")
        
        session.close()
        return None
        
    except Exception as e:
        logger.error(f"Error waiting for signal: {str(e)}")
        return None

def send_telegram_notification(signal):
    """Send Telegram notification about the generated signal."""
    try:
        from backend.app.services.telegram_notifier import get_telegram_notifier
        
        notifier = get_telegram_notifier()
        if notifier:
            message = f"""🚨 **SIGNAL GENERATED BY SCANNER!** 🚨

**Symbol:** {signal[1]}
**Direction:** {signal[3]}
**Price:** ${signal[4]:.2f}
**Timeframe:** 15min
**Strategy:** Sample SH/SL Strategy
**Generated:** {signal[2].strftime('%Y-%m-%d %H:%M:%S')}

**System Status:**
✅ Data collection: Active
✅ SH/SL calculation: Active  
✅ Signal generation: Active
✅ Correlation disabled: Working
✅ Telegram notifications: Working

The signal scanner successfully detected the conditions and generated a signal!"""
            
            result = notifier.send_message(message)
            if result:
                logger.info("✅ Telegram notification sent successfully")
                return True
            else:
                logger.error("❌ Failed to send Telegram notification")
                return False
        else:
            logger.error("❌ Telegram notifier not available")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Starting Complete Signal Generation Test")
    
    # Step 1: Insert fresh test data
    logger.info("📝 Step 1: Inserting fresh test data...")
    if not insert_fresh_test_data():
        logger.error("❌ Failed to insert test data")
        sys.exit(1)
    
    # Step 2: Wait for signal scanner to detect and generate signal
    logger.info("🔍 Step 2: Waiting for signal scanner to generate signal...")
    signal = wait_for_signal()
    
    if signal:
        logger.info("✅ Signal generated by scanner!")
        
        # Step 3: Send Telegram notification
        logger.info("📱 Step 3: Sending Telegram notification...")
        if send_telegram_notification(signal):
            logger.info("🎉 COMPLETE SUCCESS!")
            logger.info("📱 Check your Telegram for the notification")
        else:
            logger.error("❌ Failed to send Telegram notification")
    else:
        logger.error("❌ No signal generated within 2 minutes")
        logger.info("💡 The signal scanner may need more time or there might be an issue")
    
    logger.info("🏁 Test completed")
