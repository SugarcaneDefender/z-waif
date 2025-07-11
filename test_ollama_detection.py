#!/usr/bin/env python3
"""
Test script for Ollama model detection and selection functions.
This demonstrates all three approaches:
1. Auto-detect available models
2. Auto-select and set a model
3. Interactive model selection
"""

import sys
import os

# Add the utils directory to the path so we can import settings
sys.path.append('utils')

from settings import (
    auto_detect_ollama_models,
    auto_detect_and_set_ollama_model,
    choose_ollama_model,
    update_env_setting
)

def main():
    print("=" * 60)
    print("OLLAMA MODEL DETECTION AND SELECTION TEST")
    print("=" * 60)
    
    # Test 1: Auto-detect available models
    print("\n1. AUTO-DETECTING AVAILABLE MODELS")
    print("-" * 40)
    models = auto_detect_ollama_models()
    if models:
        print(f"✅ Found {len(models)} models:")
        for i, model in enumerate(models, 1):
            print(f"   {i}. {model}")
    else:
        print("❌ No models detected")
    
    # Test 2: Auto-select and set a model
    print("\n2. AUTO-SELECTING AND SETTING A MODEL")
    print("-" * 40)
    selected_model = auto_detect_and_set_ollama_model()
    if selected_model:
        print(f"✅ Auto-selected model: {selected_model}")
    else:
        print("❌ Could not auto-select a model")
    
    # Test 3: Interactive selection (commented out to avoid blocking)
    print("\n3. INTERACTIVE MODEL SELECTION")
    print("-" * 40)
    print("Note: Interactive selection is available but not run automatically.")
    print("To use it, call: choose_ollama_model()")
    
    # Show current environment variable
    print("\n4. CURRENT ENVIRONMENT SETTING")
    print("-" * 40)
    current_env_model = os.getenv("ZW_OLLAMA_MODEL", "NOT SET")
    print(f"ZW_OLLAMA_MODEL environment variable: {current_env_model}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main() 