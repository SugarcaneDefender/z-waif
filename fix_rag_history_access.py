#!/usr/bin/env python3
"""
Fix RAG history access by ensuring API controller loads conversation history
"""

import sys
import os
import json

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_rag_history_access():
    """Fix RAG history access by ensuring API controller loads conversation history"""
    
    print("=== Fixing RAG History Access ===")
    
    try:
        from utils import settings
        from utils import based_rag
        import API.Oogabooga_Api_Support as api_controller
        
        # Initialize settings
        print("Initializing settings...")
        settings.initialize_settings()
        
        # Load conversation history directly into API controller
        print("Loading conversation history into API controller...")
        try:
            with open("LiveLog.json", "r") as openfile:
                api_controller.ooga_history = json.load(openfile)
            print(f"✓ Loaded {len(api_controller.ooga_history)} messages into API controller")
        except Exception as e:
            print(f"✗ Error loading conversation history: {e}")
            return False
        
        # Force RAG recalculation with the loaded history
        print("Forcing RAG recalculation with loaded history...")
        based_rag.manual_recalculate_database()
        
        print("✓ RAG recalculation complete!")
        
        # Test RAG message
        print("Testing RAG message...")
        rag_message = based_rag.call_rag_message()
        print(f"✓ RAG message: {rag_message[:300]}...")
        
        # Check if RAG is now working
        if "No memory currently!" not in rag_message:
            print("✓ RAG system is now working properly!")
            return True
        else:
            print("✗ RAG system still showing 'No memory currently!'")
            return False
        
    except Exception as e:
        print(f"✗ Error during RAG fix: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_with_direct_history():
    """Test RAG system by directly loading history into the RAG module"""
    
    print("\n=== Testing RAG with Direct History ===")
    
    try:
        from utils import settings
        from utils import based_rag
        
        # Initialize settings
        settings.initialize_settings()
        
        # Load conversation history directly
        print("Loading conversation history directly...")
        with open("LiveLog.json", "r") as openfile:
            conversation_history = json.load(openfile)
        
        print(f"✓ Loaded {len(conversation_history)} messages")
        
        # Manually set the history database in RAG
        based_rag.history_database = conversation_history
        
        # Force RAG recalculation
        print("Forcing RAG recalculation...")
        based_rag.manual_recalculate_database()
        
        # Test RAG message
        rag_message = based_rag.call_rag_message()
        print(f"✓ RAG message: {rag_message[:300]}...")
        
        if "No memory currently!" not in rag_message:
            print("✓ RAG system is working with direct history!")
            return True
        else:
            print("✗ RAG system still not working")
            return False
            
    except Exception as e:
        print(f"✗ Error testing RAG with direct history: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting RAG history access fix...")
    
    # Try the first approach
    success = fix_rag_history_access()
    
    if not success:
        print("\nTrying alternative approach...")
        success = test_rag_with_direct_history()
    
    if success:
        print("\n✓ RAG system should now be working properly!")
    else:
        print("\n✗ RAG system fix failed")
    
    print("\n=== RAG History Access Fix Complete ===") 