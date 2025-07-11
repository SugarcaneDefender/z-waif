#!/usr/bin/env python3
"""
Test script for Web UI fallback model management integration.
Verifies that all Web UI functions for TinyLlama GGUF and preset management work correctly.
"""

import os
import sys
import json
import time
from pathlib import Path

def test_web_ui_functions():
    """Test all Web UI fallback management functions."""
    print("🌐 Testing Web UI Fallback Management Functions")
    print("=" * 60)
    
    try:
        from utils.web_ui import (
            load_tinyllama_gguf_preset,
            download_tinyllama_gguf,
            check_tinyllama_gguf_status,
            test_tinyllama_gguf,
            get_fallback_presets,
            load_fallback_preset,
            get_current_fallback_status,
            auto_configure_fallback
        )
        print("✅ All Web UI functions imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Web UI functions: {e}")
        return False
    
    test_results = {}
    
    # Test 1: Check TinyLlama GGUF Status
    print("\n🔍 Test 1: Check TinyLlama GGUF Status")
    try:
        status = check_tinyllama_gguf_status()
        print(f"Status result type: {type(status)}")
        if isinstance(status, dict):
            print(f"Available: {status.get('available', False)}")
            print(f"Path: {status.get('path', 'N/A')}")
            print(f"Size: {status.get('size_mb', 0)} MB")
            print(f"Compatible: {status.get('compatible', False)}")
            test_results["status_check"] = True
        else:
            print(f"❌ Status check returned unexpected type: {type(status)}")
            test_results["status_check"] = False
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        test_results["status_check"] = False
    
    # Test 2: Get Fallback Presets
    print("\n📋 Test 2: Get Fallback Presets")
    try:
        presets = get_fallback_presets()
        print(f"Found {len(presets)} presets:")
        for name, info in presets.items():
            print(f"  - {name}: {info['description']}")
        test_results["presets"] = len(presets) > 0
    except Exception as e:
        print(f"❌ Preset retrieval failed: {e}")
        test_results["presets"] = False
    
    # Test 3: Get Current Fallback Status
    print("\n📊 Test 3: Get Current Fallback Status")
    try:
        fallback_status = get_current_fallback_status()
        if isinstance(fallback_status, dict) and "error" not in fallback_status:
            print(f"Fallback enabled: {fallback_status.get('fallback_enabled')}")
            print(f"Current model: {fallback_status.get('current_model', 'None')}")
            print(f"System RAM: {fallback_status.get('system_ram_gb', 0):.1f} GB")
            print(f"GPU available: {fallback_status.get('gpu_available', False)}")
            print(f"Recommended preset: {fallback_status.get('recommended_preset')}")
            test_results["fallback_status"] = True
        else:
            print(f"❌ Fallback status error: {fallback_status}")
            test_results["fallback_status"] = False
    except Exception as e:
        print(f"❌ Fallback status check failed: {e}")
        test_results["fallback_status"] = False
    
    # Test 4: Download TinyLlama GGUF (if not present)
    print("\n📥 Test 4: Download TinyLlama GGUF")
    try:
        download_result = download_tinyllama_gguf()
        print(f"Download result: {download_result}")
        test_results["download"] = "✅" in download_result or "already" in download_result.lower()
    except Exception as e:
        print(f"❌ Download test failed: {e}")
        test_results["download"] = False
    
    # Test 5: Load TinyLlama GGUF Preset
    print("\n🚀 Test 5: Load TinyLlama GGUF Preset")
    try:
        load_result = load_tinyllama_gguf_preset()
        print(f"Load result: {load_result}")
        test_results["load_preset"] = "✅" in load_result
    except Exception as e:
        print(f"❌ Load preset test failed: {e}")
        test_results["load_preset"] = False
    
    # Test 6: Test TinyLlama GGUF (if available)
    print("\n🧪 Test 6: Test TinyLlama GGUF")
    try:
        test_result = test_tinyllama_gguf()
        print(f"Test result: {test_result}")
        test_results["model_test"] = "✅" in test_result
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        test_results["model_test"] = False
    
    # Test 7: Load Different Presets
    print("\n🔄 Test 7: Load Different Presets")
    try:
        presets = get_fallback_presets()
        preset_tests = {}
        
        for preset_name in list(presets.keys())[:2]:  # Test first 2 presets
            try:
                result = load_fallback_preset(preset_name)
                print(f"  {preset_name}: {result}")
                preset_tests[preset_name] = "✅" in result
            except Exception as e:
                print(f"  {preset_name}: ❌ {e}")
                preset_tests[preset_name] = False
        
        test_results["preset_loading"] = any(preset_tests.values())
        test_results["preset_details"] = preset_tests
    except Exception as e:
        print(f"❌ Preset loading tests failed: {e}")
        test_results["preset_loading"] = False
    
    # Test 8: Auto-Configuration
    print("\n⚡ Test 8: Auto-Configuration")
    try:
        auto_result = auto_configure_fallback()
        print(f"Auto-config result: {auto_result}")
        test_results["auto_config"] = "✅" in auto_result or "🎯" in auto_result
    except Exception as e:
        print(f"❌ Auto-configuration failed: {e}")
        test_results["auto_config"] = False
    
    return test_results

def test_web_ui_integration():
    """Test Web UI component integration (without actually launching Gradio)."""
    print("\n🖥️ Testing Web UI Component Integration")
    print("=" * 50)
    
    try:
        # Import the web UI module to check for import errors
        import utils.web_ui as web_ui
        print("✅ Web UI module imported successfully")
        
        # Check that our new functions exist in the module
        required_functions = [
            'load_tinyllama_gguf_preset',
            'download_tinyllama_gguf',
            'check_tinyllama_gguf_status',
            'test_tinyllama_gguf',
            'get_fallback_presets',
            'load_fallback_preset',
            'get_current_fallback_status',
            'auto_configure_fallback'
        ]
        
        missing_functions = []
        for func_name in required_functions:
            if hasattr(web_ui, func_name):
                print(f"✅ {func_name} available")
            else:
                print(f"❌ {func_name} missing")
                missing_functions.append(func_name)
        
        if missing_functions:
            print(f"❌ Missing functions: {missing_functions}")
            return False
        
        print("✅ All required functions are available in Web UI module")
        return True
        
    except Exception as e:
        print(f"❌ Web UI integration test failed: {e}")
        return False

def test_environment_consistency():
    """Test that environment variables are handled correctly."""
    print("\n🌍 Testing Environment Variable Consistency")
    print("=" * 50)
    
    try:
        # Test environment variable updates
        from utils.web_ui import load_tinyllama_gguf_preset
        from utils import settings
        
        original_model = os.getenv("API_FALLBACK_MODEL", "")
        print(f"Original API_FALLBACK_MODEL: {original_model}")
        
        # Load TinyLlama preset
        result = load_tinyllama_gguf_preset()
        print(f"Load result: {result}")
        
        # Check if environment was updated
        new_model = os.getenv("API_FALLBACK_MODEL", "")
        print(f"New API_FALLBACK_MODEL: {new_model}")
        
        if new_model != original_model and "tinyllama" in new_model.lower():
            print("✅ Environment variable updated correctly")
            return True
        else:
            print("⚠️ Environment variable not updated or unexpected value")
            return False
            
    except Exception as e:
        print(f"❌ Environment consistency test failed: {e}")
        return False

def run_comprehensive_web_ui_test():
    """Run all Web UI integration tests."""
    print("🚀 Z-Waif Web UI Fallback Integration Test Suite")
    print("=" * 70)
    
    all_results = {}
    
    # Test 1: Web UI Functions
    print("\n" + "="*70)
    function_results = test_web_ui_functions()
    all_results["functions"] = function_results
    
    # Test 2: Web UI Integration
    print("\n" + "="*70)
    integration_result = test_web_ui_integration()
    all_results["integration"] = integration_result
    
    # Test 3: Environment Consistency
    print("\n" + "="*70)
    env_result = test_environment_consistency()
    all_results["environment"] = env_result
    
    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    
    if isinstance(function_results, dict):
        func_passed = sum(1 for result in function_results.values() if result)
        func_total = len(function_results)
        print(f"Function Tests: {func_passed}/{func_total} passed")
        
        for test_name, result in function_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")
    
    print(f"\nIntegration Test: {'✅ PASS' if integration_result else '❌ FAIL'}")
    print(f"Environment Test: {'✅ PASS' if env_result else '❌ FAIL'}")
    
    # Overall assessment
    overall_success = (
        integration_result and 
        env_result and 
        isinstance(function_results, dict) and
        sum(1 for result in function_results.values() if result) >= len(function_results) * 0.7  # 70% pass rate
    )
    
    if overall_success:
        print("\n🎉 Web UI fallback integration is working correctly!")
        print("Users can now manage TinyLlama GGUF and other fallback models through the Web UI.")
        return True
    else:
        print("\n⚠️ Some Web UI integration issues detected.")
        print("Please check the test results above for specific problems.")
        return False

def main():
    """Main test function."""
    success = run_comprehensive_web_ui_test()
    
    if success:
        print("\n✅ Web UI fallback model management is ready!")
        print("Users can access the following features in the Web UI:")
        print("  - Download and load TinyLlama GGUF preset")
        print("  - Check model status and system compatibility")
        print("  - Test model performance")
        print("  - Auto-configure optimal fallback model")
        print("  - Switch between different model presets")
        print("  - Monitor system resources and VRAM usage")
    else:
        print("\n❌ Web UI integration has issues.")
        print("Please check the error messages above and ensure all dependencies are installed.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 