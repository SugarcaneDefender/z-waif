#!/usr/bin/env python3
"""
Quick Z-WAIF System Test
Tests core functionality without starting the full application
"""

import os
import sys
from dotenv import load_dotenv

# Load environment first
load_dotenv()

def test_basic_functionality():
    """Test basic system functionality"""
    print("🧪 QUICK Z-WAIF FUNCTIONALITY TEST")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing core imports...")
        import API.api_controller as api
        from utils.ai_handler import AIHandler
        from utils import settings
        print("✅ Core modules imported successfully")
        
        # Test AI Handler
        print("\n🤖 Testing AI Handler...")
        ai_handler = AIHandler()
        
        # Test contextual chatpops
        test_contexts = [
            {"platform": "personal"},
            {"platform": "twitch"},
            {"platform": "voice"}
        ]
        
        print("🎯 Testing contextual chatpops...")
        for context in test_contexts:
            chatpop = ai_handler.get_contextual_chatpop(context, "Hello!")
            platform = context["platform"]
            print(f"  {platform}: '{chatpop}'")
        
        # Test environment
        print("\n⚙️ Testing environment...")
        char_name = os.environ.get('CHAR_NAME', 'Unknown')
        api_type = os.environ.get('API_TYPE', 'Unknown')
        print(f"  Character: {char_name}")
        print(f"  API Type: {api_type}")
        
        # Test settings
        print("\n📋 Testing settings...")
        print(f"  Chatpops enabled: {settings.use_chatpops}")
        print(f"  Chatpop phrases loaded: {len(settings.chatpop_phrases)}")
        print(f"  Twitch enabled: {settings.twitch_enabled}")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✨ Z-WAIF system is ready to run!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1) 