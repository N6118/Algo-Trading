#!/usr/bin/env python3
"""
Data Flow Monitor
Monitors if fresh data is being collected after service restart
"""

import psycopg2
import time
from datetime import datetime, timedelta
import sys

# Database connection
DB_URI = "postgresql://postgres:password@100.121.186.86:5432/theodb"

def check_data_flow():
    """Check if fresh data is being collected"""
    try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        
        # Get current time
        cur.execute("SELECT NOW()")
        current_time = cur.fetchone()[0]
        
        # Check recent tick data
        cur.execute("""
            SELECT COUNT(*) as recent_ticks, MAX(timestamp) as latest_tick
            FROM stock_ticks 
            WHERE timestamp > NOW() - INTERVAL '5 minutes'
        """)
        tick_result = cur.fetchone()
        
        # Check recent SH/SL data
        cur.execute("""
            SELECT COUNT(*) as recent_shsl, MAX(created) as latest_shsl
            FROM tbl_ohlc_fifteen_output 
            WHERE created > NOW() - INTERVAL '1 hour'
        """)
        shsl_result = cur.fetchone()
        
        # Check recent signals
        cur.execute("""
            SELECT COUNT(*) as recent_signals, MAX(signal_time) as latest_signal
            FROM generated_signals 
            WHERE signal_time > NOW() - INTERVAL '1 hour'
        """)
        signal_result = cur.fetchone()
        
        print(f"🕐 Current Time: {current_time}")
        print(f"📊 Recent Tick Data: {tick_result[0]} records, Latest: {tick_result[1]}")
        print(f"📈 Recent SH/SL Data: {shsl_result[0]} records, Latest: {shsl_result[1]}")
        print(f"🎯 Recent Signals: {signal_result[0]} records, Latest: {signal_result[1]}")
        
        # Determine status
        if tick_result[0] > 0:
            print("✅ Fresh tick data is flowing!")
        else:
            print("❌ No fresh tick data")
            
        if shsl_result[0] > 0:
            print("✅ Fresh SH/SL calculations are happening!")
        else:
            print("❌ No fresh SH/SL calculations")
            
        if signal_result[0] > 0:
            print("✅ Fresh signals are being generated!")
        else:
            print("❌ No fresh signals")
        
        cur.close()
        conn.close()
        
        return tick_result[0] > 0
        
    except Exception as e:
        print(f"❌ Error checking data flow: {e}")
        return False

def monitor_continuously(interval_seconds=30):
    """Monitor data flow continuously"""
    print("🔍 Starting continuous data flow monitoring...")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        while True:
            print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 30)
            
            has_data = check_data_flow()
            
            if has_data:
                print("🎉 Data flow is working!")
            else:
                print("⚠️ No fresh data detected")
            
            print(f"⏳ Waiting {interval_seconds} seconds...")
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        monitor_continuously()
    else:
        check_data_flow()
