import re
from collections import Counter
from typing import List, Dict, Optional
from utils.user_relationships import get_relationship_data, add_personality_trait
from utils.zw_logging import log_info

def analyze_conversation_style(message: str, user_id: str, platform: str) -> str:
    """
    Analyze the conversation style based on message content and patterns.
    Returns a descriptive style tag.
    """
    # Convert to lowercase for analysis
    text = message.lower()
    
    # Initialize style markers
    markers = {
        "formal": 0,
        "casual": 0,
        "friendly": 0,
        "technical": 0,
        "emotional": 0
    }
    
    # Formal markers
    formal_patterns = [
        r'\b(please|thank you|regards|sincerely|would you|could you)\b',
        r'\b(furthermore|moreover|however|therefore|thus)\b',
        r'[.;:]'  # Proper punctuation
    ]
    
    # Casual markers
    casual_patterns = [
        r'\b(hey|hi|hello|sup|yo|thanks)\b',
        r'[!?]{2,}',  # Multiple punctuation
        r'lol|omg|wow'  # Casual expressions
    ]
    
    # Friendly markers
    friendly_patterns = [
        r'\b(friend|buddy|pal|mate)\b',
        r'[:;]-?[)D]',  # Basic emoticons
        r'❤|😊|🙂|👋'  # Emojis
    ]
    
    # Technical markers
    technical_patterns = [
        r'\b(code|program|error|bug|function|api|data)\b',
        r'\b(html|css|js|python|java|c\+\+)\b',
        r'[<>{}[\]()]'  # Code-like characters
    ]
    
    # Emotional markers
    emotional_patterns = [
        r'\b(love|hate|happy|sad|angry|excited)\b',
        r'[!]{3,}',  # Multiple exclamation marks
        r'😢|😭|😡|🥰|😍'  # Emotional emojis
    ]
    
    # Check each pattern type
    for pattern in formal_patterns:
        if re.search(pattern, text):
            markers["formal"] += 1
            
    for pattern in casual_patterns:
        if re.search(pattern, text):
            markers["casual"] += 1
            
    for pattern in friendly_patterns:
        if re.search(pattern, text):
            markers["friendly"] += 1
            
    for pattern in technical_patterns:
        if re.search(pattern, text):
            markers["technical"] += 1
            
    for pattern in emotional_patterns:
        if re.search(pattern, text):
            markers["emotional"] += 1
    
    # Get the dominant style
    dominant_style = max(markers.items(), key=lambda x: x[1])[0]
    
    # If no clear style is detected, default to casual
    if markers[dominant_style] == 0:
        return "casual"
        
    return dominant_style

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