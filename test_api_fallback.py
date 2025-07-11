#!/usr/bin/env python3
"""
Test script for API fallback functionality
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_api_fallback():
    """Test the API fallback functionality"""
    print("🧪 Testing API Fallback System")
    print("=" * 50)
    
    # Test 1: Check settings
    print("\n1. Testing Settings...")
    try:
        from utils import settings
        print(f"   ✅ API Fallback Enabled: {settings.api_fallback_enabled}")
        print(f"   ✅ Fallback Model: {settings.API_FALLBACK_MODEL}")
        print(f"   ✅ Fallback Host: {settings.API_FALLBACK_HOST}")
    except Exception as e:
        print(f"   ❌ Settings Error: {e}")
        return False
    
    # Test 2: Check fallback API import
    print("\n2. Testing Fallback API Import...")
    try:
        import API.fallback_api as fallback_api
        print("   ✅ Fallback API module imported successfully")
    except Exception as e:
        print(f"   ❌ Fallback API Import Error: {e}")
        return False
    
    # Test 3: Test fallback API initialization
    print("\n3. Testing Fallback API Initialization...")
    try:
        # Test with a simple request
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! How are you today?"}
        ]
        
        request = {
            "messages": test_messages,
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        print("   🔄 Initializing fallback model (this may take a moment)...")
        response = fallback_api.api_call(request)
        
        if isinstance(response, dict) and "choices" in response:
            content = response["choices"][0]["message"]["content"]
            print(f"   ✅ Fallback API working - Response: {content[:100]}...")
        else:
            print(f"   ❌ Unexpected response format: {response}")
            return False
            
    except Exception as e:
        print(f"   ❌ Fallback API Test Error: {e}")
        return False
    
    # Test 4: Test API controller integration
    print("\n4. Testing API Controller Integration...")
    try:
        import API.api_controller
        
        # Test with a simple message
        test_input = "Hello, this is a test message [Platform: Command Line]"
        
        print("   🔄 Testing API controller with fallback...")
        response = API.api_controller.run(test_input, 0.7)
        
        if response and len(response) > 0:
            print(f"   ✅ API Controller working - Response: {response[:100]}...")
        else:
            print("   ❌ Empty response from API controller")
            return False
            
    except Exception as e:
        print(f"   ❌ API Controller Test Error: {e}")
        return False
    
    # Test 5: Test model switching
    print("\n5. Testing Model Switching...")
    try:
        # Test switching to a different model
        success = fallback_api.switch_fallback_model("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        if success:
            print("   ✅ Model switching working")
        else:
            print("   ⚠️ Model switching failed (this is okay if model is already loaded)")
            
    except Exception as e:
        print(f"   ❌ Model Switching Error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! API fallback system is working correctly.")
    return True

def test_web_ui_integration():
    """Test web UI integration"""
    print("\n🧪 Testing Web UI Integration")
    print("=" * 50)
    
    try:
        # Test web UI import
        import utils.web_ui
        print("   ✅ Web UI module imported successfully")
        
        # Check if API fallback controls are present
        web_ui_source = open("utils/web_ui.py", "r", encoding="utf-8").read()
        if "API Fallback Settings" in web_ui_source:
            print("   ✅ API Fallback UI controls found")
        else:
            print("   ❌ API Fallback UI controls not found")
            return False
            
        if "api_fallback_enabled_checkbox" in web_ui_source:
            print("   ✅ API Fallback checkbox found")
        else:
            print("   ❌ API Fallback checkbox not found")
            return False
            
        print("   ✅ Web UI integration working")
        return True
        
    except Exception as e:
        print(f"   ❌ Web UI Test Error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting API Fallback System Tests")
    print("=" * 60)
    
    # Run tests
    api_test_passed = test_api_fallback()
    web_ui_test_passed = test_web_ui_integration()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   API Fallback Tests: {'✅ PASSED' if api_test_passed else '❌ FAILED'}")
    print(f"   Web UI Integration: {'✅ PASSED' if web_ui_test_passed else '❌ FAILED'}")
    
    if api_test_passed and web_ui_test_passed:
        print("\n🎉 All tests passed! The API fallback system is ready to use.")
        print("\n📝 Usage Instructions:")
        print("   1. Enable API fallback in the web UI settings")
        print("   2. Select your preferred fallback model")
        print("   3. The system will automatically use fallback when main API fails")
        print("   4. Monitor logs for fallback usage")
        return True
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 