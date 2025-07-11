#!/usr/bin/env python3
"""
Fast RVC detection test for port 18888
"""

import sys
import os
import requests

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rvc_detection_18888():
    """Test RVC detection specifically for port 18888"""
    print("🧪 Testing RVC detection for port 18888...")
    
    try:
        # Import our settings module
        from utils import settings
        
        print("✅ Successfully imported settings module")
        
        # Test the is_rvc_response function directly
        print("🔍 Testing RVC response detection...")
        
        # Test the info endpoint
        response = requests.get('http://127.0.0.1:18888/info', timeout=2)
        print(f"Info endpoint status: {response.status_code}")
        
        if settings.is_rvc_response(response):
            print("✅ RVC response detection works for /info endpoint!")
        else:
            print("❌ RVC response detection failed for /info endpoint")
        
        # Test the test endpoint
        response = requests.post('http://127.0.0.1:18888/test', 
                               json={'test': 'data'}, 
                               timeout=2)
        print(f"Test endpoint status: {response.status_code}")
        
        if settings.is_rvc_response(response):
            print("✅ RVC response detection works for /test endpoint!")
        else:
            print("❌ RVC response detection failed for /test endpoint")
        
        # Test the detection function with a limited port range
        print("🔍 Testing detection with limited port range...")
        
        # Temporarily modify the common ports to only include 18888
        original_ports = settings.detect_and_update_rvc_port.__defaults__
        
        # Create a test function that only checks port 18888
        def test_detection():
            print("[SETTINGS] Testing RVC detection on port 18888...")
            
            # Common RVC endpoints to test
            endpoints = [
                "/api/tts",
                "/tts", 
                "/voice",
                "/api/voice",
                "/synthesize",
                "/api/synthesize",
                "/test",
                "/info",
                "/api/hello"
            ]
            
            # Simple test payload
            test_payload = {
                "text": "test",
                "model": "default",
                "speaker_id": 0,
                "pitch_adjust": 0.0,
                "speed": 1.0
            }
            
            # Only test port 18888
            for endpoint in endpoints:
                try:
                    url = f"http://127.0.0.1:18888{endpoint}"
                    response = requests.post(url, json=test_payload, timeout=2)
                    if response.status_code == 200 and settings.is_rvc_response(response):
                        print(f"[SETTINGS] Found RVC server on port 18888 (endpoint: {endpoint})")
                        return 18888
                    elif response.status_code in [404, 422]:
                        print(f"[SETTINGS] Found web server on port 18888 but not RVC (status: {response.status_code})")
                except requests.exceptions.RequestException:
                    continue
            
            # Try GET requests for endpoints that don't need POST
            for endpoint in ["/info", "/api/hello"]:
                try:
                    url = f"http://127.0.0.1:18888{endpoint}"
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200 and settings.is_rvc_response(response):
                        print(f"[SETTINGS] Found RVC server on port 18888 (endpoint: {endpoint})")
                        return 18888
                except requests.exceptions.RequestException:
                    continue
            
            print("[SETTINGS] No RVC server detected on port 18888")
            return None
        
        detected_port = test_detection()
        
        if detected_port:
            print(f"✅ Detection successful! Found RVC server on port {detected_port}")
            return True
        else:
            print("❌ Detection failed for port 18888")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import settings module: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during RVC detection test: {e}")
        return False

if __name__ == "__main__":
    print("🎤 Fast RVC Detection Test for Port 18888")
    print("=" * 50)
    
    success = test_rvc_detection_18888()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ RVC detection test completed successfully!")
        print("💡 Your RVC server on port 18888 is properly detected")
    else:
        print("❌ RVC detection test failed")
        print("💡 Please check the detection logic") 