#!/usr/bin/env python3
"""
RVC Connection Test Script
This script helps test your RVC server connection and configuration.
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_rvc_connection():
    """Test RVC server connection with different endpoints"""
    
    # Get RVC configuration from environment
    rvc_host = os.environ.get("RVC_HOST", "127.0.0.1")
    rvc_port = os.environ.get("RVC_PORT", "7897")
    rvc_model = os.environ.get("RVC_MODEL", "default")
    rvc_speaker = os.environ.get("RVC_SPEAKER", "0")
    rvc_pitch = os.environ.get("RVC_PITCH", "0.0")
    rvc_speed = os.environ.get("RVC_SPEED", "1.0")
    
    print(f"Testing RVC connection to {rvc_host}:{rvc_port}")
    print(f"Model: {rvc_model}, Speaker: {rvc_speaker}")
    print(f"Pitch: {rvc_pitch}, Speed: {rvc_speed}")
    print("-" * 50)
    
    # Common RVC endpoints to test
    endpoints = [
        f"http://{rvc_host}:{rvc_port}/api/tts",
        f"http://{rvc_host}:{rvc_port}/tts", 
        f"http://{rvc_host}:{rvc_port}/voice",
        f"http://{rvc_host}:{rvc_port}/api/voice",
        f"http://{rvc_host}:{rvc_port}/synthesize",
        f"http://{rvc_host}:{rvc_port}/api/synthesize"
    ]
    
    # Test payload
    test_payload = {
        "text": "Hello, this is a test message.",
        "model": rvc_model,
        "speaker_id": int(rvc_speaker),
        "pitch_adjust": float(rvc_pitch),
        "speed": float(rvc_speed),
        "emotion": "Happy",
        "language": "en"
    }
    
    # Alternative payload formats
    alt_payloads = [
        test_payload,
        {
            "text": "Hello, this is a test message.",
            "model": rvc_model,
            "speaker": rvc_speaker,
            "pitch": float(rvc_pitch),
            "speed": float(rvc_speed)
        },
        {
            "text": "Hello, this is a test message.",
            "model": rvc_model,
            "speaker_id": int(rvc_speaker),
            "pitch": float(rvc_pitch),
            "speed": float(rvc_speed)
        }
    ]
    
    success = False
    
    for i, endpoint in enumerate(endpoints):
        print(f"Testing endpoint {i+1}: {endpoint}")
        
        for j, payload in enumerate(alt_payloads):
            try:
                print(f"  Trying payload format {j+1}...")
                response = requests.post(endpoint, json=payload, timeout=5)
                
                print(f"    Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"    SUCCESS! Endpoint: {endpoint}")
                    print(f"    Payload format: {j+1}")
                    print(f"    Response size: {len(response.content)} bytes")
                    success = True
                    break
                elif response.status_code == 404:
                    print(f"    Endpoint not found (404)")
                elif response.status_code == 422:
                    print(f"    Validation error (422) - wrong payload format")
                    print(f"    Response: {response.text[:200]}")
                else:
                    print(f"    Error: {response.status_code}")
                    print(f"    Response: {response.text[:200]}")
                    
            except requests.exceptions.ConnectionError:
                print(f"    Connection failed - server not running or wrong port")
            except requests.exceptions.Timeout:
                print(f"    Timeout - server not responding")
            except Exception as e:
                print(f"    Error: {e}")
        
        if success:
            break
        print()
    
    if not success:
        print("\n❌ All RVC endpoints failed!")
        print("\nTroubleshooting tips:")
        print("1. Make sure your RVC server is running")
        print("2. Check if the port is correct (default: 7897)")
        print("3. Verify the API endpoint in your RVC server documentation")
        print("4. Check if your RVC server requires authentication")
        print("5. Try running: curl -X POST http://127.0.0.1:7897/api/tts -H 'Content-Type: application/json' -d '{\"text\":\"test\"}'")
    else:
        print("\n✅ RVC connection successful!")
        print("Your RVC server is working correctly.")

if __name__ == "__main__":
    test_rvc_connection() 