#!/usr/bin/env python3
"""
Test script for Discord bot detection functionality.
This script tests the bot detection patterns without requiring a Discord connection.
"""

import json
import re
import os
from unittest.mock import Mock

# Import the bot detection function from the Discord module
import sys
sys.path.append('utils')
from z_waif_discord import load_bot_detection_config, is_bot_message

def create_mock_message(author_name, content, is_bot=False, display_name=None):
    """Create a mock Discord message for testing"""
    mock_author = Mock()
    mock_author.name = author_name
    mock_author.display_name = display_name or author_name
    mock_author.bot = is_bot
    
    mock_message = Mock()
    mock_message.author = mock_author
    mock_message.content = content
    mock_message.channel.name = "test-channel"
    
    return mock_message

def test_bot_detection():
    """Test various bot detection scenarios"""
    
    print("🧪 Testing Discord Bot Detection System")
    print("=" * 50)
    
    # Load configuration
    config = load_bot_detection_config()
    print(f"✅ Loaded configuration with {len(config.get('bot_flags', []))} bot flags")
    
    # Test cases
    test_cases = [
        # (author_name, content, expected_result, description)
        ("HumanUser", "Hello there!", False, "Normal human message"),
        ("ChatGPT_Bot", "Hello there!", True, "Bot in username"),
        ("Assistant", "How can I help you?", True, "Assistant in username"),
        ("NormalUser", "As an AI, I cannot do that", True, "AI language in content"),
        ("HumanUser", "I am a bot designed to help", True, "Bot language in content"),
        ("TestUser", "Assistant: Hello there!", True, "Assistant prefix in message"),
        ("User", "*nods and smiles*", True, "Action text pattern"),
        ("User", "[System] Processing request", True, "Bracket notation"),
        ("User", "<bot> Hello there!", True, "Tag notation"),
        ("User", "a a a a a a a a a a", True, "Repetitive words"),
        ("User", "Hi", True, "Very short message"),
        ("User", "x" * 2500, True, "Very long message"),
        ("Z-Waif", "Hello!", True, "Z-Waif in username"),
        ("ClaudeBot", "I'm here to help", True, "Claude in username"),
        ("HumanUser", "My training data includes...", True, "Training reference"),
        ("User", "I am programmed to...", True, "Programming reference"),
        ("RealPerson", "This is a normal conversation", False, "Normal conversation"),
    ]
    
    # Mock the client.user for the test
    import utils.z_waif_discord as discord_module
    discord_module.client.user = Mock()
    discord_module.client.user.name = "Z-Waif-Test"
    
    passed = 0
    failed = 0
    
    for author_name, content, expected, description in test_cases:
        mock_message = create_mock_message(author_name, content)
        result = is_bot_message(mock_message)
        
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | {description}")
        print(f"   Author: {author_name}")
        print(f"   Content: {content[:50]}{'...' if len(content) > 50 else ''}")
        print(f"   Expected: {expected}, Got: {result}")
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Bot detection is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the configuration.")
    
    return failed == 0

def test_configuration_customization():
    """Test that users can customize the configuration"""
    print("\n🔧 Testing Configuration Customization")
    print("=" * 50)
    
    # Test custom configuration
    custom_config = {
        "bot_detection_enabled": True,
        "bot_flags": ["custombot", "myai"],
        "ai_indicators": ["custom ai language"],
        "ignored_users": ["FriendBot"],
        "ignored_channels": ["bot-testing"],
        "detection_settings": {
            "check_username": True,
            "check_message_content": True,
            "min_message_length": 5,
            "max_message_length": 1500
        }
    }
    
    # Save custom config temporarily
    config_path = "Configurables/DiscordBotDetection.json"
    original_config = None
    
    try:
        # Backup original config
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                original_config = json.load(f)
        
        # Write custom config
        with open(config_path, 'w') as f:
            json.dump(custom_config, f, indent=2)
        
        # Reload and test
        import utils.z_waif_discord as discord_module
        reloaded_config = discord_module.load_bot_detection_config()
        
        print(f"✅ Custom bot flags: {reloaded_config.get('bot_flags', [])}")
        print(f"✅ Custom ignored users: {reloaded_config.get('ignored_users', [])}")
        print(f"✅ Custom ignored channels: {reloaded_config.get('ignored_channels', [])}")
        
        # Test custom detection
        mock_message = create_mock_message("CustomBot", "Hello!")
        result = is_bot_message(mock_message)
        print(f"✅ Custom bot detection: {result}")
        
    finally:
        # Restore original config
        if original_config:
            with open(config_path, 'w') as f:
                json.dump(original_config, f, indent=2)
        elif os.path.exists(config_path):
            os.remove(config_path)

def main():
    """Run all tests"""
    print("🚀 Discord Bot Detection Test Suite")
    print("=" * 60)
    
    # Test basic functionality
    success = test_bot_detection()
    
    # Test configuration customization
    test_configuration_customization()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
        print("✅ The Discord bot detection system is ready to prevent infinite loops.")
    else:
        print("⚠️ Some tests failed. Please check the configuration.")
    
    print("\n📝 Usage Instructions:")
    print("1. The bot detection is automatically enabled when the Discord module starts")
    print("2. Customize detection patterns in Configurables/DiscordBotDetection.json")
    print("3. Add specific bot names to 'ignored_users' list")
    print("4. Add specific channels to 'ignored_channels' list")
    print("5. Adjust detection sensitivity in 'detection_settings'")

if __name__ == "__main__":
    main() 