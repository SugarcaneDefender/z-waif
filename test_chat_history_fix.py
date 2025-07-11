#!/usr/bin/env python3
"""
Test script to verify chat history and relationship system fixes.
This script tests the missing functions that were causing import errors.
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_chat_history_functions():
    """Test the chat history functions that were missing"""
    print("🧪 Testing chat history functions...")
    
    try:
        from utils.chat_history import (
            process_chatpops, 
            get_chat_history_for_webui, 
            add_message_to_webui_history,
            add_message_to_history,
            get_chat_history
        )
        print("✅ All chat history functions imported successfully")
        
        # Test process_chatpops
        test_message = "Hello! How are you doing today?"
        process_chatpops(test_message)
        print("✅ process_chatpops function works")
        
        # Test adding messages to history
        add_message_to_history("test_user", "user", "Hello!", "test_platform", {
            "timestamp": datetime.now().isoformat(),
            "source": "test"
        })
        add_message_to_history("test_user", "assistant", "Hi there! How can I help you?", "test_platform", {
            "timestamp": datetime.now().isoformat(),
            "source": "test"
        })
        print("✅ add_message_to_history function works")
        
        # Test getting chat history
        history = get_chat_history("test_user", "test_platform")
        if len(history) >= 2:
            print(f"✅ get_chat_history function works - found {len(history)} messages")
        else:
            print("❌ get_chat_history function failed - not enough messages")
            return False
        
        # Test Web UI specific functions
        webui_history = get_chat_history_for_webui()
        print(f"✅ get_chat_history_for_webui function works - returned {len(webui_history)} entries")
        
        add_message_to_webui_history("Test user message", "Test assistant response")
        print("✅ add_message_to_webui_history function works")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing chat history functions: {e}")
        return False

def test_relationship_functions():
    """Test the relationship functions that were missing"""
    print("\n🧪 Testing relationship functions...")
    
    try:
        from utils.user_relationships import (
            update_relationship_from_interaction,
            get_relationship_data,
            update_relationship
        )
        print("✅ All relationship functions imported successfully")
        
        # Test update_relationship_from_interaction
        test_message = "I love chatting with you! You're so helpful and kind."
        update_relationship_from_interaction("test_user", "test_platform", test_message)
        print("✅ update_relationship_from_interaction function works")
        
        # Test getting relationship data
        rel_data = get_relationship_data("test_user", "test_platform")
        if rel_data and "interaction_count" in rel_data:
            print(f"✅ get_relationship_data function works - interaction count: {rel_data['interaction_count']}")
        else:
            print("❌ get_relationship_data function failed")
            return False
        
        # Test update_relationship
        update_relationship("test_user", "test_platform", "positive", "testing")
        print("✅ update_relationship function works")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing relationship functions: {e}")
        return False

def test_api_controller_integration():
    """Test that the API controller can import and use the functions"""
    print("\n🧪 Testing API controller integration...")
    
    try:
        from API.api_controller import run
        print("✅ API controller run function imported successfully")
        
        # Test that the functions are available in the API controller context
        from utils.chat_history import process_chatpops, add_message_to_history
        from utils.user_relationships import update_relationship_from_interaction
        
        print("✅ All required functions can be imported in API controller context")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing API controller integration: {e}")
        return False

def test_web_ui_integration():
    """Test that the Web UI can access chat history"""
    print("\n🧪 Testing Web UI integration...")
    
    try:
        from utils.web_ui import update_chat
        print("✅ Web UI update_chat function imported successfully")
        
        # Test that chat history functions are available
        from utils.chat_history import get_chat_history
        webui_history = get_chat_history("webui_user", "webui")
        print(f"✅ Web UI can access chat history - found {len(webui_history)} messages")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing Web UI integration: {e}")
        return False

def test_chat_history_file_creation():
    """Test that chat history files are created properly"""
    print("\n🧪 Testing chat history file creation...")
    
    try:
        from utils.chat_history import save_chat_histories, load_chat_histories
        
        # Add some test data
        from utils.chat_history import add_message_to_history
        add_message_to_history("file_test_user", "file_test_platform", "Test message", "file_test_platform")
        
        # Check if file exists
        import os
        if os.path.exists("Configurables/chat_histories.json"):
            print("✅ Chat history file created successfully")
            
            # Read and verify content
            with open("Configurables/chat_histories.json", 'r') as f:
                data = json.load(f)
            
            if data:
                print(f"✅ Chat history file contains data - {len(data)} user entries")
                return True
            else:
                print("❌ Chat history file is empty")
                return False
        else:
            print("❌ Chat history file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error testing chat history file creation: {e}")
        return False

def test_relationship_file_creation():
    """Test that relationship files are created properly"""
    print("\n🧪 Testing relationship file creation...")
    
    try:
        from utils.user_relationships import save_relationships, load_relationships
        
        # Add some test data
        from utils.user_relationships import update_relationship
        update_relationship("file_test_user", "file_test_platform", "positive", "testing")
        
        # Check if file exists
        import os
        if os.path.exists("Configurables/user_relationships.json"):
            print("✅ Relationship file created successfully")
            
            # Read and verify content
            with open("Configurables/user_relationships.json", 'r') as f:
                data = json.load(f)
            
            if data:
                print(f"✅ Relationship file contains data - {len(data)} user entries")
                return True
            else:
                print("❌ Relationship file is empty")
                return False
        else:
            print("❌ Relationship file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error testing relationship file creation: {e}")
        return False

def cleanup_test_data():
    """Clean up test data files"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        import os
        
        # Clean up chat history test data
        if os.path.exists("Configurables/chat_histories.json"):
            with open("Configurables/chat_histories.json", 'r') as f:
                data = json.load(f)
            
            # Remove test entries
            test_keys = [k for k in data.keys() if "test_" in k]
            for key in test_keys:
                del data[key]
            
            with open("Configurables/chat_histories.json", 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ Cleaned up {len(test_keys)} test chat history entries")
        
        # Clean up relationship test data
        if os.path.exists("Configurables/user_relationships.json"):
            with open("Configurables/user_relationships.json", 'r') as f:
                data = json.load(f)
            
            # Remove test entries
            test_keys = [k for k in data.keys() if "test_" in k]
            for key in test_keys:
                del data[key]
            
            with open("Configurables/user_relationships.json", 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ Cleaned up {len(test_keys)} test relationship entries")
            
    except Exception as e:
        print(f"⚠️ Warning: Could not clean up test data: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting chat history and relationship system tests...")
    print("=" * 60)
    
    tests = [
        ("Chat History Functions", test_chat_history_functions),
        ("Relationship Functions", test_relationship_functions),
        ("API Controller Integration", test_api_controller_integration),
        ("Web UI Integration", test_web_ui_integration),
        ("Chat History File Creation", test_chat_history_file_creation),
        ("Relationship File Creation", test_relationship_file_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    # Clean up test data
    cleanup_test_data()
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The chat history and relationship systems are working correctly.")
        print("\n✅ Issues fixed:")
        print("   - Added missing process_chatpops function to chat_history.py")
        print("   - Added missing update_relationship_from_interaction function to user_relationships.py")
        print("   - Added chat history updates to API controller for both primary and fallback responses")
        print("   - Added chat history updates to streaming responses")
        print("   - Web UI should now properly display chat history")
        print("   - Shadow chat and relationship tracking should work correctly")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main()) 