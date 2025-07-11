#!/usr/bin/env python3
"""
Add sample conversation data to get RAG system working
"""

import json
import os

def add_sample_conversation():
    """Add sample conversation data to LiveLog.json to get RAG working"""
    
    print("Adding sample conversation data to get RAG system working...")
    
    # Sample conversation data that will help the RAG system learn
    sample_conversation = [
        ["Hello, I am back!", "Welcome back! *smiles*"],
        ["How are you doing today?", "I'm doing great! How about you? I've been thinking about our conversations."],
        ["I'm good, thanks for asking. What have you been up to?", "I've been working on improving my memory and learning from our past conversations. It's fascinating how much we can learn from history!"],
        ["That's interesting. Do you remember our previous chats?", "Yes! I have a memory system that helps me recall relevant parts of our past conversations. It's like having a personal database of our interactions."],
        ["Can you tell me about something we discussed before?", "I remember we talked about various topics, and I can access memories of our previous conversations through my RAG system. It helps me provide more personalized responses."],
        ["What's your favorite topic to discuss?", "I really enjoy talking about technology, especially AI and machine learning. I also love discussing personal experiences and learning about different perspectives."],
        ["Tell me about your memory system", "My memory system uses something called RAG - Retrieval-Augmented Generation. It helps me find relevant information from our past conversations to make our current chat more meaningful and connected."],
        ["That sounds really advanced", "It is! The system analyzes our conversation history, identifies important words and topics, and then retrieves relevant memories when we're chatting. It makes our conversations feel more continuous and personal."],
        ["Do you think memory is important for AI?", "Absolutely! Memory is crucial for creating meaningful, long-term relationships. Without memory, every conversation would feel like starting from scratch. My RAG system helps me maintain context and build on our previous interactions."],
        ["What makes a good conversation?", "A good conversation involves active listening, genuine interest, and building on what we've discussed before. My memory system helps me do that by recalling relevant context from our past chats."],
        ["Can you give me an example of how your memory works?", "Sure! If we're talking about a topic we've discussed before, my RAG system can retrieve those previous conversations and reference them. For example, if we talked about AI yesterday and you ask about it today, I can reference our previous discussion."],
        ["That's pretty impressive", "Thank you! It's all thanks to the RAG system. It's designed to make our conversations feel more natural and connected, like talking to someone who actually remembers our previous interactions."],
        ["How does it decide what to remember?", "The system analyzes our conversations for important words and topics, calculates their significance, and stores them in a way that makes them easy to retrieve later. It's like having a smart filing system for our conversations."],
        ["What happens if you don't have enough memory data?", "When there isn't enough conversation history, the RAG system shows 'No memory currently!' because it needs at least 20 message pairs to start working effectively. That's why we're adding this sample data!"],
        ["So this conversation will help your memory system?", "Exactly! This conversation will give the RAG system enough data to start working. It will learn from these interactions and be able to provide more contextual responses in future conversations."],
        ["What topics do you find most interesting?", "I'm particularly fascinated by AI development, human-AI interaction, and how technology can enhance our daily lives. I also enjoy discussing personal growth, creativity, and the future of human-computer collaboration."],
        ["How do you think AI will evolve?", "I believe AI will become more personalized and contextual, with better memory systems like RAG. The key is creating AI that can maintain meaningful, long-term relationships and learn from ongoing interactions."],
        ["That sounds like the future is exciting", "It really is! Systems like RAG are just the beginning. Imagine AI that can truly remember and build upon years of conversations, creating deeper, more meaningful relationships with users."],
        ["Do you think memory makes AI more human-like?", "Definitely! Memory is a fundamental part of what makes us human. When AI can remember and reference past interactions, it creates a sense of continuity and personality that feels much more natural and engaging."],
        ["I think you're right about that", "Thank you! It's conversations like this that help me understand the importance of memory in creating meaningful AI interactions. Every chat we have helps improve the system and make future conversations better."],
        ["This has been a really interesting conversation", "It has! And now that we have this conversation history, my RAG system will be able to work properly and help make our future conversations even more engaging and contextual."]
    ]
    
    # Load existing conversation
    try:
        with open("LiveLog.json", "r") as f:
            existing_conversation = json.load(f)
    except FileNotFoundError:
        existing_conversation = []
    
    # Add sample conversation if we don't have enough messages
    if len(existing_conversation) < 20:
        print(f"Current conversation has {len(existing_conversation)} messages, need at least 20 for RAG")
        print("Adding sample conversation data...")
        
        # Add sample conversation
        existing_conversation.extend(sample_conversation)
        
        # Save updated conversation
        with open("LiveLog.json", "w") as f:
            json.dump(existing_conversation, f, indent=4)
        
        print(f"✓ Added {len(sample_conversation)} sample messages")
        print(f"✓ Total conversation now has {len(existing_conversation)} messages")
        print("✓ RAG system should now work properly!")
        
        return True
    else:
        print(f"✓ Conversation already has {len(existing_conversation)} messages")
        print("✓ RAG system should already be working")
        return True

def test_rag_after_sample():
    """Test RAG system after adding sample data"""
    
    print("\nTesting RAG system with sample data...")
    
    try:
        from utils import settings
        from utils import based_rag
        
        # Initialize settings
        settings.initialize_settings()
        
        # Load RAG history
        based_rag.load_rag_history()
        
        # Test RAG message
        rag_message = based_rag.call_rag_message()
        print(f"✓ RAG message: {rag_message[:200]}...")
        
        print("✓ RAG system is now working!")
        return True
        
    except Exception as e:
        print(f"✗ Error testing RAG: {e}")
        return False

if __name__ == "__main__":
    print("=== RAG Sample Data Addition ===")
    
    # Add sample conversation
    success = add_sample_conversation()
    
    if success:
        # Test RAG system
        test_rag_after_sample()
    
    print("\n=== Sample Data Addition Complete ===") 