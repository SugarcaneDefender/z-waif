#!/usr/bin/env python3
"""
Comprehensive Z-WAIF System Check
This script verifies that all major components are working properly.
"""

import os
import sys
import json
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Load environment first
load_dotenv()

def print_header(title):
    """Print a nice header for each test section"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_result(test_name, success, details=None, warning=False):
    """Print test result with consistent formatting"""
    if success:
        symbol = "✅" if not warning else "⚠️"
        status = "PASS" if not warning else "WARN"
    else:
        symbol = "❌"
        status = "FAIL"
    
    print(f"{symbol} {test_name}: {status}")
    if details:
        print(f"   {details}")

def test_environment():
    """Test environment configuration"""
    print_header("ENVIRONMENT CONFIGURATION")
    
    # Check .env file exists
    env_exists = os.path.exists('.env')
    print_result("Environment file exists", env_exists)
    
    if not env_exists:
        return False
    
    # Check required environment variables
    required_vars = [
        'CHAR_NAME', 'YOUR_NAME', 'API_TYPE', 'HOST_PORT'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    env_complete = len(missing_vars) == 0
    if missing_vars:
        print_result("Required environment variables", False, f"Missing: {', '.join(missing_vars)}")
    else:
        print_result("Required environment variables", True, "All required vars present")
    
    # Check character name
    char_name = os.environ.get('CHAR_NAME', '')
    print_result("Character name configured", bool(char_name), f"Name: {char_name}")
    
    return env_complete

def test_dependencies():
    """Test Python dependencies"""
    print_header("PYTHON DEPENDENCIES")
    
    critical_deps = [
        'colorama', 'emoji', 'requests', 'dotenv', 'gradio'
    ]
    
    discord_deps = [
        'discord', 'nacl'  # PyNaCl imports as 'nacl'
    ]
    
    optional_deps = [
        'sseclient', 'humanize', 'ollama'
    ]
    
    all_critical_ok = True
    
    for dep in critical_deps:
        try:
            __import__(dep)
            print_result(f"Critical dependency: {dep}", True)
        except ImportError as e:
            print_result(f"Critical dependency: {dep}", False, str(e))
            all_critical_ok = False
    
    # Check Discord dependencies (important for voice support)
    for dep in discord_deps:
        try:
            __import__(dep)
            print_result(f"Discord dependency: {dep}", True)
        except ImportError:
            print_result(f"Discord dependency: {dep}", False, "Needed for Discord voice support", warning=True)
    
    for dep in optional_deps:
        try:
            __import__(dep)
            print_result(f"Optional dependency: {dep}", True)
        except ImportError:
            print_result(f"Optional dependency: {dep}", False, "Not installed (optional)", warning=True)
    
    return all_critical_ok

def test_file_structure():
    """Test critical file structure"""
    print_header("FILE STRUCTURE")
    
    critical_files = [
        'main.py',
        'API/api_controller.py',
        'utils/ai_handler.py',
        'utils/settings.py',
        'Configurables/Chatpops.json',
        'LiveLog.json'
    ]
    
    critical_dirs = [
        'API',
        'utils',
        'Configurables'
    ]
    
    all_files_ok = True
    
    for file_path in critical_files:
        exists = os.path.exists(file_path)
        print_result(f"Critical file: {file_path}", exists)
        if not exists:
            all_files_ok = False
    
    for dir_path in critical_dirs:
        exists = os.path.isdir(dir_path)
        print_result(f"Critical directory: {dir_path}", exists)
        if not exists:
            all_files_ok = False
    
    return all_files_ok

def test_configurations():
    """Test configuration files"""
    print_header("CONFIGURATION FILES")
    
    configs_ok = True
    
    # Test chatpops
    try:
        with open('Configurables/Chatpops.json', 'r') as f:
            chatpops = json.load(f)
        
        chatpops_count = len(chatpops)
        chatpops_ok = chatpops_count >= 50
        print_result("Chatpops configuration", chatpops_ok, f"{chatpops_count} phrases loaded")
        if not chatpops_ok:
            configs_ok = False
    except Exception as e:
        print_result("Chatpops configuration", False, str(e))
        configs_ok = False
    
    # Test LiveLog
    try:
        with open('LiveLog.json', 'r') as f:
            history = json.load(f)
        
        print_result("Chat history file", True, f"{len(history)} entries")
    except Exception as e:
        print_result("Chat history file", False, str(e))
        configs_ok = False
    
    return configs_ok

def test_core_modules():
    """Test core module imports"""
    print_header("CORE MODULE IMPORTS")
    
    core_modules = [
        ('main', 'Main application'),
        ('API.api_controller', 'API Controller'),
        ('utils.ai_handler', 'AI Handler'),
        ('utils.settings', 'Settings'),
        ('utils.voice', 'Voice system'),
        ('utils.web_ui', 'Web UI')
    ]
    
    all_modules_ok = True
    
    for module_name, description in core_modules:
        try:
            __import__(module_name)
            print_result(f"{description}", True, f"Module: {module_name}")
        except Exception as e:
            print_result(f"{description}", False, f"{module_name}: {str(e)}")
            all_modules_ok = False
    
    return all_modules_ok

def test_enhanced_features():
    """Test enhanced AI features"""
    print_header("ENHANCED AI FEATURES")
    
    features_ok = True
    
    try:
        from utils.ai_handler import AIHandler
        ai_handler = AIHandler()
        
        # Test contextual chatpops
        test_contexts = [
            {"platform": "personal"},
            {"platform": "voice"},
            {"platform": "twitch"}
        ]
        
        for context in test_contexts:
            try:
                chatpop = ai_handler.get_contextual_chatpop(context, "Hello there!")
                platform = context["platform"]
                print_result(f"Contextual chatpops ({platform})", True, f"Generated: '{chatpop}'")
            except Exception as e:
                print_result(f"Contextual chatpops ({platform})", False, str(e))
                features_ok = False
                
    except Exception as e:
        print_result("Enhanced AI features", False, f"AI Handler error: {str(e)}")
        features_ok = False
    
    return features_ok

def test_api_endpoints():
    """Test API configuration"""
    print_header("API CONFIGURATION")
    
    api_ok = True
    
    # Check API type
    api_type = os.environ.get('API_TYPE', 'Oobabooga')
    print_result("API type configured", True, f"Type: {api_type}")
    
    # Check host configuration
    host_port = os.environ.get('HOST_PORT', '127.0.0.1:5000')
    print_result("API host configured", True, f"Host: {host_port}")
    
    # Test API module import based on type
    try:
        if api_type == "Ollama":
            import API.ollama_api
            print_result("API module (Ollama)", True)
        else:
            import API.oobaooga_api
            print_result("API module (Oobabooga)", True)
    except Exception as e:
        print_result(f"API module ({api_type})", False, str(e))
        api_ok = False
    
    return api_ok

def test_startup_capability():
    """Test if the system can start up properly"""
    print_header("STARTUP CAPABILITY")
    
    startup_ok = True
    
    try:
        # Test main module initialization
        import main
        print_result("Main module initialization", True)
        
        # Test if we can access key functions
        if hasattr(main, 'run_program'):
            print_result("Main run function available", True)
        else:
            print_result("Main run function available", False)
            startup_ok = False
            
    except Exception as e:
        print_result("Startup capability", False, str(e))
        startup_ok = False
    
    return startup_ok

def run_comprehensive_check():
    """Run all system checks"""
    print("🚀 Z-WAIF COMPREHENSIVE SYSTEM CHECK")
    print(f"🐍 Python {sys.version}")
    print(f"📁 Working Directory: {os.getcwd()}")
    
    tests = [
        ("Environment", test_environment),
        ("Dependencies", test_dependencies),
        ("File Structure", test_file_structure),
        ("Configurations", test_configurations),
        ("Core Modules", test_core_modules),
        ("Enhanced Features", test_enhanced_features),
        ("API Configuration", test_api_endpoints),
        ("Startup Capability", test_startup_capability)
    ]
    
    results = {}
    total_tests = len(tests)
    passed_tests = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed_tests += 1
        except Exception as e:
            print_result(f"{test_name} (EXCEPTION)", False, str(e))
            results[test_name] = False
            print(f"Exception details: {traceback.format_exc()}")
    
    # Final summary
    print_header("FINAL SUMMARY")
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL SYSTEMS GO! Z-WAIF is ready to run!")
        return True
    elif passed_tests >= total_tests * 0.8:
        print("⚠️ MOSTLY READY - Some non-critical issues detected")
        return True
    else:
        print("❌ SYSTEM NOT READY - Critical issues need to be resolved")
        return False

if __name__ == "__main__":
    try:
        success = run_comprehensive_check()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ SYSTEM CHECK FAILED: {e}")
        print(traceback.format_exc())
        sys.exit(1) 