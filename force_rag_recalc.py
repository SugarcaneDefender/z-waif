#!/usr/bin/env python3
"""
Force RAG recalculation with new conversation data
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def force_rag_recalculation():
    """Force RAG system to recalculate with new conversation data"""
    
    print("=== Force RAG Recalculation ===")
    
    try:
        from utils import settings
        from utils import based_rag
        
        # Initialize settings
        print("Initializing settings...")
        settings.initialize_settings()
        
        # Force manual recalculation
        print("Forcing RAG recalculation...")
        based_rag.manual_recalculate_database()
        
        print("✓ RAG recalculation complete!")
        
        # Test RAG message
        print("Testing RAG message...")
        rag_message = based_rag.call_rag_message()
        print(f"✓ RAG message: {rag_message[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during RAG recalculation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting forced RAG recalculation...")
    success = force_rag_recalculation()
    
    if success:
        print("\n✓ RAG system should now be working properly!")
    else:
        print("\n✗ RAG recalculation failed")
    
    print("\n=== RAG Recalculation Complete ===") 