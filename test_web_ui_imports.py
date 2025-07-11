#!/usr/bin/env python3
"""
Test script to verify Web UI imports and functionality
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_web_ui_imports():
    """Test that all Web UI imports work correctly"""
    
    print("=== Testing Web UI Imports ===")
    
    # Test basic imports
    try:
        import gradio as gr
        print("✅ Gradio import successful")
    except ImportError as e:
        print(f"❌ Gradio import failed: {e}")
        return False
    
    try:
        import colorama
        print("✅ Colorama import successful")
    except ImportError as e:
        print(f"❌ Colorama import failed: {e}")
        return False
    
    # Test utils imports
    try:
        from utils import zw_logging
        print("✅ zw_logging import successful")
    except ImportError as e:
        print(f"❌ zw_logging import failed: {e}")
        return False
    
    try:
        from utils import settings
        print("✅ settings import successful")
    except ImportError as e:
        print(f"❌ settings import failed: {e}")
        return False
    
    try:
        from utils import hotkeys
        print("✅ hotkeys import successful")
    except ImportError as e:
        print(f"❌ hotkeys import failed: {e}")
        return False
    
    try:
        from utils import tag_task_controller
        print("✅ tag_task_controller import successful")
    except ImportError as e:
        print(f"❌ tag_task_controller import failed: {e}")
        return False
    
    try:
        from utils import voice
        print("✅ voice import successful")
    except ImportError as e:
        print(f"❌ voice import failed: {e}")
        return False
    
    # Test chat history import with error handling
    try:
        from utils import chat_history
        print("✅ chat_history import successful")
    except ImportError as e:
        print(f"⚠️ chat_history import failed (will use fallback): {e}")
    
    # Test API imports
    try:
        import API.api_controller
        print("✅ API.api_controller import successful")
    except ImportError as e:
        print(f"❌ API.api_controller import failed: {e}")
        return False
    
    try:
        import API.character_card
        print("✅ API.character_card import successful")
    except ImportError as e:
        print(f"❌ API.character_card import failed: {e}")
        return False
    
    # Test fallback API import with error handling
    try:
        from API.fallback_api import (
            discover_models, try_fallbacks, get_model_info, get_system_info, 
            check_model_compatibility, switch_fallback_model,
            get_available_vram_gb, estimate_model_vram_requirement
        )
        print("✅ API.fallback_api import successful")
    except ImportError as e:
        print(f"⚠️ API.fallback_api import failed (will use fallback): {e}")
    
    # Test Web UI module import
    try:
        import utils.web_ui
        print("✅ utils.web_ui import successful")
    except ImportError as e:
        print(f"❌ utils.web_ui import failed: {e}")
        return False
    
    print("\n=== Testing Web UI Functions ===")
    
    # Test basic Web UI functions
    try:
        from utils.web_ui import shadowchats_button_click
        result = shadowchats_button_click()
        print(f"✅ shadowchats_button_click: {result}")
    except Exception as e:
        print(f"❌ shadowchats_button_click failed: {e}")
    
    try:
        from utils.web_ui import update_chat
        result = update_chat()
        print(f"✅ update_chat: {len(result) if isinstance(result, list) else 'error'}")
    except Exception as e:
        print(f"❌ update_chat failed: {e}")
    
    try:
        from utils.web_ui import get_system_status
        result = get_system_status()
        print(f"✅ get_system_status: {result[:100] if isinstance(result, str) else 'success'}")
    except Exception as e:
        print(f"❌ get_system_status failed: {e}")
    
    print("\n=== Web UI Import Test Complete ===")
    return True

def test_web_ui_launch():
    """Test Web UI launch function"""
    
    print("\n=== Testing Web UI Launch ===")
    
    try:
        from utils.web_ui import launch_demo
        print("✅ launch_demo function import successful")
        
        # Don't actually launch, just test the function exists
        print("✅ Web UI launch function is available")
        return True
        
    except Exception as e:
        print(f"❌ Web UI launch test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Web UI functionality test...")
    
    # Test imports
    imports_ok = test_web_ui_imports()
    
    # Test launch function
    launch_ok = test_web_ui_launch()
    
    if imports_ok and launch_ok:
        print("\n🎉 All Web UI tests passed!")
        print("✅ Web UI should work correctly")
    else:
        print("\n❌ Some Web UI tests failed")
        print("⚠️ There may be issues with the Web UI")
    
    print("\n=== Test Complete ===") 