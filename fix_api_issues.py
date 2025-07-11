#!/usr/bin/env python3
"""
Script to help fix API and quantization issues
"""

import os
import json
from pathlib import Path

def check_env_configuration():
    """Check and suggest fixes for environment configuration"""
    print("🔧 Checking API Configuration...")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ No .env file found!")
        print("💡 Create one from env_example.txt")
        return False
    
    # Read current configuration
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract key settings
        lines = content.split('\n')
        host_port = None
        api_type = None
        
        for line in lines:
            if line.startswith('HOST_PORT='):
                host_port = line.split('=', 1)[1].strip()
            elif line.startswith('API_TYPE='):
                api_type = line.split('=', 1)[1].strip()
        
        print(f"📡 Current API Configuration:")
        print(f"   HOST_PORT: {host_port}")
        print(f"   API_TYPE: {api_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def suggest_quantization_fixes():
    """Suggest fixes for quantization issues"""
    print("\n🔧 Quantization Issue Fixes:")
    print("=" * 50)
    print("The error shows: 'Blockwise quantization only supports 16/32-bit floats, but got torch.uint8'")
    print("\n💡 Solutions:")
    print("1. **Disable 4-bit quantization in Oobabooga:**")
    print("   - Go to Oobabooga Web UI")
    print("   - In Model tab, set 'Bits' to 16 or 32")
    print("   - Or uncheck '4-bit quantization'")
    print("\n2. **Use a different model:**")
    print("   - Try a model that doesn't require 4-bit quantization")
    print("   - Or use a GGUF model instead")
    print("\n3. **Update bitsandbytes:**")
    print("   - pip install --upgrade bitsandbytes")
    print("\n4. **Use CPU mode temporarily:**")
    print("   - Set 'Device' to 'CPU' in Oobabooga")

def suggest_api_fixes():
    """Suggest fixes for API issues"""
    print("\n🔧 API Configuration Fixes:")
    print("=" * 50)
    print("1. **Check Oobabooga is running with OpenAI extension:**")
    print("   - Make sure you started Oobabooga with: --extensions openai")
    print("   - Or enable the OpenAI extension in the Web UI")
    print("\n2. **Find the correct port:**")
    print("   - Check Oobabooga console for the port number")
    print("   - Usually it's 7860, 7861, or 5000")
    print("\n3. **Test the API manually:**")
    print("   - Open browser to http://127.0.0.1:PORT")
    print("   - Look for API documentation or test endpoints")
    print("\n4. **Update HOST_PORT in .env:**")
    print("   - Set HOST_PORT to the correct port")
    print("   - Format: 127.0.0.1:PORT")

def create_test_script():
    """Create a test script to verify API connection"""
    test_script = '''#!/usr/bin/env python3
"""
Test script to verify API connection
"""

import requests
import json

def test_api_connection(port):
    """Test API connection on specific port"""
    print(f"🔍 Testing API on port {port}...")
    
    # Test basic connectivity
    try:
        response = requests.get(f"http://127.0.0.1:{port}", timeout=5)
        print(f"✅ Basic connectivity: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Basic connectivity failed: {e}")
        return False
    
    # Test OpenAI API endpoint
    try:
        payload = {
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10,
            "temperature": 0.7
        }
        
        response = requests.post(
            f"http://127.0.0.1:{port}/v1/chat/completions",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ OpenAI API endpoint working!")
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print(f"✅ Response: {content[:50]}...")
            return True
        else:
            print(f"❌ API endpoint returned {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    # Test common ports
    ports = [5000, 7860, 7861, 7862, 7863, 7864]
    
    for port in ports:
        if test_api_connection(port):
            print(f"🎉 API working on port {port}")
            print(f"💡 Update your .env file with: HOST_PORT=127.0.0.1:{port}")
            break
        print("-" * 30)
'''
    
    with open("test_api_connection.py", "w") as f:
        f.write(test_script)
    
    print("\n📝 Created test_api_connection.py")
    print("💡 Run: python test_api_connection.py")

def main():
    """Main function"""
    print("🔧 Z-Waif API Issue Fixer")
    print("=" * 50)
    
    # Check current configuration
    check_env_configuration()
    
    # Suggest fixes
    suggest_quantization_fixes()
    suggest_api_fixes()
    
    # Create test script
    create_test_script()
    
    print("\n" + "=" * 50)
    print("🎯 Next Steps:")
    print("1. Fix the quantization issue in Oobabooga")
    print("2. Find the correct API port")
    print("3. Update your .env file")
    print("4. Test the connection")
    print("5. Restart Z-Waif")

if __name__ == "__main__":
    main() 