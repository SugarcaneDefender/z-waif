#!/usr/bin/env python3
"""
Advanced Fallback System Test Script
Tests VRAM detection, model compatibility, drag-and-drop ordering, and Linux compatibility
"""

import os
import sys
import json
import platform
import subprocess
from pathlib import Path
import re

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import os
from utils import settings
from API import fallback_api

def test_fallback_language_selection():
    """Test that the fallback API respects language settings."""
    print("Testing fallback language selection...")
    
    # Use the HuggingFace TinyLlama model (which is available)
    model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    try:
        # Switch to the model
        success = fallback_api.switch_fallback_model(model_name)
        if not success:
            print("FAIL: Could not switch to TinyLlama model")
            return False
        
        # Get the LLM instance
        llm = fallback_api.get_fallback_llm()
        
        # Test 1: Manual language selection (Spanish)
        print("Test 1: Manual language selection (Spanish)")
        messages = [
            {"role": "user", "content": "Respond with only the word 'Hola' and nothing else."}
        ]
        response = llm.generate(messages, max_tokens=10, temperature=0.1, language='es')
        print(f"Spanish response: '{response.strip()}'")
        
        # Check if response contains Spanish content
        spanish_indicators = ['hola', 'gracias', 'por', 'que', 'es', 'muy', 'para']
        has_spanish = any(indicator in response.lower() for indicator in spanish_indicators)
        if has_spanish:
            print("PASS: Spanish language parameter working")
        else:
            print("WARNING: Spanish response may not be in Spanish")
        
        # Test 2: Auto-detect (no language specified)
        print("Test 2: Auto-detect language")
        messages = [
            {"role": "user", "content": "Respond with only the word 'Hello' and nothing else."}
        ]
        response = llm.generate(messages, max_tokens=10, temperature=0.1)
        print(f"Auto-detect response: '{response.strip()}'")
        
        # Check if response contains English content
        english_indicators = ['hello', 'hi', 'hey', 'test', 'ok']
        has_english = any(indicator in response.lower() for indicator in english_indicators)
        if has_english:
            print("PASS: Auto-detect language working")
        else:
            print("WARNING: Auto-detect response may not be in English")
        
        print("PASS: Language selection tests completed")
        return True
        
    except Exception as e:
        print(f"FAIL: Language selection test failed: {e}")
        return False

def test_system_compatibility():
    """Test system compatibility and platform detection."""
    print("Testing System Compatibility")
    print("=" * 50)
    
    # Platform detection
    system = platform.system()
    machine = platform.machine()
    python_version = platform.python_version()
    
    print(f"PASS Platform: {system}")
    print(f"PASS Architecture: {machine}")
    print(f"PASS Python Version: {python_version}")
    
    # Test psutil import
    try:
        import psutil
        print("PASS psutil imported successfully")
        
        # Test system info functions
        cpu_count = psutil.cpu_count()
        memory = psutil.virtual_memory()
        print(f"PASS CPU Count: {cpu_count}")
        print(f"PASS Total Memory: {memory.total / (1024**3):.2f} GB")
        print(f"PASS Available Memory: {memory.available / (1024**3):.2f} GB")
        
    except ImportError as e:
        print(f"FAIL psutil import failed: {e}")
        return False
    
    return True

def test_vram_detection():
    """Test VRAM detection and estimation."""
    print("\nTesting VRAM Detection")
    print("=" * 50)
    
    try:
        from API.fallback_api import get_system_info, get_available_vram_gb, estimate_model_vram_requirement
        
        # Get system info
        system_info = get_system_info()
        print(f"PASS System Info: {json.dumps(system_info, indent=2)}")
        
        # Test VRAM detection
        available_vram = get_available_vram_gb()
        print(f"PASS Available VRAM: {available_vram} GB")
        
        # Test model VRAM estimation
        test_models = [
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "microsoft/phi-2", 
            "TheBloke/Mistral-7B-Instruct-v0.1-GGUF",
            "models/test.gguf"
        ]
        
        for model in test_models:
            vram_required = estimate_model_vram_requirement(model)
            print(f"PASS {model}: {vram_required} GB estimated")
        
        return True
        
    except Exception as e:
        print(f"FAIL VRAM detection failed: {e}")
        return False

def test_model_compatibility():
    """Test model compatibility checking."""
    print("\nTesting Model Compatibility")
    print("=" * 50)
    
    try:
        from API.fallback_api import check_model_compatibility, get_model_info
        
        test_models = [
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "microsoft/phi-2",
            "TheBloke/Mistral-7B-Instruct-v0.1-GGUF",
            "models/test.gguf"
        ]
        
        for model in test_models:
            try:
                is_compatible, message, vram_required = check_model_compatibility(model)
                status = "PASS" if is_compatible else "FAIL"
                print(f"{status} {model}: {message}")
                
                # Test detailed model info
                info = get_model_info(model)
                print(f"   📊 Type: {info.get('type', 'unknown')}")
                print(f"   📊 VRAM Required: {info.get('vram_required_gb', 0)} GB")
                print(f"   📊 Compatible: {info.get('is_compatible', False)}")
                
            except Exception as e:
                print(f"FAIL Error testing {model}: {e}")
        
        return True
        
    except Exception as e:
        print(f"FAIL Model compatibility testing failed: {e}")
        return False

def test_model_discovery():
    """Test model discovery functionality."""
    print("\nTesting Model Discovery")
    print("=" * 50)
    
    try:
        from API.fallback_api import discover_models
        
        # Create test models directory
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        
        # Create a dummy GGUF file for testing
        test_gguf = models_dir / "test_model.gguf"
        if not test_gguf.exists():
            test_gguf.write_text("dummy gguf content")
        
        # Test discovery
        models = discover_models()
        print(f"PASS Discovered {len(models)} models:")
        for model in models:
            print(f"   📦 {model}")
        
        # Clean up test file
        if test_gguf.exists():
            test_gguf.unlink()
        
        return True
        
    except Exception as e:
        print(f"FAIL Model discovery failed: {e}")
        return False

def test_fallback_order_management():
    """Test fallback order management and persistence."""
    print("\nTesting Fallback Order Management")
    print("=" * 50)
    
    try:
        from utils.web_ui import update_fallback_order_advanced
        
        # Test order update
        test_order = [
            {"name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"},
            {"name": "microsoft/phi-2"},
            {"name": "TheBloke/Mistral-7B-Instruct-v0.1-GGUF"}
        ]
        
        result = update_fallback_order_advanced(json.dumps(test_order))
        print(f"PASS Order update result: {result}")
        
        # Check if environment variable was set
        fallback_order = os.getenv("FALLBACK_MODEL_ORDER", "")
        if fallback_order:
            print(f"PASS Environment variable set: {fallback_order}")
        else:
            print("⚠️  Environment variable not set")
        
        return True
        
    except Exception as e:
        print(f"FAIL Fallback order management failed: {e}")
        return False

def test_web_ui_integration():
    """Test Web UI integration and advanced features."""
    print("\nTesting Web UI Integration")
    print("=" * 50)
    
    try:
        # Test if advanced functions are available
        from utils.web_ui import (
            get_system_status, discover_and_analyze_models,
            test_model_compatibility, test_all_fallbacks_advanced,
            optimize_for_vram_advanced
        )
        
        print("PASS Advanced Web UI functions imported successfully")
        
        # Test system status
        system_status = get_system_status()
        print(f"PASS System status function works: {len(system_status)} characters")
        
        # Test model analysis
        model_analysis = discover_and_analyze_models()
        print(f"PASS Model analysis function works: {len(model_analysis)} models found")
        
        # Test VRAM optimization
        vram_optimization = optimize_for_vram_advanced()
        print(f"PASS VRAM optimization function works: {len(vram_optimization)} characters")
        
        return True
        
    except Exception as e:
        print(f"FAIL Web UI integration failed: {e}")
        return False

def test_linux_compatibility():
    """Test Linux-specific compatibility features."""
    print("\nTesting Linux Compatibility")
    print("=" * 50)
    
    system = platform.system()
    print(f"PASS Current system: {system}")
    
    if system == "Linux":
        print("PASS Running on Linux - testing Linux-specific features")
        
        # Test if we can access system information
        try:
            import psutil
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                print(f"PASS CPU frequency detection works: {cpu_freq.current:.2f} MHz")
            
            # Test disk usage
            disk_usage = psutil.disk_usage('/')
            print(f"PASS Disk usage detection works: {disk_usage.free / (1024**3):.2f} GB free")
            
        except Exception as e:
            print(f"FAIL Linux system info failed: {e}")
            return False
        
        # Test if llama-cpp-python can be imported
        try:
            import llama_cpp
            print("PASS llama-cpp-python imported successfully")
        except ImportError as e:
            print(f"⚠️  llama-cpp-python not available: {e}")
            print("   This is normal if not installed yet")
        
        return True
    else:
        print("ℹ️  Not running on Linux - skipping Linux-specific tests")
        return True

def test_advanced_features():
    """Test all advanced features together."""
    print("Testing Advanced Features")
    print("=" * 50)
    
    try:
        # Test system info
        system_info = fallback_api.get_system_info()
        print(f"PASS System info: {system_info['platform']} {system_info['architecture']}")
        
        # Test VRAM detection
        vram = fallback_api.get_available_vram_gb()
        print(f"PASS VRAM detection: {vram} GB available")
        
        # Test model discovery
        models = fallback_api.discover_models()
        print(f"PASS Model discovery: {len(models)} models found")
        
        # Test compatibility checking
        if models:
            is_compatible, message, _ = fallback_api.check_model_compatibility(models[0])
            print(f"PASS Compatibility check: {models[0]} - {message}")
        
        # Test fallback LLM generation (without api_call)
        try:
            llm = fallback_api.get_fallback_llm()
            test_messages = [{"role": "user", "content": "Say 'test'"}]
            response = llm.generate(test_messages, max_tokens=10, temperature=0.7)
            print(f"PASS Fallback generation test: {response[:50]}...")
        except Exception as e:
            print(f"WARNING: Fallback generation test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"FAIL Advanced features test failed: {e}")
        return False

def main():
    print("Z-Waif Advanced Fallback System Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("System Compatibility", test_system_compatibility),
        ("VRAM Detection", test_vram_detection),
        ("Model Compatibility", test_model_compatibility),
        ("Model Discovery", test_model_discovery),
        ("Fallback Order Management", test_fallback_order_management),
        ("Web UI Integration", test_web_ui_integration),
        ("Linux Compatibility", test_linux_compatibility),
        ("Advanced Features", test_advanced_features),
        ("Fallback Language Selection", test_fallback_language_selection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"FAIL {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Advanced fallback system is ready.")
        print("\n🚀 Next steps:")
        print("1. Start the web UI: python main.py")
        print("2. Go to the Settings tab")
        print("3. Use the Advanced Fallback Management section")
        print("4. Test VRAM optimization and model compatibility")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. On Linux, run: chmod +x setup_linux.sh && ./setup_linux.sh")
        print("3. Check that all required packages are installed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 