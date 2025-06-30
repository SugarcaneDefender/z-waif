import time
from typing import Any, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta

# Track recent AI messages to prevent self-response loops
recent_ai_messages: Dict[str, Set[str]] = (
    {}
)  # platform_channel -> set of recent message hashes
message_timestamps: Dict[str, float] = {}  # message_hash -> timestamp
cooldown_timers: Dict[str, float] = {}  # platform_channel -> last response time

# Configuration
MESSAGE_COOLDOWN_SECONDS = 3.0  # Minimum time between AI responses in same channel. Float because it can be reassigned.
MEMORY_CLEANUP_INTERVAL = 300  # 5 minutes
MESSAGE_MEMORY_DURATION = 60  # Remember messages for 1 minute
last_cleanup = time.time()


def should_ai_respond(message_content: str, platform: str, channel: str) -> bool:
    """
    Determine if the AI should respond to this message
    Returns False if this appears to be an AI's own message or if on cooldown
    """
    global last_cleanup

    # Cleanup old messages periodically
    current_time = time.time()
    if current_time - last_cleanup > MEMORY_CLEANUP_INTERVAL:
        cleanup_old_messages()
        last_cleanup = current_time

    channel_key = f"{platform}_{channel}"
    message_hash = hash_message(message_content)

    # Check if this message was recently sent by the AI
    if channel_key in recent_ai_messages:
        if message_hash in recent_ai_messages[channel_key]:
            print(
                f"Skipping AI response - message appears to be our own: {message_content[:50]}..."
            )
            return False

    # Check cooldown timer
    if channel_key in cooldown_timers:
        time_since_last = current_time - cooldown_timers[channel_key]
        if time_since_last < MESSAGE_COOLDOWN_SECONDS:
            print(
                f"Skipping AI response - cooldown active ({MESSAGE_COOLDOWN_SECONDS - time_since_last:.1f}s remaining)"
            )
            return False

    # Additional checks for obvious AI patterns
    if is_likely_ai_message(message_content):
        print(
            f"Skipping AI response - message appears AI-generated: {message_content[:50]}..."
        )
        return False

    return True


def record_ai_message(message_content: str, platform: str, channel: str):
    """Record that the AI sent this message to prevent responding to it later"""
    channel_key = f"{platform}_{channel}"
    message_hash = hash_message(message_content)
    current_time = time.time()

    # Initialize storage for this channel if needed
    if channel_key not in recent_ai_messages:
        recent_ai_messages[channel_key] = set()

    # Record the message
    recent_ai_messages[channel_key].add(message_hash)
    message_timestamps[message_hash] = current_time
    cooldown_timers[channel_key] = current_time

    print(f"Recorded AI message for {channel_key}: {message_content[:50]}...")


def hash_message(content: str) -> str:
    """Create a hash of the message content for tracking"""
    # Normalize the content for better matching
    normalized = content.lower().strip()
    # Remove common variations
    normalized = (
        normalized.replace("@", "").replace("!", "").replace("?", "").replace(".", "")
    )
    return str(hash(normalized))


def is_likely_ai_message(content: str) -> bool:
    """Check if a message appears to be AI-generated based on patterns"""
    content_lower = content.lower().strip()

    # Check for common AI response patterns
    ai_patterns = [
        "i'm an ai",
        "as an ai",
        "i don't have",
        "i can't actually",
        "i'm not able to",
        "as a language model",
        "i apologize",
        "let me help you",
        "here's what i can tell you",
        "based on my training",
        "i understand you're",
    ]

    for pattern in ai_patterns:
        if pattern in content_lower:
            return True

    # Check for excessive politeness or formal language (potential AI indicators)
    formal_indicators = [
        "please feel free to",
        "i'd be happy to",
        "certainly! i can",
        "of course! here's",
        "absolutely! let me",
    ]

    for indicator in formal_indicators:
        if indicator in content_lower:
            return True

    return False


def cleanup_old_messages():
    """Remove old message records to prevent memory bloat"""
    current_time = time.time()
    cutoff_time = current_time - MESSAGE_MEMORY_DURATION

    # Clean up message timestamps and references
    hashes_to_remove = []
    for message_hash, timestamp in message_timestamps.items():
        if timestamp < cutoff_time:
            hashes_to_remove.append(message_hash)

    # Remove from timestamps
    for message_hash in hashes_to_remove:
        del message_timestamps[message_hash]

    # Remove from channel message sets
    for channel_key in recent_ai_messages:
        recent_ai_messages[channel_key] = {
            msg_hash
            for msg_hash in recent_ai_messages[channel_key]
            if msg_hash not in hashes_to_remove
        }

    if hashes_to_remove:
        print(f"Cleaned up {len(hashes_to_remove)} old message records")


def set_channel_cooldown(
    platform: str, channel: str, cooldown_seconds: Optional[float] = None
):
    """Manually set a cooldown for a specific channel"""
    if cooldown_seconds is None:
        cooldown_seconds = MESSAGE_COOLDOWN_SECONDS

    channel_key = f"{platform}_{channel}"
    cooldown_timers[channel_key] = time.time() + cooldown_seconds
    print(f"Set cooldown for {channel_key}: {cooldown_seconds} seconds")


def get_channel_status(platform: str, channel: str) -> Dict[str, Any]:
    """Get status information for a specific channel"""
    channel_key = f"{platform}_{channel}"
    current_time = time.time()

    status = {
        "channel": channel_key,
        "recent_messages_count": len(recent_ai_messages.get(channel_key, set())),
        "on_cooldown": False,
        "cooldown_remaining": 0,
        "last_response_time": None,
    }

    # Check cooldown status
    if channel_key in cooldown_timers:
        time_since_last = current_time - cooldown_timers[channel_key]
        if time_since_last < MESSAGE_COOLDOWN_SECONDS:
            status["on_cooldown"] = True
            status["cooldown_remaining"] = MESSAGE_COOLDOWN_SECONDS - time_since_last

        status["last_response_time"] = datetime.fromtimestamp(
            cooldown_timers[channel_key]
        ).isoformat()

    return status


def get_all_channel_stats() -> Dict[str, Any]:
    """Get statistics for all tracked channels"""
    stats: dict[str, int | dict[str, Any]] = {
        "total_channels": len(recent_ai_messages),
        "total_tracked_messages": len(message_timestamps),
        "channels_on_cooldown": 0,
        "channels": {},
    }

    for channel_key in recent_ai_messages:
        platform, channel = channel_key.split("_", 1)
        channel_status = get_channel_status(platform, channel)
        stats["channels"][channel_key] = channel_status  # type: ignore

        if channel_status["on_cooldown"]:
            stats["channels_on_cooldown"] += 1  # type: ignore

    return stats


def reset_channel_tracking(platform: str, channel: str):
    """Reset all tracking for a specific channel"""
    channel_key = f"{platform}_{channel}"

    # Remove from recent messages
    if channel_key in recent_ai_messages:
        # Get all message hashes for this channel
        message_hashes = recent_ai_messages[channel_key].copy()

        # Remove from timestamps
        for message_hash in message_hashes:
            if message_hash in message_timestamps:
                del message_timestamps[message_hash]

        # Clear the channel's message set
        del recent_ai_messages[channel_key]

    # Remove cooldown
    if channel_key in cooldown_timers:
        del cooldown_timers[channel_key]

    print(f"Reset tracking for channel: {channel_key}")


def update_cooldown_settings(new_cooldown: float):
    """Update the global cooldown setting"""
    global MESSAGE_COOLDOWN_SECONDS
    old_cooldown = MESSAGE_COOLDOWN_SECONDS
    MESSAGE_COOLDOWN_SECONDS = new_cooldown
    print(f"Updated message cooldown from {old_cooldown}s to {new_cooldown}s")


# Auto-cleanup function that can be called periodically
def maintenance_cleanup():
    """Perform maintenance cleanup of old data"""
    cleanup_old_messages()

    # Remove empty channel entries
    empty_channels = [
        channel_key
        for channel_key, messages in recent_ai_messages.items()
        if not messages
    ]

    for channel_key in empty_channels:
        del recent_ai_messages[channel_key]

    if empty_channels:
        print(f"Removed {len(empty_channels)} empty channel entries")
