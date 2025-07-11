# This example requires the 'message_content' intent.
import asyncio
import json
import os
import time
import re
from dotenv import load_dotenv

import discord
import main
import API.api_controller
from utils import settings
from utils.zw_logging import log_error

# Load environment variables
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.presences = True  # Enable presence intent for online status

client = discord.Client(intents=intents)

# Get Discord token from environment variable
discord_enabled_string = os.environ.get("MODULE_DISCORD")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DISCORD_CHANNEL = os.environ.get("DISCORD_CHANNEL", None)  # Optional specific channel

# Load bot detection configuration
def load_bot_detection_config():
    """Load bot detection patterns from configuration file"""
    config_path = "Configurables/DiscordBotDetection.json"
    default_config = {
        "bot_detection_enabled": True,
        "bot_flags": [
            "bot", "ai", "assistant", "helper", "automated", "auto", "chatbot", "waifu", "waif",
            "gpt", "claude", "bard", "copilot", "siri", "alexa", "cortana", "z-waif", "zwaif"
        ],
        "ai_indicators": [
            "as an ai", "as an assistant", "i am an ai", "i am a bot", "i am an assistant",
            "language model", "ai assistant", "artificial intelligence", "machine learning",
            "trained on", "my training", "my knowledge", "my capabilities", "i cannot",
            "i am not able", "i do not have", "i don't have access", "i am designed",
            "my purpose is", "my function is", "i am programmed", "my programming"
        ],
        "bot_names": [
            "bot", "ai", "assistant", "helper", "automated", "auto", "chatbot", "waifu", "waif",
            "gpt", "claude", "bard", "copilot", "siri", "alexa", "cortana", "z-waif", "zwaif",
            "chatgpt", "openai", "anthropic", "google", "microsoft", "amazon", "apple"
        ],
        "ignored_users": [],
        "ignored_channels": [],
        "detection_settings": {
            "check_username": True,
            "check_display_name": True,
            "check_message_content": True,
            "check_message_patterns": True,
            "check_message_length": True,
            "check_repetitive_words": True,
            "min_message_length": 3,
            "max_message_length": 2000,
            "max_word_repetition": 3,
            "max_words_for_repetition_check": 20
        }
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"[DISCORD] Loaded bot detection configuration from {config_path}")
                return config
        else:
            print(f"[DISCORD] Bot detection config not found, using defaults")
            return default_config
    except Exception as e:
        print(f"[DISCORD] Error loading bot detection config: {e}, using defaults")
        return default_config

# Load the configuration
BOT_DETECTION_CONFIG = load_bot_detection_config()

def is_bot_message(message):
    """
    Comprehensive bot detection to prevent infinite loops.
    Returns True if the message appears to be from another AI/bot.
    """
    # Check if bot detection is enabled
    if not BOT_DETECTION_CONFIG.get("bot_detection_enabled", True):
        return False
    
    # Don't respond to our own messages
    if message.author == client.user:
        return True
    
    # Check if the author is marked as a bot
    if message.author.bot:
        return True
    
    # Check ignored users list
    ignored_users = BOT_DETECTION_CONFIG.get("ignored_users", [])
    if message.author.name.lower() in [user.lower() for user in ignored_users]:
        print(f"[DISCORD] Ignoring message from ignored user: {message.author.name}")
        return True
    
    # Check ignored channels list
    ignored_channels = BOT_DETECTION_CONFIG.get("ignored_channels", [])
    if message.channel.name.lower() in [channel.lower() for channel in ignored_channels]:
        print(f"[DISCORD] Ignoring message from ignored channel: {message.channel.name}")
        return True
    
    settings = BOT_DETECTION_CONFIG.get("detection_settings", {})
    
    # Check username for bot indicators
    if settings.get("check_username", True):
        username_lower = message.author.name.lower()
        display_name_lower = message.author.display_name.lower()
        
        bot_flags = BOT_DETECTION_CONFIG.get("bot_flags", [])
        for bot_flag in bot_flags:
            if bot_flag in username_lower or bot_flag in display_name_lower:
                print(f"[DISCORD] Detected bot by username: {message.author.name} (contains '{bot_flag}')")
                return True
        
        # Check for bot names in username
        bot_names = BOT_DETECTION_CONFIG.get("bot_names", [])
        for bot_name in bot_names:
            if bot_name in username_lower or bot_name in display_name_lower:
                print(f"[DISCORD] Detected bot by name: {message.author.name} (contains '{bot_name}')")
                return True
    
    # Check message content for AI indicators
    if settings.get("check_message_content", True):
        content_lower = message.content.lower()
        
        # Check for AI language patterns
        ai_indicators = BOT_DETECTION_CONFIG.get("ai_indicators", [])
        for ai_indicator in ai_indicators:
            if ai_indicator in content_lower:
                print(f"[DISCORD] Detected AI message by content: '{ai_indicator}' in message")
                return True
        
        # Check for formal AI responses using configurable patterns
        from utils.formal_filter import is_formal_response, get_formal_filter_config
        config = get_formal_filter_config()
        if is_formal_response(content_lower, config):
            print(f"[DISCORD] Detected AI message by formal pattern")
            return True
        
        # Additional AI-specific patterns
        ai_patterns = [
            r'\b(as an ai|as an assistant|i am an ai|i am a bot)\b',
            r'\b(language model|ai assistant|artificial intelligence)\b',
            r'\b(my training|my knowledge|my capabilities)\b',
            r'\b(i cannot|i am not able|i do not have access)\b',
            r'\b(my purpose is|my function is|i am designed)\b'
        ]
        
        for pattern in ai_patterns:
            if re.search(pattern, content_lower):
                print(f"[DISCORD] Detected AI message by AI pattern: '{pattern}'")
                return True
    
    # Check for bot-like response patterns
    if settings.get("check_message_patterns", True):
        bot_response_patterns = [
            r'^[A-Z][a-z]+:\s',  # "Assistant: " or "Bot: " patterns
            r'^\*[^*]+\*',       # Action text like "*nods*"
            r'^\[[^\]]+\]',      # Bracket notation like "[System]"
            r'^<[^>]+>',         # Tag notation like "<bot>"
        ]
        
        for pattern in bot_response_patterns:
            if re.match(pattern, message.content.strip()):
                print(f"[DISCORD] Detected bot message by response pattern: '{pattern}'")
                return True
    
    # Check for very short or very long messages (common bot patterns)
    if settings.get("check_message_length", True):
        min_length = settings.get("min_message_length", 3)
        max_length = settings.get("max_message_length", 2000)
        
        if len(message.content.strip()) < min_length or len(message.content) > max_length:
            print(f"[DISCORD] Detected potential bot message by length: {len(message.content)} chars")
            return True
    
    # Check for repetitive patterns (common in bot loops)
    if settings.get("check_repetitive_words", True):
        words = message.content.lower().split()
        max_repetition = settings.get("max_word_repetition", 3)
        max_words = settings.get("max_words_for_repetition_check", 20)
        
        if len(words) > 5:
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # If any word appears more than max_repetition times in a short message, likely a bot
            for word, count in word_freq.items():
                if count > max_repetition and len(words) < max_words:
                    print(f"[DISCORD] Detected repetitive bot message: '{word}' appears {count} times")
                    return True
    
    return False

if discord_enabled_string == "ON":
    if not DISCORD_TOKEN:
        print("[DISCORD] Error: DISCORD_TOKEN not found in environment variables!")
        print("[DISCORD] Please set DISCORD_TOKEN in your .env file")
    else:
        print("[DISCORD] Discord token loaded successfully")

@client.event
async def on_ready():
    print(f'[DISCORD] We have logged in as {client.user}')
    print(f'[DISCORD] Bot is ready and listening for messages')
    if DISCORD_CHANNEL:
        print(f'[DISCORD] Will respond in channel: {DISCORD_CHANNEL}')
    else:
        print(f'[DISCORD] Will respond in all channels')
    
    # Print bot detection status
    if BOT_DETECTION_CONFIG.get("bot_detection_enabled", True):
        print(f'[DISCORD] Bot detection enabled with {len(BOT_DETECTION_CONFIG.get("bot_flags", []))} flags')
    else:
        print(f'[DISCORD] Bot detection disabled')
    # Explicitly set presence to online
    await client.change_presence(status=discord.Status.online)

@client.event
async def on_message(message):
    """Enhanced message processing with full AI integration"""
    if message.author == client.user:
        return
            
    try:
        # Extract message details
        username = message.author.name
        user_id = str(message.author.id)
        channel = message.channel.name if hasattr(message.channel, 'name') else 'DM'
        content = message.content.strip()
        
        print(f"[DISCORD] Received message from {username} in {channel}: '{content}'")
        
        # Skip if empty message
        if not content:
            print(f"[DISCORD] Skipping empty message from {username}")
            return
                
        # Handle bot commands first
        if content.startswith('!'):
            try:
                await client.process_commands(message)
            except Exception as e:
                log_error(f"Error handling commands: {e}")
            return

        # Check shadow chat settings
        if not settings.speak_shadowchats and not content.lower().startswith(settings.char_name.lower()):
            print(f"[DISCORD] Skipping message due to shadow chat settings")
            return

        # Check speak only when spoken to
        if settings.speak_only_spokento and not content.lower().startswith(settings.char_name.lower()):
            print(f"[DISCORD] Skipping message - not spoken to directly")
            return
                
        # Format message with platform context
        platform_message = f"[Platform: Discord Chat] {content}"
        
        # Send through main system with platform context
        try:
            import main
            clean_reply = main.send_platform_aware_message(platform_message, platform="discord")
            
            if clean_reply and clean_reply.strip():
                # Log the interaction to chat history
                try:
                    from utils.chat_history import add_message_to_history
                    add_message_to_history(user_id, "user", content, "discord", {
                        "username": username,
                        "channel": channel
                    })
                    add_message_to_history(user_id, "assistant", clean_reply, "discord")
                except Exception as e:
                    log_error(f"Could not log to chat history: {e}")
                
                # Send the response
                await message.channel.send(clean_reply)
                print(f"[DISCORD] Sent response to {username}: {clean_reply}")
                
                # Handle voice if enabled
                if settings.speak_shadowchats and not settings.stream_chats:
                    main.main_message_speak()
                    
        except Exception as e:
            log_error(f"Error processing Discord message: {e}")
            await message.channel.send("Sorry, I'm having trouble processing messages right now.")
                
    except Exception as e:
        log_error(f"Error in Discord on_message: {e}")
        try:
            await message.channel.send("Sorry, I encountered an error processing your message.")
        except:
            pass

def run_z_waif_discord():
    if not DISCORD_TOKEN:
        print("[DISCORD] Cannot start Discord bot: No token provided")
        return
    
    try:
        print("[DISCORD] Starting Discord bot...")
        client.run(DISCORD_TOKEN)
    except discord.LoginFailure:
        print("[DISCORD] Failed to login: Invalid Discord token")
    except Exception as e:
        print(f"[DISCORD] Error starting Discord bot: {e}")
