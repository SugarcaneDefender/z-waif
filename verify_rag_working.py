#!/usr/bin/env python3
"""
Verify RAG system is working
"""

import sys
import os
import json

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_rag_working():
    """Verify that the RAG system is working properly"""
    
    print("=== Verifying RAG System ===")
    
    try:
        from utils import settings
        from utils import based_rag
        
        # Initialize settings
        print("Initializing settings...")
        settings.initialize_settings()
        
        # Load conversation history
        print("Loading conversation history...")
        with open("LiveLog.json", "r") as openfile:
            conversation_history = json.load(openfile)
        
        print(f"✓ Loaded {len(conversation_history)} messages")
        
        # Set history database
        based_rag.history_database = conversation_history
        
        # Force RAG recalculation
        print("Forcing RAG recalculation...")
        based_rag.manual_recalculate_database()
        
        # Test RAG with a simple message
        test_message = "Hello, how are you doing?"
        test_previous = "I'm doing great! How about you?"
        
        print(f"Testing RAG with: '{test_message}'")
        
        # Call run_based_rag to generate memory
        based_rag.run_based_rag(test_message, test_previous)
        
        # Get the RAG message
        rag_message = based_rag.call_rag_message()
        
        print(f"✓ RAG Message: {rag_message[:200]}...")
        
        if "No memory currently!" not in rag_message:
            print("✓ RAG system is working properly!")
            print("✓ Memory retrieval is functional!")
            return True
        else:
            print("✗ RAG system is not working")
            return False
            
    except Exception as e:
        print(f"✗ Error verifying RAG: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting RAG verification...")
    
    success = verify_rag_working()
    
    if success:
        print("\n🎉 RAG system is working properly!")
        print("The system can now retrieve relevant memories from conversation history.")
    else:
        print("\n❌ RAG system verification failed")
    
    print("\n=== RAG Verification Complete ===") 