import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from utils.logging import log_info, log_error

# Store user contexts in memory and persist to file
USER_CONTEXTS_FILE = "Configurables/user_contexts.json"
user_contexts = {}

def load_user_contexts():
    """Load user contexts from file on startup"""
    global user_contexts
    try:
        if os.path.exists(USER_CONTEXTS_FILE):
            with open(USER_CONTEXTS_FILE, 'r', encoding='utf-8') as f:
                user_contexts = json.load(f)
            log_info(f"Loaded {len(user_contexts)} user contexts")
        else:
            user_contexts = {}
            log_info("No existing user contexts file found, starting fresh")
    except Exception as e:
        log_error(f"Error loading user contexts: {e}")
        user_contexts = {}

def save_user_contexts():
    """Save user contexts to file"""
    try:
        os.makedirs(os.path.dirname(USER_CONTEXTS_FILE), exist_ok=True)
        with open(USER_CONTEXTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_contexts, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_error(f"Error saving user contexts: {e}")

def get_user_context(user_id: str, platform: str) -> Dict[str, Any]:
    """Get user context for a specific user and platform"""
    user_key = f"{platform}_{user_id}"
    
    if user_key not in user_contexts:
        # Create new user context
        user_contexts[user_key] = {
            "user_id": user_id,
            "platform": platform,
            "username": "",
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "message_count": 0,
            "personality_traits": [],
            "interests": [],
            "conversation_style": "friendly",
            "relationship_level": "stranger",
            "last_topics": [],
            "custom_data": {}
        }
        save_user_contexts()
    
    return user_contexts[user_key].copy()

def update_user_context(user_id: str, updates: Dict[str, Any], platform: str):
    """Update user context with new information"""
    user_key = f"{platform}_{user_id}"
    
    if user_key not in user_contexts:
        get_user_context(user_id, platform)  # Create if doesn't exist
    
    # Update last seen
    user_contexts[user_key]["last_seen"] = datetime.now().isoformat()
    
    # Increment message count if specified
    if "message_count" in updates:
        user_contexts[user_key]["message_count"] += updates["message_count"]
        del updates["message_count"]  # Don't overwrite with the increment value
    
    # Update other fields
    for key, value in updates.items():
        if key in user_contexts[user_key]:
            user_contexts[user_key][key] = value
        else:
            user_contexts[user_key]["custom_data"][key] = value
    
    save_user_contexts()

def add_user_interest(user_id: str, platform: str, interest: str):
    """Add an interest to user's profile"""
    user_key = f"{platform}_{user_id}"
    context = get_user_context(user_id, platform)
    
    if interest not in context["interests"]:
        context["interests"].append(interest)
        # Keep only last 10 interests
        context["interests"] = context["interests"][-10:]
        user_contexts[user_key]["interests"] = context["interests"]
        save_user_contexts()

def add_user_topic(user_id: str, platform: str, topic: str):
    """Add a recent topic to user's profile"""
    user_key = f"{platform}_{user_id}"
    context = get_user_context(user_id, platform)
    
    if topic not in context["last_topics"]:
        context["last_topics"].append(topic)
        # Keep only last 5 topics
        context["last_topics"] = context["last_topics"][-5:]
        user_contexts[user_key]["last_topics"] = context["last_topics"]
        save_user_contexts()

def update_relationship_level(user_id: str, platform: str, level: str):
    """Update user's relationship level"""
    valid_levels = ["stranger", "acquaintance", "friend", "close_friend", "vip"]
    if level in valid_levels:
        update_user_context(user_id, {"relationship_level": level}, platform)

def get_user_stats(platform: Optional[str] = None) -> Dict[str, Any]:
    """Get statistics about users"""
    stats = {
        "total_users": 0,
        "by_platform": {},
        "by_relationship": {},
        "active_last_24h": 0
    }
    
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    for user_key, context in user_contexts.items():
        if platform is None or context["platform"] == platform:
            stats["total_users"] += 1
            
            # Platform stats
            plt = context["platform"]
            if plt not in stats["by_platform"]:
                stats["by_platform"][plt] = 0
            stats["by_platform"][plt] += 1
            
            # Relationship stats
            rel = context["relationship_level"]
            if rel not in stats["by_relationship"]:
                stats["by_relationship"][rel] = 0
            stats["by_relationship"][rel] += 1
            
            # Active users
            last_seen = datetime.fromisoformat(context["last_seen"])
            if last_seen > cutoff_time:
                stats["active_last_24h"] += 1
    
    return stats

def cleanup_old_users(days_inactive: int = 30):
    """Remove users who haven't been active for a specified number of days"""
    cutoff_time = datetime.now() - timedelta(days=days_inactive)
    keys_to_remove = []
    
    for user_key, context in user_contexts.items():
        last_seen = datetime.fromisoformat(context["last_seen"])
        if last_seen < cutoff_time:
            keys_to_remove.append(user_key)
    
    for key in keys_to_remove:
        del user_contexts[key]
    
    if keys_to_remove:
        save_user_contexts()
        log_info(f"Cleaned up {len(keys_to_remove)} inactive users")

# Load contexts on module import
load_user_contexts() 