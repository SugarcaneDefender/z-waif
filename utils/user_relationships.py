import json
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from utils.zw_logging import log_info, log_error
from utils.user_context import get_user_context, update_user_context

# File to store relationship data
RELATIONSHIPS_FILE = "Configurables/user_relationships.json"
relationships_data = {}

# Relationship progression thresholds
RELATIONSHIP_THRESHOLDS = {
    "stranger": {"messages": 0, "days": 0},
    "acquaintance": {"messages": 5, "days": 1},
    "friend": {"messages": 20, "days": 3},
    "close_friend": {"messages": 50, "days": 7},
    "vip": {"messages": 100, "days": 14}
}

# Personality types for different relationship levels
PERSONALITY_RESPONSES = {
    "stranger": {
        "greetings": ["Hi there!", "Hello!", "Hey!", "Nice to meet you!"],
        "tone": "polite",
        "enthusiasm": 0.6
    },
    "acquaintance": {
        "greetings": ["Hey again!", "Good to see you!", "What's up?", "Back again!"],
        "tone": "friendly",
        "enthusiasm": 0.7
    },
    "friend": {
        "greetings": ["Hey buddy!", "What's good?", "Yo!", "How's it going?"],
        "tone": "casual",
        "enthusiasm": 0.8
    },
    "close_friend": {
        "greetings": ["Yooo!", "My friend!", "What's happening?", "Hey there, awesome human!"],
        "tone": "enthusiastic",
        "enthusiasm": 0.9
    },
    "vip": {
        "greetings": ["The legend returns!", "VIP in the house!", "My favorite person!", "Look who it is!"],
        "tone": "excited",
        "enthusiasm": 1.0
    }
}

def load_relationships():
    """Load relationship data from file"""
    global relationships_data
    try:
        if os.path.exists(RELATIONSHIPS_FILE):
            with open(RELATIONSHIPS_FILE, 'r', encoding='utf-8') as f:
                relationships_data = json.load(f)
            log_info(f"Loaded relationships for {len(relationships_data)} users")
        else:
            relationships_data = {}
            log_info("No existing relationships file found, starting fresh")
    except Exception as e:
        log_error(f"Error loading relationships: {e}")
        relationships_data = {}

def save_relationships():
    """Save relationship data to file"""
    try:
        os.makedirs(os.path.dirname(RELATIONSHIPS_FILE), exist_ok=True)
        with open(RELATIONSHIPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(relationships_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_error(f"Error saving relationships: {e}")

def get_relationship_data(user_id: str, platform: str) -> Dict[str, Any]:
    """Get relationship data for a user"""
    user_key = f"{platform}_{user_id}"

    if user_key not in relationships_data:
        # For personal Web UI or command-line use we want a closer relationship by default
        default_level = "stranger"
        if platform.lower() in ("webui", "personal", "cmd"):
            default_level = "close_friend"

        relationships_data[user_key] = {
            "user_id": user_id,
            "platform": platform,
            "relationship_level": default_level,
            "interaction_count": 0,
            "positive_interactions": 0,
            "negative_interactions": 0,
            "favorite_topics": [],
            "conversation_style": "unknown",
            "special_notes": [],
            "first_interaction": datetime.now().isoformat(),
            "last_interaction": datetime.now().isoformat(),
            "total_chat_time": 0,
            "personality_traits": []
        }
        save_relationships()

    return relationships_data[user_key]

def update_relationship(user_id: str, platform: str, interaction_type: str = "neutral", topic: str = None):
    """Update relationship based on interaction"""
    user_key = f"{platform}_{user_id}"
    rel_data = get_relationship_data(user_id, platform)

    # Update interaction counts
    rel_data["interaction_count"] += 1
    rel_data["last_interaction"] = datetime.now().isoformat()

    # Track interaction type
    if interaction_type == "positive":
        rel_data["positive_interactions"] += 1
    elif interaction_type == "negative":
        rel_data["negative_interactions"] += 1

    # Add topic if provided
    if topic and topic not in rel_data["favorite_topics"]:
        rel_data["favorite_topics"].append(topic)
        # Keep only last 10 topics
        rel_data["favorite_topics"] = rel_data["favorite_topics"][-10:]

    # Check for relationship level progression
    old_level = rel_data["relationship_level"]
    new_level = calculate_relationship_level(rel_data)

    if new_level != old_level:
        rel_data["relationship_level"] = new_level
        log_info(f"User {user_id} relationship progressed from {old_level} to {new_level}")

        # Update user context as well
        update_user_context(user_id, {"relationship_level": new_level}, platform)

    relationships_data[user_key] = rel_data
    save_relationships()

def calculate_relationship_level(rel_data: Dict[str, Any]) -> str:
    """Calculate relationship level based on interaction data"""
    interaction_count = rel_data["interaction_count"]
    first_interaction = datetime.fromisoformat(rel_data["first_interaction"])
    days_known = (datetime.now() - first_interaction).days

    # Factor in positive vs negative interactions
    positive_ratio = 1.0
    if rel_data["interaction_count"] > 0:
        positive_ratio = rel_data["positive_interactions"] / rel_data["interaction_count"]

    # Reduce progression for users with many negative interactions
    if positive_ratio < 0.3:
        interaction_count = int(interaction_count * 0.5)
    elif positive_ratio > 0.8:
        interaction_count = int(interaction_count * 1.2)

    # Determine level based on thresholds
    current_level = "stranger"
    for level, thresholds in RELATIONSHIP_THRESHOLDS.items():
        if (interaction_count >= thresholds["messages"] and
            days_known >= thresholds["days"]):
            current_level = level

    return current_level

def format_message_with_relationship(message: str, username: str, platform: str) -> str:
    """Format a message with relationship context for the AI"""
    user_context = get_user_context(username, platform)
    rel_data = get_relationship_data(username, platform)

    relationship_level = rel_data["relationship_level"]
    interaction_count = rel_data["interaction_count"]

    # Build context for the AI
    context_parts = [
        f"[User Context: {username} is a {relationship_level}",
        f"with {interaction_count} previous interactions",
    ]

    if rel_data["favorite_topics"]:
        topics = ", ".join(rel_data["favorite_topics"][-3:])  # Last 3 topics
        context_parts.append(f"interested in: {topics}")

    if rel_data["personality_traits"]:
        traits = ", ".join(rel_data["personality_traits"])
        context_parts.append(f"personality: {traits}")

    context_parts.append(f"respond as {relationship_level} with {PERSONALITY_RESPONSES[relationship_level]['tone']} tone]")

    context_string = " ".join(context_parts)

    return f"{context_string}\n\n{username}: {message}"

def add_relationship_context_to_response(response: str, username: str, platform: str) -> str:
    """Add relationship-specific context to AI response"""
    rel_data = get_relationship_data(username, platform)
    relationship_level = rel_data["relationship_level"]

    if relationship_level not in PERSONALITY_RESPONSES:
        return response

    personality = PERSONALITY_RESPONSES[relationship_level]

    # Occasionally add a greeting for returning users
    if (rel_data["interaction_count"] > 1 and
        random.random() < 0.15 and  # 15% chance
        len(response) < 100):  # Only for shorter responses

        greeting = random.choice(personality["greetings"])
        response = f"{greeting} {response}"

    # Adjust enthusiasm based on relationship level
    if personality["enthusiasm"] > 0.8 and len(response) < 150:
        # Add enthusiasm for close relationships
        if not response.endswith(('!', '?')):
            if random.random() < 0.4:  # 40% chance
                response += "!"

    # Add personalization for VIPs
    if relationship_level == "vip" and random.random() < 0.1:  # 10% chance
        vip_additions = [
            " You're awesome! 🌟",
            " Thanks for being here! 💜",
            " You always ask great questions! 🤔",
            " Love chatting with you! 😊"
        ]
        response += random.choice(vip_additions)

    return response



def add_personality_trait(user_id: str, platform: str, trait: str):
    """Add a personality trait to user's profile"""
    rel_data = get_relationship_data(user_id, platform)

    if trait not in rel_data["personality_traits"]:
        rel_data["personality_traits"].append(trait)
        # Keep only last 5 traits
        rel_data["personality_traits"] = rel_data["personality_traits"][-5:]
        relationships_data[f"{platform}_{user_id}"] = rel_data
        save_relationships()

def get_relationship_stats(platform: Optional[str] = None) -> Dict[str, Any]:
    """Get relationship statistics"""
    stats = {
        "total_users": 0,
        "by_relationship_level": {},
        "avg_interactions": 0,
        "most_active_users": []
    }

    filtered_users = []
    for user_key, rel_data in relationships_data.items():
        if platform is None or rel_data["platform"] == platform:
            filtered_users.append(rel_data)

    stats["total_users"] = len(filtered_users)

    if not filtered_users:
        return stats

    # Count by relationship level
    for rel_data in filtered_users:
        level = rel_data["relationship_level"]
        stats["by_relationship_level"][level] = stats["by_relationship_level"].get(level, 0) + 1

    # Calculate average interactions
    total_interactions = sum(rel_data["interaction_count"] for rel_data in filtered_users)
    stats["avg_interactions"] = total_interactions / len(filtered_users)

    # Find most active users
    sorted_users = sorted(filtered_users, key=lambda x: x["interaction_count"], reverse=True)
    stats["most_active_users"] = [
        {
            "user_id": user["user_id"],
            "platform": user["platform"],
            "interactions": user["interaction_count"],
            "relationship_level": user["relationship_level"]
        }
        for user in sorted_users[:5]
    ]

    return stats

def promote_user_relationship(user_id: str, platform: str, new_level: str):
    """Manually promote a user's relationship level"""
    if new_level not in RELATIONSHIP_THRESHOLDS:
        log_error(f"Invalid relationship level: {new_level}")
        return False

    rel_data = get_relationship_data(user_id, platform)
    old_level = rel_data["relationship_level"]
    rel_data["relationship_level"] = new_level

    relationships_data[f"{platform}_{user_id}"] = rel_data
    save_relationships()

    # Also update user context
    update_user_context(user_id, {"relationship_level": new_level}, platform)

    log_info(f"Manually promoted {user_id} from {old_level} to {new_level}")
    return True

def cleanup_inactive_relationships(days_inactive: int = 30):
    """Clean up relationships for users who haven't been active"""
    cutoff_time = datetime.now() - timedelta(days=days_inactive)
    users_to_remove = []

    for user_key, rel_data in relationships_data.items():
        last_interaction = datetime.fromisoformat(rel_data["last_interaction"])
        if last_interaction < cutoff_time:
            users_to_remove.append(user_key)

    for user_key in users_to_remove:
        del relationships_data[user_key]

    if users_to_remove:
        save_relationships()
        log_info(f"Cleaned up {len(users_to_remove)} inactive relationships")

def update_relationship_status(user_id: str, platform: str, status: str):
    """Update the relationship status for a user."""
    user_key = f"{platform}_{user_id}"
    rel_data = get_relationship_data(user_id, platform)
    rel_data["relationship_status"] = status
    relationships_data[user_key] = rel_data
    save_relationships()
    log_info(f"Updated relationship status for {user_id} to {status}")

# --- Relationship Status Functions Needed by z_waif_twitch.py ---
def get_relationship_status(user_id: str, platform: str) -> str:
    """Get the relationship status for a user."""
    rel_data = get_relationship_data(user_id, platform)
    return rel_data.get("relationship_status", "unknown")

def get_user_relationship_level(user_id: str, platform: str) -> str:
    """Get the relationship level for a user"""
    rel_data = get_relationship_data(user_id, platform)
    return rel_data["relationship_level"]

def get_relationship_context(level: str) -> str:
    """Get context string for a relationship level"""
    if level not in PERSONALITY_RESPONSES:
        return ""
    return f"[Relationship: {level}, Tone: {PERSONALITY_RESPONSES[level]['tone']}]"

def get_relationship_history(user_id: str, platform: str):
    """Get the relationship history for a user."""
    rel_data = get_relationship_data(user_id, platform)
    return rel_data.get("relationship_history", [])

def set_relationship_level(user_id: str, platform: str, level: str):
    """Set the relationship level for a user."""
    user_key = f"{platform}_{user_id}"
    rel_data = get_relationship_data(user_id, platform)
    rel_data["relationship_level"] = level
    relationships_data[user_key] = rel_data
    save_relationships()
    log_info(f"Set relationship level for {user_id} to {level}")

def set_relationship_status(user_id: str, platform: str, status: str):
    """Set the relationship status for a user."""
    user_key = f"{platform}_{user_id}"
    rel_data = get_relationship_data(user_id, platform)
    rel_data["relationship_status"] = status
    relationships_data[user_key] = rel_data
    save_relationships()
    log_info(f"Set relationship status for {user_id} to {status}")

def set_relationship_history(user_id: str, platform: str, history):
    """Set the relationship history for a user"""
    user_key = f"{platform}_{user_id}"
    if user_key in relationships_data:
        relationships_data[user_key]["history"] = history
        save_relationships()
        log_info(f"Set relationship history for {user_id} on {platform}")

def update_relationship_from_interaction(user_id: str, platform: str, message_content: str):
    """
    Update relationship based on message interaction.
    This function analyzes the message content and updates the relationship accordingly.
    
    Args:
        user_id: The user ID
        platform: The platform (e.g., 'webui', 'discord', 'twitch')
        message_content: The message content to analyze
    """
    try:
        if not message_content or not message_content.strip():
            return
        
        # Analyze message sentiment and content
        interaction_type = "neutral"
        topic = None
        
        # Simple sentiment analysis (could be enhanced with proper NLP)
        message_lower = message_content.lower()
        
        # Positive indicators
        positive_words = ["thanks", "thank you", "great", "awesome", "love", "like", "good", "nice", "cool", "amazing", "wonderful", "fantastic", "excellent", "perfect", "beautiful", "sweet", "kind", "helpful", "appreciate", "grateful"]
        # Negative indicators
        negative_words = ["hate", "terrible", "awful", "bad", "horrible", "stupid", "idiot", "dumb", "useless", "annoying", "frustrating", "angry", "mad", "upset", "disappointed", "sad", "depressed"]
        
        # Check for positive/negative sentiment
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if positive_count > negative_count:
            interaction_type = "positive"
        elif negative_count > positive_count:
            interaction_type = "negative"
        
        # Extract potential topics (simple keyword extraction)
        words = message_lower.split()
        # Filter out common words and short words
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "must", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "her", "its", "our", "their", "this", "that", "these", "those", "what", "when", "where", "why", "how", "who", "which", "that", "this", "these", "those"}
        
        potential_topics = [word for word in words if len(word) > 3 and word not in common_words]
        if potential_topics:
            topic = potential_topics[0]  # Use the first potential topic
        
        # Update the relationship
        update_relationship(user_id, platform, interaction_type, topic)
        
        log_info(f"Updated relationship for {user_id} ({platform}): {interaction_type} interaction")
        
    except Exception as e:
        log_error(f"Error updating relationship from interaction: {e}")

# =============================================================================
# INITIALIZATION
# =============================================================================
# Load relationship data from file on startup
load_relationships() 