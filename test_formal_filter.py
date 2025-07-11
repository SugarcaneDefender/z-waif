#!/usr/bin/env python3
"""
Test script for the formal filter functionality.
This script tests the configurable formal filter with different settings.
"""

import os
import sys
import json

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import settings
from utils.formal_filter import (
    is_formal_response, 
    filter_formal_response, 
    test_formal_filter,
    get_formal_filter_instruction
)

def test_formal_filter_basic():
    """Test basic formal filter functionality."""
    print("=== Testing Basic Formal Filter ===")
    
    # Test texts
    test_texts = [
        "How can I assist you today?",
        "I'm here to be of service!",
        "What can I do for you?",
        "Hey! How's it going?",
        "Hi there! What's up?",
        "How may I help you with that?",
        "To be of service, I can help you with that.",
        "Is there anything I can help you with?",
        "How can I be of assistance?",
        "What would you like me to help you with?",
        "Hey! What's on your mind?",
        "Hi! How are you doing today?"
    ]
    
    # Test with different configurations
    configs = [
        {"enabled": False, "strength": "medium"},
        {"enabled": True, "strength": "low"},
        {"enabled": True, "strength": "medium"},
        {"enabled": True, "strength": "high"}
    ]
    
    for config in configs:
        print(f"\n--- Testing with config: {config} ---")
        
        for text in test_texts:
            result = test_formal_filter(text, config)
            status = "🚫 FORMAL" if result["is_formal"] else "✅ NATURAL"
            print(f"{status}: {text}")
            if result["is_formal"] and result["replacement"]:
                print(f"   → Replacement: {result['replacement']}")

def test_custom_phrases():
    """Test custom phrases functionality."""
    print("\n=== Testing Custom Phrases ===")
    
    # Test with custom phrases
    custom_config = {
        "enabled": True,
        "strength": "medium",
        "phrases": [
            "how can i assist you",
            "to be of service",
            "what can i do for you",
            "custom phrase test"
        ],
        "patterns": [],
        "replacements": ["Hey! How's it going?"]
    }
    
    test_texts = [
        "How can I assist you today?",
        "I'm here to be of service!",
        "What can I do for you?",
        "This is a custom phrase test",
        "Hey! How's it going?",
        "Hi there! What's up?"
    ]
    
    for text in test_texts:
        result = test_formal_filter(text, custom_config)
        status = "🚫 FORMAL" if result["is_formal"] else "✅ NATURAL"
        print(f"{status}: {text}")
        if result["is_formal"] and result["replacement"]:
            print(f"   → Replacement: {result['replacement']}")

def test_custom_patterns():
    """Test custom regex patterns functionality."""
    print("\n=== Testing Custom Patterns ===")
    
    # Test with custom patterns
    custom_config = {
        "enabled": True,
        "strength": "medium",
        "phrases": [],
        "patterns": [
            r'\bcustom\s+pattern\s+test\b',
            r'\bto\s+be\s+of\s+service\b',
            r'\bhow\s+can\s+i\s+assist\b'
        ],
        "replacements": ["Hey! How's it going?"]
    }
    
    test_texts = [
        "This is a custom pattern test",
        "I'm here to be of service!",
        "How can I assist you?",
        "Hey! How's it going?",
        "Hi there! What's up?"
    ]
    
    for text in test_texts:
        result = test_formal_filter(text, custom_config)
        status = "🚫 FORMAL" if result["is_formal"] else "✅ NATURAL"
        print(f"{status}: {text}")
        if result["is_formal"] and result["replacement"]:
            print(f"   → Replacement: {result['replacement']}")

def test_replacement_modes():
    """Test different replacement modes."""
    print("\n=== Testing Replacement Modes ===")
    
    # Test with different replacement modes
    replacement_modes = ["natural", "casual", "friendly", "custom"]
    
    for mode in replacement_modes:
        print(f"\n--- Testing {mode} replacement mode ---")
        
        config = {
            "enabled": True,
            "strength": "medium",
            "replacement_mode": mode
        }
        
        formal_text = "How can I assist you today?"
        result = test_formal_filter(formal_text, config)
        
        if result["is_formal"] and result["replacement"]:
            print(f"Original: {formal_text}")
            print(f"Replacement ({mode}): {result['replacement']}")

def test_filter_formal_response():
    """Test the filter_formal_response function."""
    print("\n=== Testing filter_formal_response Function ===")
    
    test_texts = [
        "How can I assist you today?",
        "Hey! How's it going?",
        "I'm here to be of service!",
        "Hi there! What's up?"
    ]
    
    for text in test_texts:
        filtered = filter_formal_response(text)
        if filtered != text:
            print(f"Original: {text}")
            print(f"Filtered: {filtered}")
        else:
            print(f"Unchanged: {text}")

def test_formal_filter_instruction():
    """Test the formal filter instruction generation."""
    print("\n=== Testing Formal Filter Instructions ===")
    
    strengths = ["low", "medium", "high"]
    
    for strength in strengths:
        config = {"enabled": True, "strength": strength}
        instruction = get_formal_filter_instruction(config)
        print(f"\n--- {strength.upper()} strength instruction ---")
        print(instruction)

def test_settings_integration():
    """Test integration with settings module."""
    print("\n=== Testing Settings Integration ===")
    
    # Test getting config from settings
    config = settings.get_formal_filter_config()
    print(f"Current config from settings:")
    print(json.dumps(config, indent=2))
    
    # Test with settings config
    test_text = "How can I assist you today?"
    result = test_formal_filter(test_text, config)
    print(f"\nTest with settings config:")
    print(f"Text: {test_text}")
    print(f"Is formal: {result['is_formal']}")
    if result["replacement"]:
        print(f"Replacement: {result['replacement']}")

def main():
    """Run all tests."""
    print("🧪 Formal Filter Test Suite")
    print("=" * 50)
    
    try:
        test_formal_filter_basic()
        test_custom_phrases()
        test_custom_patterns()
        test_replacement_modes()
        test_filter_formal_response()
        test_formal_filter_instruction()
        test_settings_integration()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 