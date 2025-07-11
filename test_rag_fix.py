#!/usr/bin/env python3
"""
Test script to diagnose and fix RAG issues
"""

import os
import sys
import json

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rag_system():
    """Test the RAG system and fix any issues"""
    
    print("=== RAG System Diagnostic ===")
    
    # Test 1: Check if settings module can be imported
    try:
        from utils import settings
        print("✓ Settings module imported successfully")
    except Exception as e:
        print(f"✗ Error importing settings: {e}")
        return False
    
    # Test 2: Initialize settings
    try:
        settings.initialize_settings()
        print("✓ Settings initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing settings: {e}")
        return False
    
    # Test 3: Check if rag_enabled exists
    try:
        rag_enabled = getattr(settings, 'rag_enabled', None)
        print(f"✓ RAG enabled setting: {rag_enabled}")
    except Exception as e:
        print(f"✗ Error checking rag_enabled: {e}")
        return False
    
    # Test 4: Check if based_rag module can be imported
    try:
        from utils import based_rag
        print("✓ Based RAG module imported successfully")
    except Exception as e:
        print(f"✗ Error importing based_rag: {e}")
        return False
    
    # Test 5: Check RAG database files
    rag_files = [
        "RAG_Database/LiveRAG_Words.json",
        "RAG_Database/LiveRAG_HistoryWordID.json", 
        "RAG_Database/LiveRAG_History.json"
    ]
    
    for file_path in rag_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                print(f"✓ {file_path} exists and is valid JSON")
            except Exception as e:
                print(f"✗ {file_path} exists but is invalid JSON: {e}")
        else:
            print(f"✗ {file_path} does not exist")
    
    # Test 6: Test RAG functions
    try:
        from utils import based_rag
        current_message = based_rag.current_rag_message
        is_setting_up = based_rag.is_setting_up
        print(f"✓ RAG current message: {current_message}")
        print(f"✓ RAG is setting up: {is_setting_up}")
    except Exception as e:
        print(f"✗ Error accessing RAG variables: {e}")
    
    # Test 7: Test RAG message call
    try:
        from utils import based_rag
        rag_message = based_rag.call_rag_message()
        print(f"✓ RAG message call successful: {rag_message[:100]}...")
    except Exception as e:
        print(f"✗ Error calling RAG message: {e}")
    
    print("\n=== RAG Diagnostic Complete ===")
    return True

def fix_rag_issues():
    """Fix common RAG issues"""
    
    print("\n=== Fixing RAG Issues ===")
    
    # Fix 1: Ensure settings are initialized
    try:
        from utils import settings
        settings.initialize_settings()
        print("✓ Settings re-initialized")
    except Exception as e:
        print(f"✗ Error re-initializing settings: {e}")
    
    # Fix 2: Ensure RAG database directory exists
    if not os.path.exists("RAG_Database"):
        os.makedirs("RAG_Database")
        print("✓ Created RAG_Database directory")
    
    # Fix 3: Create default RAG files if they don't exist
    default_files = {
        "RAG_Database/LiveRAG_Words.json": {
            "word": ["", " ", "the", "it"],
            "count": [1, 1, 1, 1],
            "value": [0.0, 0.0, 0.0, 0.0],
            "total_word_count": 0
        },
        "RAG_Database/LiveRAG_HistoryWordID.json": {
            "me": [],
            "her": [],
            "scores": []
        },
        "RAG_Database/LiveRAG_History.json": [
            ["Start of all history!", "Start of all history!"]
        ]
    }
    
    for file_path, default_data in default_files.items():
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w') as f:
                    json.dump(default_data, f, indent=4)
                print(f"✓ Created default {file_path}")
            except Exception as e:
                print(f"✗ Error creating {file_path}: {e}")
    
    # Fix 4: Test RAG initialization
    try:
        from utils import based_rag
        based_rag.load_rag_history()
        print("✓ RAG history loaded successfully")
    except Exception as e:
        print(f"✗ Error loading RAG history: {e}")
    
    print("\n=== RAG Fixes Complete ===")

if __name__ == "__main__":
    print("Starting RAG diagnostic and fix...")
    
    # Run diagnostic
    success = test_rag_system()
    
    if not success:
        print("\nRunning fixes...")
        fix_rag_issues()
        
        print("\nRe-running diagnostic...")
        test_rag_system()
    
    print("\nRAG diagnostic and fix complete!") 