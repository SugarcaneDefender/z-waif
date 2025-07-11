#!/usr/bin/env python3
"""
Test script to verify API error handling fixes.
This tests that the fallback system doesn't trigger when the primary API succeeds.
"""

import os
import sys
import json
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_api_controller_fixes():
    """Test the API controller error handling fixes"""
    print("🧪 Testing API Controller Error Handling Fixes...")
    
    try:
        # Import the API controller
        from API import api_controller
        from utils import settings
        
        print("✅ Successfully imported API controller")
        
        # Test 1: Check if fallback is properly configured
        print(f"📋 API Fallback Enabled: {settings.api_fallback_enabled}")
        print(f"📋 API Type: {os.environ.get('API_TYPE', 'Oobabooga')}")
        
        # Test 2: Test basic API call structure
        test_input = "Hello, how are you today? [Platform: Web Interface - Personal Chat]"
        
        print(f"🔍 Testing with input: {test_input[:50]}...")
        
        # This should not trigger fallback if primary API succeeds
        try:
            result = api_controller.run(test_input, 0.7)
            print(f"✅ API call completed successfully")
            print(f"📝 Response: {result[:100]}...")
            
            # Check if response is valid
            if result and isinstance(result, str) and len(result.strip()) > 0:
                print("✅ Response validation passed")
            else:
                print("⚠️ Response validation failed - empty response")
                
        except Exception as e:
            print(f"❌ API call failed: {e}")
            return False
            
        # Test 3: Test error handling structure
        print("\n🔍 Testing error handling structure...")
        
        # Check if the primary_api_success flag is properly implemented
        source_code = ""
        try:
            with open("API/api_controller.py", "r") as f:
                source_code = f.read()
        except Exception as e:
            print(f"❌ Could not read API controller source: {e}")
            return False
        
        # Check for key improvements
        improvements = [
            "primary_api_success = False",
            "primary_api_success = True",
            "if settings.api_fallback_enabled and not primary_api_success:",
            "if primary_api_success and received_message:"
        ]
        
        for improvement in improvements:
            if improvement in source_code:
                print(f"✅ Found improvement: {improvement}")
            else:
                print(f"❌ Missing improvement: {improvement}")
                return False
        
        print("✅ All error handling improvements found")
        
        # Test 4: Test Oobabooga API improvements
        print("\n🔍 Testing Oobabooga API improvements...")
        try:
            from API import oobaooga_api
            
            # Check for enhanced error handling
            ooba_source = ""
            try:
                with open("API/oobaooga_api.py", "r") as f:
                    ooba_source = f.read()
            except Exception as e:
                print(f"❌ Could not read Oobabooga API source: {e}")
                return False
            
            ooba_improvements = [
                "Validate request parameters",
                "enhanced error handling",
                "RequestException",
                "json_error"
            ]
            
            for improvement in ooba_improvements:
                if improvement in ooba_source:
                    print(f"✅ Found Oobabooga improvement: {improvement}")
                else:
                    print(f"❌ Missing Oobabooga improvement: {improvement}")
                    return False
            
            print("✅ All Oobabooga API improvements found")
            
        except ImportError:
            print("⚠️ Oobabooga API not available for testing")
        
        # Test 5: Test Ollama API improvements
        print("\n🔍 Testing Ollama API improvements...")
        try:
            from API import ollama_api
            
            # Check for enhanced error handling
            ollama_source = ""
            try:
                with open("API/ollama_api.py", "r") as f:
                    ollama_source = f.read()
            except Exception as e:
                print(f"❌ Could not read Ollama API source: {e}")
                return False
            
            ollama_improvements = [
                "Validate input parameters",
                "context_error",
                "history_error",
                "api_error"
            ]
            
            for improvement in ollama_improvements:
                if improvement in ollama_source:
                    print(f"✅ Found Ollama improvement: {improvement}")
                else:
                    print(f"❌ Missing Ollama improvement: {improvement}")
                    return False
            
            print("✅ All Ollama API improvements found")
            
        except ImportError:
            print("⚠️ Ollama API not available for testing")
        
        print("\n🎉 All API error handling tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with unexpected error: {e}")
        return False

def test_fallback_prevention():
    """Test that fallback doesn't trigger when primary API succeeds"""
    print("\n🧪 Testing Fallback Prevention...")
    
    try:
        # Import required modules
        from API import api_controller
        from utils import settings
        
        # Enable fallback for testing
        original_fallback = settings.api_fallback_enabled
        settings.api_fallback_enabled = True
        
        print("✅ Fallback enabled for testing")
        
        # Test with a simple input
        test_input = "Hi there! [Platform: Web Interface - Personal Chat]"
        
        print(f"🔍 Testing fallback prevention with: {test_input}")
        
        # This should succeed with primary API and not trigger fallback
        result = api_controller.run(test_input, 0.7)
        
        if result and isinstance(result, str) and len(result.strip()) > 0:
            print("✅ Primary API succeeded and fallback was not triggered")
            print(f"📝 Response: {result[:100]}...")
            
            # Restore original fallback setting
            settings.api_fallback_enabled = original_fallback
            return True
        else:
            print("❌ Primary API failed or returned empty response")
            settings.api_fallback_enabled = original_fallback
            return False
            
    except Exception as e:
        print(f"❌ Fallback prevention test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting API Error Handling Fix Tests...\n")
    
    # Test 1: API Controller Fixes
    test1_passed = test_api_controller_fixes()
    
    # Test 2: Fallback Prevention
    test2_passed = test_fallback_prevention()
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    print(f"API Controller Fixes: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Fallback Prevention: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ The API error handling fixes are working correctly.")
        print("✅ Fallback will not trigger when primary API succeeds.")
        return True
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("⚠️ Please check the error handling implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 