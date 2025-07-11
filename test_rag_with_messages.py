#!/usr/bin/env python3
"""
Test RAG by calling run_based_rag with sample messages
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rag_with_messages():
    """Test RAG by calling run_based_rag with sample messages"""
    
    print("=== Testing RAG with Sample Messages ===")
    
    try:
        from utils import settings
        from utils import based_rag
        
        # Initialize settings
        print("Initializing settings...")
        settings.initialize_settings()
        
        # Load conversation history directly
        print("Loading conversation history...")
        with open("LiveLog.json", "r") as openfile:
            conversation_history = json.load(openfile)
        
        print(f"✓ Loaded {len(conversation_history)} messages")
        
        # Manually set the history database in RAG
        based_rag.history_database = conversation_history
        
        # Force RAG recalculation
        print("Forcing RAG recalculation...")
        based_rag.manual_recalculate_database()
        
        # Test RAG with sample messages
        print("Testing RAG with sample messages...")
        
        # Use the last message from conversation as test
        if len(conversation_history) > 0:
            last_message = conversation_history[-1]
            user_message = last_message[0]
            ai_message = last_message[1]
            
            print(f"Testing with user message: {user_message[:50]}...")
            print(f"Testing with AI message: {ai_message[:50]}...")
            
            # Call run_based_rag to update current_rag_message
            based_rag.run_based_rag(user_message, ai_message)
            
            # Now test the RAG message
            rag_message = based_rag.call_rag_message()
            print(f"✓ RAG message: {rag_message[:300]}...")
            
            if "No memory currently!" not in rag_message:
                print("✓ RAG system is now working properly!")
                return True
            else:
                print("✗ RAG system still showing 'No memory currently!'")
                return False
        else:
            print("✗ No conversation history to test with")
            return False
            
    except Exception as e:
        print(f"✗ Error testing RAG with messages: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_with_simple_messages():
    """Test RAG with simple messages to see if it works"""
    
    print("\n=== Testing RAG with Simple Messages ===")
    
    try:
        from utils import settings
        from utils import based_rag
        
        # Initialize settings
        settings.initialize_settings()
        
        # Load conversation history
        with open("LiveLog.json", "r") as openfile:
            conversation_history = json.load(openfile)
        
        # Set history database
        based_rag.history_database = conversation_history
        
        # Force RAG recalculation
        based_rag.manual_recalculate_database()
        
        # Test with simple messages
        test_user_message = "Hello, how are you?"
        test_ai_message = "I'm doing great! How about you?"
        
        print(f"Testing with simple messages...")
        print(f"User: {test_user_message}")
        print(f"AI: {test_ai_message}")
        
        # Call run_based_rag
        based_rag.run_based_rag(test_user_message, test_ai_message)
        
        # Check RAG message
        rag_message = based_rag.call_rag_message()
        print(f"✓ RAG message: {rag_message[:300]}...")
        
        if "No memory currently!" not in rag_message:
            print("✓ RAG system is working with simple messages!")
            return True
        else:
            print("✗ RAG system still not working")
            return False
            
    except Exception as e:
        print(f"✗ Error testing RAG with simple messages: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import json
    
    print("Starting RAG message testing...")
    
    # Try the first approach
    success = test_rag_with_messages()
    
    if not success:
        print("\nTrying with simple messages...")
        success = test_rag_with_simple_messages()
    
    if success:
        print("\n✓ RAG system should now be working properly!")
    else:
        print("\n✗ RAG system testing failed")
    
    print("\n=== RAG Message Testing Complete ===") 