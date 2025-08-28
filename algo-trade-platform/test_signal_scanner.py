#!/usr/bin/env python3

import sys
import os
from urllib.parse import quote_plus

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.app.signal_scanner.scanner import SignalScanner
from backend.app.signal_scanner.db_schema import SignalConfig
from backend.app.signal_scanner.correlation_strategy import CorrelationStrategy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import pandas as pd

def test_signal_scanner():
    # Database connection
    password = quote_plus('password')
    uri = f'postgresql://postgres:{password}@localhost:5432/theodb'
    engine = create_engine(uri)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get the active config
        config = session.query(SignalConfig).filter(SignalConfig.id == 1).first()
        if not config:
            print("No active config found")
            return
        
        print(f"Testing with config: {config.name}")
        
        # Create correlation strategy directly
        strategy = CorrelationStrategy(config)
        
        # Get latest data manually
        query = """
        SELECT symbol, created, close, sh_price, sl_price, sh_status, sl_status 
        FROM tbl_ohlc_fifteen_output 
        WHERE symbol IN ('MES', 'VIX') 
        ORDER BY created DESC 
        LIMIT 10
        """
        
        df = pd.read_sql_query(query, engine)
        print("\nLatest data:")
        print(df.to_string())
        
        # Get MES and VIX data separately
        mes_data = df[df['symbol'] == 'MES'].iloc[0]
        vix_data = df[df['symbol'] == 'VIX'].iloc[0]
        
        print(f"\nMES Data:")
        print(f"  Close: {mes_data['close']}")
        print(f"  SH: {mes_data['sh_price']}")
        print(f"  SL: {mes_data['sl_price']}")
        print(f"  SH Status: {mes_data['sh_status']}")
        print(f"  SL Status: {mes_data['sl_status']}")
        
        print(f"\nVIX Data:")
        print(f"  Close: {vix_data['close']}")
        print(f"  SH: {vix_data['sh_price']}")
        print(f"  SL: {vix_data['sl_price']}")
        print(f"  SH Status: {vix_data['sh_status']}")
        print(f"  SL Status: {vix_data['sl_status']}")
        
        # Check buy conditions manually
        mes_price = mes_data['close']
        vix_price = vix_data['close']
        mes_sh = mes_data['sh_price']
        vix_sl = vix_data['sl_price']
        
        print(f"\nBuy Conditions Check:")
        print(f"  MES Close ({mes_price}) > MES SH ({mes_sh}): {mes_price > mes_sh}")
        print(f"  VIX Close ({vix_price}) < VIX SL ({vix_sl}): {vix_price < vix_sl}")
        print(f"  Both conditions met: {mes_price > mes_sh and vix_price < vix_sl}")
        
        # Create scanner and test
        scanner = SignalScanner()
        scanner.setup_database()
        
        # Scan for signals
        signals = scanner.scan_for_signals(config)
        
        print(f"\nGenerated {len(signals)} signals")
        
        # Print signal details
        for signal in signals:
            print(f"Signal: {signal.symbol} {signal.direction} at ${signal.price:.2f}")
            print(f"  Time: {signal.signal_time}")
            print(f"  Status: {signal.status}")
            print("---")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_signal_scanner()
