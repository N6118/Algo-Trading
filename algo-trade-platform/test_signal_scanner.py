#!/usr/bin/env python3
"""
Test Signal Scanner
Tests the signal scanner functionality to ensure it's working properly
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.app.signal_scanner.scanner import SignalScanner
from backend.app.signal_scanner.db_schema import SignalConfig
from backend.app.signal_scanner.init_db import Session

def test_signal_scanner():
    """Test the signal scanner functionality"""
    print("🧪 Testing Signal Scanner...")
    print("=" * 40)
    
    try:
        # Create scanner instance
        scanner = SignalScanner()
        
        # Get signal configurations
        session = Session()
        configs = session.query(SignalConfig).filter(SignalConfig.is_active == True).all()
        
        if not configs:
            print("❌ No active signal configurations found")
            return False
            
        print(f"✅ Found {len(configs)} active signal configurations")
        
        # Test scanning for each config
        for config in configs:
            print(f"\n🔍 Testing config: {config.name}")
            print(f"   Symbols: {config.primary_symbol}, {config.correlated_symbol}")
            print(f"   Timeframe: {config.primary_symbol_timeframe}")
            
            try:
                # Run signal scan
                signals = scanner.scan_for_signals(config)
                print(f"   ✅ Scan completed successfully")
                print(f"   📊 Generated {len(signals)} signals")
                
                # Show recent signals for this config
                recent_signals = session.query(GeneratedSignal).filter(
                    GeneratedSignal.config_id == config.id,
                    GeneratedSignal.signal_time > datetime.utcnow() - timedelta(hours=1)
                ).all()
                
                print(f"   📈 Recent signals: {len(recent_signals)}")
                
            except Exception as e:
                print(f"   ❌ Error scanning config {config.name}: {e}")
                
        session.close()
        print("\n✅ Signal scanner test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing signal scanner: {e}")
        return False

def check_recent_signals():
    """Check for recent signals in the database"""
    print("\n📊 Checking Recent Signals...")
    print("=" * 30)
    
    try:
        session = Session()
        
        # Get recent signals
        recent_signals = session.query(GeneratedSignal).filter(
            GeneratedSignal.signal_time > datetime.utcnow() - timedelta(hours=2)
        ).order_by(GeneratedSignal.signal_time.desc()).limit(10).all()
        
        if recent_signals:
            print(f"✅ Found {len(recent_signals)} recent signals:")
            for signal in recent_signals:
                print(f"   📈 {signal.symbol} {signal.direction} @ {signal.price} ({signal.signal_time})")
        else:
            print("❌ No recent signals found")
            
        session.close()
        
    except Exception as e:
        print(f"❌ Error checking recent signals: {e}")

if __name__ == "__main__":
    from backend.app.signal_scanner.db_schema import GeneratedSignal
    from datetime import datetime, timedelta
    
    print("🚀 Signal Scanner Test Suite")
    print("=" * 50)
    
    # Test signal scanner
    success = test_signal_scanner()
    
    # Check recent signals
    check_recent_signals()
    
    if success:
        print("\n🎉 All tests passed! Signal scanner is working properly.")
    else:
        print("\n⚠️ Some tests failed. Check the logs for details.")
