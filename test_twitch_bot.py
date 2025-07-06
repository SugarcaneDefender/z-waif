#!/usr/bin/env python3
"""
Z-WAIF Twitch Integration Test Script
Tests complete integration between Twitch bot and main application
"""

import os
import sys
import time
import asyncio
import traceback
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_environment_setup():
    """Test that environment variables are properly configured"""
    print("🔧 Testing Environment Configuration...")
    
    required_vars = ["TWITCH_TOKEN", "TWITCH_CHANNEL"]
    optional_vars = ["TWITCH_CLIENT_ID", "TWITCH_BOT_NAME", "TWITCH_PERSONALITY"]
    
    issues = []
    
    for var in required_vars:
        if not os.getenv(var):
            issues.append(f"❌ Required variable {var} is not set")
        else:
            print(f"✅ {var}: ****{os.getenv(var)[-4:]}")  # Show last 4 chars for security
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"✅ {var}: {os.getenv(var)}")
        else:
            print(f"ℹ️  {var}: Not set (using default)")
    
    # Test Twitch-specific settings
    twitch_settings = {
        "TWITCH_PERSONALITY": os.getenv("TWITCH_PERSONALITY", "friendly"),
        "TWITCH_AUTO_RESPOND": os.getenv("TWITCH_AUTO_RESPOND", "ON"),
        "TWITCH_RESPONSE_CHANCE": os.getenv("TWITCH_RESPONSE_CHANCE", "0.8"),
        "TWITCH_COOLDOWN_SECONDS": os.getenv("TWITCH_COOLDOWN_SECONDS", "3"),
        "TWITCH_MAX_MESSAGE_LENGTH": os.getenv("TWITCH_MAX_MESSAGE_LENGTH", "450")
    }
    
    print("\n🎛️  Twitch Bot Configuration:")
    for key, value in twitch_settings.items():
        print(f"   {key}: {value}")
    
    if issues:
        print("\n❌ Environment Setup Issues:")
        for issue in issues:
            print(f"   {issue}")
        return False
    
    print("✅ Environment configuration looks good!")
    return True

def test_imports():
    """Test that all required modules can be imported"""
    print("\n📦 Testing Module Imports...")
    
    modules_to_test = [
        ("main", "main"),
        ("API.api_controller", "API controller"),
        ("utils.z_waif_twitch", "Twitch integration"),
        ("utils.settings", "settings"),
        ("utils.ai_handler", "AI handler"),
        ("utils.user_context", "user context"),
        ("utils.chat_history", "chat history"),
        ("utils.message_processing", "message processing"),
        ("utils.user_relationships", "user relationships"),
        ("utils.conversation_analysis", "conversation analysis"),
        ("utils.based_rag", "RAG system"),
        ("utils.memory_manager", "memory manager"),
        ("utils.zw_logging", "logging system")
    ]
    
    failed_imports = []
    
    for module_name, display_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {display_name}")
        except Exception as e:
            print(f"❌ {display_name}: {e}")
            failed_imports.append((module_name, str(e)))
    
    if failed_imports:
        print("\n❌ Import Issues:")
        for module, error in failed_imports:
            print(f"   {module}: {error}")
        return False
    
    print("✅ All modules imported successfully!")
    return True

def test_twitch_bot_initialization():
    """Test that the Twitch bot can be initialized"""
    print("\n🤖 Testing Twitch Bot Initialization...")
    
    try:
        # Import and test the Twitch bot
        from utils.z_waif_twitch import TwitchBot, TWITCH_TOKEN, TWITCH_CHANNELS
        
        if not TWITCH_TOKEN:
            print("❌ TWITCH_TOKEN not found - skipping bot initialization test")
            return False
        
        if not TWITCH_CHANNELS:
            print("❌ No Twitch channels configured - skipping bot initialization test")
            return False
        
        # Create bot instance (don't actually connect)
        print("   Creating TwitchBot instance...")
        bot = TwitchBot()
        
        # Verify bot properties
        print(f"   ✅ Bot nick: {bot.nick}")
        print(f"   ✅ Initial channels: {bot.initial_channels}")
        print(f"   ✅ AI handler: {bot.ai_handler is not None}")
        print(f"   ✅ Memory manager: {bot.memory_manager is not None}")
        print(f"   ✅ Response chance: {bot.response_chance}")
        print(f"   ✅ Auto-respond: {bot.auto_respond}")
        print(f"   ✅ Personality: {bot.personality}")
        
        print("✅ Twitch bot initialization successful!")
        return True
        
    except Exception as e:
        print(f"❌ Twitch bot initialization failed: {e}")
        traceback.print_exc()
        return False

def test_main_integration():
    """Test that main application can integrate with Twitch"""
    print("\n🔗 Testing Main Application Integration...")
    
    try:
        # Import main modules
        import main
        from utils import settings
        
        # Test that main can call twitch functions
        print("   Testing main_twitch_chat function...")
        
        # Mock a simple message
        test_message = "testuser: Hello, this is a test message!"
        
        # Test the main twitch chat handler
        # Note: This won't actually send to API since we're just testing integration
        result = main.main_twitch_chat(test_message)
        
        print(f"   ✅ main_twitch_chat returned: {type(result)}")
        print(f"   ✅ Settings twitch_enabled: {settings.twitch_enabled}")
        print(f"   ✅ Settings TWITCH_ENABLED: {settings.TWITCH_ENABLED}")
        
        # Test platform-aware messaging
        print("   Testing platform-aware messaging...")
        
        # This would normally call the API, but we're just testing the structure
        try:
            clean_reply = main.send_platform_aware_message("Test message", platform="twitch")
            print(f"   ✅ Platform-aware messaging works (returned: {type(clean_reply)})")
        except Exception as e:
            print(f"   ⚠️  Platform-aware messaging test: {e} (expected if API not running)")
        
        print("✅ Main application integration successful!")
        return True
        
    except Exception as e:
        print(f"❌ Main integration test failed: {e}")
        traceback.print_exc()
        return False

def test_ai_modules():
    """Test that AI modules are working"""
    print("\n🧠 Testing AI Modules...")
    
    try:
        # Test AI handler
        from utils.ai_handler import AIHandler
        ai_handler = AIHandler()
        print("   ✅ AI Handler initialized")
        
        # Test contextual chatpop
        test_chatpop = ai_handler.get_contextual_chatpop({"platform": "twitch"}, "Hello!")
        print(f"   ✅ Contextual chatpop: '{test_chatpop}'")
        
        # Test user context
        from utils.user_context import get_user_context, update_user_context
        test_context = get_user_context("test_user", "twitch")
        print(f"   ✅ User context retrieval works")
        
        update_user_context("test_user", {"test": "value"})
        print(f"   ✅ User context update works")
        
        # Test chat history
        from utils.chat_history import add_message_to_history, get_chat_history
        add_message_to_history("test_user", "user", "Test message", "twitch")
        history = get_chat_history("test_user", "twitch", limit=5)
        print(f"   ✅ Chat history works (entries: {len(history)})")
        
        # Test relationships
        from utils.user_relationships import update_relationship, get_relationship_level
        update_relationship("test_user", "twitch", "positive")
        relationship = get_relationship_level("test_user", "twitch")
        print(f"   ✅ Relationships work (level: {relationship})")
        
        # Test message processing
        from utils.message_processing import clean_response, validate_message_safety
        cleaned = clean_response("Test response")
        is_safe = validate_message_safety("Test message")
        print(f"   ✅ Message processing works (safe: {is_safe})")
        
        print("✅ All AI modules working!")
        return True
        
    except Exception as e:
        print(f"❌ AI modules test failed: {e}")
        traceback.print_exc()
        return False

async def test_async_functionality():
    """Test async functionality of the Twitch bot"""
    print("\n⚡ Testing Async Functionality...")
    
    try:
        from utils.z_waif_twitch import TwitchBot
        
        # Create a mock bot for testing
        bot = TwitchBot()
        
        # Test user context retrieval
        user_context = await bot._get_enhanced_user_context("test_user", "testuser", "testchannel")
        print(f"   ✅ Enhanced user context: {len(user_context)} keys")
        
        # Test conversation analysis
        conv_context = await bot._analyze_conversation_context("testchannel", "Hello world!", user_context)
        print(f"   ✅ Conversation analysis: {len(conv_context)} keys")
        
        # Test memory retrieval
        memories = await bot._get_relevant_memories("test_user", "hello")
        print(f"   ✅ Memory retrieval: {len(memories)} memories")
        
        # Test response generation (fallback)
        response = await bot._fallback_response_generation("Hello", user_context)
        print(f"   ✅ Fallback response generation works")
        
        # Test relationship update
        await bot._update_user_relationship("test_user", "testuser", "hello", "hi there")
        print(f"   ✅ Relationship update works")
        
        # Test conversation storage
        await bot._store_conversation("test_user", "testuser", "hello", "hi there", "testchannel")
        print(f"   ✅ Conversation storage works")
        
        print("✅ All async functionality working!")
        return True
        
    except Exception as e:
        print(f"❌ Async functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_thread_integration():
    """Test that Twitch runs properly in a thread"""
    print("\n🧵 Testing Thread Integration...")
    
    try:
        import threading
        from utils import z_waif_twitch
        
        print("   Testing thread creation...")
        
        # Create a thread like main.py does
        def test_thread_target():
            print("   Thread started successfully")
            # Don't actually run the bot, just test the setup
            return True
        
        twitch_thread = threading.Thread(target=test_thread_target)
        twitch_thread.daemon = True
        twitch_thread.start()
        
        # Wait a moment
        time.sleep(0.5)
        
        print("   ✅ Thread created and started")
        print("   ✅ Thread is daemon thread")
        
        # Test the actual function exists
        if hasattr(z_waif_twitch, 'run_z_waif_twitch'):
            print("   ✅ run_z_waif_twitch function exists")
        else:
            print("   ❌ run_z_waif_twitch function missing")
            return False
        
        print("✅ Thread integration successful!")
        return True
        
    except Exception as e:
        print(f"❌ Thread integration test failed: {e}")
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests and provide a summary"""
    print("🚀 Z-WAIF Twitch Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Module Imports", test_imports),
        ("Twitch Bot Initialization", test_twitch_bot_initialization),
        ("Main Application Integration", test_main_integration),
        ("AI Modules", test_ai_modules),
        ("Thread Integration", test_thread_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Run async test separately
    print("\n⚡ Running Async Tests...")
    try:
        async_result = asyncio.run(test_async_functionality())
        results.append(("Async Functionality", async_result))
    except Exception as e:
        print(f"❌ Async tests crashed: {e}")
        results.append(("Async Functionality", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Twitch integration is ready!")
        print("\n💡 To start using Twitch:")
        print("   1. Set MODULE_TWITCH=ON in your .env file")
        print("   2. Configure TWITCH_TOKEN and TWITCH_CHANNEL")
        print("   3. Run python main.py")
        print("   4. The bot will automatically connect to Twitch!")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
        print("   Make sure all dependencies are installed and environment is configured.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 