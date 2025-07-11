#!/usr/bin/env python3
"""
Test script to verify URI refresh mechanism works correctly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Testing URI Refresh Mechanism ===")
print(f"Initial HOST_PORT: {os.getenv('HOST_PORT', '127.0.0.1:5000')}")

# Import settings and test Oobabooga detection
import utils.settings as settings

print("\n--- Testing Oobabooga Detection ---")
detected_port = settings.auto_detect_oobabooga()

print(f"\nDetected port: {detected_port}")
print(f"Updated HOST_PORT: {os.getenv('HOST_PORT', '127.0.0.1:5000')}")

# Test the URI generation functions directly
print("\n--- Testing URI Generation Functions ---")

# Test API controller URI generation
def test_api_controller_uris():
    """Test API controller URI generation without importing the module"""
    host = os.getenv("HOST_PORT", "127.0.0.1:5000")
    if host.startswith("http://"):
        return {
            'URI': f'{host}/api/v1/generate',
            'URI_CHAT': f'{host}/api/v1/chat',
            'URI_STREAM': f'{host}/api/v1/stream',
            'URL_MODEL': f'{host}/api/v1/model'
        }
    else:
        return {
            'URI': f'http://{host}/api/v1/generate',
            'URI_CHAT': f'http://{host}/api/v1/chat',
            'URI_STREAM': f'http://{host}/api/v1/stream',
            'URL_MODEL': f'http://{host}/api/v1/model'
        }

# Test Oobabooga API URI generation
def test_oobabooga_uris():
    """Test Oobabooga API URI generation without importing the module"""
    host = os.getenv("HOST_PORT", "127.0.0.1:5000")
    if host.startswith("http://"):
        return host
    else:
        return f'http://{host}'

uris = test_api_controller_uris()
base_uri = test_oobabooga_uris()

print(f"API Controller URIs:")
print(f"  URI: {uris['URI']}")
print(f"  URI_CHAT: {uris['URI_CHAT']}")
print(f"  URI_STREAM: {uris['URI_STREAM']}")
print(f"  URL_MODEL: {uris['URL_MODEL']}")

print(f"\nOobabooga API BASE_URI: {base_uri}")

# Test if the URIs point to the correct port
print(f"\n--- Testing URI Ports ---")
import re

uri_port_match = re.search(r':(\d+)', uris['URI'])
if uri_port_match:
    uri_port = uri_port_match.group(1)
    print(f"URI port: {uri_port}")
    print(f"Expected port: {detected_port}")
    print(f"Ports match: {uri_port == str(detected_port)}")

base_uri_port_match = re.search(r':(\d+)', base_uri)
if base_uri_port_match:
    base_uri_port = base_uri_port_match.group(1)
    print(f"BASE_URI port: {base_uri_port}")
    print(f"Expected port: {detected_port}")
    print(f"Ports match: {base_uri_port == str(detected_port)}")

print("\n=== Test Complete ===") 