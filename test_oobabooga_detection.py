#!/usr/bin/env python3
"""
Test script for Oobabooga server detection functionality
"""

import sys
import os
import time

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_oobabooga_detection():
    """Test the Oobabooga server detection functionality"""
    print("🧪 Testing Oobabooga server detection...")
    
    try:
        # Import our settings module
        from utils import settings
        
        print("✅ Successfully imported settings module")
        
        # Test the detection function
        print("🔍 Running automatic detection...")
        detected_port = settings.auto_detect_oobabooga()
        
        if detected_port:
            print(f"✅ Detection successful! Found server on port {detected_port}")
            
            # Test if the .env file was updated
            if os.path.exists(".env"):
                with open(".env", 'r') as f:
                    content = f.read()
                    if f"HOST_PORT=127.0.0.1:{detected_port}" in content:
                        print("✅ .env file was updated correctly")
                    else:
                        print("⚠️ .env file may not have been updated correctly")
            else:
                print("⚠️ .env file not found")
                
        else:
            print("⚠️ No Oobabooga server detected")
            print("💡 Make sure Oobabooga is running and try again")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

def test_manual_detection():
    """Test manual detection without updating .env"""
    print("\n🧪 Testing manual detection (no .env update)...")
    
    try:
        from utils import settings
        
        # Test just the detection part
        detected_port = settings.detect_and_update_oobabooga_port()
        
        if detected_port:
            print(f"✅ Manual detection successful! Found server on port {detected_port}")
        else:
            print("⚠️ Manual detection found no server")
            
    except Exception as e:
        print(f"❌ Manual detection test failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 Z-WAIF Oobabooga Detection Test")
    print("=" * 60)
    
    # Test 1: Full detection with .env update
    success1 = test_oobabooga_detection()
    
    # Wait a moment
    time.sleep(1)
    
    # Test 2: Manual detection
    success2 = test_manual_detection()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 60)
    
    return success1 and success2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 