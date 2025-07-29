#!/usr/bin/env python3
"""
Test script for SL/TP Calculator
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.sl_tp_calculator import SLTPCalculator

def test_sl_tp_calculator():
    """Test the SL/TP calculator"""
    print("🧪 Testing SL/TP Calculator...")
    
    calculator = SLTPCalculator()
    
    # Test database connection
    if not calculator.connect_db():
        print("❌ Database connection failed")
        return False
    
    print("✅ Database connection successful")
    
    # Test getting data for VIX
    df = calculator.get_latest_15min_data('VIX', limit=50)
    if df.empty:
        print("❌ No data available for VIX")
        return False
    
    print(f"✅ Retrieved {len(df)} rows for VIX")
    print(f"📊 Latest data: {df['created'].max()}")
    
    # Test SL/TP calculation
    df_calculated = calculator.calculate_sl_tp(df, 'VIX')
    if df_calculated.empty:
        print("❌ SL/TP calculation failed")
        return False
    
    print("✅ SL/TP calculation successful")
    
    # Check if we have calculated values
    latest_row = df_calculated.iloc[-1]
    print(f"📈 Latest close: {latest_row['close']}")
    print(f"🛑 Stop Loss: {latest_row['sl_price']}")
    print(f"📊 ATR: {latest_row['atr']}")
    
    # Test saving to output table
    calculator.save_to_output_table(df_calculated, 'VIX')
    print("✅ Data saved to output table")
    
    calculator.connection.close()
    print("✅ Test completed successfully!")
    return True

if __name__ == "__main__":
    test_sl_tp_calculator() 