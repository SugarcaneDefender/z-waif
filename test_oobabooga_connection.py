#!/usr/bin/env python3
"""
Test Oobabooga connectivity and available endpoints
"""

import requests
import json

def test_basic_connectivity():
    """Test basic connectivity to Oobabooga"""
    print("🔍 Testing Basic Connectivity...")
    print("=" * 50)
    
    try:
        response = requests.get("http://127.0.0.1:7860/", timeout=5)
        print(f"✅ Basic connectivity: {response.status_code}")
        if response.status_code == 200:
            print("✅ Oobabooga Web UI is accessible")
            return True
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_api_endpoints():
    """Test various API endpoints"""
    print("\n🔍 Testing API Endpoints...")
    print("=" * 50)
    
    endpoints = [
        ("/api/generate", "POST", {"prompt": "Hello", "max_new_tokens": 10}),
        ("/api/v1/generate", "POST", {"prompt": "Hello", "max_new_tokens": 10}),
        ("/api/completions", "POST", {"data": [{"prompt": "Hello", "max_new_tokens": 10}]}),
        ("/v1/chat/completions", "POST", {"messages": [{"role": "user", "content": "Hello"}]}),
        ("/api/v1/model", "GET", None),
        ("/api/model", "GET", None),
    ]
    
    working_endpoints = []
    
    for endpoint, method, payload in endpoints:
        try:
            url = f"http://127.0.0.1:7860{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, json=payload, timeout=5)
            
            print(f"{endpoint} ({method}): {response.status_code}")
            
            if response.status_code in [200, 201]:
                print(f"✅ {endpoint} is working!")
                working_endpoints.append(endpoint)
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"   Response keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
                    except:
                        print(f"   Response: {response.text[:100]}...")
            elif response.status_code in [404, 405]:
                print(f"❌ {endpoint} not available")
            else:
                print(f"⚠️  {endpoint} returned {response.status_code}")
                
        except Exception as e:
            print(f"❌ {endpoint} error: {e}")
    
    return working_endpoints

def test_simple_generation():
    """Test simple text generation if any endpoints work"""
    print("\n🔍 Testing Simple Generation...")
    print("=" * 50)
    
    # Try the most common endpoint first
    try:
        payload = {
            "prompt": "Hello! How are you today?",
            "max_new_tokens": 20,
            "temperature": 0.7,
            "do_sample": True
        }
        
        response = requests.post("http://127.0.0.1:7860/api/generate", json=payload, timeout=10)
        print(f"Generate endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Generation successful!")
            print(f"Response: {result}")
            
            if 'results' in result and result['results']:
                text = result['results'][0].get('text', '')
                print(f"Generated text: {text}")
                return True
        else:
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"Generation test failed: {e}")
    
    return False

def main():
    """Main test function"""
    print("🚀 Oobabooga API Connection Test")
    print("=" * 60)
    
    # Test basic connectivity
    if not test_basic_connectivity():
        print("\n❌ Cannot connect to Oobabooga. Please ensure it's running.")
        return
    
    # Test API endpoints
    working_endpoints = test_api_endpoints()
    
    # Test generation
    generation_works = test_simple_generation()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    if working_endpoints:
        print(f"✅ Working endpoints: {', '.join(working_endpoints)}")
    else:
        print("❌ No API endpoints are working")
    
    if generation_works:
        print("✅ Text generation is working!")
        print("💡 Z-Waif should be able to connect successfully")
    else:
        print("❌ Text generation is not working")
        print("💡 This might be a configuration issue with Oobabooga")
    
    print("\n💡 If no endpoints work, try:")
    print("   1. Restart Oobabooga with: python server.py --listen --api")
    print("   2. Check if the model is fully loaded")
    print("   3. Verify API settings in Oobabooga Web UI")

if __name__ == "__main__":
    main() 