#!/usr/bin/env python3
"""
SL/TP Calculator Service
Integrates the stop-loss and take-profit calculation logic from attempt.py
into the real-time data collection pipeline.
"""

import psycopg2
import pandas as pd
import numpy as np
import logging
import time
import os
import sys
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from pathlib import Path
import json

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.telegram_notifier import send_connection_status

# Set Telegram environment variables
os.environ['TELEGRAM_BOT_TOKEN'] = '8468875074:AAEeCH6H5NfNzHFobMAaw4epxa2v8nZvw_8'
os.environ['TELEGRAM_CHAT_ID'] = '2074764227'

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Database configuration
DB_PASSWORD = "password"
DB_URI = os.getenv('DB_URI', f"postgresql://postgres:{quote_plus(DB_PASSWORD)}@localhost:5432/theodb")

# Default config values (same as attempt.py)
DEFAULT_CONFIG = {
    "atr_trail_sl": {
        "atr_length": 14,
        "atr_multiplier": 2
    },
    "dc": {
        "dc_length": 20,
        "dc_source": "length"
    }
}

def calculate_atr(high, low, close, length=14):
    """Calculate Average True Range manually"""
    try:
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR using simple moving average
        atr = true_range.rolling(window=length).mean()
        
        return atr
    except Exception as e:
        logger.error(f"Error calculating ATR: {e}")
        return pd.Series([np.nan] * len(high))

def load_config():
    """Load configuration from file or use defaults"""
    config_path = os.getenv('CONFIG_PATH', 'config/config.json')
    try:
        with open(config_path, 'r') as json_file:
            return json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load config from {config_path}: {str(e)}")
        logger.warning("Using default configuration")
        return DEFAULT_CONFIG

class SLTPCalculator:
    def __init__(self):
        """Initialize the SL/TP calculator."""
        self.config = load_config()
        self.connection = None
        self.last_processed_time = None
        self.symbols = ['MES', 'VIX']
        self.last_processed_timestamps = {} # Dictionary to store last processed timestamp for each symbol

        
        # Set Telegram environment variables
        os.environ['TELEGRAM_BOT_TOKEN'] = '8468875074:AAEeCH6H5NfNzHFobMAaw4epxa2v8nZvw_8'
        os.environ['TELEGRAM_CHAT_ID'] = '2074764227'

    def connect_db(self):
        """Connect to the database"""
        try:
            self.connection = psycopg2.connect(DB_URI)
            logger.info("✅ Database connection established")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def get_latest_15min_data(self, symbol, limit=100):
        """Get latest 15-minute OHLC data for a symbol"""
        try:
            # First, try to refresh the continuous aggregate to ensure we have the latest data
            try:
                refresh_query = """
                    CALL refresh_continuous_aggregate('stock_ohlc_15min', NOW() - INTERVAL '1 hour', NOW());
                """
                # Execute outside of any transaction
                with self.connection.cursor() as cur:
                    cur.execute("COMMIT")  # End any existing transaction
                    cur.execute(refresh_query)
                    self.connection.commit()
                logger.info(f"✅ Refreshed continuous aggregate for {symbol}")
            except Exception as e:
                logger.warning(f"⚠️ Could not refresh continuous aggregate: {e}")
                # Reset connection state
                self.connection.rollback()
            
            query = """
                SELECT created, token, symbol, open, high, low, close, volume
                FROM stock_ohlc_15min 
                WHERE symbol = %s 
                ORDER BY created DESC 
                LIMIT %s
            """
            df = pd.read_sql_query(query, self.connection, params=(symbol, limit))
            if not df.empty:
                df = df.sort_values('created').reset_index(drop=True)
                df['n'] = range(len(df))
            return df
        except Exception as e:
            logger.error(f"❌ Error getting 15min data for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_sl_tp(self, df, symbol):
        """Calculate SL/TP values using the logic from attempt.py"""
        if df.empty or len(df) < 20:
            return df
        
        try:
            # Initialize arrays (same as attempt.py)
            FhArray = [0]  # Fractal High Array
            FlArray = [0]  # Fractal Low Array
            ShArray = [0]  # Swing High Array
            SlArray = [0]  # Swing Low Array
            
            # Initialize columns
            df["atr"] = None
            df["atr_trail_stop_loss"] = None
            df["dc_upper"] = None
            df["dc_lower"] = None
            df["dc_mid"] = None
            df["fh_price"] = None
            df["fl_price"] = None
            df["fh_status"] = None
            df["fl_status"] = None
            df["sh_price"] = None
            df["sl_price"] = None
            df["sh_status"] = None
            df["sl_status"] = None
            df["lowestfrom1stlow"] = None
            df["highestfrom1sthigh"] = None
            df["fl_dbg"] = None
            df["fh_dbg"] = None
            df["dpivot"] = None
            df["ds1"] = None
            df["ds2"] = None
            df["ds3"] = None
            df["ds4"] = None
            df["ds5"] = None
            df["dr1"] = None
            df["dr2"] = None
            df["dr3"] = None
            df["dr4"] = None
            df["dr5"] = None
            df["wpivot"] = None
            df["ws1"] = None
            df["ws2"] = None
            df["ws3"] = None
            df["ws4"] = None
            df["ws5"] = None
            df["wr1"] = None
            df["wr2"] = None
            df["wr3"] = None
            df["wr4"] = None
            df["wr5"] = None
            df["mpivot"] = None
            df["ms1"] = None
            df["ms2"] = None
            df["ms3"] = None
            df["ms4"] = None
            df["ms5"] = None
            df["mr1"] = None
            df["mr2"] = None
            df["mr3"] = None
            df["mr4"] = None
            df["mr5"] = None
            df["n"] = None
            df["n_lookback"] = None
            df["fharray"] = None
            df["flarray"] = None
            df["sharray"] = None
            df["slarray"] = None
            df["need_break_fractal_up"] = None
            df["anchorarray"] = None
            df["anchor1starray"] = None
            df["anchorcntrarray"] = None
            df["high1starray"] = None
            df["low1starray"] = None
            df["lowdailycur"] = None
            df["highdailycur"] = None
            df["lowweeklycur"] = None
            df["highweeklycur"] = None
            df["lowmonthlycur"] = None
            df["highmonthlycur"] = None
            df["lowdaily"] = None
            df["highdaily"] = None
            df["lowweekly"] = None
            df["highweekly"] = None
            df["lowmonthly"] = None
            df["highmonthly"] = None
            df["dpivotcur"] = None
            df["wpivotcur"] = None
            df["mpivotcur"] = None
            df["direction"] = None
            
            # Calculate ATR
            df["atr"] = calculate_atr(df["high"], df["low"], df["close"], 
                               length=self.config["atr_trail_sl"]["atr_length"])
            
            # Initialize variables
            need_break_fractal_up = True
            lowDailyCur = df.iloc[0]["low"]
            highDailyCur = df.iloc[0]["high"]
            lowDaily = None
            highDaily = None
            dailyPivot = None
            dailyPivotCur = None
            
            # Process each row
            for n in range(len(df)):
                if n < 2:  # Skip first two rows for fractal calculation
                    continue
                    
                close = df.iloc[n]["close"]
                high = df.iloc[n]["high"]
                low = df.iloc[n]["low"]
                
                # 1. ATR Trailing Stop Loss
                atrMultiplier = self.config["atr_trail_sl"]["atr_multiplier"]
                atr_value = df.iloc[n]["atr"]
                
                if pd.isna(atr_value):
                    df.iloc[n, df.columns.get_loc("atr_trail_stop_loss")] = -1
                else:
                    stop = atr_value * atrMultiplier
                    
                    if n > 0:
                        atrTrailingstop1 = df.iloc[n-1]["atr_trail_stop_loss"]
                        
                        if not pd.isna(atrTrailingstop1) and atrTrailingstop1 != -1:
                            if close > df.iloc[n-1]["close"]:
                                df.iloc[n, df.columns.get_loc("atr_trail_stop_loss")] = max(atrTrailingstop1, close - stop)
                            else:
                                df.iloc[n, df.columns.get_loc("atr_trail_stop_loss")] = min(atrTrailingstop1, close + stop)
                        else:
                            df.iloc[n, df.columns.get_loc("atr_trail_stop_loss")] = close - stop
                    else:
                        df.iloc[n, df.columns.get_loc("atr_trail_stop_loss")] = close + stop
                
                # 2. Fractal High/Low calculation (simplified)
                if n >= 2:
                    # Check for fractal high
                    if (df.iloc[n-2]["high"] < df.iloc[n-1]["high"] and 
                        df.iloc[n-1]["high"] > df.iloc[n]["high"]):
                        FhArray.insert(0, n-1)
                        df.iloc[n-1, df.columns.get_loc("fh_status")] = True
                        df.iloc[n-1, df.columns.get_loc("fh_price")] = df.iloc[n-1]["high"]
                    
                    # Check for fractal low
                    if (df.iloc[n-2]["low"] > df.iloc[n-1]["low"] and 
                        df.iloc[n-1]["low"] < df.iloc[n]["low"]):
                        FlArray.insert(0, n-1)
                        df.iloc[n-1, df.columns.get_loc("fl_status")] = True
                        df.iloc[n-1, df.columns.get_loc("fl_price")] = df.iloc[n-1]["low"]
                
                # 3. Swing High/Low calculation
                if len(FhArray) > 0 and len(FlArray) > 0:
                    minListSh = df[(df.index >= ShArray[0]) & (df.index <= n)]["low"].min()
                    minListShN = df[(df.index >= ShArray[0]) & (df.index <= n) & 
                                   (df["low"] == minListSh)].index[0] if len(df[(df.index >= ShArray[0]) & (df.index <= n) & (df["low"] == minListSh)]) > 0 else None
                    
                    maxListSl = df[(df.index >= SlArray[0]) & (df.index <= n)]["high"].max()
                    maxListSlN = df[(df.index >= SlArray[0]) & (df.index <= n) & 
                                   (df["high"] == maxListSl)].index[0] if len(df[(df.index >= SlArray[0]) & (df.index <= n) & (df["high"] == maxListSl)]) > 0 else None
                    
                    if need_break_fractal_up:
                        if minListShN is not None:
                            SlArray.insert(0, minListShN)
                            need_break_fractal_up = False
                            df.iloc[minListShN, df.columns.get_loc("sl_status")] = True
                        
                        if maxListSlN is not None:
                            ShArray.insert(0, maxListSlN)
                            need_break_fractal_up = True
                            df.iloc[maxListSlN, df.columns.get_loc("sh_status")] = True
                    
                    # Set SL/TP prices
                    if len(SlArray) > 0:
                        try:
                            df.iloc[n, df.columns.get_loc("sl_price")] = float(df.iloc[SlArray[0]]["low"])
                        except:
                            df.iloc[n, df.columns.get_loc("sl_price")] = 0
                    
                    if len(ShArray) > 0:
                        try:
                            df.iloc[n, df.columns.get_loc("sh_price")] = float(df.iloc[ShArray[0]]["high"])
                        except:
                            df.iloc[n, df.columns.get_loc("sh_price")] = 0
                
                # 4. Donchian Channel
                if self.config["dc"]["dc_source"] == "length":
                    dc_length = self.config["dc"]["dc_length"]
                    if n >= dc_length:
                        df.iloc[n, df.columns.get_loc("dc_upper")] = df.iloc[n-dc_length+1:n+1]["high"].max()
                        df.iloc[n, df.columns.get_loc("dc_lower")] = df.iloc[n-dc_length+1:n+1]["low"].min()
                        df.iloc[n, df.columns.get_loc("dc_mid")] = (df.iloc[n]["dc_upper"] + df.iloc[n]["dc_lower"]) / 2
                
                # Store arrays as text
                df.iloc[n, df.columns.get_loc("fharray")] = str(FhArray[:10])  # Keep last 10
                df.iloc[n, df.columns.get_loc("flarray")] = str(FlArray[:10])
                df.iloc[n, df.columns.get_loc("sharray")] = str(ShArray[:10])
                df.iloc[n, df.columns.get_loc("slarray")] = str(SlArray[:10])
                
                # Clean up arrays to prevent memory issues
                if len(FhArray) > 100:
                    FhArray = FhArray[:100]
                if len(FlArray) > 100:
                    FlArray = FlArray[:100]
                if len(ShArray) > 100:
                    ShArray = ShArray[:100]
                if len(SlArray) > 100:
                    SlArray = SlArray[:100]
            
            logger.info(f"✅ SL/TP calculation completed for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error calculating SL/TP for {symbol}: {e}")
            return df
    
    def save_to_output_table(self, df, symbol):
        """Save calculated values to the output table"""
        try:
            if df.empty:
                return
            
            # Prepare data for insertion
            columns = ["created", "token", "symbol", "open", "close", "high", "low", "volume", 
                      "atr", "atr_trail_stop_loss", "dc_upper", "dc_lower", "dc_mid", 
                      "fh_price", "fl_price", "fh_status", "fl_status", "sh_price", "sl_price", 
                      "sh_status", "sl_status", "lowestfrom1stlow", "highestfrom1sthigh", 
                      "fl_dbg", "fh_dbg", "dpivot", "ds1", "ds2", "ds3", "ds4", "ds5", 
                      "dr1", "dr2", "dr3", "dr4", "dr5", "wpivot", "ws1", "ws2", "ws3", 
                      "ws4", "ws5", "wr1", "wr2", "wr3", "wr4", "wr5", "mpivot", "ms1", 
                      "ms2", "ms3", "ms4", "ms5", "mr1", "mr2", "mr3", "mr4", "mr5", 
                      "n", "n_lookback", "fharray", "flarray", "sharray", "slarray", 
                      "need_break_fractal_up", "anchorarray", "anchor1starray", "anchorcntrarray", 
                      "high1starray", "low1starray", "lowdailycur", "highdailycur", 
                      "lowweeklycur", "highweeklycur", "lowmonthlycur", "highmonthlycur", 
                      "lowdaily", "highdaily", "lowweekly", "highweekly", "lowmonthly", 
                      "highmonthly", "dpivotcur", "wpivotcur", "mpivotcur", "direction"]
            
            # Filter only the latest rows to avoid duplicates
            latest_time = df["created"].max()
            df_latest = df[df["created"] >= latest_time - timedelta(minutes=30)]
            
            if not df_latest.empty:
                # Insert data
                placeholders = ", ".join(["%s"] * len(columns))
                query = f"""
                    INSERT INTO tbl_ohlc_fifteen_output ({', '.join(columns)})
                    VALUES ({placeholders})
                    ON CONFLICT ON CONSTRAINT tbl_ohlc_fifteen_output_created_token_n_key
                    DO UPDATE SET
                        atr = EXCLUDED.atr,
                        atr_trail_stop_loss = EXCLUDED.atr_trail_stop_loss,
                        dc_upper = EXCLUDED.dc_upper,
                        dc_lower = EXCLUDED.dc_lower,
                        dc_mid = EXCLUDED.dc_mid,
                        fh_price = EXCLUDED.fh_price,
                        fl_price = EXCLUDED.fl_price,
                        sh_price = EXCLUDED.sh_price,
                        sl_price = EXCLUDED.sl_price,
                        fh_status = EXCLUDED.fh_status,
                        fl_status = EXCLUDED.fl_status,
                        sh_status = EXCLUDED.sh_status,
                        sl_status = EXCLUDED.sl_status
                """
                
                with self.connection.cursor() as cur:
                    for _, row in df_latest.iterrows():
                        values = [row[col] for col in columns]
                        cur.execute(query, values)
                    
                    self.connection.commit()
                
                logger.info(f"✅ Saved {len(df_latest)} rows to output table for {symbol}")
                
                # Send Telegram notification for new SL/TP values
                latest_row = df_latest.iloc[-1]
                if not pd.isna(latest_row["sl_price"]) and latest_row["sl_price"] > 0:
                    sh_price_str = f"{latest_row['sh_price']:.2f}" if not pd.isna(latest_row['sh_price']) else 'N/A'
                    atr_str = f"{latest_row['atr']:.2f}" if not pd.isna(latest_row['atr']) else 'N/A'
                    
                    message = f"""
📊 <b>New SL/TP Values for {symbol}</b>

💰 <b>Current Price:</b> {latest_row['close']:.2f}
🛑 <b>Stop Loss:</b> {latest_row['sl_price']:.2f}
📈 <b>Take Profit:</b> {sh_price_str}
📊 <b>ATR:</b> {atr_str}

⏰ <b>Time:</b> {latest_row['created']}
                    """.strip()
                    
                    from backend.app.services.telegram_notifier import get_telegram_notifier
                    notifier = get_telegram_notifier()
                    if notifier:
                        notifier.send_message(message)
                        logger.info(f"✅ Telegram notification sent for {symbol} - SH/SL calculation completed")
                
        except Exception as e:
            logger.error(f"❌ Error saving to output table for {symbol}: {e}")
            if self.connection:
                self.connection.rollback()
    


    def process_symbol(self, symbol):
        """Process a single symbol"""
        try:
            # Get latest data
            df = self.get_latest_15min_data(symbol)
            if df.empty:
                logger.warning(f"⚠️ No data available for {symbol}")
                return
            
            # Check if we've already processed the latest data
            latest_timestamp = df['created'].max()
            if symbol in self.last_processed_timestamps:
                if latest_timestamp <= self.last_processed_timestamps[symbol]:
                    logger.info(f"⏭️ Already processed latest data for {symbol} at {latest_timestamp}")
                    return
            
            # Update the last processed timestamp
            self.last_processed_timestamps[symbol] = latest_timestamp
            
            # Calculate SL/TP
            df_calculated = self.calculate_sl_tp(df, symbol)
            
            # Save to output table
            self.save_to_output_table(df_calculated, symbol)
            
        except Exception as e:
            logger.error(f"❌ Error processing {symbol}: {e}")
    
    def run(self):
        """Main run loop"""
        logger.info("🚀 Starting SL/TP Calculator Service")
        
        if not self.connect_db():
            return
        
        try:
            while True:
                current_time = datetime.now()
                
                # Process each symbol
                for symbol in self.symbols:
                    self.process_symbol(symbol)
                
                # Wait for next cycle (every 15 minutes)
                logger.info("✅ SL/TP calculation cycle completed")
                time.sleep(900)  # 15 minutes
                
        except KeyboardInterrupt:
            logger.info("🛑 SL/TP Calculator Service stopped by user")
        except Exception as e:
            logger.error(f"❌ SL/TP Calculator Service error: {e}")
        finally:
            if self.connection:
                self.connection.close()

if __name__ == "__main__":
    calculator = SLTPCalculator()
    calculator.run() 