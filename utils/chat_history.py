import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from utils.zw_logging import log_info, log_error

# Store chat histories in memory and persist to file
CHAT_HISTORIES_FILE = "Configurables/chat_histories.json"
chat_histories = {}
MAX_HISTORY_PER_USER = 50  # Maximum messages to keep per user

def load_chat_histories():
    """Load chat histories from file on startup"""
    global chat_histories
    try:
        if os.path.exists(CHAT_HISTORIES_FILE):
            with open(CHAT_HISTORIES_FILE, 'r', encoding='utf-8') as f:
                chat_histories = json.load(f)
            log_info(f"Loaded chat histories for {len(chat_histories)} users")
        else:
            chat_histories = {}
            log_info("No existing chat histories file found, starting fresh")
    except Exception as e:
        log_error(f"Error loading chat histories: {e}")
        chat_histories = {}

def save_chat_histories():
    """Save chat histories to file"""
    try:
        os.makedirs(os.path.dirname(CHAT_HISTORIES_FILE), exist_ok=True)
        with open(CHAT_HISTORIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(chat_histories, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_error(f"Error saving chat histories: {e}")

def get_chat_history(user_id: str, platform: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get chat history for a specific user and platform"""
    user_key = f"{platform}_{user_id}"
    
    if user_key not in chat_histories:
        chat_histories[user_key] = []
    
    history = chat_histories[user_key]
    if limit:
        return history[-limit:]
    return history

def add_message_to_history(user_id: str, role: str, content: str, platform: str, metadata: Optional[Dict[str, Any]] = None):
    """Add a message to user's chat history"""
    user_key = f"{platform}_{user_id}"
    
    if user_key not in chat_histories:
        chat_histories[user_key] = []
    
    message = {
        "role": role,  # "user" or "assistant"
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "platform": platform,
        "metadata": metadata or {}
    }
    
    chat_histories[user_key].append(message)
    
    # Keep only the most recent messages
    if len(chat_histories[user_key]) > MAX_HISTORY_PER_USER:
        chat_histories[user_key] = chat_histories[user_key][-MAX_HISTORY_PER_USER:]
    
    save_chat_histories()

def update_chat_history(user_id: str, platform: str, new_messages: List[Dict[str, Any]]):
    """Update chat history with multiple messages"""
    user_key = f"{platform}_{user_id}"
    
    if user_key not in chat_histories:
        chat_histories[user_key] = []
    
    for message in new_messages:
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        if "platform" not in message:
            message["platform"] = platform
        
        chat_histories[user_key].append(message)
    
    # Keep only the most recent messages
    if len(chat_histories[user_key]) > MAX_HISTORY_PER_USER:
        chat_histories[user_key] = chat_histories[user_key][-MAX_HISTORY_PER_USER:]
    
    save_chat_histories()

def get_recent_context(user_id: str, platform: str, max_messages: int = 10) -> str:
    """Get recent chat context as a formatted string"""
    history = get_chat_history(user_id, platform, max_messages)
    
    if not history:
        return "No previous conversation history."
    
    context_lines = []
    for msg in history:
        role = "User" if msg["role"] == "user" else "Assistant"
        timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M")
        context_lines.append(f"[{timestamp}] {role}: {msg['content']}")
    
    return "\n".join(context_lines)

def get_conversation_summary(user_id: str, platform: str, max_messages: int = 20) -> Dict[str, Any]:
    """Get a summary of the conversation with a user"""
    history = get_chat_history(user_id, platform, max_messages)
    
    if not history:
        return {
            "total_messages": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "first_interaction": None,
            "last_interaction": None,
            "common_topics": []
        }
    
    user_messages = [msg for msg in history if msg["role"] == "user"]
    assistant_messages = [msg for msg in history if msg["role"] == "assistant"]
    
    # Extract potential topics (simple keyword extraction)
    all_content = " ".join([msg["content"].lower() for msg in user_messages])
    
    summary = {
        "total_messages": len(history),
        "user_messages": len(user_messages),
        "assistant_messages": len(assistant_messages),
        "first_interaction": history[0]["timestamp"] if history else None,
        "last_interaction": history[-1]["timestamp"] if history else None,
        "recent_topics": extract_topics_from_text(all_content)
    }
    
    return summary

def extract_topics_from_text(text: str) -> List[str]:
    """Simple topic extraction from text (can be enhanced with NLP)"""
    # This is a simple implementation - could be enhanced with proper NLP
    common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "must", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "her", "its", "our", "their", "this", "that", "these", "those"}
    
    words = text.split()
    word_freq = {}
    
    for word in words:
        word = word.strip(".,!?;:").lower()
        if len(word) > 3 and word not in common_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Return top 5 most frequent words as potential topics
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:5] if freq > 1]

def cleanup_old_histories(days_old: int = 7):
    """Clean up old chat histories"""
    cutoff_time = datetime.now() - timedelta(days=days_old)
    users_to_clean = []
    
    for user_key, history in chat_histories.items():
        if history:
            # Remove messages older than cutoff_time
            filtered_history = []
            for msg in history:
                msg_time = datetime.fromisoformat(msg["timestamp"])
                if msg_time > cutoff_time:
                    filtered_history.append(msg)
            
            if len(filtered_history) != len(history):
                chat_histories[user_key] = filtered_history
                if not filtered_history:
                    users_to_clean.append(user_key)
    
    # Remove users with no remaining history
    for user_key in users_to_clean:
        del chat_histories[user_key]
    
    if users_to_clean:
        save_chat_histories()
        log_info(f"Cleaned up old histories for {len(users_to_clean)} users")

def get_platform_stats(platform: str) -> Dict[str, Any]:
    """Get statistics for a specific platform"""
    platform_users = [key for key in chat_histories.keys() if key.startswith(f"{platform}_")]
    
    total_messages = 0
    active_conversations = 0
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    for user_key in platform_users:
        history = chat_histories[user_key]
        total_messages += len(history)
        
        if history:
            last_msg_time = datetime.fromisoformat(history[-1]["timestamp"])
            if last_msg_time > cutoff_time:
                active_conversations += 1
    
    return {
        "platform": platform,
        "total_users": len(platform_users),
        "total_messages": total_messages,
        "active_conversations_24h": active_conversations,
        "avg_messages_per_user": total_messages / len(platform_users) if platform_users else 0
    }

# Load histories on module import
load_chat_histories() 