#!/usr/bin/env python3
"""
Test script to check RVC server on port 18888
"""

import requests
import json

def test_rvc_18888():
    """Test RVC server on port 18888"""
    print("Testing RVC server on port 18888...")
    
    # Test the info endpoint
    try:
        response = requests.get('http://127.0.0.1:18888/info', timeout=2)
        print(f"Info endpoint status: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response keys: {list(data.keys())}")
                if 'version' in data and 'modelSlotIndex' in data:
                    print("✅ This appears to be a valid RVC server!")
                    return True
            except:
                print("Response is not JSON")
    except Exception as e:
        print(f"Error testing info endpoint: {e}")
    
    # Test the test endpoint
    try:
        response = requests.post('http://127.0.0.1:18888/test', 
                               json={'test': 'data'}, 
                               timeout=2)
        print(f"Test endpoint status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        if response.status_code == 200:
            print("✅ Test endpoint responded successfully!")
            return True
    except Exception as e:
        print(f"Error testing test endpoint: {e}")
    
    return False

if __name__ == "__main__":
    if test_rvc_18888():
        print("\n🎉 RVC server on port 18888 is working!")
        print("💡 This appears to be a real-time voice changer RVC server")
        print("💡 It may not support text-to-speech directly")
    else:
        print("\n❌ RVC server on port 18888 is not responding") 