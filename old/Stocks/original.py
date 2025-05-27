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
app = Flask(__name__)

@app.route('/')
def InitProcess():
  with open('dbconfig/db_config.json', 'r') as json_file:
    db_params = json.load(json_file)
 
  with open("config/config.json", 'r') as json_file:
    config = json.load(json_file)

  uri = "mysql://{}:{}@{}/{}".format(
        db_params["user"], 
        urlquote(db_params["pass"]), 
        db_params["host"], 
        db_params["db"]
        )
  input_table = 'tbl_ohlc_fifteen_input'
  output_table = 'tbl_ohlc_fifteen_output'
  engine = create_engine(uri)
  conn = engine.connect().execution_options(stream_results=True)
  tokens = pd.read_sql("SELECT DISTINCT token FROM {} where symbol not like '%fut%' and token != 0".format(input_table), conn);
  
  print("Total pair:", len(tokens))
    
  # TOKEN LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
  for token_index, token_row in tqdm(tokens.iterrows(), total = len(tokens)):
    
    # Use this line to limit token/pair
    # if token_index >= 1:
    #   continue
    
    # create output buffer
    df = pd.DataFrame()
    
    # variables =============================================================================================================================================

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
    # end of variables =============================================================================================================================================

    
    # CHUNK LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
    query = "SELECT * FROM {} where symbol not like '%fut%' and token = {}".format(input_table, token_row.token)
    for single_pair_chunk in pd.read_sql(query, conn, chunksize=1000):
      
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
        df["FhArray"] = None
        df["FlArray"] = None
        df["ShArray"] = None
        df["SlArray"] = None
        df["need_break_fractal_up"] = None
        df["anchorArray"] = None
        df["anchor1stArray"] = None
        df["anchorCntrArray"] = None
        df["high1stArray"] = None
        df["low1stArray"] = None
        df["lowDailyCur"] = None
        df["highDailyCur"] = None
        df["lowWeeklyCur"] = None
        df["highWeeklyCur"] = None
        df["lowMonthlyCur"] = None
        df["highMonthlyCur"] = None
        df["lowDaily"] = None
        df["highDaily"] = None
        df["lowWeekly"] = None
        df["highWeekly"] = None
        df["lowMonthly"] = None
        df["highMonthly"] = None
        df["dpivotCur"] = None
        df["wpivotCur"] = None
        df["mpivotCur"] = None
        df["direction"] = None
        
        
        startIndex = 0
        
      # 2 # concat new chunk
      elif(len(df) < 2000):
        df = pd.concat((df, single_pair_chunk), axis=0).reset_index(drop=True)
        startIndex = 1000 
        df.index = df.index + n - startIndex
        
      # N # delete prev chunk, concat new chunk
      else:
        df = df.iloc[1000:]
        df =  pd.concat((df, single_pair_chunk), axis=0).reset_index(drop=True)
        startIndex = 1000
        df.index = df.index + n - startIndex
              
      # calculate atr, dc =============================================================================================================================================
      df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=config["atr_trail_sl"]["atr_length"])
      df_donchian = ta.donchian(df["high"], df["low"], config["dc"]["dc_length"], config["dc"]["dc_length"])      
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
        if df.at[n, "atr"] == None or math.isnan(df.at[n, "atr"]) :
          df.at[n, "atr"] = -1
          df.at[n, "atr_trail_stop_loss"] = -1
        df.at[n, "dc_upper"] = -1
        df.at[n, "dc_lower"] = -1
        df.at[n, "dc_mid"] = -1
        df.at[n, "fl_dbg"] = -1
        df.at[n, "fh_dbg"] = -1
        
        # 1. calculate atr trail stop loss ===============================================
        atrMultiplier = config["atr_trail_sl"]["atr_multiplier"] # input
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
        lowestfrom1stlow = int(minList1StN - n)
        df.at[n, "lowestfrom1stlow"] = lowestfrom1stlow
        
        maxList1St = df[ (df.n >= high1stArray[0]) & (df.n <= n)].high.max()
        maxList1StN = df[ (df.n >= high1stArray[0]) & (df.n <= n) & (df.high == maxList1St)].head(1).n
        highestfrom1sthigh = int(maxList1StN - n)
        df.at[n, "highestfrom1sthigh"] = highestfrom1sthigh
        
        if direction == 1:
          
          for i in range(len(anchorArray)):
            
            anchorBarsBack = max(int(df.head(1).n), anchorArray[i])
            anchor1stBarsBack = max(int(df.head(1).n), anchor1stArray[i])
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
            
            anchorBarsBack = max(int(df.head(1).n), anchorArray[i])
            anchor1stBarsBack = max(int(df.head(1).n), anchor1stArray[i])
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
            lastFH = max(int(df.head(1).n), FhArray[0])
            if high > df.at[lastFH, "high"]:
                FhArray[0] = n
                df.at[ lastFH, "fh_status" ] = 0
                df.at[ n, "fh_status" ] = 1
        elif direction == -1:
            lastFL = max(int(df.head(1).n), FlArray[0])
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
        minListShN = int(df[ (df.n >= ShArray[0]) & (df.n <= n) & (df.low == minListSh)].head(1).n)
        
        maxListSl = df[ (df.n >= SlArray[0]) & (df.n <= n)].high.max()
        maxListSlN = int(df[ (df.n >= SlArray[0]) & (df.n <= n) & (df.high == maxListSl)].head(1).n)
        
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
          if not math.isnan(df_donchian.at[index, "DCU_"+ str(config["dc"]["dc_length"]) + "_" + str(config["dc"]["dc_length"])]):
            df.at[n, "dc_upper"] = df_donchian.at[index, "DCU_"+ str(config["dc"]["dc_length"]) + "_" + str(config["dc"]["dc_length"])]
            df.at[n, "dc_lower"] = df_donchian.at[index, "DCU_"+ str(config["dc"]["dc_length"]) + "_" + str(config["dc"]["dc_length"])]
            df.at[n, "dc_mid"] = df_donchian.at[index, "DCU_"+ str(config["dc"]["dc_length"]) + "_" + str(config["dc"]["dc_length"])]
            df.at[n, "n_lookback"] = int(max(0, np.nanmin([df.at[n, "n_lookback"], n-(config["dc"]["dc_length"]+1)])))
          
        # 5. Swing DC ===============================================
        else:
          df.at[n, "dc_upper"] = df[ (df.n >= (ShArray[config["dc"]["dc_length"]-1] if len(ShArray) >= config["dc"]["dc_length"] else 0)) & (df.n <= n)].high.max()
          df.at[n, "dc_lower"] = df[ (df.n >= (SlArray[config["dc"]["dc_length"]-1] if len(SlArray) >= config["dc"]["dc_length"] else 0)) & (df.n <= n)].low.min()
          df.at[n, "dc_mid"] = (df.at[n, "dc_upper"] + df.at[n, "dc_lower"])/2
          df.at[n, "n_lookback"] = int(max(0, np.nanmin([df.at[n, "n_lookback"], ShArray[config["dc"]["dc_length"]-1] if len(ShArray) >= config["dc"]["dc_length"] else 0])))
          df.at[n, "n_lookback"] = int(max(0, np.nanmin([df.at[n, "n_lookback"], SlArray[config["dc"]["dc_length"]-1] if len(SlArray) >= config["dc"]["dc_length"] else 0])))

        # 6. Pivot ===============================================
        
        curDate = df.at[n, "created"].isocalendar()
        prevDate = df.at[n-1, "created"].isocalendar() if len(df[df.n == n-1]) == 1 else None        

        curWeek = df.at[n, "created"].week
        prevWeek = df.at[n-1, "created"].week if len(df[df.n == n-1]) == 1 else None
        
        curMonth = df.at[n, "created"].month_name()
        prevMonth = df.at[n-1, "created"].month_name() if len(df[df.n == n-1]) == 1 else None
        
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
        df.at[n, "FhArray"] = FhArray[:]
        df.at[n, "FlArray"] = FlArray[:]
        df.at[n, "ShArray"] = ShArray[:]
        df.at[n, "SlArray"] = SlArray[:]
        df.at[n, "need_break_fractal_up"] = 1 if need_break_fractal_up else 0
        df.at[n, "anchorArray"] = anchorArray[:]
        df.at[n, "anchor1stArray"] = anchor1stArray[:]
        df.at[n, "anchorCntrArray"] = anchorCntrArray[:]
        df.at[n, "high1stArray"] = high1stArray[:]
        df.at[n, "low1stArray"] = low1stArray[:]
        df.at[n, "lowDailyCur"] = lowDailyCur
        df.at[n, "highDailyCur"] = highDailyCur
        df.at[n, "lowWeeklyCur"] = lowWeeklyCur
        df.at[n, "highWeeklyCur"] = highWeeklyCur
        df.at[n, "lowMonthlyCur"] = lowMonthlyCur
        df.at[n, "highMonthlyCur"] = highMonthlyCur
        df.at[n, "lowDaily"] = lowDaily
        df.at[n, "highDaily"] = highDaily
        df.at[n, "lowWeekly"] = lowWeekly
        df.at[n, "highWeekly"] = highWeekly
        df.at[n, "lowMonthly"] = lowMonthly
        df.at[n, "highMonthly"] = highMonthly
        df.at[n, "dpivotCur"] = dailyPivotCur
        df.at[n, "wpivotCur"] = weeklyPivotCur
        df.at[n, "mpivotCur"] = monthlyPivotCur
        df.at[n, "direction"] = direction
        
        # variable memory management
        FhArray = FhArray[:100]
        FlArray = FlArray[:100]
        ShArray = ShArray[:100]
        SlArray = SlArray[:100]  
        n = n + 1
      # END OF ROW LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
      
      # Output Management ===============================================
      if(len(df) <= 1000) and token_index == 0:
        df.iloc[:500].to_csv('output_data_stock.csv',mode='w', header=True, index=False)
        
      # N # append new chunk to csv
      elif(len(df) <= 1000):
        df.iloc[:500].to_csv('output_data_stock.csv',mode='a', header=False, index=False)
      
      else:
        df.iloc[500:1500].to_csv('output_data_stock.csv', mode='a', header=False, index=False)
      
      # Output Management End ===============================================
        
    # END OF CHUNK LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
    if len(df) <= 1000:
      df.iloc[500:].to_csv('output_data_stock.csv', mode='a', header=False, index=False)
    else:
      df.iloc[1500:].to_csv('output_data_stock.csv', mode='a', header=False, index=False)
    # Use for all? enable when debugging
    # break
  # END OF TOKEN LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

  # Bulk CSV to SQL
  engine.execute("DROP TABLE IF EXISTS %s" % output_table)
  engine.execute("""
      CREATE TABLE %s(
          id INT,
          token INT,
          symbol  VARCHAR(500) NULL,
          open DOUBLE,
          close DOUBLE,
          high DOUBLE,
          low DOUBLE,
          volume DOUBLE,
          created DATETIME,
          atr DOUBLE NULL,
          atr_trail_stop_loss DOUBLE NULL,
          dc_upper DOUBLE NULL,
          dc_lower DOUBLE NULL,
          dc_mid DOUBLE NULL,
          fh_price DOUBLE,
          fl_price DOUBLE,
          fh_status BOOLEAN,
          fl_status BOOLEAN,
          sh_price DOUBLE,
          sl_price DOUBLE,
          sh_status BOOLEAN,
          sl_status BOOLEAN,
          lowestfrom1stlow INT,
          highestfrom1sthigh INT,
          fl_dbg INT,
          fh_dbg INT,
          dpivot DOUBLE,
          ds1 DOUBLE,
          ds2 DOUBLE,
          ds3 DOUBLE,
          ds4 DOUBLE,
          ds5 DOUBLE,
          dr1 DOUBLE,
          dr2 DOUBLE,
          dr3 DOUBLE,
          dr4 DOUBLE,
          dr5 DOUBLE,
          wpivot DOUBLE,
          ws1 DOUBLE,
          ws2 DOUBLE,
          ws3 DOUBLE,
          ws4 DOUBLE,
          ws5 DOUBLE,
          wr1 DOUBLE,
          wr2 DOUBLE,
          wr3 DOUBLE,
          wr4 DOUBLE,
          wr5 DOUBLE,
          mpivot DOUBLE,
          ms1 DOUBLE,
          ms2 DOUBLE,
          ms3 DOUBLE,
          ms4 DOUBLE,
          ms5 DOUBLE,
          mr1 DOUBLE,
          mr2 DOUBLE,
          mr3 DOUBLE,
          mr4 DOUBLE,
          mr5 DOUBLE,
          n INT,
          n_lookback INT,
          FhArray TEXT,
          FlArray TEXT,
          ShArray TEXT,
          SlArray TEXT,
          need_break_fractal_up BOOL,
          anchorArray TEXT,
          anchor1stArray TEXT,
          anchorCntrArray TEXT,
          high1stArray TEXT,
          low1stArray TEXT,
          lowDailyCur DOUBLE,
          highDailyCur DOUBLE,
          lowWeeklyCur DOUBLE,
          highWeeklyCur DOUBLE,
          lowMonthlyCur DOUBLE,
          highMonthlyCur DOUBLE,
          lowDaily DOUBLE,
          highDaily DOUBLE,
          lowWeekly DOUBLE,
          highWeekly DOUBLE,
          lowMonthly DOUBLE,
          highMonthly DOUBLE,
          dpivotCur DOUBLE,
          wpivotCur DOUBLE,
          mpivotCur DOUBLE,
          direction BOOL,
          PRIMARY KEY (id)
      );
  """ % output_table)
  
  query = """INSERT INTO {} 
          VALUES
          (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
          )"""
  query = query.format(output_table)
  
  with open('output_data_stock.csv') as file:
    reader = csv.reader(file)
    next(reader)  # Skip first line (headers)
    data = list(reader)
  engine.execute(query, data)
  os.remove("output_data_stock.csv")
  startdate = datetime.now()
  return str(startdate)

@app.route('/update')
def UpdateProcess():
  with open('dbconfig/db_config.json', 'r') as json_file:
    db_params = json.load(json_file)
 
  with open("config/config.json", 'r') as json_file:
    config = json.load(json_file)

  uri = "mysql://{}:{}@{}/{}".format(
        db_params["user"], 
        urlquote(db_params["pass"]), 
        db_params["host"], 
        db_params["db"]
        )
  input_table = 'tbl_ohlc_fifteen_input'
  output_table = 'tbl_ohlc_fifteen_output'
  engine = create_engine(uri)
  conn = engine.connect().execution_options(stream_results=True)
  startdate = datetime.now()
  tokens = pd.read_sql("SELECT DISTINCT token FROM {} where symbol not like '%fut%' and token != 0".format(input_table), conn);
  
  print("Total pair:", len(tokens))
    
  # TOKEN LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
  for token_index, token_row in tqdm(tokens.iterrows(), total = len(tokens)):
    
    # Use this line to limit token/pair
    # if token_index >= 1:
    #   continue
    
    # create output buffer
    df = pd.DataFrame()

    # CHECK LAST UPDATED ROW ON OTBL <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
    query = "select id, n, n_lookback from {otbl} where token={token} order by id desc LIMIT 1".format(
              otbl = output_table, 
              token = token_row.token
            )
    if len(pd.read_sql(query, conn).head(1).n_lookback) > 0:
      last_updated_n_lookback = int(pd.read_sql(query, conn).head(1).n_lookback)
      last_updated_id = int(pd.read_sql(query, conn).head(1).id)
      last_updated_n = int(pd.read_sql(query, conn).head(1).n)
      
      # GET N ROW NEEDED FROM OTBL <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
      query = "SELECT * FROM {otbl} WHERE token = {token} AND n >= {last_updated_n_lookback}".format(
                itbl = input_table, 
                otbl = output_table, 
                token = token_row.token,
                last_updated_id = last_updated_id,
                last_updated_n_lookback = last_updated_n_lookback
              )
      df = pd.read_sql(query, conn).iloc[:]
    else:
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
      FhArray = list(map(lambda x: int(x), list(df.tail(1).FhArray)[0][1:-1].split(", ")))
      FlArray = list(map(lambda x: int(x), list(df.tail(1).FlArray)[0][1:-1].split(", ")))    

      ShArray = list(map(lambda x: int(x), list(df.tail(1).ShArray)[0][1:-1].split(", ")))
      SlArray = list(map(lambda x: int(x), list(df.tail(1).SlArray)[0][1:-1].split(", ")))
      
      need_break_fractal_up = True if int(df.tail(1).need_break_fractal_up) == 1 else False

      anchorArray = list(map(lambda x: int(x), list(df.tail(1).anchorArray)  [0][1:-1].split(", ")))
      anchor1stArray = list(map(lambda x: int(x), list(df.tail(1).anchor1stArray)[0][1:-1].split(", ")))  
      anchorCntrArray = list(map(lambda x: int(x), list(df.tail(1).anchorCntrArray)[0][1:-1].split(", ")))  

      high1stArray = list(map(lambda x: int(x), list(df.tail(1).high1stArray)[0][1:-1].split(", ")))  
      low1stArray = list(map(lambda x: int(x), list(df.tail(1).low1stArray)[0][1:-1].split(", ")))  
      
      # Pivot variable
      lowDailyCur = float(df.tail(1).lowDailyCur)
      highDailyCur = float(df.tail(1).highDailyCur)
      lowWeeklyCur = float(df.tail(1).lowWeeklyCur)
      highWeeklyCur = float(df.tail(1).highWeeklyCur)
      lowMonthlyCur = float(df.tail(1).lowMonthlyCur)
      highMonthlyCur = float(df.tail(1).highMonthlyCur)
      lowDaily = float(df.tail(1).lowDaily)
      highDaily = float(df.tail(1).highDaily)
      lowWeekly = float(df.tail(1).lowWeekly)
      highWeekly = float(df.tail(1).highWeekly)
      lowMonthly = float(df.tail(1).lowMonthly)
      highMonthly = float(df.tail(1).highMonthly)
      dailyPivot = float(df.tail(1).dpivot)
      weeklyPivot = float(df.tail(1).wpivot)
      monthlyPivot = float(df.tail(1).mpivot)
      dailyPivotCur = float(df.tail(1).dpivotCur)
      weeklyPivotCur = float(df.tail(1).wpivotCur)
      monthlyPivotCur = float(df.tail(1).mpivotCur)
    
      n = int(df.tail(1).n) + 1
      direction = int(df.tail(1).direction)
    # end of variables =============================================================================================================================================

    
    # CHUNK LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
    query = "SELECT * FROM {} WHERE symbol not like '%fut%' and token = {} AND id > {}".format(input_table, token_row.token, last_updated_id)
    for single_pair_chunk in pd.read_sql(query, conn, chunksize=1000):
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
        df["FhArray"] = None
        df["FlArray"] = None
        df["ShArray"] = None
        df["SlArray"] = None
        df["need_break_fractal_up"] = None
        df["anchorArray"] = None
        df["anchor1stArray"] = None
        df["anchorCntrArray"] = None
        df["high1stArray"] = None
        df["low1stArray"] = None
        df["lowDailyCur"] = None
        df["highDailyCur"] = None
        df["lowWeeklyCur"] = None
        df["highWeeklyCur"] = None
        df["lowMonthlyCur"] = None
        df["highMonthlyCur"] = None
        df["lowDaily"] = None
        df["highDaily"] = None
        df["lowWeekly"] = None
        df["highWeekly"] = None
        df["lowMonthly"] = None
        df["highMonthly"] = None
        df["dpivotCur"] = None
        df["wpivotCur"] = None
        df["mpivotCur"] = None
        df["direction"] = None
        
        startIndex = 0
        
      # 2 # concat new chunk
      elif(len(df) < 2000):
        startIndex = len(df)
        df = pd.concat((df, single_pair_chunk), axis=0).reset_index(drop=True)
        df.index = df.index + int(df.head(1).n)
        
      # N # delete prev chunk, concat new chunk
      else:
        df = df.iloc[1000:]
        df =  pd.concat((df, single_pair_chunk), axis=0).reset_index(drop=True)
        startIndex = 1000
        df.index = df.index + n - startIndex
              
      # calculate atr, dc =============================================================================================================================================
      if startIndex==0:
        df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=config["atr_trail_sl"]["atr_length"])
      # df_atr = ta.atr(df["high"], df["low"], df["close"], length=config["atr_trail_sl"]["atr_length"])
      df_donchian = ta.donchian(df["high"], df["low"], config["dc"]["dc_length"], config["dc"]["dc_length"])  
      # df_donchian.index = df_donchian.index + n - startIndex 
      
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
        lowestfrom1stlow = int(minList1StN - n)
        df.at[n, "lowestfrom1stlow"] = lowestfrom1stlow
        
        maxList1St = df[ (df.n >= high1stArray[0]) & (df.n <= n)].high.max()
        maxList1StN = df[ (df.n >= high1stArray[0]) & (df.n <= n) & (df.high == maxList1St)].head(1).n
        highestfrom1sthigh = int(maxList1StN - n)
        df.at[n, "highestfrom1sthigh"] = highestfrom1sthigh
        
        if direction == 1:
          
          for i in range(len(anchorArray)):
            
            anchorBarsBack = max(int(df.head(1).n), anchorArray[i])
            anchor1stBarsBack = max(int(df.head(1).n), anchor1stArray[i])
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
            
            anchorBarsBack = max(int(df.head(1).n), anchorArray[i])
            anchor1stBarsBack = max(int(df.head(1).n), anchor1stArray[i])
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
            lastFH = max(int(df.head(1).n), FhArray[0])
            if high > df.at[lastFH, "high"]:
                FhArray[0] = n
                df.at[ lastFH, "fh_status" ] = 0
                df.at[ n, "fh_status" ] = 1
        elif direction == -1:
            lastFL = max(int(df.head(1).n), FlArray[0])
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
        minListShN = int(df[ (df.n >= ShArray[0]) & (df.n <= n) & (df.low == minListSh)].head(1).n)
        
        maxListSl = df[ (df.n >= SlArray[0]) & (df.n <= n)].high.max()
        maxListSlN = int(df[ (df.n >= SlArray[0]) & (df.n <= n) & (df.high == maxListSl)].head(1).n)
        
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
          if not math.isnan(df_donchian.at[index, "DCU_"+ str(config["dc"]["dc_length"]) + "_" + str(config["dc"]["dc_length"])]):
            df.at[n, "dc_upper"] = df_donchian.at[index, "DCU_"+ str(config["dc"]["dc_length"]) + "_" + str(config["dc"]["dc_length"])]
            df.at[n, "dc_lower"] = df_donchian.at[index, "DCU_"+ str(config["dc"]["dc_length"]) + "_" + str(config["dc"]["dc_length"])]
            df.at[n, "dc_mid"] = df_donchian.at[index, "DCU_"+ str(config["dc"]["dc_length"]) + "_" + str(config["dc"]["dc_length"])]
            df.at[n, "n_lookback"] = int(max(0, np.nanmin([df.at[n, "n_lookback"], n-(config["dc"]["dc_length"]+1)])))
          
        # 5. Swing DC ===============================================
        else:
          df.at[n, "dc_upper"] = df[ (df.n >= (ShArray[config["dc"]["dc_length"]-1] if len(ShArray) >= config["dc"]["dc_length"] else 0)) & (df.n <= n)].high.max()
          df.at[n, "dc_lower"] = df[ (df.n >= (SlArray[config["dc"]["dc_length"]-1] if len(SlArray) >= config["dc"]["dc_length"] else 0)) & (df.n <= n)].low.min()
          df.at[n, "dc_mid"] = (df.at[n, "dc_upper"] + df.at[n, "dc_lower"])/2
          df.at[n, "n_lookback"] = int(max(0, np.nanmin([df.at[n, "n_lookback"], ShArray[config["dc"]["dc_length"]-1] if len(ShArray) >= config["dc"]["dc_length"] else 0])))
          df.at[n, "n_lookback"] = int(max(0, np.nanmin([df.at[n, "n_lookback"], SlArray[config["dc"]["dc_length"]-1] if len(SlArray) >= config["dc"]["dc_length"] else 0])))
        
        # 6. Pivot ===============================================
        
        curDate = df.at[n, "created"].isocalendar()
        prevDate = df.at[n-1, "created"].isocalendar() if len(df[df.n == n-1]) == 1 else None        

        curWeek = df.at[n, "created"].week
        prevWeek = df.at[n-1, "created"].week if len(df[df.n == n-1]) == 1 else None
        
        curMonth = df.at[n, "created"].month_name()
        prevMonth = df.at[n-1, "created"].month_name() if len(df[df.n == n-1]) == 1 else None
        
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
        df.at[n, "FhArray"] = FhArray[:]
        df.at[n, "FlArray"] = FlArray[:]
        df.at[n, "ShArray"] = ShArray[:]
        df.at[n, "SlArray"] = SlArray[:]
        df.at[n, "need_break_fractal_up"] = 1 if need_break_fractal_up else 0
        df.at[n, "anchorArray"] = anchorArray[:]
        df.at[n, "anchor1stArray"] = anchor1stArray[:]
        df.at[n, "anchorCntrArray"] = anchorCntrArray[:]
        df.at[n, "high1stArray"] = high1stArray[:]
        df.at[n, "low1stArray"] = low1stArray[:]
        df.at[n, "lowDailyCur"] = lowDailyCur
        df.at[n, "highDailyCur"] = highDailyCur
        df.at[n, "lowWeeklyCur"] = lowWeeklyCur
        df.at[n, "highWeeklyCur"] = highWeeklyCur
        df.at[n, "lowMonthlyCur"] = lowMonthlyCur
        df.at[n, "highMonthlyCur"] = highMonthlyCur
        df.at[n, "lowDaily"] = lowDaily
        df.at[n, "highDaily"] = highDaily
        df.at[n, "lowWeekly"] = lowWeekly
        df.at[n, "highWeekly"] = highWeekly
        df.at[n, "lowMonthly"] = lowMonthly
        df.at[n, "highMonthly"] = highMonthly
        df.at[n, "dpivotCur"] = dailyPivotCur
        df.at[n, "wpivotCur"] = weeklyPivotCur
        df.at[n, "mpivotCur"] = monthlyPivotCur
        df.at[n, "direction"] = direction
        
        # variable memory management
        FhArray = FhArray[:100]
        FlArray = FlArray[:100]
        ShArray = ShArray[:100]
        SlArray = SlArray[:100]  
        n = n + 1
      # END OF ROW LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
      
      # Output Management ===============================================
      if(len(df) <= 1000) and token_index == 0:
        df.iloc[:500].to_csv('output_data_stock.csv',mode='w', header=True, index=False)
        
      # N # append new chunk to csv
      elif(len(df) <= 1000):
        df.iloc[:500].to_csv('output_data_stock.csv',mode='a', header=False, index=False)
      
      else:
        df.iloc[500:1500].to_csv('output_data_stock.csv', mode='a', header=False, index=False)
      
      # Output Management End ===============================================
        
    # END OF CHUNK LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
    if len(df) <= 1000:
      df.iloc[500:].to_csv('output_data_stock.csv', mode='a', header=False, index=False)
    else:
      df.iloc[1500:].to_csv('output_data_stock.csv', mode='a', header=False, index=False)
    # Use for all? enable when debugging
    # break
  # END OF TOKEN LOOP <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
  
  # Bulk CSV to SQL
  query = """REPLACE INTO {} 
          VALUES
          (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
          )"""
  query = query.format(output_table)
  
  with open('output_data_stock.csv') as file:
    reader = csv.reader(file)
    next(reader)  # Skip first line (headers)
    data = list(reader)
  engine.execute(query, data)
  os.remove("output_data_stock.csv")
  enddate = datetime.now()
  engine.execute("INSERT INTO tbl_market_logtime (start, end, type) VALUES  ('%s', '%s', '15min update')" % (str(startdate), str(enddate)) )
  return str(startdate)
  
  
if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=False, port=5005, threaded=True)
  
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
    
