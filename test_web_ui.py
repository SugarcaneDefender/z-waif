#!/usr/bin/env python
"""
Web UI Diagnostic Test Script

This script helps diagnose and troubleshoot web UI issues, including 500 errors.
Run this script to check for common problems and get detailed diagnostics.

Usage:
    python test_web_ui.py
"""

import os
import sys
import socket
import requests
import time
import json
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def check_port_availability(port):
    """Check if a port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except OSError:
            return False

def test_web_ui_connection(port, timeout=5):
    """Test connection to web UI"""
    try:
        response = requests.get(f"http://localhost:{port}", timeout=timeout)
        return response.status_code, response.text[:200] if response.text else ""
    except requests.exceptions.ConnectionError:
        return None, "Connection refused"
    except requests.exceptions.Timeout:
        return None, "Connection timeout"
    except Exception as e:
        return None, str(e)

def check_environment_variables():
    """Check environment variables related to web UI"""
    print_section("Environment Variables")
    
    env_vars = {
        "WEB_UI_PORT": "Web UI port",
        "WEB_UI_SHARE": "Web UI sharing",
        "WEB_UI_THEME": "Web UI theme",
        "HOST_PORT": "Oobabooga API port",
        "API_TYPE": "API type"
    }
    
    for var, description in env_vars.items():
        value = os.getenv(var, "Not set")
        print(f"  {var}: {value} ({description})")

def check_port_status():
    """Check status of common ports"""
    print_section("Port Status")
    
    common_ports = [7864, 7860, 7861, 7862, 7863, 5000, 5007, 18888]
    
    for port in common_ports:
        available = check_port_availability(port)
        status = "✅ Available" if available else "❌ In Use"
        print(f"  Port {port}: {status}")

def check_web_ui_health():
    """Check web UI health and connectivity"""
    print_section("Web UI Health Check")
    
    # Get configured port
    web_ui_port = int(os.getenv("WEB_UI_PORT", "7864"))
    print(f"Configured Web UI port: {web_ui_port}")
    
    # Check if port is available
    if check_port_availability(web_ui_port):
        print(f"✅ Port {web_ui_port} is available")
    else:
        print(f"❌ Port {web_ui_port} is in use")
        
        # Try to find alternative port
        for alt_port in range(web_ui_port + 1, web_ui_port + 10):
            if check_port_availability(alt_port):
                print(f"💡 Alternative port {alt_port} is available")
                break
    
    # Test connection if port is in use (might be web UI running)
    print(f"\nTesting connection to port {web_ui_port}...")
    status_code, response_text = test_web_ui_connection(web_ui_port)
    
    if status_code is None:
        print(f"❌ Connection failed: {response_text}")
    elif status_code == 200:
        print(f"✅ Web UI is running and responding (Status: {status_code})")
        if "gradio" in response_text.lower():
            print("✅ Confirmed Gradio interface detected")
        else:
            print("⚠️ Response doesn't appear to be Gradio")
    elif status_code == 500:
        print(f"❌ Web UI returned 500 error (Status: {status_code})")
        print("💡 This indicates a server-side error in the web UI")
    else:
        print(f"⚠️ Web UI returned unexpected status: {status_code}")

def check_dependencies():
    """Check if required dependencies are installed"""
    print_section("Dependencies")
    
    required_packages = [
        "gradio",
        "requests", 
        "flask",
        "colorama",
        "emoji"
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is missing")

def check_file_structure():
    """Check if required files exist"""
    print_section("File Structure")
    
    required_files = [
        "utils/web_ui.py",
        "utils/settings.py",
        "main.py",
        ".env"
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")

def check_api_connectivity():
    """Check API connectivity"""
    print_section("API Connectivity")
    
    host_port = os.getenv("HOST_PORT", "127.0.0.1:5000")
    api_type = os.getenv("API_TYPE", "Oobabooga")
    
    print(f"API Type: {api_type}")
    print(f"API Host/Port: {host_port}")
    
    # Test API connection
    try:
        if ":" in host_port:
            host, port = host_port.split(":")
            port = int(port)
        else:
            host = host_port
            port = 5000
            
        response = requests.get(f"http://{host}:{port}/v1/engines/", timeout=5)
        if response.status_code == 200:
            print("✅ API server is responding")
        else:
            print(f"⚠️ API server returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ API connection failed: {e}")

def suggest_solutions():
    """Suggest solutions based on common issues"""
    print_section("Troubleshooting Suggestions")
    
    print("🔧 Common solutions for 500 errors:")
    print("  1. Check if another application is using the same port")
    print("  2. Restart Z-WAIF completely")
    print("  3. Check firewall settings")
    print("  4. Update Gradio: pip install --upgrade gradio")
    print("  5. Clear browser cache and cookies")
    print("  6. Try a different port in your .env file")
    print("  7. Check the log.txt file for detailed error messages")
    
    print("\n🔧 If web UI won't start:")
    print("  1. Ensure all dependencies are installed")
    print("  2. Check Python version compatibility")
    print("  3. Try running as administrator")
    print("  4. Check antivirus software interference")

def main():
    """Main diagnostic function"""
    print_header("Z-WAIF Web UI Diagnostic Tool")
    
    print("This tool will help diagnose web UI issues and 500 errors.")
    print("Running comprehensive checks...")
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded")
    except ImportError:
        print("⚠️ python-dotenv not installed, using system environment")
    except Exception as e:
        print(f"⚠️ Error loading environment: {e}")
    
    # Run all checks
    check_environment_variables()
    check_port_status()
    check_web_ui_health()
    check_dependencies()
    check_file_structure()
    check_api_connectivity()
    suggest_solutions()
    
    print_header("Diagnostic Complete")
    print("If you're still experiencing issues, please:")
    print("1. Check the log.txt file for detailed error messages")
    print("2. Try restarting Z-WAIF completely")
    print("3. Contact support with the diagnostic output above")

if __name__ == "__main__":
    main() 