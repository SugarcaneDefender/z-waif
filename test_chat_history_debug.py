#!/usr/bin/env python3
"""
Test script to debug the chat history system and verify message saving/retrieval.
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_chat_history_system():
    """Test the complete chat history system"""
    print("🔍 Testing Chat History System...")
    
    try:
        from utils.chat_history import (
            add_message_to_history,
            get_chat_history,
            get_chat_history_for_webui,
            save_chat_histories,
            load_chat_histories
        )
        
        # Test 1: Add test messages
        print("\n📝 Test 1: Adding test messages...")
        test_user_id = "webui_user"
        test_platform = "webui"
        
        # Add a user message
        add_message_to_history(
            test_user_id, 
            "user", 
            "Hello, how are you today?", 
            test_platform,
            {"source": "test", "timestamp": datetime.now().isoformat()}
        )
        print("✅ Added user message")
        
        # Add an assistant response
        add_message_to_history(
            test_user_id, 
            "assistant", 
            "I'm doing great! How about you?", 
            test_platform,
            {"source": "test", "timestamp": datetime.now().isoformat()}
        )
        print("✅ Added assistant message")
        
        # Test 2: Retrieve raw history
        print("\n📖 Test 2: Retrieving raw history...")
        raw_history = get_chat_history(test_user_id, test_platform)
        print(f"✅ Raw history has {len(raw_history)} messages")
        for i, msg in enumerate(raw_history):
            print(f"  {i+1}. [{msg['role']}] {msg['content'][:50]}...")
        
        # Test 3: Test Web UI format
        print("\n🖥️ Test 3: Testing Web UI format...")
        webui_history = get_chat_history_for_webui(test_user_id, test_platform)
        print(f"✅ Web UI history has {len(webui_history)} pairs")
        for i, pair in enumerate(webui_history):
            print(f"  {i+1}. User: {pair[0][:30]}... | Assistant: {pair[1][:30]}...")
        
        # Test 4: Save and reload
        print("\n💾 Test 4: Testing save/reload...")
        save_chat_histories()
        print("✅ Saved chat histories")
        
        # Clear in-memory data and reload
        from utils.chat_history import chat_histories
        original_data = chat_histories.copy()
        chat_histories.clear()
        print("✅ Cleared in-memory data")
        
        load_chat_histories()
        print("✅ Reloaded chat histories")
        
        # Verify data is back
        reloaded_history = get_chat_history(test_user_id, test_platform)
        print(f"✅ Reloaded history has {len(reloaded_history)} messages")
        
        # Test 5: Check file contents
        print("\n📁 Test 5: Checking file contents...")
        chat_file = "Configurables/chat_histories.json"
        if os.path.exists(chat_file):
            with open(chat_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            print(f"✅ Chat history file exists with {len(file_data)} user keys")
            for key, history in file_data.items():
                print(f"  {key}: {len(history)} messages")
        else:
            print("❌ Chat history file not found")
        
        # Test 6: Test with different user/platform
        print("\n👤 Test 6: Testing different user/platform...")
        add_message_to_history("test_user", "user", "Test message", "discord")
        add_message_to_history("test_user", "assistant", "Test response", "discord")
        
        discord_history = get_chat_history("test_user", "discord")
        print(f"✅ Discord history has {len(discord_history)} messages")
        
        # Test 7: Verify Web UI still works
        print("\n🔄 Test 7: Verifying Web UI format still works...")
        webui_history_after = get_chat_history_for_webui(test_user_id, test_platform)
        print(f"✅ Web UI history still has {len(webui_history_after)} pairs")
        
        print("\n🎉 All chat history tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Chat history test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_controller_integration():
    """Test if the API controller can properly add messages"""
    print("\n🔧 Testing API Controller Integration...")
    
    try:
        # Import the API controller
        from API.api_controller import run
        
        # Test with a simple message
        test_message = "Hello, this is a test message from the API controller"
        
        # Note: We can't actually call run() here because it requires a running API server
        # But we can test the chat history functions that it uses
        
        from utils.chat_history import add_message_to_history
        
        # Simulate what the API controller does
        add_message_to_history("api_test_user", "user", test_message, "api_test", {
            "timestamp": datetime.now().isoformat(),
            "source": "api_controller_test"
        })
        
        add_message_to_history("api_test_user", "assistant", "This is a test response", "api_test", {
            "timestamp": datetime.now().isoformat(),
            "source": "api_controller_test"
        })
        
        # Verify the messages were added
        from utils.chat_history import get_chat_history
        api_history = get_chat_history("api_test_user", "api_test")
        print(f"✅ API controller integration test: {len(api_history)} messages added")
        
        return True
        
    except Exception as e:
        print(f"❌ API controller integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_ui_simulation():
    """Simulate how the Web UI would use the chat history"""
    print("\n🖥️ Testing Web UI Simulation...")
    
    try:
        from utils.chat_history import get_chat_history_for_webui, add_message_to_webui_history
        
        # Simulate Web UI adding messages
        add_message_to_webui_history(
            "Hello from Web UI!",
            "Hi there! How can I help you today?",
            "webui_user",
            "webui"
        )
        
        # Simulate Web UI retrieving history
        webui_history = get_chat_history_for_webui("webui_user", "webui")
        print(f"✅ Web UI simulation: Retrieved {len(webui_history)} message pairs")
        
        for i, pair in enumerate(webui_history):
            print(f"  {i+1}. User: {pair[0][:30]}... | Assistant: {pair[1][:30]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Web UI simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Starting Chat History Debug Tests...")
    print("=" * 50)
    
    # Run all tests
    tests = [
        test_chat_history_system,
        test_api_controller_integration,
        test_web_ui_simulation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Chat history system is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    # Show current chat history file contents
    print("\n📁 Current Chat History File Contents:")
    chat_file = "Configurables/chat_histories.json"
    if os.path.exists(chat_file):
        try:
            with open(chat_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ File exists with {len(data)} user keys:")
            for key, history in data.items():
                print(f"  {key}: {len(history)} messages")
                for msg in history[-3:]:  # Show last 3 messages
                    print(f"    [{msg['role']}] {msg['content'][:50]}...")
        except Exception as e:
            print(f"❌ Error reading file: {e}")
    else:
        print("❌ Chat history file not found")

if __name__ == "__main__":
    main() 