#!/usr/bin/env python3
"""
Test script to verify autochat and mic toggle functionality
This script helps test the fix for the autochat/mic toggle conflict
"""

import time
import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_autochat_mic_logic():
    """Test the autochat and mic toggle logic"""
    
    print("Testing Autochat and Mic Toggle Logic")
    print("=" * 50)
    
    try:
        from utils import hotkeys
        
        # Test initial states
        print(f"Initial states:")
        print(f"  Autochat: {hotkeys.get_autochat_toggle()}")
        print(f"  Mic: {hotkeys.get_speak_input()}")
        print()
        
        # Test 1: Toggle autochat ON
        print("Test 1: Toggle autochat ON")
        hotkeys.input_toggle_autochat_from_ui()
        print(f"  Autochat: {hotkeys.get_autochat_toggle()}")
        print(f"  Mic: {hotkeys.get_speak_input()}")
        print()
        
        # Test 2: Simulate a chat command
        print("Test 2: Simulate chat command processing")
        command = hotkeys.get_command_nonblocking()
        print(f"  Command returned: {command}")
        
        if command == "CHAT":
            print("  ✓ Autochat correctly triggered CHAT command")
        else:
            print(f"  ✗ Expected CHAT command, got: {command}")
        print()
        
        # Test 3: Simulate stack_wipe_inputs (should preserve autochat state)
        print("Test 3: Simulate stack_wipe_inputs")
        hotkeys.stack_wipe_inputs()
        print(f"  After wipe - Autochat: {hotkeys.get_autochat_toggle()}")
        print(f"  After wipe - Mic: {hotkeys.get_speak_input()}")
        
        if hotkeys.get_autochat_toggle() and hotkeys.get_speak_input():
            print("  ✓ Autochat and mic states preserved correctly")
        else:
            print("  ✗ States not preserved correctly")
        print()
        
        # Test 4: Toggle autochat OFF
        print("Test 4: Toggle autochat OFF")
        hotkeys.input_toggle_autochat_from_ui()
        print(f"  Autochat: {hotkeys.get_autochat_toggle()}")
        print(f"  Mic: {hotkeys.get_speak_input()}")
        print()
        
        # Test 5: Manual mic toggle
        print("Test 5: Manual mic toggle")
        hotkeys.speak_input_toggle_from_ui()
        print(f"  Mic: {hotkeys.get_speak_input()}")
        print()
        
        # Test 6: Reset states
        print("Test 6: Reset to clean state")
        hotkeys.reset_mic_state()
        print(f"  Final - Autochat: {hotkeys.get_autochat_toggle()}")
        print(f"  Final - Mic: {hotkeys.get_speak_input()}")
        print()
        
        print("✓ All tests completed!")
        print("\nTo test in the actual application:")
        print("1. Start Z-WAIF")
        print("2. Toggle Auto-Chat ON - mic should automatically enable")
        print("3. Speak - it should record and respond")
        print("4. Toggle Auto-Chat OFF - mic state should be preserved")
        print("5. Toggle Auto-Chat ON again - should work properly")
        
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Make sure you're running this from the Z-WAIF project directory")
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    test_autochat_mic_logic() 