"""
Formal Filter Utility Module

This module provides configurable formal language detection and replacement functionality.
It can be used to filter out formal/customer-service language from AI responses and replace
them with more natural, casual responses.
"""

import re
import random
from typing import List, Dict, Any, Optional
from utils import settings

def is_formal_response(text: str, config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Check if a response contains formal language based on the current configuration.
    
    Args:
        text: The text to check
        config: Optional configuration override. If None, uses settings.get_formal_filter_config()
    
    Returns:
        True if formal language is detected, False otherwise
    """
    if not text or not config:
        return False
    
    if not config.get("enabled", True):
        return False
    
    text_lower = text.lower()
    
    # Check custom phrases first
    phrases = config.get("phrases", [])
    for phrase in phrases:
        if phrase in text_lower:
            return True
    
    # Check custom patterns
    patterns = config.get("patterns", [])
    for pattern in patterns:
        try:
            if re.search(pattern, text_lower):
                return True
        except re.error:
            # Skip invalid regex patterns
            continue
    
    return False

def get_replacement_response(config: Optional[Dict[str, Any]] = None, platform_context: str = "") -> str:
    """
    Get a replacement response based on the current configuration and platform context.
    
    Args:
        config: Optional configuration override. If None, uses settings.get_formal_filter_config()
        platform_context: Platform context string to determine appropriate fallback
    
    Returns:
        A natural replacement response
    """
    if not config:
        config = settings.get_formal_filter_config()
    
    replacements = config.get("replacements", [])
    if not replacements:
        # Fallback responses if none configured
        replacements = [
            "Hey! How's it going?",
            "Hi there! What's up?",
            "Hey! How are you doing?",
            "What's on your mind?"
        ]
    
    # Choose a random replacement
    replacement = random.choice(replacements)
    
    # Add platform-specific context if available
    if platform_context:
        if "Twitch" in platform_context:
            return "Hey! How's it going? What's up?"
        elif "Discord" in platform_context:
            return "Hey there! What's on your mind? 😊"
        elif "Web Interface" in platform_context:
            return "Hi there! How are you feeling today?"
        elif "Command Line" in platform_context:
            return "Hey! How are you doing? What's on your mind?"
        elif "Voice Chat" in platform_context:
            return "Hey! How are you doing?"
        elif "Minecraft" in platform_context:
            return "Hey! What's up? How's the game going?"
        elif "Alarm" in platform_context:
            return "Hi! How can I help you today?"
        elif "Hangout" in platform_context:
            return "Hey! What's on your mind?"
    
    return replacement

def filter_formal_response(response_content: str, config: Optional[Dict[str, Any]] = None, 
                         platform_context: str = "", messages: Optional[List] = None) -> str:
    """
    Filter formal responses and replace them with natural alternatives.
    
    Args:
        response_content: The response content to filter
        config: Optional configuration override
        platform_context: Platform context for appropriate fallbacks
        messages: Optional message history for context detection
    
    Returns:
        The filtered response content
    """
    if not config:
        config = settings.get_formal_filter_config()
    
    if not config.get("enabled", True):
        return response_content
    
    # Detect platform from messages if not provided
    if not platform_context and messages:
        messages_str = str(messages)
        if "[Platform: Twitch Chat]" in messages_str:
            platform_context = "Twitch"
        elif "[Platform: Discord]" in messages_str:
            platform_context = "Discord"
        elif "[Platform: Web Interface" in messages_str:
            platform_context = "Web Interface"
        elif "[Platform: Command Line" in messages_str:
            platform_context = "Command Line"
        elif "[Platform: Voice Chat" in messages_str:
            platform_context = "Voice Chat"
        elif "[Platform: Minecraft" in messages_str:
            platform_context = "Minecraft"
        elif "[Platform: Alarm" in messages_str:
            platform_context = "Alarm"
        elif "[Platform: Hangout" in messages_str:
            platform_context = "Hangout"
    
    # Check if response is formal
    if is_formal_response(response_content, config):
        print(f"[FORMAL_FILTER] Detected formal response: '{response_content[:50]}...'")
        replacement = get_replacement_response(config, platform_context)
        print(f"[FORMAL_FILTER] Replacing with: '{replacement}'")
        return replacement
    
    return response_content

def clean_history_of_formal_responses(history: List, config: Optional[Dict[str, Any]] = None) -> List:
    """
    Clean conversation history of formal responses to prevent reinforcement.
    
    Args:
        history: List of conversation history entries
        config: Optional configuration override
    
    Returns:
        Cleaned history with formal responses replaced
    """
    if not config:
        config = settings.get_formal_filter_config()
    
    if not config.get("enabled", True):
        return history
    
    cleaned_history = []
    
    for entry in history:
        if len(entry) >= 2:
            user_msg = entry[0]
            assistant_msg = entry[1]
            
            if user_msg:
                cleaned_history.append([user_msg, assistant_msg])
            elif assistant_msg and is_formal_response(assistant_msg, config):
                # Replace formal responses with natural ones
                print(f"[FORMAL_FILTER] Filtering formal response from history: '{assistant_msg[:50]}...'")
                natural_fallback = get_replacement_response(config)
                cleaned_history.append([user_msg, natural_fallback])
            else:
                cleaned_history.append([user_msg, assistant_msg])
        else:
            cleaned_history.append(entry)
    
    return cleaned_history

def get_formal_filter_instruction(config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get the formal filter instruction to add to character cards.
    
    Args:
        config: Optional configuration override
    
    Returns:
        The formal filter instruction string
    """
    if not config:
        config = settings.get_formal_filter_config()
    
    if not config.get("enabled", True):
        return ""
    
    strength = config.get("strength", "medium")
    
    if strength == "low":
        return """

CRITICAL: Avoid formal or customer-service language. Do not say phrases like:
- "How can I assist you"
- "to be of service" 
- "to assist"

Respond like a real friend having a casual conversation."""
    
    elif strength == "high":
        return """

CRITICAL: NEVER use formal or customer-service language. NEVER say phrases like:
- "How can I assist you"
- "to be of service" 
- "to assist"
- "What can I do for you"
- "How can I help you today"
- "How may I help you"
- Any variation of "assist", "help", "support", "service" in formal context
- "What would you like me to help you with"
- "How can I be of assistance"
- "Is there anything I can help you with"

ALWAYS respond like a real friend having a casual conversation. Use natural, friendly language."""
    
    else:  # medium
        return """

CRITICAL: NEVER use formal or customer-service language. NEVER say phrases like:
- "How can I assist you"
- "to be of service" 
- "to assist"
- "What can I do for you"
- "How can I help you today"
- "How may I help you"
- Any variation of "assist", "help", "support", "service" in formal context

ALWAYS respond like a real friend having a casual conversation. Use natural, friendly language."""

def test_formal_filter(text: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Test the formal filter on a given text and return detailed results.
    
    Args:
        text: The text to test
        config: Optional configuration override
    
    Returns:
        Dictionary with test results
    """
    if not config:
        config = settings.get_formal_filter_config()
    
    result = {
        "text": text,
        "is_formal": False,
        "detected_phrases": [],
        "detected_patterns": [],
        "replacement": None,
        "config_used": {
            "enabled": config.get("enabled", True),
            "strength": config.get("strength", "medium"),
            "phrases_count": len(config.get("phrases", [])),
            "patterns_count": len(config.get("patterns", []))
        }
    }
    
    if not config.get("enabled", True):
        return result
    
    text_lower = text.lower()
    
    # Check phrases
    phrases = config.get("phrases", [])
    for phrase in phrases:
        if phrase in text_lower:
            result["detected_phrases"].append(phrase)
    
    # Check patterns
    patterns = config.get("patterns", [])
    for pattern in patterns:
        try:
            if re.search(pattern, text_lower):
                result["detected_patterns"].append(pattern)
        except re.error:
            continue
    
    # Determine if formal
    result["is_formal"] = bool(result["detected_phrases"] or result["detected_patterns"])
    
    # Get replacement if formal
    if result["is_formal"]:
        result["replacement"] = get_replacement_response(config)
    
    return result 

def get_formal_filter_config():
    """Get formal filter configuration for bot detection"""
    return {
        "formal_patterns": [
            r'\b(as an ai|as an assistant|i am an ai|i am a bot)\b',
            r'\b(language model|ai assistant|artificial intelligence)\b',
            r'\b(my training|my knowledge|my capabilities)\b',
            r'\b(i cannot|i am not able|i do not have access)\b',
            r'\b(my purpose is|my function is|i am designed)\b',
            r'\b(i\'m here to help|i\'m designed to assist)\b',
            r'\b(based on my training|according to my knowledge)\b'
        ],
        "formal_indicators": [
            "however", "furthermore", "therefore", "consequently", 
            "nevertheless", "moreover", "additionally", "specifically"
        ],
        "min_formal_score": 0.6
    } 