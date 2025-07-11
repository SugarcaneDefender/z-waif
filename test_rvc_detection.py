#!/usr/bin/env python3
"""
Test script for RVC server detection functionality
"""

import sys
import os
import time

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rvc_detection():
    """Test the RVC server detection functionality"""
    print("🧪 Testing RVC server detection...")
    
    try:
        # Import our settings module
        from utils import settings
        
        print("✅ Successfully imported settings module")
        
        # Test the detection function
        print("🔍 Running automatic RVC detection...")
        detected_port = settings.auto_detect_rvc()
        
        if detected_port:
            print(f"✅ Detection successful! Found RVC server on port {detected_port}")
            
            # Check if .env file was updated
            try:
                with open(".env", "r") as f:
                    env_content = f.read()
                    if f"RVC_PORT={detected_port}" in env_content:
                        print("✅ .env file successfully updated with RVC port")
                    else:
                        print("⚠️ .env file may not have been updated correctly")
            except FileNotFoundError:
                print("⚠️ .env file not found - may have been created from template")
            
            return True
        else:
            print("⚠️ No RVC server detected")
            print("💡 Make sure your RVC server is running on a common port (7897, 7860, etc.)")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import settings module: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during RVC detection test: {e}")
        return False

def test_manual_detection():
    """Test manual RVC detection with different ports"""
    print("\n🧪 Testing manual RVC detection...")
    
    try:
        from utils import settings
        
        # Test common RVC ports
        test_ports = [7897, 7860, 8000, 8080, 5000]
        
        for port in test_ports:
            print(f"🔍 Testing port {port}...")
            if settings.detect_and_update_rvc_port():
                print(f"✅ RVC server found on port {port}")
                return True
            else:
                print(f"❌ No RVC server on port {port}")
        
        print("⚠️ No RVC server found on any common ports")
        return False
        
    except Exception as e:
        print(f"❌ Error during manual detection test: {e}")
        return False

def main():
    """Main test function"""
    print("🎤 RVC Server Detection Test")
    print("=" * 50)
    
    # Test automatic detection
    success1 = test_rvc_detection()
    
    # Test manual detection
    success2 = test_manual_detection()
    
    print("\n" + "=" * 50)
    if success1 or success2:
        print("✅ RVC detection test completed successfully!")
        print("💡 Your RVC server is properly configured")
    else:
        print("❌ RVC detection test failed")
        print("💡 Please ensure your RVC server is running")
        print("💡 Common RVC ports: 7897, 7860, 8000, 8080")
    
    print("\n🔧 To manually test RVC detection, run:")
    print("   python -c \"from utils import settings; settings.auto_detect_rvc()\"")

if __name__ == "__main__":
    main() 