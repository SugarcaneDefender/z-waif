#!/usr/bin/env python3
"""
Test Z-Waif API connection with the updated Oobabooga format
"""

import sys
import os

# Add the current directory to the path so we can import Z-Waif modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_zwaif_api():
    """Test the Z-Waif API connection"""
    print("🧪 Testing Z-Waif API Connection...")
    print("=" * 50)
    
    try:
        # Import the Z-Waif API module
        from API import oobaooga_api
        
        # Test a simple API call
        print("Testing API call...")
        response = oobaooga_api.api_call(
            user_input="Hello! How are you today?",
            temp_level=0.7,
            max_tokens=50,
            streaming=False
        )
        
        print(f"✅ API Response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_zwaif_api()
    if success:
        print("\n🎉 Z-Waif API is working correctly!")
    else:
        print("\n❌ Z-Waif API needs fixing.") 