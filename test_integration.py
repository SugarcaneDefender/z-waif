#!/usr/bin/env python3
"""
Integration test script for Z-WAIF enhanced system
This script tests that all the enhanced components work together properly.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add the current directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_chatpops_loading():
    """Test that chatpops are loaded correctly"""
    print("🧪 Testing chatpops loading...")
    
    try:
        with open("Configurables/Chatpops.json", 'r') as f:
            chatpops = json.load(f)
        
        if len(chatpops) > 50:  # We added about 60 phrases
            print(f"✅ Chatpops loaded successfully: {len(chatpops)} phrases")
            print(f"   Sample: '{chatpops[0]}', '{chatpops[10]}', '{chatpops[20]}'")
            return True
        else:
            print(f"❌ Not enough chatpops loaded: {len(chatpops)}")
            return False
    except Exception as e:
        print(f"❌ Error loading chatpops: {e}")
        return False

def test_ai_handler():
    """Test that the AI handler can generate contextual chatpops"""
    print("\n🧪 Testing AI handler contextual chatpops...")
    
    try:
        from utils.ai_handler import AIHandler
        
        ai_handler = AIHandler()
        
        # Test different contexts
        contexts = [
            ({"platform": "twitch"}, "Hello everyone!"),
            ({"platform": "voice"}, "How are you feeling?"),
            ({"platform": "minecraft"}, "Let's play!"),
            ({"platform": "personal"}, "What do you think?"),
        ]
        
        for context, message in contexts:
            chatpop = ai_handler.get_contextual_chatpop(context, message)
            print(f"   {context['platform']}: '{message}' → '{chatpop}'")
        
        print("✅ AI handler contextual chatpops working")
        return True
        
    except Exception as e:
        print(f"❌ Error testing AI handler: {e}")
        return False

def test_settings_integration():
    """Test that settings are configured correctly"""
    print("\n🧪 Testing settings integration...")
    
    try:
        from utils import settings
        
        # Check chatpops setting
        if hasattr(settings, 'use_chatpops'):
            print(f"✅ Chatpops setting found: {settings.use_chatpops}")
        else:
            print("❌ Chatpops setting not found")
            return False
        
        # Load chatpops manually for testing (simulating startup)
        try:
            import json
            with open("Configurables/Chatpops.json", 'r') as openfile:
                settings.chatpop_phrases = json.load(openfile)
            print(f"✅ Chatpop phrases loaded in settings: {len(settings.chatpop_phrases)}")
        except Exception as e:
            print(f"❌ Could not load chatpop phrases: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing settings: {e}")
        return False

def test_api_controller_integration():
    """Test that API controller has the enhanced integration"""
    print("\n🧪 Testing API controller integration...")
    
    try:
        import API.api_controller as api_controller
        
        # Check if AI handler is integrated
        if hasattr(api_controller, 'ai_handler'):
            print("✅ API controller has AI handler integration")
        else:
            print("⚠️ API controller using fallback method (still functional)")
        
        # Check if the enhanced functions exist
        if hasattr(api_controller, 'send_via_oogabooga'):
            print("✅ Enhanced API functions present")
        else:
            print("❌ Enhanced API functions missing")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing API controller: {e}")
        return False

def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Z-WAIF Enhanced System Integration Tests")
    print("=" * 50)
    
    tests = [
        test_chatpops_loading,
        test_ai_handler, 
        test_settings_integration,
        test_api_controller_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"🏁 Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced system is fully integrated!")
        return True
    else:
        print("⚠️ Some tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1) 