import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from utils.zw_logging import log_info, log_error
from pathlib import Path

# Store user contexts in memory and persist to file
CONTEXT_FILE = Path("Configurables/user_contexts.json")
user_contexts = {}

def load_user_contexts():
    """Load user contexts from the JSON file."""
    if CONTEXT_FILE.exists():
        with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_user_contexts(contexts):
    """Save user contexts to the JSON file."""
    CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:
        json.dump(contexts, f, indent=4)

def get_user_context(user_id, platform):
    """Get user context for a specific user and platform."""
    contexts = load_user_contexts()
    key = f"{platform}:{user_id}"
    
    if key not in contexts:
        # Initialize new user context
        contexts[key] = {
            "username": user_id,
            "platform": platform,
            "interests": [],
            "personality_traits": [],
            "interaction_count": 0,
            "last_interaction": None,
            "favorite_topics": [],
            "engagement_level": "new"
        }
        save_user_contexts(contexts)
    
    return contexts[key]

def update_user_context(user_id: str, platform: str, updates: dict):
    """Update user context with new information."""
    contexts = load_user_contexts()
    key = f"{platform}:{user_id}"
    
    if key not in contexts:
        contexts[key] = get_user_context(user_id, platform)
    
    # Handle interaction count increment
    if "interaction_count" in updates:
        current_count = contexts[key].get("interaction_count", 0)
        contexts[key]["interaction_count"] = current_count + updates["interaction_count"]
        del updates["interaction_count"]  # Remove so it doesn't get overwritten below
    
    # Update the rest of the fields
    contexts[key].update(updates)
    
    # Save the updated contexts
    save_user_contexts(contexts)
    return contexts[key]

def analyze_user_interests(messages):
    """Analyze user messages to extract potential interests."""
    # TODO: Implement interest analysis logic
    return []

def analyze_personality_traits(messages):
    """Analyze user messages to determine personality traits."""
    # TODO: Implement personality analysis logic
    return []

def add_user_interest(user_id: str, platform: str, interest: str):
    """Add an interest to user's profile"""
    user_key = f"{platform}_{user_id}"
    context = get_user_context(user_id, platform)
    
    if interest not in context["interests"]:
        context["interests"].append(interest)
        # Keep only last 10 interests
        context["interests"] = context["interests"][-10:]
        user_contexts[user_key]["interests"] = context["interests"]
        save_user_contexts(user_contexts)

def add_user_topic(user_id: str, platform: str, topic: str):
    """Add a recent topic to user's profile"""
    user_key = f"{platform}_{user_id}"
    context = get_user_context(user_id, platform)
    
    if topic not in context["favorite_topics"]:
        context["favorite_topics"].append(topic)
        # Keep only last 5 topics
        context["favorite_topics"] = context["favorite_topics"][-5:]
        user_contexts[user_key]["favorite_topics"] = context["favorite_topics"]
        save_user_contexts(user_contexts)

def update_relationship_level(user_id: str, platform: str, level: str):
    """Update user's relationship level"""
    valid_levels = ["stranger", "acquaintance", "friend", "close_friend", "vip"]
    if level in valid_levels:
        update_user_context(user_id, platform, {"engagement_level": level})

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
            rel = context["engagement_level"]
            if rel not in stats["by_relationship"]:
                stats["by_relationship"][rel] = 0
            stats["by_relationship"][rel] += 1
            
            # Active users
            last_seen = datetime.fromisoformat(context["last_interaction"])
            if last_seen > cutoff_time:
                stats["active_last_24h"] += 1
    
    return stats

def cleanup_old_users(days_inactive: int = 30):
    """Remove users who haven't been active for a specified number of days"""
    cutoff_time = datetime.now() - timedelta(days=days_inactive)
    keys_to_remove = []
    
    for user_key, context in user_contexts.items():
        last_seen = datetime.fromisoformat(context["last_interaction"])
        if last_seen < cutoff_time:
            keys_to_remove.append(user_key)
    
    for key in keys_to_remove:
        del user_contexts[key]
    
    if keys_to_remove:
        save_user_contexts(user_contexts)
        log_info(f"Cleaned up {len(keys_to_remove)} inactive users")

# Load contexts on module import
user_contexts = load_user_contexts() 