import re
import html
from utils.logging import log_info

def clean_response(response: str, platform: str) -> str:
    """Clean and format AI response for specific platform"""
    if not response:
        return ""
    
    # Basic cleaning
    cleaned = response.strip()
    
    # Remove HTML entities
    cleaned = html.unescape(cleaned)
    
    # Platform-specific cleaning
    if platform.lower() == "twitch":
        cleaned = clean_for_twitch(cleaned)
    elif platform.lower() == "discord":
        cleaned = clean_for_discord(cleaned)
    else:
        cleaned = clean_general(cleaned)
    
    return cleaned

def clean_for_twitch(response: str) -> str:
    """Clean response specifically for Twitch chat"""
    # Twitch chat has character limits and specific formatting rules
    
    # Remove action indicators and RP markers that might confuse viewers
    response = re.sub(r'\*[^*]*\*', '', response)  # Remove *actions*
    response = re.sub(r'\([^)]*\)', '', response)  # Remove (thoughts)
    
    # Remove system prompts or meta text
    response = re.sub(r'\[System[^\]]*\]', '', response, flags=re.IGNORECASE)
    response = re.sub(r'\[Assistant[^\]]*\]', '', response, flags=re.IGNORECASE)
    
    # Remove excessive line breaks
    response = re.sub(r'\n+', ' ', response)
    
    # Limit length for Twitch (max 500 chars is safe)
    if len(response) > 450:
        response = response[:447] + "..."
    
    # Remove leading/trailing quotes if they wrap the entire message
    response = response.strip('"\'')
    
    # Ensure no offensive content markers
    response = filter_inappropriate_content(response)
    
    return response.strip()

def clean_for_discord(response: str) -> str:
    """Clean response specifically for Discord"""
    # Discord has more lenient formatting but still needs cleaning
    
    # Keep some formatting but clean up excessive markup
    response = re.sub(r'\*{3,}', '**', response)  # Reduce excessive bold
    response = re.sub(r'_{3,}', '__', response)   # Reduce excessive underline
    
    # Remove system prompts
    response = re.sub(r'\[System[^\]]*\]', '', response, flags=re.IGNORECASE)
    
    # Limit length for Discord (2000 char limit)
    if len(response) > 1900:
        response = response[:1897] + "..."
    
    # Clean up line breaks (max 2 consecutive)
    response = re.sub(r'\n{3,}', '\n\n', response)
    
    return response.strip()

def clean_general(response: str) -> str:
    """General cleaning for other platforms"""
    # Remove system prompts and meta text
    response = re.sub(r'\[System[^\]]*\]', '', response, flags=re.IGNORECASE)
    response = re.sub(r'\[Assistant[^\]]*\]', '', response, flags=re.IGNORECASE)
    
    # Clean up excessive whitespace
    response = re.sub(r'\s+', ' ', response)
    response = re.sub(r'\n{3,}', '\n\n', response)
    
    return response.strip()

def filter_inappropriate_content(response: str) -> str:
    """Filter out potentially inappropriate content to comply with platform TOS"""
    # Basic filters for Twitch TOS compliance
    
    # Remove or replace potentially problematic words/phrases
    # This is a basic implementation - could be enhanced with more sophisticated filtering
    
    # Remove excessive caps (which might be seen as shouting)
    if response.isupper() and len(response) > 10:
        response = response.lower().capitalize()
    
    # Ensure appropriate language (basic filter)
    inappropriate_patterns = [
        r'\b(hate|discrimination|harassment)\b',
        r'\b(self-harm|suicide)\b',
        r'\b(illegal|drugs|violence)\b'
    ]
    
    for pattern in inappropriate_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            # Log potential issue and provide safe fallback
            log_info(f"Filtered potentially inappropriate content: {pattern}")
            return "I'd like to keep our conversation positive and fun! 😊"
    
    return response

def format_username_mention(username: str, platform: str) -> str:
    """Format username mention for specific platform"""
    if platform.lower() == "twitch":
        return f"@{username}"
    elif platform.lower() == "discord":
        return f"<@{username}>"  # This would need actual user ID because Discord
    else:
        return f"@{username}"

def truncate_message(message: str, max_length: int, suffix: str = "...") -> str:
    """Truncate message to specified length with suffix"""
    if len(message) <= max_length:
        return message
    
    truncate_length = max_length - len(suffix)
    return message[:truncate_length].rstrip() + suffix

def escape_markdown(text: str) -> str:
    """Escape markdown characters to prevent formatting issues"""
    markdown_chars = ['*', '_', '`', '~', '|', '\\']
    for char in markdown_chars:
        text = text.replace(char, f'\\{char}')
    return text

def extract_emotes_and_mentions(message: str) -> dict[str, list[str]]:
    """Extract emotes and mentions from a message"""
    # Extract Twitch emotes (basic pattern)
    emotes = re.findall(r'\b[A-Z][a-z]*[A-Z][a-zA-Z]*\b', message)
    
    # Extract mentions
    mentions = re.findall(r'@(\w+)', message)
    
    # Extract hashtags
    hashtags = re.findall(r'#(\w+)', message)
    
    return {
        'emotes': emotes,
        'mentions': mentions,
        'hashtags': hashtags
    }

def add_personality_flavor(response: str, personality_type: str = "friendly") -> str:
    """Add personality-specific flavor to responses"""
    if personality_type == "enthusiastic":
        # Add more exclamation points and energy
        if not response.endswith(('!', '?', '.')):
            response += "!"
        
        # Add occasional emotes
        energy_emotes = ["😄", "🎉", "✨", "💫"]
        if len(response) < 100:  # Only for shorter messages
            import random
            if random.random() < 0.3:  # 30% chance
                response += f" {random.choice(energy_emotes)}"
    
    elif personality_type == "sarcastic":
        # Add subtle sarcastic markers (very carefully for TOS compliance)
        if "..." not in response and len(response) < 50:
            response += "..."
    
    elif personality_type == "supportive":
        # Add supportive language
        supportive_starters = ["That's interesting!", "I hear you!", "Totally understand!"]
        if len(response) > 20:
            import random
            if random.random() < 0.2:  # 20% chance
                response = f"{random.choice(supportive_starters)} {response}"
    
    return response

def validate_message_safety(message: str, platform: str) -> tuple[bool, str]:
    """Validate message safety for platform TOS compliance"""
    # Basic safety checks
    
    # Check length limits
    max_lengths = {
        "twitch": 500,
        "discord": 2000,
        "default": 1000
    }
    
    max_len = max_lengths.get(platform.lower(), max_lengths["default"])
    if len(message) > max_len:
        return False, f"Message too long for {platform} (max: {max_len} chars)"
    
    # Check for spam patterns
    if len(set(message.replace(' ', ''))) < 3 and len(message) > 10:
        return False, "Message appears to be spam (too repetitive)"
    
    # Check for excessive caps
    if message.isupper() and len(message) > 20:
        return False, "Message is all caps (may be considered shouting)"
    
    # Check for excessive special characters
    special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s]', message)) / len(message)
    if special_char_ratio > 0.5:
        return False, "Message contains too many special characters"
    
    return True, "Message is safe" 