#!/usr/bin/env python3
"""
Test script to verify soft reset and TTS functionality.
Tests both normal operation and potential loop scenarios.
"""

import sys
import os
import json
import time
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_history_state():
    """Verify the state of both history systems"""
    print("\n📋 Checking history state...")
    
    # Check LiveLog.json
    try:
        with open("LiveLog.json", 'r') as f:
            old_history = json.load(f)
        print(f"✓ LiveLog.json has {len(old_history)} messages")
        
        # Print last few messages
        print("\nLast few messages in LiveLog.json:")
        for msg in old_history[-3:]:
            print(f"  User: {msg[0][:50]}...")
            print(f"  Assistant: {msg[1][:50]}...")
            print()
            
    except Exception as e:
        print(f"❌ Error reading LiveLog.json: {e}")
    
    # Check platform histories
    try:
        with open("Configurables/chat_histories.json", 'r') as f:
            platform_histories = json.load(f)
        print(f"\n✓ Platform histories for {len(platform_histories)} users")
        
        # Print details for webui user
        webui_key = "webui_webui_user"
        if webui_key in platform_histories:
            webui_history = platform_histories[webui_key]
            print(f"  WebUI user has {len(webui_history)} messages")
            
            # Print last few messages
            print("\nLast few WebUI messages:")
            for msg in webui_history[-3:]:
                print(f"  {msg['role']}: {msg['content'][:50]}...")
                print(f"  Timestamp: {msg['timestamp']}")
                print()
    except Exception as e:
        print(f"❌ Error reading platform histories: {e}")

def setup_test_environment():
    """Setup test environment with required settings"""
    import utils.settings as settings
    
    # Ensure required attributes exist
    if not hasattr(settings, 'rag_enabled'):
        settings.rag_enabled = False
    if not hasattr(settings, 'MODULE_RAG'):
        settings.MODULE_RAG = "OFF"
    if not hasattr(settings, 'speak_shadowchats'):
        settings.speak_shadowchats = True
    if not hasattr(settings, 'stream_chats'):
        settings.stream_chats = False
    
    return settings

def test_soft_reset():
    """Test soft reset functionality"""
    print("\n🔄 Testing soft reset...")
    
    try:
        # Setup test environment
        settings = setup_test_environment()
        
        from API.api_controller import soft_reset, ooga_history
        from utils.chat_history import add_message_to_history, get_chat_history
        
        # Add some test messages first
        print("\n1️⃣ Adding test messages...")
        test_messages = [
            ("Hello!", "Hi there! How can I help you today?"),
            ("How are you?", "I'm doing great! Thanks for asking."),
            ("Tell me a joke", "Why did the AI go to school? To improve its neural network! 😄")
        ]
        
        for user_msg, assistant_msg in test_messages:
            # Add to both history systems
            add_message_to_history("webui_user", "user", user_msg, "webui")
            add_message_to_history("webui_user", "assistant", assistant_msg, "webui")
            
            ooga_history.append([
                user_msg,
                assistant_msg,
                assistant_msg,
                [],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])
        
        print("✓ Added test messages")
        verify_history_state()
        
        # Test single soft reset
        print("\n2️⃣ Testing single soft reset...")
        soft_reset()
        print("✓ Soft reset completed")
        verify_history_state()
        
        # Wait a moment to ensure timestamps are different
        time.sleep(1)
        
        # Verify no immediate second reset
        print("\n3️⃣ Testing immediate second reset (should be blocked)...")
        soft_reset()
        print("✓ Second reset attempt completed")
        verify_history_state()
        
        # Test TTS functionality
        print("\n4️⃣ Testing TTS functionality...")
        try:
            from utils.voice import speak
            
            # Save original settings
            original_speak = settings.speak_shadowchats
            original_stream = settings.stream_chats
            
            # Test different TTS scenarios
            test_scenarios = [
                (True, True, "should speak - shadowchats enabled"),
                (True, False, "should speak - shadowchats enabled, not streaming"),
                (False, True, "should not speak - shadowchats disabled, streaming"),
                (False, False, "should speak - not streaming")
            ]
            
            for speak_setting, stream_setting, description in test_scenarios:
                settings.speak_shadowchats = speak_setting
                settings.stream_chats = stream_setting
                print(f"\nTesting TTS ({description})...")
                
                try:
                    speak("This is a test message")
                    print("✓ TTS completed")
                except Exception as e:
                    print(f"❌ TTS failed: {e}")
            
            # Restore original settings
            settings.speak_shadowchats = original_speak
            settings.stream_chats = original_stream
            
        except ImportError:
            print("⚠️ TTS tests skipped - voice module not available")
        except Exception as e:
            print(f"❌ Error during TTS tests: {e}")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Error during tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_soft_reset() 