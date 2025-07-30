from sqlalchemy import create_engine
from urllib.parse import quote_plus as urlquote
from datetime import datetime
import pandas as pd
import pandas_ta as ta
import json
import math
import os
import csv
import sys
from tqdm import tqdm
import numpy as np
from flask import Flask
from sqlalchemy import text
from pathlib import Path
import traceback
import logging

# Set up logging configuration
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Create a log filename with timestamp
log_filename = os.path.join(log_directory, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logging to write to both file and console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Default config values
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

# Load configuration
config = load_config()

app = Flask(__name__)

# Add after app creation
app.logger.setLevel(logging.DEBUG)

@app.route('/')
def InitProcess():
    try:
        # Remote database configuration
        password = os.getenv("DB_PASSWORD", "password")
        encoded_password = urlquote(password)
        uri = f"postgresql://postgres:{encoded_password}@localhost:5432/theodb"
        
        input_table = 'stock_ohlc_15min'
        output_table = 'tbl_ohlc_fifteen_output'
        engine = create_engine(uri)
        
        # Check if the output table exists and create it if not
        with engine.connect() as conn:
            try:
                # Check if table exists
                check_query = text(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{output_table}')")
                result = conn.execute(check_query).scalar()
                
                if not result:
                    logger.info(f"Creating output table {output_table}")
                    # Create table if it doesn't exist with appropriate primary key and unique constraint
                    create_table_query = text(f"""
                        CREATE TABLE IF NOT EXISTS {output_table} (
                            id SERIAL PRIMARY KEY,
                            created TIMESTAMP,
                            token INTEGER,
                            symbol VARCHAR(20),
                            open DOUBLE PRECISION,
                            close DOUBLE PRECISION,
                            high DOUBLE PRECISION,
                            low DOUBLE PRECISION,
                            volume DOUBLE PRECISION,
                            atr DOUBLE PRECISION,
                            atr_trail_stop_loss DOUBLE PRECISION,
                            dc_upper DOUBLE PRECISION,
                            dc_lower DOUBLE PRECISION,
                            dc_mid DOUBLE PRECISION,
                            fh_price DOUBLE PRECISION,
                            fl_price DOUBLE PRECISION,
                            fh_status BOOLEAN,
                            fl_status BOOLEAN,
                            sh_price DOUBLE PRECISION,
                            sl_price DOUBLE PRECISION,
                            sh_status BOOLEAN,
                            sl_status BOOLEAN,
                            lowestfrom1stlow INTEGER,
                            highestfrom1sthigh INTEGER,
                            fl_dbg INTEGER,
                            fh_dbg INTEGER,
                            dpivot DOUBLE PRECISION,
                            ds1 DOUBLE PRECISION,
                            ds2 DOUBLE PRECISION,
                            ds3 DOUBLE PRECISION,
                            ds4 DOUBLE PRECISION,
                            ds5 DOUBLE PRECISION,
                            dr1 DOUBLE PRECISION,
                            dr2 DOUBLE PRECISION,
                            dr3 DOUBLE PRECISION,
                            dr4 DOUBLE PRECISION,
                            dr5 DOUBLE PRECISION,
                            wpivot DOUBLE PRECISION,
                            ws1 DOUBLE PRECISION,
                            ws2 DOUBLE PRECISION,
                            ws3 DOUBLE PRECISION,
                            ws4 DOUBLE PRECISION,
                            ws5 DOUBLE PRECISION,
                            wr1 DOUBLE PRECISION,
                            wr2 DOUBLE PRECISION,
                            wr3 DOUBLE PRECISION,
                            wr4 DOUBLE PRECISION,
                            wr5 DOUBLE PRECISION,
                            mpivot DOUBLE PRECISION,
                            ms1 DOUBLE PRECISION,
                            ms2 DOUBLE PRECISION,
                            ms3 DOUBLE PRECISION,
                            ms4 DOUBLE PRECISION,
                            ms5 DOUBLE PRECISION,
                            mr1 DOUBLE PRECISION,
                            mr2 DOUBLE PRECISION,
                            mr3 DOUBLE PRECISION,
                            mr4 DOUBLE PRECISION,
                            mr5 DOUBLE PRECISION,
                            n INTEGER,
                            n_lookback INTEGER,
                            fharray TEXT,
                            flarray TEXT,
                            sharray TEXT,
                            slarray TEXT,
                            need_break_fractal_up BOOLEAN,
                            anchorarray TEXT,
                            anchor1starray TEXT,
                            anchorcntrarray TEXT,
                            high1starray TEXT,
                            low1starray TEXT,
                            lowdailycur DOUBLE PRECISION,
                            highdailycur DOUBLE PRECISION,
                            lowweeklycur DOUBLE PRECISION,
                            highweeklycur DOUBLE PRECISION,
                            lowmonthlycur DOUBLE PRECISION,
                            highmonthlycur DOUBLE PRECISION,
                            lowdaily DOUBLE PRECISION,
                            highdaily DOUBLE PRECISION,
                            lowweekly DOUBLE PRECISION,
                            highweekly DOUBLE PRECISION,
                            lowmonthly DOUBLE PRECISION,
                            highmonthly DOUBLE PRECISION,
                            dpivotcur DOUBLE PRECISION,
                            wpivotcur DOUBLE PRECISION,
                            mpivotcur DOUBLE PRECISION,
                            direction BOOLEAN,
                            UNIQUE(created, token, n)
                        )
                    """)
                    conn.execute(create_table_query)
                    conn.commit()
                    logger.info(f"Created output table {output_table} with unique constraint on (created, token, n)")
                else:
                    # Check if the unique constraint exists
                    constraint_query = text(f"""
                        SELECT COUNT(*) FROM pg_constraint 
                        WHERE conname = '{output_table}_created_token_n_key' 
                        AND conrelid = '{output_table}'::regclass
                    """)
                    
                    try:
                        constraint_exists = conn.execute(constraint_query).scalar()
                        
                        if not constraint_exists:
                            # Add the unique constraint if it doesn't exist
                            logger.info(f"Adding unique constraint to {output_table}")
                            add_constraint_query = text(f"""
                                ALTER TABLE {output_table}
                                ADD CONSTRAINT {output_table}_created_token_n_key UNIQUE (created, token, n)
                            """)
                            conn.execute(add_constraint_query)
                            conn.commit()
                            logger.info(f"Added unique constraint on (created, token, n) to {output_table}")
                    except Exception as e:
                        logger.error(f"Error checking/adding constraint: {str(e)}")
                        # If there's an error, try a different approach to add the constraint
                        try:
                            add_constraint_query = text(f"""
                                DO $$
                                BEGIN
                                    BEGIN
                                        ALTER TABLE {output_table} ADD CONSTRAINT {output_table}_created_token_n_key UNIQUE (created, token, n);
                                    EXCEPTION
                                        WHEN duplicate_table THEN
                                            NULL;
                                    END;
                                END $$;
                            """)
                            conn.execute(add_constraint_query)
                            conn.commit()
                            logger.info(f"Added unique constraint on (created, token, n) to {output_table} using alternative method")
                        except Exception as e2:
                            logger.error(f"Failed to add constraint using alternative method: {str(e2)}")
            except Exception as e:
                logger.error(f"Error checking/creating table: {str(e)}")
        
        # First connection to get tokens
        with engine.connect() as conn:
            # Modified query to ensure we get results
            query = """
                SELECT DISTINCT token 
                FROM stock_ohlc_15min 
                WHERE token != 0
                ORDER BY token
            """
            
            # Execute query and check if we got results
            tokens = pd.read_sql(query, conn)
            
        if tokens is None or len(tokens) == 0:
            logger.warning("No tokens found in database")
            return "No data to process", 404
            
        logger.info(f"Found {len(tokens)} tokens to process")
        print("Total pair:", len(tokens))
        
        # Create output file if first run
        if os.path.exists('output_data_stock.csv'):
            os.remove('output_data_stock.csv')

        # TOKEN LOOP
        for token_index, token_row in tqdm(tokens.iterrows(), total=len(tokens)):
            # Verify token exists
            if token_row is None or 'token' not in token_row:
                logger.warning(f"Invalid token row: {token_row}")
                continue

            token_id = token_row.token
            logger.info(f"Processing token {token_id} (index {token_index}/{len(tokens)})")
            logger.debug(f"Processing token {token_row.token}")
            
            # Initialize variables before processing chunks
            n = 0  # Add this line to initialize n
            FhArray = [0]
            FlArray = [0]
            ShArray = [0]
            SlArray = [0]
            need_break_fractal_up = True
            anchorArray = [0]
            anchor1stArray = [0]
            anchorCntrArray = [0]
            high1stArray = [0]
            low1stArray = [0]
            
            # Pivot variables
            lowDailyCur = None
            highDailyCur = None
            lowWeeklyCur = None
            highWeeklyCur = None
            lowMonthlyCur = None
            highMonthlyCur = None
            lowDaily = None
            highDaily = None
            lowWeekly = None
            highWeekly = None
            lowMonthly = None
            highMonthly = None
            dailyPivotCur = None
            weeklyPivotCur = None
            monthlyPivotCur = None
            direction = 1

            # create output buffer
            df = pd.DataFrame()

            # CHUNK LOOP - Create a new connection for each token
            query = """
                SELECT * 
                FROM {} 
                WHERE symbol NOT LIKE '%%fut%%' 
                AND token = {}
            """.format(input_table, token_row.token)
            
            chunk_count = 0
            # Create a fresh connection for each token's data processing
            with engine.connect() as conn:
                for single_pair_chunk in pd.read_sql(query, conn, chunksize=1000):
                    chunk_count += 1
                    if single_pair_chunk is None or len(single_pair_chunk) == 0:
                        continue
                        
                    logger.debug(f"Processing chunk {chunk_count} for token {token_row.token}")

                    # memory management ==============================================================================================
                    # 1 # use chunk as initiation
                    if(len(df) == 0):
                        df = single_pair_chunk.iloc[:]
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
                        
                        # DEBUG
                        df["lowestfrom1stlow"] = None
                        df["highestfrom1sthigh"] = None
                        
                        df["fl_dbg"] = None
                        df["fh_dbg"] = None
                        
                        # Pivot        
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

                        # indexer
                        df["n"] = None
                        df["n_lookback"] = None
                        
                        # process variable       
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
                        
                        
                        startIndex = 0
                        
                      # 2 # concat new chunk
                    elif(len(df) < 2000):
                        startIndex = len(df)
                        df = pd.concat((df, single_pair_chunk), axis=0).reset_index(drop=True)
                        # Fix possible index issues by preserving the n value
                        current_n = n
                        df.index = df.index + int(df.head(1).n)
                        n = current_n  # Restore the correct n value
                        
                      # N # delete prev chunk, concat new chunk
                    else:
                        # Save the current processing position before resetting dataframe
                        current_n = n
                        df = df.iloc[1000:]
                        df =  pd.concat((df, single_pair_chunk), axis=0).reset_index(drop=True)
                        startIndex = 1000
                        df.index = df.index + current_n - startIndex
                        # Restore n for correct continuation
                        n = current_n
                              
                      # calculate atr, dc =============================================================================================================================================
                    df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=config["atr_trail_sl"]["atr_length"])
                    try:
                        df_donchian = ta.donchian(df["high"], df["low"], lower_length=config["dc"]["dc_length"], upper_length=config["dc"]["dc_length"])
                        if df_donchian is None:
                            logger.warning("Donchian channel calculation returned None")
                        else:
                            logger.debug(f"Successfully calculated donchian channels with shape {df_donchian.shape}")
                    except Exception as e:
                        logger.error(f"Error calculating donchian channels: {str(e)}")
                        df_donchian = None

                    # Only adjust index if df_donchian is not None
                    if df_donchian is not None:
                        df_donchian.index = df_donchian.index + n - startIndex
                      
                      # ROW LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
                    for index, row in df.iloc[startIndex:].iterrows():
                        high = row["high"]
                        low = row["low"]
                        close = row["close"]
                        df.at[n, "n"] = n
                        df.at[n, "fh_status"] = 0
                        df.at[n, "fl_status"] = 0
                        df.at[n, "sh_status"] = 0
                        df.at[n, "sl_status"] = 0
                        df.at[n, "dc_upper"] = -1
                        df.at[n, "dc_lower"] = -1
                        df.at[n, "dc_mid"] = -1
                        df.at[n, "fl_dbg"] = -1
                        df.at[n, "fh_dbg"] = -1
                        
                        # 1. calculate atr trail stop loss ===============================================
                        atrMultiplier = config["atr_trail_sl"]["atr_multiplier"] # input
                        
                        # Check if ATR is None or NaN and set default value
                        if df.at[n, "atr"] is None or pd.isna(df.at[n, "atr"]):
                            df.at[n, "atr"] = -1
                            df.at[n, "atr_trail_stop_loss"] = -1
                            
                        stop = df.at[n, "atr"] * atrMultiplier
                        close1 = df.at[n-1, "close"] if n-1 != -1 else None
                        atrTrailingstop1 = df.at[index-1, "atr_trail_stop_loss"] if n-1 != -1 else None
                        atrTrailingstop1 = close if (atrTrailingstop1 == None) else atrTrailingstop1
                        if df.at[n,'atr_trail_stop_loss'] != -1:
                          if close > atrTrailingstop1 and close1>atrTrailingstop1:
                            df.at[n,'atr_trail_stop_loss'] = max(atrTrailingstop1, close-stop)
                          elif close<atrTrailingstop1 and close1<atrTrailingstop1:
                            df.at[n,'atr_trail_stop_loss'] = min(atrTrailingstop1, close+stop)
                          elif close>atrTrailingstop1:
                            df.at[n,'atr_trail_stop_loss'] = close - stop 
                          else:
                            df.at[n,'atr_trail_stop_loss'] = close + stop
                          
                        # 2. FH FL ===============================================
                                
                        # # Searching for New Anchor
                        if direction == 1:
                            # not first anchor
                            for i in range(len(anchorArray)):
                                anchorBarsBack = n-anchorArray[i]
                                if len(df[(df.n == n-anchorBarsBack) & ((high < df.high) | (close < df.close))]) >= 1:
                                    anchorArray.insert(0, n)
                                    anchor1stArray.insert(0, -1)
                                    anchorCntrArray.insert(0, 0)
                                    break
                        elif direction == -1:
                            # not first anchor
                            for i in range(len(anchorArray)):
                                anchorBarsBack = n-anchorArray[i]
                                if len(df[(df.n == n-anchorBarsBack) & ((low > df.low) | (close > df.close))]) >= 1:
                                    anchorArray.insert(0, n)
                                    anchor1stArray.insert(0, -1)
                                    anchorCntrArray.insert(0, 0)
                                    break
                        
                        # Searching for Anchor Breaker and Calculate Breaker Counter
                        minList1St = df[ (df.n >= low1stArray[0]) & (df.n <= n)].low.min()
                        minList1StN = df[ (df.n >= low1stArray[0]) & (df.n <= n) & (df.low == minList1St)].head(1).n
                        lowestfrom1stlow = int(minList1StN.iloc[0] - n)
                        df.at[n, "lowestfrom1stlow"] = lowestfrom1stlow
                        
                        maxList1St = df[ (df.n >= high1stArray[0]) & (df.n <= n)].high.max()
                        maxList1StN = df[ (df.n >= high1stArray[0]) & (df.n <= n) & (df.high == maxList1St)].head(1).n
                        highestfrom1sthigh = int(maxList1StN.iloc[0] - n)
                        df.at[n, "highestfrom1sthigh"] = highestfrom1sthigh
                        
                        if direction == 1:
                          
                          for i in range(len(anchorArray)):
                            
                            anchorBarsBack = max(int(df.head(1).n.iloc[0]), anchorArray[i])
                            anchor1stBarsBack = max(int(df.head(1).n.iloc[0]), anchor1stArray[i])
                            anchorCounter  = anchorCntrArray[i]
                            
                            if high > df.at[anchorBarsBack, "high"] and close > df.at[anchorBarsBack, "close"]:
                            
                              anchorCntrArray[i] = anchorCounter+1
                              if anchorCounter == 0 and anchorCntrArray[i] == 1:
                                anchor1stArray[i] = n
                              if anchorCounter == 1 and anchorCntrArray[i] == 2:
                              
                                # insert the FL value to array
                                FlArray.insert(0, n+lowestfrom1stlow)
                                high1stArray.insert(0, anchor1stBarsBack)
                                
                                # # Handle anomali of rule number 6
                                if FhArray[0] > FlArray[0]:
                                  df.at[ FhArray[0], "fh_status" ] = 0
                                  FhArray[0] = int(df.at[FlArray[0], "highestfrom1sthigh"] + FlArray[0])
                                  df.at[ FhArray[0], "fh_status" ] = 1
                                  
                                # create FL label
                                lastFl = FlArray[0]            
                                df.at[ lastFl, "fl_status" ] = 1                                  
                                
                                df.at[ anchorBarsBack, "fl_dbg" ] = 0
                                df.at[ anchor1stBarsBack, "fl_dbg" ] = 1
                                df.at[ n, "fl_dbg" ] = 2
                                
                                # reset all array needed
                                anchorArray     = [n]
                                anchor1stArray  = [0]
                                anchorCntrArray = [0]
                                direction = -1
                                
                                # end loop
                                break  
                                      
                        # Searching for Anchor Breaker and Calculate Breaker Counter
                        elif direction == -1:
                          for i in range(len(anchorArray)):
                            
                            anchorBarsBack = max(int(df.head(1).n.iloc[0]), anchorArray[i])
                            anchor1stBarsBack = max(int(df.head(1).n.iloc[0]), anchor1stArray[i])
                            anchorCounter  = anchorCntrArray[i]
                            
                            if low < df.at[anchorBarsBack, "low"] and close < df.at[anchorBarsBack, "close"]:
                              anchorCntrArray[i] = anchorCounter+1
                              if anchorCounter == 0 and anchorCntrArray[i]==1:
                                anchor1stArray[i] = n
                              if anchorCounter == 1 and anchorCntrArray[i]==2:
                                  
                                # insert the FH value to array
                                FhArray.insert(0, n+highestfrom1sthigh)
                                low1stArray.insert(0, anchor1stBarsBack)
                                
                                # Handle anomali of rule number 6
                                if FlArray[0] > FhArray[0]:
                                  df.at[ FlArray[0], "fl_status" ] = 0
                                  FlArray[0] = int(df.at[FhArray[0], "lowestfrom1stlow"] + FhArray[0])
                                  df.at[ FlArray[0], "fl_status" ] = 1
                                
                                    
                                # create FH label
                                lastFh = FhArray[0]
                                df.at[ lastFh, "fh_status" ] = 1                                                    
                                df.at[ anchorBarsBack, "fh_dbg" ] = 0
                                df.at[ anchor1stBarsBack, "fh_dbg" ] = 1
                                df.at[ n, "fh_dbg" ] = 2
                                
                                # reset all array needed
                                anchorArray     = [n]
                                anchor1stArray  = [0]
                                anchorCntrArray = [0]
                                direction = 1
                                
                                # end loop
                                break
                                
                        # searching for rule number 6
                        if direction == 1:
                            lastFH = max(int(df.head(1).n.iloc[0]), FhArray[0])
                            if high > df.at[lastFH, "high"]:
                                FhArray[0] = n
                                df.at[ lastFH, "fh_status" ] = 0
                                df.at[ n, "fh_status" ] = 1
                        elif direction == -1:
                            lastFL = max(int(df.head(1).n.iloc[0]), FlArray[0])
                            if low < df.at[lastFL, "low"]:
                                FlArray[0] = n
                                df.at[ lastFL, "fl_status" ] = 0
                                df.at[ n, "fl_status" ] = 1
                                
                        try:
                          df.at[ n, "fl_price" ] = float(df.at[FlArray[0], "low"])
                        except:
                          df.at[ n, "fl_price" ] = 0
                        try:
                          df.at[ n, "fh_price" ] = float(df.at[FhArray[0], "high"])
                        except:
                          df.at[ n, "fh_price" ] = 0
                        
                        # 3. SH SL ===============================================
                               
                        minListSh = df[ (df.n >= ShArray[0]) & (df.n <= n)].low.min()
                        minListShN = int(df[ (df.n >= ShArray[0]) & (df.n <= n) & (df.low == minListSh)].head(1).n.iloc[0])
                        
                        maxListSl = df[ (df.n >= SlArray[0]) & (df.n <= n)].high.max()
                        maxListSlN = int(df[ (df.n >= SlArray[0]) & (df.n <= n) & (df.high == maxListSl)].head(1).n.iloc[0])
                        
                        LowestSinceLastFl = df[ (df.n >= FlArray[0]) & (df.n <= n)].low.min()
                        HighestSinceLastFh = df[ (df.n >= FhArray[0]) & (df.n <= n)].high.max()

                        if need_break_fractal_up:
                          if len(df[(df.n == FhArray[0]) & (HighestSinceLastFh != df.high)]) == 1:
                            SlArray.insert(0, minListShN)
                            need_break_fractal_up = False
                            df.at[ SlArray[0], "sl_status" ] = 1
                          else:
                            if len(df[(df.n == FlArray[0]) & (LowestSinceLastFl != df.low)]) == 1:
                              ShArray.insert(0, maxListSlN)
                              need_break_fractal_up = True
                              df.at[ ShArray[0], "sh_status" ] = 1
                          
                          try:
                            df.at[ n, "sl_price" ] = float(df.at[SlArray[0], "low"])
                          except:
                            df.at[ n, "sl_price" ] = 0
                          try:
                            df.at[ n, "sh_price" ] = float(df.at[ShArray[0], "high"])
                          except:
                            df.at[ n, "sh_price" ] = 0
                        
                        df.at[n, "n_lookback"] = ShArray[1] if len(ShArray) >= 2 else 0 if df.at[n, "n_lookback"] == None else int(np.nanmin([df.at[n, "n_lookback"], ShArray[1] if len(ShArray) >= 2 else 0]))
                        df.at[n, "n_lookback"] = SlArray[1] if len(SlArray) >= 2 else 0 if df.at[n, "n_lookback"] == None else int(np.nanmin([df.at[n, "n_lookback"], SlArray[1] if len(SlArray) >= 2 else 0]))
                         
                        df.at[n, "n_lookback"] = int(max(0, np.nanmin([df.at[n, "n_lookback"], n-(config["atr_trail_sl"]["atr_length"]+1)])))
                                       
                        # 4. Normal dc ===============================================
                        if config["dc"]["dc_source"] == "length":
                            if df_donchian is not None and index in df_donchian.index:
                                dc_col = f"DCU_{config['dc']['dc_length']}_{config['dc']['dc_length']}"
                                if dc_col in df_donchian.columns and not pd.isna(df_donchian.at[index, dc_col]):
                                    df.at[n, "dc_upper"] = df_donchian.at[index, dc_col]
                                    df.at[n, "dc_lower"] = df_donchian.at[index, dc_col]
                                    df.at[n, "dc_mid"] = df_donchian.at[index, dc_col]
                                    df.at[n, "n_lookback"] = int(max(0, np.nanmin([df.at[n, "n_lookback"], n-(config["dc"]["dc_length"]+1)])))
                          
                        # 5. Swing DC ===============================================
                        else:
                          df.at[n, "dc_upper"] = df[ (df.n >= (ShArray[config["dc"]["dc_length"]-1] if len(ShArray) >= config["dc"]["dc_length"] else 0)) & (df.n <= n)].high.max()
                          df.at[n, "dc_lower"] = df[ (df.n >= (SlArray[config["dc"]["dc_length"]-1] if len(SlArray) >= config["dc"]["dc_length"] else 0)) & (df.n <= n)].low.min()
                          df.at[n, "dc_mid"] = (df.at[n, "dc_upper"] + df.at[n, "dc_lower"])/2
                          df.at[n, "n_lookback"] = int(max(0, np.nanmin([df.at[n, "n_lookback"], ShArray[config["dc"]["dc_length"]-1] if len(ShArray) >= config["dc"]["dc_length"] else 0])))
                          df.at[n, "n_lookback"] = int(max(0, np.nanmin([df.at[n, "n_lookback"], SlArray[config["dc"]["dc_length"]-1] if len(SlArray) >= config["dc"]["dc_length"] else 0])))

                        # 6. Pivot ===============================================
                        
                        curDate = df.at[n, "created"].isocalendar() if pd.notnull(df.at[n, "created"]) else None
                        prevDate = df.at[n-1, "created"].isocalendar() if n > 0 and pd.notnull(df.at[n-1, "created"]) else None

                        curWeek = df.at[n, "created"].week if pd.notnull(df.at[n, "created"]) else None
                        prevWeek = df.at[n-1, "created"].week if n > 0 and pd.notnull(df.at[n-1, "created"]) else None
                        
                        curMonth = df.at[n, "created"].month_name() if pd.notnull(df.at[n, "created"]) else None
                        prevMonth = df.at[n-1, "created"].month_name() if n > 0 and pd.notnull(df.at[n-1, "created"]) else None
                        
                        # Daily
                        if curDate != prevDate:
                          lowDaily = lowDailyCur
                          highDaily = highDailyCur
                          dailyPivot = dailyPivotCur
                          
                          lowDailyCur = low
                          highDailyCur = high
                        else:
                          lowDailyCur = min(low, lowDailyCur)
                          highDailyCur = max(high, highDailyCur)
                        
                        dailyPivotCur = (close + highDailyCur + lowDailyCur) / 3
                        
                        if dailyPivot != None and dailyPivot != -1:
                          dr1 = (2*dailyPivot) - lowDaily
                          ds1 = (2*dailyPivot) - highDaily
                          dr2 = (dailyPivot) + (highDaily - lowDaily)
                          ds2 = (dailyPivot) - (highDaily - lowDaily)
                          dr3 = (dr1) + (highDaily - lowDaily)
                          ds3 = (ds1) - (highDaily - lowDaily)
                          dr4 = (dr3) + (dr2 - dr1)
                          ds4 = (ds3) - (ds1 - ds2)
                          dr5 = (dr4) + (dr3 - dr2)
                          ds5 = (ds4) - (ds2 - ds3)
                        else:
                          dr1 = -1
                          ds1 = -1
                          dr2 = -1
                          ds2 = -1
                          dr3 = -1
                          ds3 = -1
                          dr4 = -1
                          ds4 = -1
                          dr5 = -1
                          ds5 = -1
                          dailyPivot = -1
                          lowDaily = -1
                          highDaily = -1
                        
                        df.at[n, 'dpivot'] = dailyPivot
                        df.at[n, 'dr1'] = dr1
                        df.at[n, 'ds1'] = ds1
                        df.at[n, 'dr2'] = dr2
                        df.at[n, 'ds2'] = ds2
                        df.at[n, 'dr3'] = dr3
                        df.at[n, 'ds3'] = ds3
                        df.at[n, 'dr4'] = dr4
                        df.at[n, 'ds4'] = ds4
                        df.at[n, 'dr5'] = dr5
                        df.at[n, 'ds5'] = ds5
                        
                        # Weekly
                        if curWeek != prevWeek:
                          lowWeekly = lowWeeklyCur
                          highWeekly = highWeeklyCur
                          weeklyPivot = weeklyPivotCur
                          
                          lowWeeklyCur = low
                          highWeeklyCur = high
                        else:
                          lowWeeklyCur = min(low, lowWeeklyCur)
                          highWeeklyCur = max(high, highWeeklyCur)
                          
                        weeklyPivotCur = (close + highWeeklyCur + lowWeeklyCur) / 3
                        
                        if weeklyPivot != None and weeklyPivot != -1:
                          wr1 = (2*weeklyPivot) - lowWeekly
                          ws1 = (2*weeklyPivot) - highWeekly
                          wr2 = (weeklyPivot) + (highWeekly - lowWeekly)
                          ws2 = (weeklyPivot) - (highWeekly - lowWeekly)
                          wr3 = (wr1) + (highWeekly - lowWeekly)
                          ws3 = (ws1) - (highWeekly - lowWeekly)
                          wr4 = (wr3) + (wr2 - wr1)
                          ws4 = (ws3) - (ws1 - ws2)
                          wr5 = (wr4) + (wr3 - wr2)
                          ws5 = (ws4) - (ws2 - ws3)
                        else:
                          wr1 = -1
                          ws1 = -1
                          wr2 = -1
                          ws2 = -1
                          wr3 = -1
                          ws3 = -1
                          wr4 = -1
                          ws4 = -1
                          wr5 = -1
                          ws5 = -1
                          weeklyPivot = -1
                          lowWeekly = -1
                          highWeekly = -1
                        
                        df.at[n, 'wpivot'] = weeklyPivot
                        df.at[n, 'wr1'] = wr1
                        df.at[n, 'ws1'] = ws1
                        df.at[n, 'wr2'] = wr2
                        df.at[n, 'ws2'] = ws2
                        df.at[n, 'wr3'] = wr3
                        df.at[n, 'ws3'] = ws3
                        df.at[n, 'wr4'] = wr4
                        df.at[n, 'ws4'] = ws4
                        df.at[n, 'wr5'] = wr5
                        df.at[n, 'ws5'] = ws5
                            
                        # Monthly
                        if curMonth != prevMonth:
                          lowMonthly = lowMonthlyCur
                          highMonthly = highMonthlyCur
                          monthlyPivot = monthlyPivotCur
                          
                          lowMonthlyCur = low
                          highMonthlyCur = high
                        else:
                          lowMonthlyCur = min(low, lowMonthlyCur)
                          highMonthlyCur = max(high, highMonthlyCur)
                        
                        monthlyPivotCur = (close + highMonthlyCur + lowMonthlyCur) / 3
                        
                        if monthlyPivot != None and monthlyPivot != -1:
                          mr1 = (2*monthlyPivot) - lowMonthly
                          ms1 = (2*monthlyPivot) - highMonthly
                          mr2 = (monthlyPivot) + (highMonthly - lowMonthly)
                          ms2 = (monthlyPivot) - (highMonthly - lowMonthly)
                          mr3 = (mr1) + (highMonthly - lowMonthly)
                          ms3 = (ms1) - (highMonthly - lowMonthly)
                          mr4 = (mr3) + (mr2 - mr1)
                          ms4 = (ms3) - (ms1 - ms2)
                          mr5 = (mr4) + (mr3 - mr2)
                          ms5 = (ms4) - (ms2 - ms3)    
                        else:
                          mr1 = -1
                          ms1 = -1
                          mr2 = -1
                          ms2 = -1
                          mr3 = -1
                          ms3 = -1
                          mr4 = -1
                          ms4 = -1
                          mr5 = -1
                          ms5 = -1  
                          monthlyPivot = -1
                          lowMonthly = -1
                          highMonthly = -1
                        
                        df.at[n, 'mpivot'] = monthlyPivot
                        df.at[n, 'mr1'] = mr1
                        df.at[n, 'ms1'] = ms1
                        df.at[n, 'mr2'] = mr2 
                        df.at[n, 'ms2'] = ms2 
                        df.at[n, 'mr3'] = mr3
                        df.at[n, 'ms3'] = ms3
                        df.at[n, 'mr4'] = mr4 
                        df.at[n, 'ms4'] = ms4 
                        df.at[n, 'mr5'] = mr5 
                        df.at[n, 'ms5'] = ms5  
                        
                        # 7. process variable
                        df.at[n, "fharray"] = FhArray[:]
                        df.at[n, "flarray"] = FlArray[:]
                        df.at[n, "sharray"] = ShArray[:]
                        df.at[n, "slarray"] = SlArray[:]
                        df.at[n, "need_break_fractal_up"] = 1 if need_break_fractal_up else 0
                        df.at[n, "anchorarray"] = anchorArray[:]
                        df.at[n, "anchor1starray"] = anchor1stArray[:]
                        df.at[n, "anchorcntrarray"] = anchorCntrArray[:]
                        df.at[n, "high1starray"] = high1stArray[:]
                        df.at[n, "low1starray"] = low1stArray[:]
                        df.at[n, "lowdailycur"] = lowDailyCur
                        df.at[n, "highdailycur"] = highDailyCur
                        df.at[n, "lowweeklycur"] = lowWeeklyCur
                        df.at[n, "highweeklycur"] = highWeeklyCur
                        df.at[n, "lowmonthlycur"] = lowMonthlyCur
                        df.at[n, "highmonthlycur"] = highMonthlyCur
                        df.at[n, "lowdaily"] = lowDaily
                        df.at[n, "highdaily"] = highDaily
                        df.at[n, "lowweekly"] = lowWeekly
                        df.at[n, "highweekly"] = highWeekly
                        df.at[n, "lowmonthly"] = lowMonthly
                        df.at[n, "highmonthly"] = highMonthly
                        df.at[n, "dpivotcur"] = dailyPivotCur
                        df.at[n, "wpivotcur"] = weeklyPivotCur
                        df.at[n, "mpivotcur"] = monthlyPivotCur
                        df.at[n, "direction"] = direction
                        
                        # variable memory management
                        FhArray = FhArray[:100]
                        FlArray = FlArray[:100]
                        ShArray = ShArray[:100]
                        SlArray = SlArray[:100]  
                        n = n + 1
                        # END OF ROW LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
                        
                        # Output Management ===============================================
                        if 'token' in df.columns:
                            df_valid = df.dropna(subset=['token', 'symbol', 'open', 'high', 'low', 'close', 'volume'])
                            
                            # Process numeric columns
                            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'atr', 'atr_trail_stop_loss', 
                                           'dc_upper', 'dc_lower', 'dc_mid', 'fh_price', 'fl_price', 'sh_price', 'sl_price',
                                           'dpivot', 'ds1', 'ds2', 'ds3', 'ds4', 'ds5', 'dr1', 'dr2', 'dr3', 'dr4', 'dr5',
                                           'wpivot', 'ws1', 'ws2', 'ws3', 'ws4', 'ws5', 'wr1', 'wr2', 'wr3', 'wr4', 'wr5',
                                           'mpivot', 'ms1', 'ms2', 'ms3', 'ms4', 'ms5', 'mr1', 'mr2', 'mr3', 'mr4', 'mr5',
                                           'lowdailycur', 'highdailycur', 'lowweeklycur', 'highweeklycur',
                                           'lowmonthlycur', 'highmonthlycur', 'lowdaily', 'highdaily',
                                           'lowweekly', 'highweekly', 'lowmonthly', 'highmonthly',
                                           'dpivotcur', 'wpivotcur', 'mpivotcur']
                            for col in numeric_cols:
                                if col in df_valid.columns:
                                    # Convert empty strings to NaN first
                                    df_valid[col] = df_valid[col].replace('', np.nan)
                                    df_valid[col] = pd.to_numeric(df_valid[col], errors='coerce')
                            
                            int_cols = ['lowestfrom1stlow', 'highestfrom1sthigh', 'fl_dbg', 'fh_dbg', 'n', 'n_lookback']
                            for col in int_cols:
                                if col in df_valid.columns:
                                    # Convert empty strings to NaN first
                                    df_valid[col] = df_valid[col].replace('', np.nan)
                                    df_valid[col] = pd.to_numeric(df_valid[col], errors='coerce')
                                    # Convert to integer, but handle NaN values
                                    df_valid[col] = df_valid[col].astype('Int64')  # pandas nullable integer type
                            
                            df_valid['token'] = df_valid['token'].astype('int64')
                            
                            bool_cols = ['fh_status', 'fl_status', 'sh_status', 'sl_status', 'need_break_fractal_up', 'direction']
                            for col in bool_cols:
                                if col in df_valid.columns:
                                    df_valid[col] = df_valid[col].astype(bool)
                            
                            # Define the desired order of columns (all names in lowercase as created by PostgreSQL)
                            desired_columns = [
                                "created", "token", "symbol", "open", "close", "high", "low", "volume", "atr", "atr_trail_stop_loss",
                                "dc_upper", "dc_lower", "dc_mid", "fh_price", "fl_price", "fh_status", "fl_status", "sh_price", "sl_price",
                                "sh_status", "sl_status", "lowestfrom1stlow", "highestfrom1sthigh", "fl_dbg", "fh_dbg", "dpivot", "ds1",
                                "ds2", "ds3", "ds4", "ds5", "dr1", "dr2", "dr3", "dr4", "dr5", "wpivot", "ws1", "ws2", "ws3", "ws4",
                                "ws5", "wr1", "wr2", "wr3", "wr4", "wr5", "mpivot", "ms1", "ms2", "ms3", "ms4", "ms5", "mr1", "mr2",
                                "mr3", "mr4", "mr5", "n", "n_lookback", "fharray", "flarray", "sharray", "slarray", "need_break_fractal_up",
                                "anchorarray", "anchor1starray", "anchorcntrarray", "high1starray", "low1starray", "lowdailycur",
                                "highdailycur", "lowweeklycur", "highweeklycur", "lowmonthlycur", "highmonthlycur", "lowdaily",
                                "highdaily", "lowweekly", "highweekly", "lowmonthly", "highmonthly", "dpivotcur", "wpivotcur", "mpivotcur",
                                "direction"
                            ]
                            
                            # Create a new DataFrame with only the columns that exist in df_valid
                            # and in the correct order
                            ordered_columns = [col for col in desired_columns if col in df_valid.columns.str.lower()]
                            df_valid.columns = df_valid.columns.str.lower()
                            df_valid = df_valid[ordered_columns]
                            
                            # Ensure created is a proper timestamp
                            if 'created' in df_valid.columns:
                                df_valid['created'] = pd.to_datetime(df_valid['created'], errors='coerce')
                                # Drop rows with invalid timestamps
                                df_valid = df_valid.dropna(subset=['created'])
                            
                            # CSV output logic from original code
                            if len(df_valid) <= 1000:
                                if token_index == 0:
                                    df_valid.iloc[:500].to_csv('output_data_stock.csv', mode='w', header=True, index=False)
                                else:
                                    df_valid.iloc[:500].to_csv('output_data_stock.csv', mode='a', header=False, index=False)
                            else:
                                df_valid.iloc[500:1500].to_csv('output_data_stock.csv', mode='a', header=False, index=False)
                        else:
                            logger.warning(f"No token column found in dataframe for token_index {token_index}")
                            continue
                        
                        # Output Management End ===============================================
                            
                    # END OF CHUNK LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
                    if len(df_valid) <= 1000:
                      # Make sure we output all remaining rows
                      df_valid.iloc[500:].to_csv('output_data_stock.csv', mode='a', header=False, index=False)
                    else:
                      # Make sure we output all remaining rows
                      df_valid.iloc[1500:].to_csv('output_data_stock.csv', mode='a', header=False, index=False)
                    # Use for all? enable when debugging
                    # break
                    # END OF TOKEN LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

                # Bulk CSV-to-SQL operations
                with engine.connect() as conn:
                    # Now use INSERT with ON CONFLICT to handle existing records
                    # Note: We're not dropping the table anymore, just inserting/updating data
                    columns = [
                        "token", "symbol", "open", "close", "high", "low", "volume", "created",
                        "atr", "atr_trail_stop_loss", "dc_upper", "dc_lower", "dc_mid", "fh_price",
                        "fl_price", "fh_status", "fl_status", "sh_price", "sl_price", "sh_status",
                        "sl_status", "lowestfrom1stlow", "highestfrom1sthigh", "fl_dbg", "fh_dbg",
                        "dpivot", "ds1", "ds2", "ds3", "ds4", "ds5", "dr1", "dr2", "dr3", "dr4",
                        "dr5", "wpivot", "ws1", "ws2", "ws3", "ws4", "ws5", "wr1", "wr2", "wr3",
                        "wr4", "wr5", "mpivot", "ms1", "ms2", "ms3", "ms4", "ms5", "mr1", "mr2",
                        "mr3", "mr4", "mr5", "n", "n_lookback", "fharray", "flarray", "sharray",
                        "slarray", "need_break_fractal_up", "anchorarray", "anchor1starray",
                        "anchorcntrarray", "high1starray", "low1starray", "lowdailycur",
                        "highdailycur", "lowweeklycur", "highweeklycur", "lowmonthlycur",
                        "highmonthlycur", "lowdaily", "highdaily", "lowweekly", "highweekly",
                        "lowmonthly", "highmonthly", "dpivotcur", "wpivotcur", "mpivotcur",
                        "direction"
                    ]
                    placeholders = ", ".join([f":{col}" for col in columns])
                    query = f"""
                        INSERT INTO {output_table} ({', '.join(columns)}) 
                        VALUES ({placeholders})
                        ON CONFLICT ON CONSTRAINT {output_table}_created_token_n_key 
                        DO UPDATE SET 
                        {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['created', 'token', 'n']])}
                    """
                    
                    data = []
                    with open('output_data_stock.csv', newline='') as csvfile:
                        # Define the proper column names based on your schema
                        # This ensures we don't rely on the first row of the CSV as headers
                        fieldnames = [
                            "created","token", "symbol", "open", "close", "high", "low", "volume",
                            "atr", "atr_trail_stop_loss", "dc_upper", "dc_lower", "dc_mid", "fh_price",
                            "fl_price", "fh_status", "fl_status", "sh_price", "sl_price", "sh_status",
                            "sl_status", "lowestfrom1stlow", "highestfrom1sthigh", "fl_dbg", "fh_dbg",
                            "dpivot", "ds1", "ds2", "ds3", "ds4", "ds5", "dr1", "dr2", "dr3", "dr4",
                            "dr5", "wpivot", "ws1", "ws2", "ws3", "ws4", "ws5", "wr1", "wr2", "wr3",
                            "wr4", "wr5", "mpivot", "ms1", "ms2", "ms3", "ms4", "ms5", "mr1", "mr2",
                            "mr3", "mr4", "mr5", "n", "n_lookback", "fharray", "flarray", "sharray",
                            "slarray", "need_break_fractal_up", "anchorarray", "anchor1starray",
                            "anchorcntrarray", "high1starray", "low1starray", "lowdailycur",
                            "highdailycur", "lowweeklycur", "highweeklycur", "lowmonthlycur",
                            "highmonthlycur", "lowdaily", "highdaily", "lowweekly", "highweekly",
                            "lowmonthly", "highmonthly", "dpivotcur", "wpivotcur", "mpivotcur",
                            "direction"
                        ]
                        
                        valid_rows = 0
                        skipped_rows = 0
                        
                        # Function to process a single row to avoid code duplication
                        def process_row(row, data, skipped_rows, valid_rows):
                            try:
                                # Validate and convert the created field
                                created_val = row.get('created')
                                if created_val is None or str(created_val).strip() == "" or str(created_val).lower() in ["nan", "none"]:
                                    # Skip the row due to invalid created value
                                    logger.warning(f"Skipping row due to invalid created value: {created_val}")
                                    skipped_rows += 1
                                    return skipped_rows, valid_rows
                                else:
                                    # Try converting to datetime
                                    try:
                                        row['created'] = pd.to_datetime(created_val)
                                    except Exception as e:
                                        logger.warning(f"Error converting created value: {created_val} - {str(e)}")
                                        skipped_rows += 1
                                        return skipped_rows, valid_rows
                            
                                # More lenient token validation
                                token_value = str(row.get('token')).strip()
                                if token_value and token_value.isdigit():
                                    row['token'] = int(token_value)
                                else:
                                    skipped_rows += 1
                                    logger.warning(f"Invalid token format: {token_value}")
                                    return skipped_rows, valid_rows

                                # Validate n value - skip rows with None as n value
                                n_value = row.get('n')
                                if n_value is None or str(n_value).strip() == "" or str(n_value).lower() == "nan" or str(n_value).lower() == "none":
                                    skipped_rows += 1
                                    logger.warning(f"Skipping row with NULL n value for token: {row.get('token')}")
                                    return skipped_rows, valid_rows

                                # Define all numeric fields based on schema
                                float_fields = [
                                    'open', 'high', 'low', 'close', 'volume',
                                    'atr', 'atr_trail_stop_loss', 'dc_upper', 'dc_lower', 'dc_mid',
                                    'fh_price', 'fl_price', 'sh_price', 'sl_price',
                                    'dpivot', 'ds1', 'ds2', 'ds3', 'ds4', 'ds5',
                                    'dr1', 'dr2', 'dr3', 'dr4', 'dr5',
                                    'wpivot', 'ws1', 'ws2', 'ws3', 'ws4', 'ws5',
                                    'wr1', 'wr2', 'wr3', 'wr4', 'wr5',
                                    'mpivot', 'ms1', 'ms2', 'ms3', 'ms4', 'ms5',
                                    'mr1', 'mr2', 'mr3', 'mr4', 'mr5',
                                    'lowdailycur', 'highdailycur', 'lowweeklycur', 'highweeklycur',
                                    'lowmonthlycur', 'highmonthlycur', 'lowdaily', 'highdaily',
                                    'lowweekly', 'highweekly', 'lowmonthly', 'highmonthly',
                                    'dpivotcur', 'wpivotcur', 'mpivotcur'
                                ]
                                
                                int_fields = [
                                    'lowestfrom1stlow', 'highestfrom1sthigh', 'fl_dbg', 'fh_dbg',
                                    'n', 'n_lookback'
                                ]
                                
                                # Process float fields
                                for field in float_fields:
                                    if field in row:
                                        try:
                                            value = str(row[field]).strip()
                                            if value == "" or value.lower() == "nan" or value.lower() == "none":
                                                row[field] = None
                                            else:
                                                row[field] = float(value)
                                        except (ValueError, TypeError):
                                            row[field] = None
                                            
                                # Process integer fields
                                for field in int_fields:
                                    if field in row and row[field] is not None:
                                        try:
                                            value = str(row[field]).strip()
                                            if value == "" or value.lower() == "nan" or value.lower() == "none":
                                                row[field] = None
                                            else:
                                                row[field] = int(float(value))  # Convert through float to handle decimal strings
                                        except (ValueError, TypeError):
                                            row[field] = None
                                    elif field in row:
                                        row[field] = None

                                # Handle boolean fields
                                bool_fields = ['fh_status', 'fl_status', 'sh_status', 'sl_status', 'need_break_fractal_up', 'direction']
                                for field in bool_fields:
                                    if field in row and row[field] is not None:
                                        try:
                                            value = str(row[field]).strip()
                                            if value == "" or value.lower() == "nan" or value.lower() == "none":
                                                row[field] = False
                                            else:
                                                row[field] = bool(int(float(value)))  # Convert through float to handle decimal strings
                                        except (ValueError, TypeError):
                                            row[field] = False
                                    elif field in row:
                                        row[field] = False

                                # Handle array fields (ensure they're never empty strings)
                                array_fields = ['fharray', 'flarray', 'sharray', 'slarray', 
                                               'anchorarray', 'anchor1starray', 'anchorcntrarray', 
                                               'high1starray', 'low1starray']
                                for field in array_fields:
                                    if field in row and (row[field] is None or str(row[field]).strip() == ""):
                                        row[field] = "[]"  # Empty array as string

                                # Build row_dict with all required columns
                                row_dict = {}
                                for col in columns:
                                    row_dict[col] = row.get(col)

                                data.append(row_dict)
                                valid_rows += 1
                                return skipped_rows, valid_rows

                            except Exception as e:
                                skipped_rows += 1
                                logger.warning(f"Error processing row: {str(e)}")
                                return skipped_rows, valid_rows
                    
                        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
                        
                        # Skip header if it exists
                        header = next(reader, None)
                        if header:
                            # Check if this is actually a header row
                            if not any(str(val).isdigit() for val in header.values()):
                                logger.info("Skipping CSV header row")
                            else:
                                # Process first row if it contains data
                                skipped_rows, valid_rows = process_row(header, data, skipped_rows, valid_rows)
                        
                        for row in reader:
                            if not row or not any(row.values()):  # Skip empty rows
                                continue
                            skipped_rows, valid_rows = process_row(row, data, skipped_rows, valid_rows)

                        logger.info(f"CSV processing summary: {valid_rows} valid rows processed, {skipped_rows} rows skipped")
                        
                        if len(data) == 0:
                            logger.warning("No valid data found in CSV, skipping insert")
                            continue  # Skip to next token
                
                with engine.connect() as conn:
                    # Process each row in a separate transaction to avoid aborting all on error
                    for row in data:
                        try:
                            with conn.begin():
                                # Log the query parameters for debugging
                                logger.debug(f"Executing SQL with parameters for token: {row.get('token')}, n: {row.get('n')}")
                                conn.execute(text(query), row)
                                logger.debug(f"Successfully inserted/updated row for token: {row.get('token')}, n: {row.get('n')}")
                        except Exception as e:
                            logger.error(f"Error executing SQL: {str(e)}")
                            logger.error(f"Row data: {row}")
                            # Continue with next row
                    # Transaction will be automatically rolled back
                
                os.remove("output_data_stock.csv")
                
            # END OF TOKEN LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

            # Return the start date after all tokens are processed
        startdate = datetime.now()
        return str(startdate)

    except Exception as e:
        logger.error(f"Error in InitProcess: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}, 500

@app.route('/update')
def UpdateProcess():
    try:
        # Define startdate at the beginning of the function
        startdate = datetime.now()
        
        # Similar changes needed here - wrap database operations in connection context
        password = os.getenv("DB_PASSWORD", "password")  # Should be in environment variable  
        encoded_password = urlquote(password)
        uri = f"postgresql://postgres:{encoded_password}@localhost:5432/theodb"
        
        input_table = 'stock_ohlc_15min'
        output_table = 'tbl_ohlc_fifteen_output'
        engine = create_engine(uri)

        # Add unique constraint on (token, n) if it doesn't exist
        with engine.connect() as conn:
            # Check if the constraint already exists
            check_constraint_query = text("""
                SELECT COUNT(*) 
                FROM pg_constraint 
                WHERE conname = 'unique_token_n' 
                AND conrelid = 'tbl_ohlc_fifteen_output'::regclass
            """)
            
            constraint_exists = conn.execute(check_constraint_query).scalar()
            
            if not constraint_exists:
                # Add the unique constraint
                add_constraint_query = text(f"""
                    ALTER TABLE {output_table}
                    ADD CONSTRAINT unique_token_n UNIQUE (token, n)
                """)
                try:
                    conn.execute(add_constraint_query)
                    conn.commit()
                    logger.info("Added unique constraint on (token, n)")
                except Exception as e:
                    logger.warning(f"Could not add unique constraint: {str(e)}")
                    # If error is due to duplicate values, we need to handle them
                    if "duplicate key value violates unique constraint" in str(e):
                        # Option: Remove duplicates keeping the latest entry
                        dedupe_query = text(f"""
                            DELETE FROM {output_table} a
                            USING (
                                SELECT token, n, MAX(id) as max_id
                                FROM {output_table}
                                GROUP BY token, n
                                HAVING COUNT(*) > 1
                            ) b
                            WHERE a.token = b.token AND a.n = b.n AND a.id != b.max_id
                        """)
                        conn.execute(dedupe_query)
                        conn.commit()
                        
                        # Try adding the constraint again
                        conn.execute(add_constraint_query)
                        conn.commit()
                        logger.info("Added unique constraint on (token, n) after deduplication")

        # Get tokens with a separate connection
        with engine.connect() as conn:
            query = text("""
                SELECT DISTINCT token 
                FROM stock_ohlc_15min 
                WHERE symbol NOT LIKE '%fut%' 
                AND token != 0
            """)
            
            tokens = pd.read_sql(query, conn)
            print("Total pair:", len(tokens))
            
        # TOKEN LOOP
        for token_index, token_row in tqdm(tokens.iterrows(), total=len(tokens)):
            # Verify token exists
            if token_row is None or 'token' not in token_row:
                logger.warning(f"Invalid token row: {token_row}")
                continue

            token_id = token_row.token
            logger.info(f"Processing token {token_id} (index {token_index}/{len(tokens)}) in UpdateProcess")
            
            # Open a new connection for each token
            with engine.connect() as conn:
                # create output buffer
                df = pd.DataFrame()

                # CHECK LAST UPDATED ROW ON OTBL <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
                query = "SELECT created, n, n_lookback FROM {} WHERE token={} ORDER BY created DESC LIMIT 1".format(
                    output_table, 
                    token_row.token
                )
                # Convert to SQLAlchemy text object
                query = text(query)
                if len(pd.read_sql(query, conn).head(1).n_lookback) > 0:
                  # Fix FutureWarning by using .iloc[0] instead of directly calling int on Series
                  result_df = pd.read_sql(query, conn).head(1)
                  last_updated_n_lookback = int(result_df.n_lookback.iloc[0])
                  last_updated_created = result_df.created.iloc[0]
                  last_updated_n = int(result_df.n.iloc[0])
                  
                  # GET N ROW NEEDED FROM OTBL <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
                  query = "SELECT * FROM {} WHERE token = {} AND n >= {}".format(
                        output_table,
                        token_row.token,
                        last_updated_n_lookback
                      )
                  # Convert to SQLAlchemy text object
                  query = text(query)
                  df = pd.read_sql(query, conn)
                else:
                  last_updated_created = None
                  last_updated_id = -1
                  last_updated_n_lookback = 0
            
                # variables =============================================================================================================================================
                if len(df) == 0:
                  FhArray = [0]
                  FlArray = [0]

                  ShArray = [0]
                  SlArray = [0]
                  
                  need_break_fractal_up = True

                  anchorArray = [0]
                  anchor1stArray = [0]
                  anchorCntrArray = [0]

                  high1stArray = [0]
                  low1stArray = [0]
                  
                  # Pivot variable
                  lowDailyCur = None
                  highDailyCur = None
                  lowWeeklyCur = None
                  highWeeklyCur = None
                  lowMonthlyCur = None
                  highMonthlyCur = None
                  lowDaily = None
                  highDaily = None
                  lowWeekly = None
                  highWeekly = None
                  lowMonthly = None
                  highMonthly = None
                  dailyPivotCur = None
                  weeklyPivotCur = None
                  monthlyPivotCur = None
                
                  n = 0
                  direction = 1
                else:
                  try:
                      # Access columns using dictionary-style with lowercase names
                      last_row = df.tail(1).iloc[0]
                      FhArray = list(map(int, last_row['fharray'][1:-1].split(", "))) if pd.notnull(last_row['fharray']) else [0]
                      FlArray = list(map(int, last_row['flarray'][1:-1].split(", "))) if pd.notnull(last_row['flarray']) else [0]
                      ShArray = list(map(int, last_row['sharray'][1:-1].split(", "))) if pd.notnull(last_row['sharray']) else [0]
                      SlArray = list(map(int, last_row['slarray'][1:-1].split(", "))) if pd.notnull(last_row['slarray']) else [0]
                      
                      need_break_fractal_up = True if last_row['need_break_fractal_up'] is not None and int(last_row['need_break_fractal_up']) == 1 else False

                      anchorArray = list(map(int, last_row['anchorarray'][1:-1].split(", "))) if pd.notnull(last_row['anchorarray']) else [0]
                      anchor1stArray = list(map(int, last_row['anchor1starray'][1:-1].split(", "))) if pd.notnull(last_row['anchor1starray']) else [0]
                      anchorCntrArray = list(map(int, last_row['anchorcntrarray'][1:-1].split(", "))) if pd.notnull(last_row['anchorcntrarray']) else [0]

                      high1stArray = list(map(int, last_row['high1starray'][1:-1].split(", "))) if pd.notnull(last_row['high1starray']) else [0]
                      low1stArray = list(map(int, last_row['low1starray'][1:-1].split(", "))) if pd.notnull(last_row['low1starray']) else [0]
                      
                      # Pivot variable
                      lowDailyCur = float(last_row['lowdailycur']) if last_row['lowdailycur'] is not None else None
                      highDailyCur = float(last_row['highdailycur']) if last_row['highdailycur'] is not None else None
                      lowWeeklyCur = float(last_row['lowweeklycur']) if last_row['lowweeklycur'] is not None else None
                      highWeeklyCur = float(last_row['highweeklycur']) if last_row['highweeklycur'] is not None else None
                      lowMonthlyCur = float(last_row['lowmonthlycur']) if last_row['lowmonthlycur'] is not None else None
                      highMonthlyCur = float(last_row['highmonthlycur']) if last_row['highmonthlycur'] is not None else None
                      lowDaily = float(last_row['lowdaily']) if last_row['lowdaily'] is not None else None
                      highDaily = float(last_row['highdaily']) if last_row['highdaily'] is not None else None
                      lowWeekly = float(last_row['lowweekly']) if last_row['lowweekly'] is not None else None
                      highWeekly = float(last_row['highweekly']) if last_row['highweekly'] is not None else None
                      lowMonthly = float(last_row['lowmonthly']) if last_row['lowmonthly'] is not None else None
                      highMonthly = float(last_row['highmonthly']) if last_row['highmonthly'] is not None else None
                      dailyPivot = float(last_row['dpivot']) if last_row['dpivot'] is not None else None
                      weeklyPivot = float(last_row['wpivot']) if last_row['wpivot'] is not None else None
                      monthlyPivot = float(last_row['mpivot']) if last_row['mpivot'] is not None else None
                      dailyPivotCur = float(last_row['dpivotcur']) if last_row['dpivotcur'] is not None else None
                      weeklyPivotCur = float(last_row['wpivotcur']) if last_row['wpivotcur'] is not None else None
                      monthlyPivotCur = float(last_row['mpivotcur']) if last_row['mpivotcur'] is not None else None
                  
                      n = int(last_row['n']) + 1 if last_row['n'] is not None else 1
                      direction = int(last_row['direction']) if last_row['direction'] is not None else 1
                  except Exception as e:
                      logger.warning(f"Error accessing DataFrame attributes: {str(e)}")
                      # Fall back to default values
                      FhArray = [0]
                      FlArray = [0]
                      ShArray = [0]
                      SlArray = [0]
                      need_break_fractal_up = True
                      anchorArray = [0]
                      anchor1stArray = [0]
                      anchorCntrArray = [0]
                      high1stArray = [0]
                      low1stArray = [0]
                      lowDailyCur = None
                      highDailyCur = None
                      lowWeeklyCur = None
                      highWeeklyCur = None
                      lowMonthlyCur = None
                      highMonthlyCur = None
                      lowDaily = None
                      highDaily = None
                      lowWeekly = None
                      highWeekly = None
                      lowMonthly = None
                      highMonthly = None
                      dailyPivotCur = None
                      weeklyPivotCur = None
                      monthlyPivotCur = None
                      dailyPivot = None
                      weeklyPivot = None
                      monthlyPivot = None
                      n = 0
                      direction = 1
                # end of variables =============================================================================================================================================

                
                # CHUNK LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
                if last_updated_created:
                    query = """
                        SELECT 
                            token, symbol, open, high, low, close, volume, created
                        FROM {} 
                        WHERE symbol NOT LIKE '%fut%' 
                        AND token = {} 
                        AND created > '{}'
                        ORDER BY created ASC
                    """.format(
                        input_table,
                        token_row.token,
                        last_updated_created
                    )
                else:
                    query = """
                        SELECT 
                            token, symbol, open, high, low, close, volume, created
                        FROM {} 
                        WHERE symbol NOT LIKE '%fut%' 
                        AND token = {}
                        ORDER BY created ASC
                    """.format(
                        input_table,
                        token_row.token
                    )
                # Convert to SQLAlchemy text object
                query = text(query)

                # Create a fresh connection for reading chunks
                with engine.connect() as chunk_conn:
                    for single_pair_chunk in pd.read_sql(query, chunk_conn, chunksize=1000):
                        # Ensure numeric columns are properly typed
                        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                        for col in numeric_cols:
                            single_pair_chunk[col] = pd.to_numeric(single_pair_chunk[col], errors='coerce')
                        
                        single_pair_chunk['token'] = single_pair_chunk['token'].astype(int)
                        
                        # memory management ==============================================================================================
                        # 1 # use chunk as initiation
                        if(len(df) == 0):
                            df = single_pair_chunk.iloc[:]
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
                            
                            # DEBUG
                            df["lowestfrom1stlow"] = None
                            df["highestfrom1sthigh"] = None
                            
                            df["fl_dbg"] = None
                            df["fh_dbg"] = None
                            
                            # Pivot        
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
                            
                            # process variable       
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
                            
                            startIndex = 0
                            
                        # 2 # concat new chunk
                        elif(len(df) < 2000):
                          startIndex = len(df)
                          df = pd.concat((df, single_pair_chunk), axis=0).reset_index(drop=True)
                          # Fix possible index issues by preserving the n value
                          current_n = n
                          df.index = df.index + int(df.head(1).n)
                          n = current_n  # Restore the correct n value
                          
                        # N # delete prev chunk, concat new chunk
                        else:
                          # Save the current processing position before resetting dataframe
                          current_n = n
                          df = df.iloc[1000:]
                          df = pd.concat((df, single_pair_chunk), axis=0).reset_index(drop=True)
                          startIndex = 1000
                          df.index = df.index + current_n - startIndex
                          # Restore n for correct continuation
                          n = current_n
                                
                        # calculate atr, dc =============================================================================================================================================
                        if startIndex==0:
                          df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=config["atr_trail_sl"]["atr_length"])
                        # df_atr = ta.atr(df["high"], df["low"], df["close"], length=config["atr_trail_sl"]["atr_length"])
                        try:
                            df_donchian = ta.donchian(df["high"], df["low"], lower_length=config["dc"]["dc_length"], upper_length=config["dc"]["dc_length"])
                            if df_donchian is None:
                                logger.warning("Donchian channel calculation returned None")
                            else:
                                logger.debug(f"Successfully calculated donchian channels with shape {df_donchian.shape}")
                        except Exception as e:
                            logger.error(f"Error calculating donchian channels: {str(e)}")
                            df_donchian = None

                        # ROW LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
                        for index, row in df.iloc[startIndex:].iterrows():
                          high = row["high"]
                          low = row["low"]
                          close = row["close"]
                          df.at[n, "n"] = n
                          df.at[n, "fh_status"] = 0
                          df.at[n, "fl_status"] = 0
                          df.at[n, "sh_status"] = 0
                          df.at[n, "sl_status"] = 0
                          df.at[n, "dc_upper"] = -1
                          df.at[n, "dc_lower"] = -1
                          df.at[n, "dc_mid"] = -1
                          df.at[n, "fl_dbg"] = -1
                          df.at[n, "fh_dbg"] = -1
                          
                          # 0. calculate ATR
                          if n <= config["atr_trail_sl"]["atr_length"]:
                            pass
                          elif n >= last_updated_n_lookback+startIndex:
                            tr = max(high-low, abs(close-row["open"]), abs(df.at[n-1, "close"]-low)) 
                            df.at[n, "atr"] = (df.at[n-1, "atr"] * (config["atr_trail_sl"]["atr_length"]-1) + tr) / config["atr_trail_sl"]["atr_length"]
                          # else:
                            
                          if df.at[n, "atr"] == None or math.isnan(df.at[n, "atr"]) :
                            df.at[n, "atr"] = -1
                            df.at[n, "atr_trail_stop_loss"] = -1
                          
                          # 1. calculate ATR trail stop loss ===============================================
                          atrMultiplier = config["atr_trail_sl"]["atr_multiplier"] # input
                          
                          # Check if ATR is None or NaN and set default value
                          if df.at[n, "atr"] is None or pd.isna(df.at[n, "atr"]):
                              df.at[n, "atr"] = -1
                              df.at[n, "atr_trail_stop_loss"] = -1
                              
                          stop = df.at[n, "atr"] * atrMultiplier
                          close1 = df.at[n-1, "close"] if n-1 != -1 else None
                          atrTrailingstop1 = df.at[index-1, "atr_trail_stop_loss"] if n-1 != -1 else None
                          atrTrailingstop1 = close if (atrTrailingstop1 == None) else atrTrailingstop1
                          if df.at[n,'atr_trail_stop_loss'] != -1:
                            if close > atrTrailingstop1 and close1>atrTrailingstop1:
                              df.at[n,'atr_trail_stop_loss'] = max(atrTrailingstop1, close-stop)
                            elif close<atrTrailingstop1 and close1<atrTrailingstop1:
                              df.at[n,'atr_trail_stop_loss'] = min(atrTrailingstop1, close+stop)
                            elif close>atrTrailingstop1:
                              df.at[n,'atr_trail_stop_loss'] = close - stop 
                            else:
                              df.at[n,'atr_trail_stop_loss'] = close + stop
                            
                          # 2. FH FL ===============================================
                                  
                          # # Searching for New Anchor        
                          if direction == 1:
                              # not first anchor
                              for i in range(len(anchorArray)):
                                  anchorBarsBack = n-anchorArray[i]
                                  if len(df[(df.n == n-anchorBarsBack) & ((high < df.high) | (close < df.close))]) >= 1:
                                      anchorArray.insert(0, n)
                                      anchor1stArray.insert(0, -1)
                                      anchorCntrArray.insert(0, 0)
                                      break
                          elif direction == -1:
                              # not first anchor
                              for i in range(len(anchorArray)):
                                  anchorBarsBack = n-anchorArray[i]
                                  if len(df[(df.n == n-anchorBarsBack) & ((low > df.low) | (close > df.close))]) >= 1:
                                      anchorArray.insert(0, n)
                                      anchor1stArray.insert(0, -1)
                                      anchorCntrArray.insert(0, 0)
                                      break
                          
                          # Searching for Anchor Breaker and Calculate Breaker Counter
                          minList1St = df[ (df.n >= low1stArray[0]) & (df.n <= n)].low.min()
                          minList1StN = int(df[ (df.n >= low1stArray[0]) & (df.n <= n) & (df.low == minList1St)].head(1).n.iloc[0])
                          
                          maxList1St = df[ (df.n >= high1stArray[0]) & (df.n <= n)].high.max()
                          maxList1StN = int(df[ (df.n >= high1stArray[0]) & (df.n <= n) & (df.high == maxList1St)].head(1).n.iloc[0])
                          
                          LowestSinceLastFl = df[ (df.n >= FlArray[0]) & (df.n <= n)].low.min()
                          HighestSinceLastFh = df[ (df.n >= FhArray[0]) & (df.n <= n)].high.max()

                          if need_break_fractal_up:
                            if len(df[(df.n == FhArray[0]) & (HighestSinceLastFh != df.high)]) == 1:
                              SlArray.insert(0, minList1StN)
                              need_break_fractal_up = False
                              df.at[ SlArray[0], "sl_status" ] = 1
                            else:
                              if len(df[(df.n == FlArray[0]) & (LowestSinceLastFl != df.low)]) == 1:
                                ShArray.insert(0, maxListSlN)
                                need_break_fractal_up = True
                                df.at[ ShArray[0], "sh_status" ] = 1
                            
                            try:
                              df.at[ n, "sl_price" ] = float(df.at[SlArray[0], "low"])
                            except:
                              df.at[ n, "sl_price" ] = 0
                            try:
                              df.at[ n, "sh_price" ] = float(df.at[ShArray[0], "high"])
                            except:
                              df.at[ n, "sh_price" ] = 0
                          
                        df.at[n, "n_lookback"] = ShArray[1] if len(ShArray) >= 2 else 0 if df.at[n, "n_lookback"] == None else int(np.nanmin([df.at[n, "n_lookback"], ShArray[1] if len(ShArray) >= 2 else 0]))
                        df.at[n, "n_lookback"] = SlArray[1] if len(SlArray) >= 2 else 0 if df.at[n, "n_lookback"] == None else int(np.nanmin([df.at[n, "n_lookback"], SlArray[1] if len(SlArray) >= 2 else 0]))
                         
                        df.at[n, "n_lookback"] = int(max(0, np.nanmin([df.at[n, "n_lookback"], n-(config["atr_trail_sl"]["atr_length"]+1)])))
                                       
                        # 4. Normal dc ===============================================
                        if config["dc"]["dc_source"] == "length":
                            if df_donchian is not None and index in df_donchian.index:
                                dc_col = f"DCU_{config['dc']['dc_length']}_{config['dc']['dc_length']}"
                                if dc_col in df_donchian.columns and not pd.isna(df_donchian.at[index, dc_col]):
                                    df.at[n, "dc_upper"] = df_donchian.at[index, dc_col]
                                    df.at[n, "dc_lower"] = df_donchian.at[index, dc_col]
                                    df.at[n, "dc_mid"] = df_donchian.at[index, dc_col]
                                    df.at[n, "n_lookback"] = int(max(0, np.nanmin([df.at[n, "n_lookback"], n-(config["dc"]["dc_length"]+1)])))
                          
                        # 5. Swing DC ===============================================
                        else:
                          df.at[n, "dc_upper"] = df[ (df.n >= (ShArray[config["dc"]["dc_length"]-1] if len(ShArray) >= config["dc"]["dc_length"] else 0)) & (df.n <= n)].high.max()
                          df.at[n, "dc_lower"] = df[ (df.n >= (SlArray[config["dc"]["dc_length"]-1] if len(SlArray) >= config["dc"]["dc_length"] else 0)) & (df.n <= n)].low.min()
                          df.at[n, "dc_mid"] = (df.at[n, "dc_upper"] + df.at[n, "dc_lower"])/2
                          df.at[n, "n_lookback"] = int(max(0, np.nanmin([df.at[n, "n_lookback"], ShArray[config["dc"]["dc_length"]-1] if len(ShArray) >= config["dc"]["dc_length"] else 0])))
                          df.at[n, "n_lookback"] = int(max(0, np.nanmin([df.at[n, "n_lookback"], SlArray[config["dc"]["dc_length"]-1] if len(SlArray) >= config["dc"]["dc_length"] else 0])))

                        # 6. Pivot ===============================================
                        
                        curDate = df.at[n, "created"].isocalendar() if pd.notnull(df.at[n, "created"]) else None
                        prevDate = df.at[n-1, "created"].isocalendar() if n > 0 and pd.notnull(df.at[n-1, "created"]) else None

                        curWeek = df.at[n, "created"].week if pd.notnull(df.at[n, "created"]) else None
                        prevWeek = df.at[n-1, "created"].week if n > 0 and pd.notnull(df.at[n-1, "created"]) else None
                        
                        curMonth = df.at[n, "created"].month_name() if pd.notnull(df.at[n, "created"]) else None
                        prevMonth = df.at[n-1, "created"].month_name() if n > 0 and pd.notnull(df.at[n-1, "created"]) else None
                        
                        # Daily
                        if curDate != prevDate:
                          lowDaily = lowDailyCur
                          highDaily = highDailyCur
                          dailyPivot = dailyPivotCur
                          
                          lowDailyCur = low
                          highDailyCur = high
                        else:
                          lowDailyCur = min(low, lowDailyCur)
                          highDailyCur = max(high, highDailyCur)
                        
                        dailyPivotCur = (close + highDailyCur + lowDailyCur) / 3
                        
                        if dailyPivot != None and dailyPivot != -1:
                          dr1 = (2*dailyPivot) - lowDaily
                          ds1 = (2*dailyPivot) - highDaily
                          dr2 = (dailyPivot) + (highDaily - lowDaily)
                          ds2 = (dailyPivot) - (highDaily - lowDaily)
                          dr3 = (dr1) + (highDaily - lowDaily)
                          ds3 = (ds1) - (highDaily - lowDaily)
                          dr4 = (dr3) + (dr2 - dr1)
                          ds4 = (ds3) - (ds1 - ds2)
                          dr5 = (dr4) + (dr3 - dr2)
                          ds5 = (ds4) - (ds2 - ds3)
                        else:
                          dr1 = -1
                          ds1 = -1
                          dr2 = -1
                          ds2 = -1
                          dr3 = -1
                          ds3 = -1
                          dr4 = -1
                          ds4 = -1
                          dr5 = -1
                          ds5 = -1
                          dailyPivot = -1
                          lowDaily = -1
                          highDaily = -1
                        
                        df.at[n, 'dpivot'] = dailyPivot
                        df.at[n, 'dr1'] = dr1
                        df.at[n, 'ds1'] = ds1
                        df.at[n, 'dr2'] = dr2
                        df.at[n, 'ds2'] = ds2
                        df.at[n, 'dr3'] = dr3
                        df.at[n, 'ds3'] = ds3
                        df.at[n, 'dr4'] = dr4
                        df.at[n, 'ds4'] = ds4
                        df.at[n, 'dr5'] = dr5
                        df.at[n, 'ds5'] = ds5
                        
                        # Weekly
                        if curWeek != prevWeek:
                          lowWeekly = lowWeeklyCur
                          highWeekly = highWeeklyCur
                          weeklyPivot = weeklyPivotCur
                          
                          lowWeeklyCur = low
                          highWeeklyCur = high
                        else:
                          lowWeeklyCur = min(low, lowWeeklyCur)
                          highWeeklyCur = max(high, highWeeklyCur)
                          
                        weeklyPivotCur = (close + highWeeklyCur + lowWeeklyCur) / 3
                        
                        if weeklyPivot != None and weeklyPivot != -1:
                          wr1 = (2*weeklyPivot) - lowWeekly
                          ws1 = (2*weeklyPivot) - highWeekly
                          wr2 = (weeklyPivot) + (highWeekly - lowWeekly)
                          ws2 = (weeklyPivot) - (highWeekly - lowWeekly)
                          wr3 = (wr1) + (highWeekly - lowWeekly)
                          ws3 = (ws1) - (highWeekly - lowWeekly)
                          wr4 = (wr3) + (wr2 - wr1)
                          ws4 = (ws3) - (ws1 - ws2)
                          wr5 = (wr4) + (wr3 - wr2)
                          ws5 = (ws4) - (ws2 - ws3)
                        else:
                          wr1 = -1
                          ws1 = -1
                          wr2 = -1
                          ws2 = -1
                          wr3 = -1
                          ws3 = -1
                          wr4 = -1
                          ws4 = -1
                          wr5 = -1
                          ws5 = -1
                          weeklyPivot = -1
                          lowWeekly = -1
                          highWeekly = -1
                        
                        df.at[n, 'wpivot'] = weeklyPivot
                        df.at[n, 'wr1'] = wr1
                        df.at[n, 'ws1'] = ws1
                        df.at[n, 'wr2'] = wr2
                        df.at[n, 'ws2'] = ws2
                        df.at[n, 'wr3'] = wr3
                        df.at[n, 'ws3'] = ws3
                        df.at[n, 'wr4'] = wr4
                        df.at[n, 'ws4'] = ws4
                        df.at[n, 'wr5'] = wr5
                        df.at[n, 'ws5'] = ws5
                            
                        # Monthly
                        if curMonth != prevMonth:
                          lowMonthly = lowMonthlyCur
                          highMonthly = highMonthlyCur
                          monthlyPivot = monthlyPivotCur
                          
                          lowMonthlyCur = low
                          highMonthlyCur = high
                        else:
                          lowMonthlyCur = min(low, lowMonthlyCur)
                          highMonthlyCur = max(high, highMonthlyCur)
                        
                        monthlyPivotCur = (close + highMonthlyCur + lowMonthlyCur) / 3
                        
                        if monthlyPivot != None and monthlyPivot != -1:
                          mr1 = (2*monthlyPivot) - lowMonthly
                          ms1 = (2*monthlyPivot) - highMonthly
                          mr2 = (monthlyPivot) + (highMonthly - lowMonthly)
                          ms2 = (monthlyPivot) - (highMonthly - lowMonthly)
                          mr3 = (mr1) + (highMonthly - lowMonthly)
                          ms3 = (ms1) - (highMonthly - lowMonthly)
                          mr4 = (mr3) + (mr2 - mr1)
                          ms4 = (ms3) - (ms1 - ms2)
                          mr5 = (mr4) + (mr3 - mr2)
                          ms5 = (ms4) - (ms2 - ms3)    
                        else:
                          mr1 = -1
                          ms1 = -1
                          mr2 = -1
                          ms2 = -1
                          mr3 = -1
                          ms3 = -1
                          mr4 = -1
                          ms4 = -1
                          mr5 = -1
                          ms5 = -1  
                          monthlyPivot = -1
                          lowMonthly = -1
                          highMonthly = -1
                        
                        df.at[n, 'mpivot'] = monthlyPivot
                        df.at[n, 'mr1'] = mr1
                        df.at[n, 'ms1'] = ms1
                        df.at[n, 'mr2'] = mr2 
                        df.at[n, 'ms2'] = ms2 
                        df.at[n, 'mr3'] = mr3
                        df.at[n, 'ms3'] = ms3
                        df.at[n, 'mr4'] = mr4 
                        df.at[n, 'ms4'] = ms4 
                        df.at[n, 'mr5'] = mr5 
                        df.at[n, 'ms5'] = ms5  
                        
                        # 7. process variable
                        df.at[n, "fharray"] = str(FhArray)
                        df.at[n, "flarray"] = str(FlArray)
                        df.at[n, "sharray"] = str(ShArray)
                        df.at[n, "slarray"] = str(SlArray)
                        df.at[n, "need_break_fractal_up"] = 1 if need_break_fractal_up else 0
                        df.at[n, "anchorarray"] = str(anchorArray)
                        df.at[n, "anchor1starray"] = str(anchor1stArray)
                        df.at[n, "anchorcntrarray"] = str(anchorCntrArray)
                        df.at[n, "high1starray"] = str(high1stArray)
                        df.at[n, "low1starray"] = str(low1stArray)
                        df.at[n, "lowdailycur"] = lowDailyCur
                        df.at[n, "highdailycur"] = highDailyCur
                        df.at[n, "lowweeklycur"] = lowWeeklyCur
                        df.at[n, "highweeklycur"] = highWeeklyCur
                        df.at[n, "lowmonthlycur"] = lowMonthlyCur
                        df.at[n, "highmonthlycur"] = highMonthlyCur
                        df.at[n, "lowdaily"] = lowDaily
                        df.at[n, "highdaily"] = highDaily
                        df.at[n, "lowweekly"] = lowWeekly
                        df.at[n, "highweekly"] = highWeekly
                        df.at[n, "lowmonthly"] = lowMonthly
                        df.at[n, "highmonthly"] = highMonthly
                        df.at[n, "dpivotcur"] = dailyPivotCur
                        df.at[n, "wpivotcur"] = weeklyPivotCur
                        df.at[n, "mpivotcur"] = monthlyPivotCur
                        df.at[n, "direction"] = direction
                        
                        # variable memory management
                        FhArray = FhArray[:100]
                        FlArray = FlArray[:100]
                        ShArray = ShArray[:100]
                        SlArray = SlArray[:100]  
                        n = n + 1
                        # END OF ROW LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
                        
                        # Output Management ===============================================
                        if 'token' in df.columns:
                            df_valid = df.dropna(subset=['token', 'symbol', 'open', 'high', 'low', 'close', 'volume'])
                            
                            # Process numeric columns
                            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'atr', 'atr_trail_stop_loss', 
                                           'dc_upper', 'dc_lower', 'dc_mid', 'fh_price', 'fl_price', 'sh_price', 'sl_price',
                                           'dpivot', 'ds1', 'ds2', 'ds3', 'ds4', 'ds5', 'dr1', 'dr2', 'dr3', 'dr4', 'dr5',
                                           'wpivot', 'ws1', 'ws2', 'ws3', 'ws4', 'ws5', 'wr1', 'wr2', 'wr3', 'wr4', 'wr5',
                                           'mpivot', 'ms1', 'ms2', 'ms3', 'ms4', 'ms5', 'mr1', 'mr2', 'mr3', 'mr4', 'mr5',
                                           'lowdailycur', 'highdailycur', 'lowweeklycur', 'highweeklycur',
                                           'lowmonthlycur', 'highmonthlycur', 'lowdaily', 'highdaily',
                                           'lowweekly', 'highweekly', 'lowmonthly', 'highmonthly',
                                           'dpivotcur', 'wpivotcur', 'mpivotcur']
                            for col in numeric_cols:
                                if col in df_valid.columns:
                                    # Convert empty strings to NaN first
                                    df_valid[col] = df_valid[col].replace('', np.nan)
                                    df_valid[col] = pd.to_numeric(df_valid[col], errors='coerce')
                            
                            int_cols = ['lowestfrom1stlow', 'highestfrom1sthigh', 'fl_dbg', 'fh_dbg', 'n', 'n_lookback']
                            for col in int_cols:
                                if col in df_valid.columns:
                                    # Convert empty strings to NaN first
                                    df_valid[col] = df_valid[col].replace('', np.nan)
                                    df_valid[col] = pd.to_numeric(df_valid[col], errors='coerce')
                                    # Convert to integer, but handle NaN values
                                    df_valid[col] = df_valid[col].astype('Int64')  # pandas nullable integer type
                            
                            df_valid['token'] = df_valid['token'].astype('int64')
                            
                            bool_cols = ['fh_status', 'fl_status', 'sh_status', 'sl_status', 'need_break_fractal_up', 'direction']
                            for col in bool_cols:
                                if col in df_valid.columns:
                                    df_valid[col] = df_valid[col].astype(bool)
                            
                            # Define the desired order of columns (all names in lowercase as created by PostgreSQL)
                            desired_columns = [
                                "created", "token", "symbol", "open", "close", "high", "low", "volume", "atr", "atr_trail_stop_loss",
                                "dc_upper", "dc_lower", "dc_mid", "fh_price", "fl_price", "fh_status", "fl_status", "sh_price", "sl_price",
                                "sh_status", "sl_status", "lowestfrom1stlow", "highestfrom1sthigh", "fl_dbg", "fh_dbg", "dpivot", "ds1",
                                "ds2", "ds3", "ds4", "ds5", "dr1", "dr2", "dr3", "dr4", "dr5", "wpivot", "ws1", "ws2", "ws3", "ws4",
                                "ws5", "wr1", "wr2", "wr3", "wr4", "wr5", "mpivot", "ms1", "ms2", "ms3", "ms4", "ms5", "mr1", "mr2",
                                "mr3", "mr4", "mr5", "n", "n_lookback", "fharray", "flarray", "sharray", "slarray", "need_break_fractal_up",
                                "anchorarray", "anchor1starray", "anchorcntrarray", "high1starray", "low1starray", "lowdailycur",
                                "highdailycur", "lowweeklycur", "highweeklycur", "lowmonthlycur", "highmonthlycur", "lowdaily",
                                "highdaily", "lowweekly", "highweekly", "lowmonthly", "highmonthly", "dpivotcur", "wpivotcur", "mpivotcur",
                                "direction"
                            ]
                            
                            # Create a new DataFrame with only the columns that exist in df_valid
                            # and in the correct order
                            ordered_columns = [col for col in desired_columns if col in df_valid.columns.str.lower()]
                            df_valid.columns = df_valid.columns.str.lower()
                            df_valid = df_valid[ordered_columns]
                            
                            # Ensure created is a proper timestamp
                            if 'created' in df_valid.columns:
                                df_valid['created'] = pd.to_datetime(df_valid['created'], errors='coerce')
                                # Drop rows with invalid timestamps
                                df_valid = df_valid.dropna(subset=['created'])
                            
                            # CSV output logic from original code
                            if len(df_valid) <= 1000:
                                if token_index == 0:
                                    df_valid.iloc[:500].to_csv('output_data_stock.csv', mode='w', header=True, index=False)
                                else:
                                    df_valid.iloc[:500].to_csv('output_data_stock.csv', mode='a', header=False, index=False)
                            else:
                                df_valid.iloc[500:1500].to_csv('output_data_stock.csv', mode='a', header=False, index=False)
                        else:
                            logger.warning(f"No token column found in dataframe for token_index {token_index}")
                            continue
                        
                        # Output Management End ===============================================
                            
                    # END OF CHUNK LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
                    if len(df_valid) <= 1000:
                      # Make sure we output all remaining rows
                      df_valid.iloc[500:].to_csv('output_data_stock.csv', mode='a', header=False, index=False)
                    else:
                      # Make sure we output all remaining rows
                      df_valid.iloc[1500:].to_csv('output_data_stock.csv', mode='a', header=False, index=False)
                    # Use for all? enable when debugging
                    # break
                    # END OF TOKEN LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

                # Bulk CSV to SQL
                # Create named parameters for the INSERT query
                columns = [
                    "token", "symbol", "open", "close", "high", "low", "volume", "created",
                    "atr", "atr_trail_stop_loss", "dc_upper", "dc_lower", "dc_mid", "fh_price",
                    "fl_price", "fh_status", "fl_status", "sh_price", "sl_price", "sh_status",
                    "sl_status", "lowestfrom1stlow", "highestfrom1sthigh", "fl_dbg", "fh_dbg",
                    "dpivot", "ds1", "ds2", "ds3", "ds4", "ds5", "dr1", "dr2", "dr3", "dr4",
                    "dr5", "wpivot", "ws1", "ws2", "ws3", "ws4", "ws5", "wr1", "wr2", "wr3",
                    "wr4", "wr5", "mpivot", "ms1", "ms2", "ms3", "ms4", "ms5", "mr1", "mr2",
                    "mr3", "mr4", "mr5", "n", "n_lookback", "fharray", "flarray", "sharray",
                    "slarray", "need_break_fractal_up", "anchorarray", "anchor1starray",
                    "anchorcntrarray", "high1starray", "low1starray", "lowdailycur",
                    "highdailycur", "lowweeklycur", "highweeklycur", "lowmonthlycur",
                    "highmonthlycur", "lowdaily", "highdaily", "lowweekly", "highweekly",
                    "lowmonthly", "highmonthly", "dpivotcur", "wpivotcur", "mpivotcur",
                    "direction"
                ]
                placeholders = ", ".join([f":{col}" for col in columns])
                
                query = f"""
                    INSERT INTO {output_table} ({', '.join(columns)}) 
                    VALUES ({placeholders})
                    ON CONFLICT (created, token, n) 
                    DO UPDATE SET 
                    {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['created', 'token', 'n']])}
                """
                
                data = []
                with open('output_data_stock.csv', newline='') as csvfile:
                    # Define the proper column names based on your schema
                    # This ensures we don't rely on the first row of the CSV as headers
                    fieldnames = [
                        "created","token", "symbol", "open", "close", "high", "low", "volume",
                        "atr", "atr_trail_stop_loss", "dc_upper", "dc_lower", "dc_mid", "fh_price",
                        "fl_price", "fh_status", "fl_status", "sh_price", "sl_price", "sh_status",
                        "sl_status", "lowestfrom1stlow", "highestfrom1sthigh", "fl_dbg", "fh_dbg",
                        "dpivot", "ds1", "ds2", "ds3", "ds4", "ds5", "dr1", "dr2", "dr3", "dr4",
                        "dr5", "wpivot", "ws1", "ws2", "ws3", "ws4", "ws5", "wr1", "wr2", "wr3",
                        "wr4", "wr5", "mpivot", "ms1", "ms2", "ms3", "ms4", "ms5", "mr1", "mr2",
                        "mr3", "mr4", "mr5", "n", "n_lookback", "fharray", "flarray", "sharray",
                        "slarray", "need_break_fractal_up", "anchorarray", "anchor1starray",
                        "anchorcntrarray", "high1starray", "low1starray", "lowdailycur",
                        "highdailycur", "lowweeklycur", "highweeklycur", "lowmonthlycur",
                        "highmonthlycur", "lowdaily", "highdaily", "lowweekly", "highweekly",
                        "lowmonthly", "highmonthly", "dpivotcur", "wpivotcur", "mpivotcur",
                        "direction"
                    ]
                    
                    valid_rows = 0
                    skipped_rows = 0
                    
                    # Function to process a single row to avoid code duplication
                    def process_row(row, data, skipped_rows, valid_rows):
                        try:
                            # Validate and convert the created field
                            created_val = row.get('created')
                            if created_val is None or str(created_val).strip() == "" or str(created_val).lower() in ["nan", "none"]:
                                # Skip the row due to invalid created value
                                logger.warning(f"Skipping row due to invalid created value: {created_val}")
                                skipped_rows += 1
                                return skipped_rows, valid_rows
                            else:
                                # Try converting to datetime
                                try:
                                    row['created'] = pd.to_datetime(created_val)
                                except Exception as e:
                                    logger.warning(f"Error converting created value: {created_val} - {str(e)}")
                                    skipped_rows += 1
                                    return skipped_rows, valid_rows
                            
                            # More lenient token validation
                            token_value = str(row.get('token')).strip()
                            if token_value and token_value.isdigit():
                                row['token'] = int(token_value)
                            else:
                                skipped_rows += 1
                                logger.warning(f"Invalid token format: {token_value}")
                                return skipped_rows, valid_rows

                            # Validate n value - skip rows with None as n value
                            n_value = row.get('n')
                            if n_value is None or str(n_value).strip() == "" or str(n_value).lower() == "nan" or str(n_value).lower() == "none":
                                skipped_rows += 1
                                logger.warning(f"Skipping row with NULL n value for token: {row.get('token')}")
                                return skipped_rows, valid_rows

                            # Define all numeric fields based on schema
                            float_fields = [
                                'open', 'high', 'low', 'close', 'volume',
                                'atr', 'atr_trail_stop_loss', 'dc_upper', 'dc_lower', 'dc_mid',
                                'fh_price', 'fl_price', 'sh_price', 'sl_price',
                                'dpivot', 'ds1', 'ds2', 'ds3', 'ds4', 'ds5',
                                'dr1', 'dr2', 'dr3', 'dr4', 'dr5',
                                'wpivot', 'ws1', 'ws2', 'ws3', 'ws4', 'ws5',
                                'wr1', 'wr2', 'wr3', 'wr4', 'wr5',
                                'mpivot', 'ms1', 'ms2', 'ms3', 'ms4', 'ms5',
                                'mr1', 'mr2', 'mr3', 'mr4', 'mr5',
                                'lowdailycur', 'highdailycur', 'lowweeklycur', 'highweeklycur',
                                'lowmonthlycur', 'highmonthlycur', 'lowdaily', 'highdaily',
                                'lowweekly', 'highweekly', 'lowmonthly', 'highmonthly',
                                'dpivotcur', 'wpivotcur', 'mpivotcur'
                            ]
                            
                            int_fields = [
                                'lowestfrom1stlow', 'highestfrom1sthigh', 'fl_dbg', 'fh_dbg',
                                'n', 'n_lookback'
                            ]
                            
                            # Process float fields
                            for field in float_fields:
                                if field in row:
                                    try:
                                        value = str(row[field]).strip()
                                        if value == "" or value.lower() == "nan" or value.lower() == "none":
                                            row[field] = None
                                        else:
                                            row[field] = float(value)
                                    except (ValueError, TypeError):
                                        row[field] = None
                                        
                            # Process integer fields
                            for field in int_fields:
                                if field in row and row[field] is not None:
                                    try:
                                        value = str(row[field]).strip()
                                        if value == "" or value.lower() == "nan" or value.lower() == "none":
                                            row[field] = None
                                        else:
                                            row[field] = int(float(value))  # Convert through float to handle decimal strings
                                    except (ValueError, TypeError):
                                        row[field] = None
                                elif field in row:
                                    row[field] = None

                            # Handle boolean fields
                            bool_fields = ['fh_status', 'fl_status', 'sh_status', 'sl_status', 'need_break_fractal_up', 'direction']
                            for field in bool_fields:
                                if field in row and row[field] is not None:
                                    try:
                                        value = str(row[field]).strip()
                                        if value == "" or value.lower() == "nan" or value.lower() == "none":
                                            row[field] = False
                                        else:
                                            row[field] = bool(int(float(value)))  # Convert through float to handle decimal strings
                                    except (ValueError, TypeError):
                                        row[field] = False
                                elif field in row:
                                    row[field] = False

                            # Handle array fields (ensure they're never empty strings)
                            array_fields = ['fharray', 'flarray', 'sharray', 'slarray', 
                                           'anchorarray', 'anchor1starray', 'anchorcntrarray', 
                                           'high1starray', 'low1starray']
                            for field in array_fields:
                                if field in row and (row[field] is None or str(row[field]).strip() == ""):
                                    row[field] = "[]"  # Empty array as string

                            # Build row_dict with all required columns
                            row_dict = {}
                            for col in columns:
                                row_dict[col] = row.get(col)

                            data.append(row_dict)
                            valid_rows += 1
                            return skipped_rows, valid_rows

                        except Exception as e:
                            skipped_rows += 1
                            logger.warning(f"Error processing row: {str(e)}")
                            return skipped_rows, valid_rows
                    
                    reader = csv.DictReader(csvfile, fieldnames=fieldnames)
                    
                    # Skip header if it exists
                    header = next(reader, None)
                    if header:
                        # Check if this is actually a header row
                        if not any(str(val).isdigit() for val in header.values()):
                            logger.info("Skipping CSV header row")
                        else:
                            # Process first row if it contains data
                            skipped_rows, valid_rows = process_row(header, data, skipped_rows, valid_rows)
                    
                    for row in reader:
                        if not row or not any(row.values()):  # Skip empty rows
                            continue
                        skipped_rows, valid_rows = process_row(row, data, skipped_rows, valid_rows)

                    logger.info(f"CSV processing summary: {valid_rows} valid rows processed, {skipped_rows} rows skipped")
                    
                    if len(data) == 0:
                        logger.warning("No valid data found in CSV, skipping insert")
                        continue  # Skip to next token
                
                with engine.connect() as conn:
                    # Process each row in a separate transaction to avoid aborting all on error
                    for row in data:
                        try:
                            with conn.begin():
                                # Log the query parameters for debugging
                                logger.debug(f"Executing SQL with parameters for token: {row.get('token')}, n: {row.get('n')}")
                                conn.execute(text(query), row)
                                logger.debug(f"Successfully inserted/updated row for token: {row.get('token')}, n: {row.get('n')}")
                        except Exception as e:
                            logger.error(f"Error executing SQL: {str(e)}")
                            logger.error(f"Row data: {row}")
                            # Continue with next row
                    # Transaction will be automatically rolled back
                
                os.remove("output_data_stock.csv")
                enddate = datetime.now()
                with engine.connect() as conn:
                    # Use proper parameter binding for PostgreSQL and the correct column name 'end_time'
                    insert_query = text('INSERT INTO tbl_market_logtime (start, end_time, type) VALUES (:start, :end_time, :type)')
                    conn.execute(insert_query, {"start": str(startdate), "end_time": str(enddate), "type": "15min update"})
                    conn.commit()
        return str(startdate)

    except Exception as e:
        logger.error(f"Error in UpdateProcess: {str(e)}")
        return {"error": str(e)}, 500
    
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=5001, threaded=True)
    
    # with open('dbconfig/db_config.json', 'r') as json_file:
    #   db_params = json.load(json_file)
    
    # with open("config/config.json", 'r') as json_file:
    #   config = json.load(json_file)

    # uri = "mysql://{}:{}@{}/{}".format(
    #         db_params["user"], 
    #         db_params["pass"], 
    #         db_params["host"], 
    #         db_params["db"]
    #       )
    # # Make sure to reinit the process if you have database with different format
    # InitProcess(uri, config)
    
    # # Update function call, should be on loop to make it live
    # UpdateProcess(uri, config)
