import re
import json
import logging
from collections import Counter
from typing import List, Dict, Optional, Any
from utils.user_relationships import get_relationship_data, add_personality_trait
from utils.zw_logging import log_info
from utils import settings

def analyze_conversation_style(message: str, user_id: str, platform: str) -> Dict[str, Any]:
    """
    Analyze the conversation style and context of a message.
    
    Args:
        message (str): The message to analyze
        user_id (str): The user's ID
        platform (str): The platform the message is from (e.g., 'twitch', 'discord')
        
    Returns:
        Dict[str, Any]: Analysis results including tone, context, etc.
    """
    analysis = {
        'tone': 'neutral',
        'formality': 'casual',
        'emotion': 'neutral',
        'context': 'general',
        'requires_memory': False
    }
    
    # Analyze tone
    if any(word in message.lower() for word in ['thank', 'thanks', 'appreciate', 'grateful']):
        analysis['tone'] = 'grateful'
    elif any(word in message.lower() for word in ['help', 'please', 'could you', 'would you']):
        analysis['tone'] = 'polite'
    elif any(word in message.lower() for word in ['!', 'wow', 'omg', 'amazing']):
        analysis['tone'] = 'excited'
        
    # Analyze formality
    if re.search(r'[A-Z]{2,}|!!+|\?{2,}', message):
        analysis['formality'] = 'very_casual'
    elif re.search(r'(please|would you|could you|kindly)', message.lower()):
        analysis['formality'] = 'formal'
        
    # Analyze emotion
    if any(emoji in message for emoji in ['😊', '😃', '😄', ':)', ':D']):
        analysis['emotion'] = 'happy'
    elif any(emoji in message for emoji in ['😢', '😭', '😔', ':(', ':(']):
        analysis['emotion'] = 'sad'
        
    # Analyze context
    if re.search(r'(remember|earlier|before|last time|yesterday)', message.lower()):
        analysis['requires_memory'] = True
        analysis['context'] = 'memory_recall'
    elif re.search(r'(help|how to|what is|explain)', message.lower()):
        analysis['context'] = 'help_request'
    elif re.search(r'(hi|hello|hey|greetings)', message.lower()):
        analysis['context'] = 'greeting'
        
    return analysis

def extract_topics(message: str) -> list:
    """Extract main topics from the message."""
    # Basic topic extraction based on keywords
    topics = []
    
    topic_keywords = {
        "greeting": ["hi", "hello", "hey", "good morning", "good evening"],
        "gaming": ["game", "play", "stream", "twitch"],
        "coding": ["code", "program", "bug", "error", "function"],
        "social": ["friend", "follow", "chat", "community"],
        "emotional": ["happy", "sad", "excited", "love", "hate"]
    }
    
    text = message.lower()
    
    for topic, keywords in topic_keywords.items():
        if any(keyword in text for keyword in keywords):
            topics.append(topic)
    
    return topics or ["general"]  # Default to "general" if no specific topics found

def analyze_sentiment(message: str) -> str:
    """Basic sentiment analysis."""
    text = message.lower()
    
    # Simple sentiment word lists
    positive = ["good", "great", "awesome", "love", "happy", "thanks", "thank", "nice", "cool", "amazing"]
    negative = ["bad", "hate", "awful", "terrible", "sad", "angry", "upset", "wrong", "stupid"]
    
    pos_count = sum(1 for word in positive if word in text)
    neg_count = sum(1 for word in negative if word in text)
    
    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"

def get_message_metadata(message: str, user_id: str, platform: str) -> dict:
    """
    Extract various metadata from a message.
    """
    return {
        "style": analyze_conversation_style(message, user_id, platform),
        "topics": extract_topics(message),
        "sentiment": analyze_sentiment(message),
        "length": len(message),
        "word_count": len(message.split())
    }

def analyze_conversation_style(message_content: str, user_id: str, platform: str):
    """Analyze and update user's conversation style"""
    rel_data = get_relationship_data(user_id, platform)
    
    # Simple style analysis
    message_lower = message_content.lower()
    
    # Detect conversation style patterns
    if any(word in message_lower for word in ['lol', 'haha', 'funny', '😂', '🤣']):
        add_personality_trait(user_id, platform, "humorous")
    
    if any(word in message_lower for word in ['?', 'how', 'what', 'why', 'when', 'where']):
        add_personality_trait(user_id, platform, "curious")
    
    if any(word in message_lower for word in ['thanks', 'thank you', 'appreciate', 'grateful']):
        add_personality_trait(user_id, platform, "polite")
    
    if len(message_content) > 100:
        add_personality_trait(user_id, platform, "verbose")
    elif len(message_content) < 20:
        add_personality_trait(user_id, platform, "concise")
    
    # Update conversation style
    styles = ["casual", "formal", "enthusiastic", "analytical", "humorous"]
    # This is a simplified implementation - could be enhanced with NLP
    if "?" in message_content:
        rel_data["conversation_style"] = "analytical"
    elif any(word in message_lower for word in ['awesome', 'cool', 'nice', '!!']):
        rel_data["conversation_style"] = "enthusiastic"
    elif len(message_content.split()) > 15:
        rel_data["conversation_style"] = "formal"
    else:
        rel_data["conversation_style"] = "casual" 