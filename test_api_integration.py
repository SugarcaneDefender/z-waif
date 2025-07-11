#!/usr/bin/env python3
"""
Comprehensive API Integration Test for Z-Waif
Tests that the API integration works correctly with the codebase patterns.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_api_controller_integration():
    """Test that the API controller can properly call the Oobabooga API"""
    print("\n🔍 Testing API Controller Integration...")
    print("=" * 50)
    
    try:
        # Import the API controller
        import API.api_controller as api_controller
        
        # Test the main API call function
        test_input = "Hello! How are you today?"
        print(f"Testing with input: {test_input}")
        
        # Call the main API function
        response = api_controller.send_via_oogabooga(test_input)
        
        print(f"Response received: {repr(response)}")
        
        if response and isinstance(response, str) and len(response.strip()) > 0:
            print("✅ API controller integration successful!")
            return True
        else:
            print("❌ API controller returned empty or invalid response")
            return False
            
    except Exception as e:
        print(f"❌ API controller integration failed: {e}")
        return False

def test_oobabooga_api_direct():
    """Test direct Oobabooga API calls"""
    print("\n🔍 Testing Direct Oobabooga API...")
    print("=" * 50)
    
    try:
        import API.oobaooga_api as oobabooga_api
        
        # Test the api_standard function
        test_request = {
            "messages": [
                {"role": "user", "content": "Hello! How are you today?"}
            ],
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        print(f"Testing api_standard with request: {test_request}")
        response = oobabooga_api.api_standard(test_request)
        
        print(f"Response received: {repr(response)}")
        
        if response and isinstance(response, str) and len(response.strip()) > 0:
            print("✅ Direct Oobabooga API successful!")
            return True
        else:
            print("❌ Direct Oobabooga API returned empty or invalid response")
            return False
            
    except Exception as e:
        print(f"❌ Direct Oobabooga API failed: {e}")
        return False

def test_character_card_loading():
    """Test character card loading"""
    print("\n🔍 Testing Character Card Loading...")
    print("=" * 50)
    
    try:
        import API.character_card as character_card
        
        # Load character card
        character_card.load_char_card()
        
        print(f"Character card loaded: {repr(character_card.character_card[:100])}...")
        
        if character_card.character_card and character_card.character_card != "No character card loaded!":
            print("✅ Character card loading successful!")
            return True
        else:
            print("❌ Character card loading failed")
            return False
            
    except Exception as e:
        print(f"❌ Character card loading failed: {e}")
        return False

def test_settings_integration():
    """Test settings integration"""
    print("\n🔍 Testing Settings Integration...")
    print("=" * 50)
    
    try:
        from utils import settings
        
        # Test key settings
        print(f"API_TYPE: {settings.API_TYPE}")
        print(f"HOST_PORT: {settings.HOST_PORT}")
        print(f"MODEL_TYPE: {settings.MODEL_TYPE}")
        print(f"CHAR_NAME: {settings.CHAR_NAME}")
        
        if settings.API_TYPE and settings.HOST_PORT:
            print("✅ Settings integration successful!")
            return True
        else:
            print("❌ Settings integration failed")
            return False
            
    except Exception as e:
        print(f"❌ Settings integration failed: {e}")
        return False

def test_formal_filter_integration():
    """Test formal filter integration"""
    print("\n🔍 Testing Formal Filter Integration...")
    print("=" * 50)
    
    try:
        from utils.formal_filter import filter_formal_response
        from utils.settings import get_formal_filter_config
        
        # Test formal filter configuration
        config = get_formal_filter_config()
        print(f"Formal filter enabled: {config['enabled']}")
        print(f"Formal filter strength: {config['strength']}")
        
        # Test formal filter on a sample response
        test_response = "How may I assist you today?"
        filtered_response = filter_formal_response(test_response)
        
        print(f"Original: {test_response}")
        print(f"Filtered: {filtered_response}")
        
        if filtered_response != test_response:
            print("✅ Formal filter is working!")
        else:
            print("ℹ️ Formal filter did not modify response (may be disabled)")
        
        return True
        
    except Exception as e:
        print(f"❌ Formal filter integration failed: {e}")
        return False

def test_chat_history_integration():
    """Test chat history integration"""
    print("\n🔍 Testing Chat History Integration...")
    print("=" * 50)
    
    try:
        from utils.chat_history import add_message_to_history, get_chat_history
        
        # Test adding messages to history
        test_user_id = "test_user"
        test_platform = "test"
        
        add_message_to_history(test_user_id, "user", "Hello!", test_platform)
        add_message_to_history(test_user_id, "assistant", "Hi there!", test_platform)
        
        # Test retrieving history
        history = get_chat_history(test_user_id, test_platform, limit=5)
        
        print(f"Chat history retrieved: {len(history)} messages")
        
        if len(history) >= 2:
            print("✅ Chat history integration successful!")
            return True
        else:
            print("❌ Chat history integration failed")
            return False
            
    except Exception as e:
        print(f"❌ Chat history integration failed: {e}")
        return False

def test_relationship_system_integration():
    """Test relationship system integration"""
    print("\n🔍 Testing Relationship System Integration...")
    print("=" * 50)
    
    try:
        from utils.user_relationships import get_user_relationship_level, get_relationship_context
        
        # Test relationship system
        test_user_id = "test_user"
        test_platform = "test"
        
        relationship_level = get_user_relationship_level(test_user_id, test_platform)
        relationship_context = get_relationship_context(relationship_level)
        
        print(f"Relationship level: {relationship_level}")
        print(f"Relationship context: {relationship_context[:100]}...")
        
        if relationship_level and relationship_context:
            print("✅ Relationship system integration successful!")
            return True
        else:
            print("❌ Relationship system integration failed")
            return False
            
    except Exception as e:
        print(f"❌ Relationship system integration failed: {e}")
        return False

def test_end_to_end_conversation():
    """Test a complete end-to-end conversation"""
    print("\n🔍 Testing End-to-End Conversation...")
    print("=" * 50)
    
    try:
        import API.api_controller as api_controller
        
        # Test multiple conversation turns
        test_inputs = [
            "Hello! How are you today?",
            "What's your favorite color?",
            "Tell me a joke!"
        ]
        
        responses = []
        for i, test_input in enumerate(test_inputs):
            print(f"\nTurn {i+1}: {test_input}")
            response = api_controller.send_via_oogabooga(test_input)
            print(f"Response: {response}")
            responses.append(response)
            
            # Small delay between requests
            time.sleep(1)
        
        # Check if we got meaningful responses
        valid_responses = [r for r in responses if r and isinstance(r, str) and len(r.strip()) > 10]
        
        if len(valid_responses) >= 2:
            print(f"✅ End-to-end conversation successful! ({len(valid_responses)}/3 valid responses)")
            return True
        else:
            print(f"❌ End-to-end conversation failed ({len(valid_responses)}/3 valid responses)")
            return False
            
    except Exception as e:
        print(f"❌ End-to-end conversation failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Starting Z-Waif API Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Settings Integration", test_settings_integration),
        ("Character Card Loading", test_character_card_loading),
        ("Formal Filter Integration", test_formal_filter_integration),
        ("Chat History Integration", test_chat_history_integration),
        ("Relationship System Integration", test_relationship_system_integration),
        ("Direct Oobabooga API", test_oobabooga_api_direct),
        ("API Controller Integration", test_api_controller_integration),
        ("End-to-End Conversation", test_end_to_end_conversation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API integration is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 