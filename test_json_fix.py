#!/usr/bin/env python3
"""
Test script to verify JSON parsing fixes
"""

import json
import os

def test_json_files():
    """Test all JSON files in Configurables directory"""
    
    print("=== Testing JSON File Parsing ===")
    
    # List of JSON files to test
    json_files = [
        "Configurables/GradioThemeColor.json",
        "Configurables/TagList.json", 
        "Configurables/TaskList.json",
        "Configurables/GamingInputs/None.json",
        "Configurables/Chatpops.json",
        "Configurables/StoppingStrings.json",
        "Configurables/SoftReset.json"
    ]
    
    all_passed = True
    
    for json_file in json_files:
        try:
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    data = json.load(f)
                print(f"✅ {json_file} - Parsed successfully")
            else:
                print(f"⚠️  {json_file} - File not found")
        except json.JSONDecodeError as e:
            print(f"❌ {json_file} - JSON Error: {e}")
            all_passed = False
        except Exception as e:
            print(f"❌ {json_file} - Error: {e}")
            all_passed = False
    
    if all_passed:
        print("\n✅ All JSON files parsed successfully!")
        return True
    else:
        print("\n❌ Some JSON files failed to parse")
        return False

def test_web_ui_import():
    """Test if web UI can import without JSON errors"""
    
    print("\n=== Testing Web UI Import ===")
    
    try:
        # Test the specific import that was failing
        with open("Configurables/GradioThemeColor.json", 'r') as openfile:
            theme_data = json.load(openfile)
            # Handle both old string format and new object format
            if isinstance(theme_data, dict):
                gradio_theme_color = theme_data.get("theme", "emerald")
            else:
                gradio_theme_color = theme_data
        
        print(f"✅ GradioThemeColor.json parsed successfully: {gradio_theme_color}")
        
        # Test other critical JSON files
        with open("Configurables/TagList.json", 'r') as f:
            tag_list = json.load(f)
        print(f"✅ TagList.json parsed successfully: {len(tag_list)} items")
        
        with open("Configurables/TaskList.json", 'r') as f:
            task_list = json.load(f)
        print(f"✅ TaskList.json parsed successfully: {len(task_list)} items")
        
        print("✅ Web UI JSON imports working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Web UI import test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing JSON parsing fixes...")
    
    json_test = test_json_files()
    web_ui_test = test_web_ui_import()
    
    if json_test and web_ui_test:
        print("\n🎉 All tests passed! JSON parsing issues should be resolved.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.") 