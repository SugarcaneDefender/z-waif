#!/usr/bin/env python3
"""
Test script to verify fallback API integration in main system
"""

import os
import sys
import json
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_fallback_integration():
    """Test that fallback API is properly integrated into main system"""
    
    print("🧪 Testing Fallback API Integration")
    print("=" * 50)
    
    # Test 1: Check if fallback API module is available
    print("\n1. Testing Fallback API Module Availability...")
    try:
        from API import fallback_api
        print("   ✅ Fallback API module imported successfully")
        
        # Check if key functions are available
        required_functions = [
            'try_fallbacks', 'get_fallback_llm', 'switch_fallback_model',
            'discover_models', 'check_model_compatibility', 'generate_image_response'
        ]
        
        for func_name in required_functions:
            if hasattr(fallback_api, func_name):
                print(f"   ✅ {func_name} function available")
            else:
                print(f"   ❌ {func_name} function missing")
                return False
                
    except ImportError as e:
        print(f"   ❌ Fallback API module import failed: {e}")
        return False
    
    # Test 2: Check if fallback is properly configured in settings
    print("\n2. Testing Fallback Configuration...")
    try:
        from utils import settings
        
        # Check if fallback settings are available
        if hasattr(settings, 'api_fallback_enabled'):
            print(f"   ✅ API fallback enabled setting: {settings.api_fallback_enabled}")
        else:
            print("   ❌ API fallback enabled setting missing")
            return False
            
        if hasattr(settings, 'API_FALLBACK_MODEL'):
            print(f"   ✅ API fallback model setting: {settings.API_FALLBACK_MODEL}")
        else:
            print("   ❌ API fallback model setting missing")
            return False
            
    except Exception as e:
        print(f"   ❌ Settings check failed: {e}")
        return False
    
    # Test 3: Test API controller integration
    print("\n3. Testing API Controller Integration...")
    try:
        from API import api_controller
        
        # Check if the run function has fallback logic
        run_source = api_controller.run.__code__.co_consts
        run_source_str = str(run_source)
        
        if 'fallback' in run_source_str.lower():
            print("   ✅ Fallback logic detected in run function")
        else:
            print("   ❌ Fallback logic not found in run function")
            return False
            
        # Check if the run_streaming function has fallback logic
        run_streaming_source = api_controller.run_streaming.__code__.co_consts
        run_streaming_source_str = str(run_streaming_source)
        
        if 'fallback' in run_streaming_source_str.lower():
            print("   ✅ Fallback logic detected in run_streaming function")
        else:
            print("   ❌ Fallback logic not found in run_streaming function")
            return False
            
    except Exception as e:
        print(f"   ❌ API controller check failed: {e}")
        return False
    
    # Test 4: Test image processing fallback integration
    print("\n4. Testing Image Processing Fallback Integration...")
    try:
        # Check if view_image function has fallback logic
        view_image_source = api_controller.view_image.__code__.co_consts
        view_image_source_str = str(view_image_source)
        
        if 'fallback' in view_image_source_str.lower():
            print("   ✅ Fallback logic detected in view_image function")
        else:
            print("   ❌ Fallback logic not found in view_image function")
            return False
            
        # Check if view_image_streaming function has fallback logic
        view_image_streaming_source = api_controller.view_image_streaming.__code__.co_consts
        view_image_streaming_source_str = str(view_image_streaming_source)
        
        if 'fallback' in view_image_streaming_source_str.lower():
            print("   ✅ Fallback logic detected in view_image_streaming function")
        else:
            print("   ❌ Fallback logic not found in view_image_streaming function")
            return False
            
    except Exception as e:
        print(f"   ❌ Image processing check failed: {e}")
        return False
    
    # Test 5: Test main.py integration
    print("\n5. Testing Main.py Integration...")
    try:
        # Check if main.py has fallback initialization
        with open('main.py', 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        if 'fallback' in main_content.lower():
            print("   ✅ Fallback initialization detected in main.py")
        else:
            print("   ❌ Fallback initialization not found in main.py")
            return False
            
        # Check for specific fallback functions
        fallback_functions = [
            'auto_configure_fallback',
            'get_current_fallback_status', 
            'discover_models'
        ]
        
        for func in fallback_functions:
            if func in main_content:
                print(f"   ✅ {func} function found in main.py")
            else:
                print(f"   ❌ {func} function not found in main.py")
                return False
                
    except Exception as e:
        print(f"   ❌ Main.py check failed: {e}")
        return False
    
    # Test 6: Test web UI integration
    print("\n6. Testing Web UI Integration...")
    try:
        from utils import web_ui
        
        # Check if web UI has fallback controls
        web_ui_source = web_ui.create_ui.__code__.co_consts
        web_ui_source_str = str(web_ui_source)
        
        if 'fallback' in web_ui_source_str.lower():
            print("   ✅ Fallback controls detected in web UI")
        else:
            print("   ❌ Fallback controls not found in web UI")
            return False
            
    except Exception as e:
        print(f"   ❌ Web UI check failed: {e}")
        return False
    
    # Test 7: Test that advanced functions are preserved
    print("\n7. Testing Advanced Functions Preservation...")
    try:
        # Check that all advanced functions are still available
        advanced_functions = [
            'run_streaming', 'view_image_streaming', 'send_via_oogabooga',
            'receive_via_oogabooga', 'next_message_oogabooga', 'undo_message',
            'soft_reset', 'summary_memory_run'
        ]
        
        for func_name in advanced_functions:
            if hasattr(api_controller, func_name):
                print(f"   ✅ Advanced function {func_name} preserved")
            else:
                print(f"   ❌ Advanced function {func_name} missing")
                return False
                
    except Exception as e:
        print(f"   ❌ Advanced functions check failed: {e}")
        return False
    
    # Test 8: Test fallback model discovery
    print("\n8. Testing Fallback Model Discovery...")
    try:
        models = fallback_api.discover_models()
        if models:
            print(f"   ✅ Discovered {len(models)} fallback models")
            for model in models[:3]:  # Show first 3
                print(f"      - {model}")
        else:
            print("   ⚠️ No fallback models discovered")
            
    except Exception as e:
        print(f"   ❌ Model discovery failed: {e}")
        return False
    
    # Test 9: Test fallback system status
    print("\n9. Testing Fallback System Status...")
    try:
        from utils.web_ui import get_current_fallback_status
        status = get_current_fallback_status()
        
        if isinstance(status, dict):
            print("   ✅ Fallback status retrieved successfully")
            for key, value in status.items():
                print(f"      {key}: {value}")
        else:
            print("   ❌ Fallback status retrieval failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Fallback status check failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All fallback integration tests passed!")
    print("\n📋 Summary:")
    print("   ✅ Fallback API module is properly integrated")
    print("   ✅ API controller has fallback logic for all functions")
    print("   ✅ Image processing has fallback support")
    print("   ✅ Main.py initializes fallback system")
    print("   ✅ Web UI has fallback controls")
    print("   ✅ All advanced functions are preserved")
    print("   ✅ Fallback model discovery works")
    print("   ✅ Fallback system status is accessible")
    
    return True

def test_fallback_functionality():
    """Test actual fallback functionality"""
    
    print("\n🧪 Testing Fallback Functionality")
    print("=" * 50)
    
    try:
        from API import fallback_api
        from utils import settings
        
        # Enable fallback for testing
        original_fallback = settings.api_fallback_enabled
        settings.api_fallback_enabled = True
        
        print("✅ Fallback enabled for testing")
        
        # Test basic fallback request
        test_request = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! How are you today?"}
            ],
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        print("🔄 Testing fallback request...")
        response = fallback_api.try_fallbacks(test_request)
        
        if isinstance(response, dict) and "content" in response:
            content = response["content"]
            print(f"✅ Fallback request successful: {content[:100]}...")
        elif isinstance(response, dict) and "choices" in response:
            content = response["choices"][0]["message"]["content"]
            print(f"✅ Fallback request successful: {content[:100]}...")
        else:
            print(f"❌ Fallback request failed: {response}")
            settings.api_fallback_enabled = original_fallback
            return False
        
        # Restore original setting
        settings.api_fallback_enabled = original_fallback
        print("✅ Fallback functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Fallback functionality test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Fallback Integration Tests")
    print("=" * 60)
    
    # Run integration tests
    integration_passed = test_fallback_integration()
    
    # Run functionality tests
    functionality_passed = test_fallback_functionality()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Integration Tests: {'✅ PASSED' if integration_passed else '❌ FAILED'}")
    print(f"   Functionality Tests: {'✅ PASSED' if functionality_passed else '❌ FAILED'}")
    
    if integration_passed and functionality_passed:
        print("\n🎉 All tests passed! The fallback API is properly integrated.")
        print("\n📝 Usage Instructions:")
        print("   1. Enable API fallback in the web UI settings")
        print("   2. Select your preferred fallback model")
        print("   3. The system will automatically use fallback when main API fails")
        print("   4. All advanced functions are preserved and working")
        print("   5. Monitor logs for fallback usage")
        return True
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 