#!/usr/bin/env python3
"""
Script to find the correct API port for Oobabooga
"""

import requests
import time

def test_port(port):
    """Test if an API is running on a specific port"""
    try:
        # Test basic connectivity
        response = requests.get(f"http://127.0.0.1:{port}", timeout=2)
        if response.status_code == 200:
            print(f"✅ Port {port}: Web server responding")
            
            # Test OpenAI-compatible API endpoint
            try:
                api_response = requests.post(
                    f"http://127.0.0.1:{port}/v1/chat/completions",
                    json={"messages": [{"role": "user", "content": "test"}], "max_tokens": 5},
                    timeout=5
                )
                if api_response.status_code == 200:
                    print(f"✅ Port {port}: OpenAI API endpoint working!")
                    return True
                else:
                    print(f"⚠️ Port {port}: API endpoint returned {api_response.status_code}")
            except Exception as e:
                print(f"❌ Port {port}: API endpoint error - {e}")
        else:
            print(f"❌ Port {port}: HTTP {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Port {port}: Connection refused")
    except requests.exceptions.Timeout:
        print(f"❌ Port {port}: Timeout")
    except Exception as e:
        print(f"❌ Port {port}: Error - {e}")
    return False

def main():
    """Test common Oobabooga ports"""
    print("🔍 Scanning for Oobabooga API server...")
    print("=" * 50)
    
    # Common ports to test
    ports = [5000, 7860, 7861, 7862, 7863, 7864, 7865, 7866, 7867, 7868, 7869, 7870]
    
    working_ports = []
    
    for port in ports:
        if test_port(port):
            working_ports.append(port)
        time.sleep(0.1)  # Small delay between tests
    
    print("\n" + "=" * 50)
    if working_ports:
        print(f"🎉 Found working API on port(s): {working_ports}")
        print(f"💡 Update your .env file with: HOST_PORT=127.0.0.1:{working_ports[0]}")
    else:
        print("❌ No working API found")
        print("💡 Make sure Oobabooga is running with the OpenAI extension enabled")

if __name__ == "__main__":
    main() 