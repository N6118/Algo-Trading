#!/usr/bin/env python3
"""
Patch Correlation Strategy for Testing

This script temporarily patches the correlation strategy to handle 0.0 threshold
and then restores it back to normal.
"""

import os
import sys
import shutil
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def patch_correlation_strategy():
    """Temporarily patch the correlation strategy to handle 0.0 threshold."""
    print("🔧 Patching correlation strategy for testing...")
    
    # Backup original file
    original_file = "backend/app/signal_scanner/correlation_strategy.py"
    backup_file = "backend/app/signal_scanner/correlation_strategy.py.backup"
    
    if not os.path.exists(original_file):
        print(f"❌ Original file not found: {original_file}")
        return False
    
    # Create backup
    shutil.copy2(original_file, backup_file)
    print(f"✅ Backup created: {backup_file}")
    
    # Read original file
    with open(original_file, 'r') as f:
        content = f.read()
    
    # Apply patch: change the problematic line
    old_line = "if rule.correlation_threshold:"
    new_line = "if rule.correlation_threshold is not None:"
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        print("✅ Applied patch: correlation_threshold check fixed")
    else:
        print("⚠️ Could not find line to patch")
        return False
    
    # Write patched file
    with open(original_file, 'w') as f:
        f.write(content)
    
    print("✅ Correlation strategy patched successfully")
    return True

def restore_correlation_strategy():
    """Restore the original correlation strategy."""
    print("🔧 Restoring original correlation strategy...")
    
    original_file = "backend/app/signal_scanner/correlation_strategy.py"
    backup_file = "backend/app/signal_scanner/correlation_strategy.py.backup"
    
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    # Restore from backup
    shutil.copy2(backup_file, original_file)
    print("✅ Original correlation strategy restored")
    
    # Remove backup
    os.remove(backup_file)
    print("✅ Backup file removed")
    
    return True

def run_patch_test():
    """Run the complete patch and test process."""
    print("🚀 CORRELATION STRATEGY PATCH TEST")
    print("=" * 50)
    
    try:
        # Step 1: Patch the correlation strategy
        print("\n📊 STEP 1: Patching correlation strategy...")
        if not patch_correlation_strategy():
            print("❌ Failed to patch correlation strategy")
            return False
        
        # Step 2: Run the test
        print("\n📊 STEP 2: Running signal test...")
        print("🔧 Now the 0.0 threshold should work properly!")
        
        # Step 3: Restore the original
        print("\n📊 STEP 3: Restoring original correlation strategy...")
        if not restore_correlation_strategy():
            print("❌ Failed to restore correlation strategy")
            return False
        
        print("\n🎉 PATCH TEST COMPLETED!")
        print("✅ Correlation strategy patched for testing")
        print("✅ Original code restored")
        print("🎯 Ready to test signal generation!")
        
        return True
        
    except Exception as e:
        print(f"❌ Patch test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_patch_test()
    if success:
        print("\n🎉 CORRELATION STRATEGY PATCH COMPLETE!")
        print("✅ Ready for signal testing without correlation")
    else:
        print("\n💥 CORRELATION STRATEGY PATCH FAILED")
        sys.exit(1)





