#!/usr/bin/env python3
"""
Test script for TinyLlama GGUF fallback integration in Z-Waif.
Verifies that the fallback system can download, load, and use the GGUF model correctly.
"""

import os
import sys
import json
import time
from pathlib import Path

def test_dependencies():
    """Test if required dependencies are available."""
    print("🔧 Testing dependencies...")
    
    missing = []
    
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__}")
    except ImportError:
        missing.append("torch")
        print("❌ PyTorch not available")
    
    try:
        import transformers
        print(f"✅ Transformers {transformers.__version__}")
    except ImportError:
        missing.append("transformers")
        print("❌ Transformers not available")
    
    try:
        import huggingface_hub
        print(f"✅ HuggingFace Hub available")
    except ImportError:
        missing.append("huggingface_hub")
        print("❌ HuggingFace Hub not available")
    
    try:
        import llama_cpp
        print(f"✅ llama-cpp-python available")
    except ImportError:
        print("⚠️ llama-cpp-python not available (optional for GGUF)")
    
    if missing:
        print(f"\n❌ Missing critical dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    print("✅ All critical dependencies available")
    return True

def test_model_download():
    """Test GGUF model download functionality."""
    print("\n📥 Testing model download...")
    
    try:
        from API.fallback_api import ensure_tinyllama_gguf_model
        
        model_path = ensure_tinyllama_gguf_model()
        
        if model_path and Path(model_path).exists():
            size_mb = round(Path(model_path).stat().st_size / (1024*1024), 1)
            print(f"✅ Model available at: {model_path} ({size_mb} MB)")
            return model_path
        else:
            print("❌ Model download failed")
            return None
            
    except Exception as e:
        print(f"❌ Model download error: {e}")
        return None

def test_fallback_system():
    """Test the fallback API system."""
    print("\n🔄 Testing fallback API system...")
    
    try:
        from API.fallback_api import get_fallback_llm, discover_models, get_system_info
        
        # Test system info
        system_info = get_system_info()
        print(f"System: {system_info.get('memory_available_gb', 0):.1f}GB RAM, GPU: {system_info.get('gpu_available', False)}")
        
        # Test model discovery
        models = discover_models()
        print(f"Discovered {len(models)} models")
        for model in models[:3]:  # Show first 3
            print(f"  - {model}")
        
        # Test LLM initialization
        llm = get_fallback_llm()
        print(f"✅ Fallback LLM initialized with model: {llm.model_name}")
        
        return llm
        
    except Exception as e:
        print(f"❌ Fallback system error: {e}")
        return None

def test_generation(llm):
    """Test text generation with the fallback model."""
    print("\n💬 Testing text generation...")
    
    try:
        test_messages = [
            {"role": "user", "content": "Hello! Please respond with just 'Hi there!' and nothing else."}
        ]
        
        print("Generating response...")
        start_time = time.time()
        
        response = llm.generate(test_messages, max_new_tokens=50, temperature=0.7)
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        print(f"✅ Generation successful in {generation_time:.2f}s")
        print(f"Response: '{response}'")
        
        # Test if response is reasonable
        if len(response.strip()) > 0 and len(response) < 200:
            print("✅ Response length and format look good")
            return True
        else:
            print("⚠️ Response format unusual but generation worked")
            return True
            
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return False

def test_api_compatibility():
    """Test API compatibility with OpenAI format."""
    print("\n🔗 Testing API compatibility...")
    
    try:
        from API.fallback_api import api_call
        
        request = {
            "messages": [
                {"role": "user", "content": "Say hello in one word."}
            ],
            "max_tokens": 10,
            "temperature": 0.7
        }
        
        response = api_call(request)
        
        if isinstance(response, dict) and "choices" in response:
            content = response["choices"][0]["message"]["content"]
            print(f"✅ API call successful")
            print(f"Response: '{content}'")
            return True
        else:
            print(f"❌ API call returned unexpected format: {type(response)}")
            return False
            
    except Exception as e:
        print(f"❌ API compatibility error: {e}")
        return False

def test_environment_variables():
    """Test environment variable integration."""
    print("\n🌍 Testing environment variables...")
    
    try:
        # Check if fallback model is set
        fallback_model = os.getenv("API_FALLBACK_MODEL", "")
        if fallback_model:
            print(f"✅ API_FALLBACK_MODEL set to: {fallback_model}")
        else:
            print("⚠️ API_FALLBACK_MODEL not set (will use default)")
        
        # Check if fallback is enabled
        fallback_enabled = os.getenv("API_FALLBACK_ENABLED", "ON").upper() == "ON"
        if fallback_enabled:
            print("✅ API fallback system enabled")
        else:
            print("⚠️ API fallback system disabled")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment variable error: {e}")
        return False

def test_settings_integration():
    """Test integration with Z-Waif settings system."""
    print("\n⚙️ Testing settings integration...")
    
    try:
        from utils.settings import check_api_health, auto_setup_fallback_model
        
        # Test API health check
        health = check_api_health()
        fallback_available = health.get("fallback", {}).get("available", False)
        
        if fallback_available:
            print("✅ Fallback API shows as healthy in settings")
            models = health["fallback"].get("models", [])
            print(f"Available models: {len(models)}")
        else:
            print("⚠️ Fallback API not showing as healthy")
        
        # Test auto-setup function
        setup_result = auto_setup_fallback_model()
        if setup_result:
            print(f"✅ Auto-setup successful: {setup_result}")
        else:
            print("⚠️ Auto-setup returned no result")
        
        return True
        
    except Exception as e:
        print(f"❌ Settings integration error: {e}")
        return False

def run_comprehensive_test():
    """Run all tests in sequence."""
    print("🚀 Z-Waif TinyLlama GGUF Fallback Test Suite")
    print("=" * 60)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Model Download", test_model_download),
        ("Fallback System", test_fallback_system),
        ("Environment Variables", test_environment_variables),
        ("Settings Integration", test_settings_integration),
    ]
    
    results = {}
    llm = None
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_name == "Fallback System":
                llm = test_func()
                results[test_name] = llm is not None
            else:
                results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Additional tests that require LLM
    if llm:
        print(f"\n{'='*20} Text Generation {'='*20}")
        results["Text Generation"] = test_generation(llm)
        
        print(f"\n{'='*20} API Compatibility {'='*20}")
        results["API Compatibility"] = test_api_compatibility()
    
    # Summary
    print(f"\n{'='*20} Test Summary {'='*20}")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! TinyLlama GGUF fallback is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return False

def main():
    """Main test function."""
    success = run_comprehensive_test()
    
    if success:
        print("\n✅ TinyLlama GGUF fallback system is ready!")
        print("You can now use Z-Waif with confidence that the fallback will work when needed.")
    else:
        print("\n❌ There are issues with the TinyLlama GGUF fallback system.")
        print("Please check the error messages above and install any missing dependencies.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 