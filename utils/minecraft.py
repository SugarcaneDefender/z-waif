import os
from utils import settings

if os.name == "posix":
    print("WARNING: minecraft is not supported on Linux/Mac")
else:
    from .windows.minecraft import *

def process_minecraft_message(message, username="minecraft_user"):
    """Process Minecraft chat messages with proper platform context."""
    if not message or not message.strip():
        print("[MINECRAFT] Received empty message")
        return None
        
    try:
        # Format message with platform context
        platform_message = f"[Platform: Minecraft] {message}"
        
        # Send through API controller directly
        from API.api_controller import api_call
        from utils import settings
        clean_reply = api_call(platform_message, settings.temp_level, max_tokens=47, streaming=False, preset=settings.model_preset)
        
        if clean_reply and clean_reply.strip():
            # Log the interaction to chat history
            try:
                from utils.chat_history import add_message_to_history
                add_message_to_history(username, "user", message, "minecraft", {
                    "username": username,
                    "platform": "minecraft"
                })
                add_message_to_history(username, "assistant", clean_reply, "minecraft")
            except Exception as e:
                print(f"[MINECRAFT] Could not log to chat history: {e}")
            
            return clean_reply
            
    except Exception as e:
        print(f"[MINECRAFT] Error processing message: {e}")
        return "Sorry, I'm having trouble processing messages right now."
        
    return None
