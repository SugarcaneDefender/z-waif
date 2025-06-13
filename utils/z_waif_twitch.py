import twitchio
from twitchio.ext import commands # type: ignore
import os
import asyncio
import random
from dotenv import load_dotenv
from utils import settings
from utils.zw_logging import (
    log_info, log_error, log_startup, log_message_length_warning,
)
import threading
from utils.user_context import get_user_context, update_user_context
from utils.message_processing import clean_response, validate_message_safety, add_personality_flavor
from utils.ai_message_tracker import should_ai_respond, record_ai_message
from utils.user_relationships import (
    add_relationship_context_to_response,
    update_relationship_status,
    get_relationship_status,
    get_relationship_level,
    get_relationship_history,
    set_relationship_level,
    set_relationship_status,
    set_relationship_history
)
from utils.conversation_analysis import analyze_conversation_style, get_message_metadata
from memory_manager import MemoryManager, MultiprocessRAG
from utils.ai_handler import AIHandler
from sentence_transformers import SentenceTransformer
from datetime import datetime
import traceback
# import main

load_dotenv()

TWITCH_TOKEN = os.getenv("TWITCH_TOKEN", "")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL", "")
TWITCH_CLIENT_ID = os.environ.get('TWITCH_CLIENT_ID', "")

if not TWITCH_TOKEN or not TWITCH_CHANNEL:
    log_error("TWITCH_TOKEN or TWITCH_CHANNEL not found. Twitch module disabled.")
else:
    log_info("Twitch credentials loaded successfully.")

class TwitchBot(commands.Bot):
    def __init__(self):
        log_startup()
        log_info("Initializing Twitch Bot with enhanced AI capabilities...")
        
        try:
            # Initialize AI components
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.rag_processor = MultiprocessRAG(self.embedding_model)
            self.memory_manager = MemoryManager(self.rag_processor)
            self.ai_handler = AIHandler()
            
            # Get credentials
            token: str = TWITCH_TOKEN
            channel: str = TWITCH_CHANNEL
            client_id = TWITCH_CLIENT_ID
            
            # Debug logging
            log_info("=== Twitch Debug Info ===")
            log_info(f"Raw Token Length: {len(token)}")
            log_info(f"Raw Token: {token}")
            log_info(f"Channel: {channel}")
            log_info(f"Client ID: {client_id}")
            
            log_info(f"=== Initializing Enhanced Twitch Bot ===")
            log_info(f"Channel: {channel}")
            log_info(f"Token Status: {'Valid' if token else 'Missing'}")
            log_info(f"Client ID Status: {'Valid' if client_id else 'Missing'}")
            log_info(f"AI Memory System: Loaded")
            log_info(f"Relationship Tracking: Active")
            log_info(f"Message Safety: Enabled")
            
            super().__init__( # type: ignore
                token=token, # type: ignore
                client_id=client_id,
                nick=channel,
                prefix='!',
                initial_channels=[channel]
            )
            log_info("Enhanced Twitch Bot initialized with AI capabilities.")
            
        except Exception as e:
            log_error(f"Failed to initialize Twitch Bot: {str(e)}")
            raise
        
    async def event_ready(self):
        try:
            log_info(f"=== Enhanced Twitch Bot Ready! ===")
            log_info(f"Connected as: {self.nick}") # type: ignore
            log_info(f"User ID: {self.user_id}")
            log_info(f"AI Systems: Online")
            log_info(f"Personality: {settings.twitch_personality}")
            log_info(f"Auto-respond: {'Enabled' if settings.twitch_auto_respond else 'Disabled'}")
            log_info("Enhanced Twitch Bot is ready and all AI systems are online!")
        except Exception as e:
            log_error(f"Error in event_ready: {str(e)}")

    async def event_message(self, message: twitchio.Message): # type: ignore
        if message.echo:
            return
            
        try:
            # Check message length
            if len(message.content) > 2000: # type: ignore
                log_message_length_warning(message.content, len(message.content), "Twitch") # type: ignore
                return
                
            log_info(f"Twitch message from {message.author.name}: {message.content}")
            
            # Handle bot commands first
            await self.handle_commands(message)
            
            # Check if we should respond to this message
            if not should_ai_respond(message.content, "twitch", str(message.channel)): # type: ignore
                log_info(f"Skipping Twitch message (own message or cooldown): {message.content[:50]}...") # type: ignore
                return
            
            # Get user information
            user_id = str(message.author.id) # type: ignore
            username: str = message.author.name # type: ignore
            user_message: str = message.content # type: ignore
            
            # Skip if message is just a command without content
            if user_message.strip() in ['!chat', '!ai'] or (user_message.startswith('!') and len(user_message.strip()) <= 10):
                return
            
            # Check if auto-respond is enabled and apply response chance
            if not settings.twitch_auto_respond or random.random() > settings.twitch_response_chance:
                # Still update user context and relationships even if not responding
                await self._update_user_data_only(user_id, username, user_message)
                return
            
            # Process the message with full AI capabilities
            await self._process_chat_message(message)
            
        except Exception as e:
            log_error(f"Error processing Twitch message: {str(e)}")
            # Don't send error messages for every chat message to avoid spam

    async def _update_user_data_only(self, user_id: str, username: str, message: str):
        """Update user data without generating a response"""
        try:
            # Update user context
            update_user_context(user_id, {
                "message_count": 1,
                "username": username
            }, "twitch")
            
            # Update relationship data
            update_relationship_status(user_id, "twitch", "neutral")
            
            # Add to memory without generating response
            await self.memory_manager.add_memory(
                f"{username}: {message}",
                context={'user_id': user_id, 'platform': 'twitch'}
            )
            
        except Exception as e:
            log_error(f"Error updating user data: {str(e)}")

    async def _process_chat_message(self, message: twitchio.Message):
        """Process an incoming chat message with enhanced context awareness"""
        try:
            user_id = str(message.author.id)
            platform = "twitch"
            
            # Update user context with new interaction
            update_user_context(user_id, platform, {
                "last_interaction": datetime.now().isoformat(),
                "interaction_count": 1,  # Will be incremented
                "username": message.author.name
            })
            
            # Analyze message content
            msg_metadata = get_message_metadata(message.content, user_id, platform)
            
            # Update user context with analysis results
            update_user_context(user_id, platform, {
                "conversation_style": msg_metadata["style"],
                "topics": msg_metadata["topics"],
                "sentiment": msg_metadata["sentiment"]
            })
            
            # Get enhanced context for AI response
            user_context = get_user_context(user_id, platform)
            relationship = get_relationship_status(user_id, platform)
            
            # Prepare enhanced prompt with context
            enhanced_prompt = self._build_enhanced_prompt(
                message.content,
                user_context,
                relationship,
                msg_metadata
            )
            
            # Get AI response
            response = await self._get_ai_response(enhanced_prompt)
            
            if response:
                # Format response with username mention
                final_response = f"@{message.author.name} {response}"
                await message.channel.send(final_response)
            else:
                log_error("No response received from AI system")
                
        except Exception as e:
            log_error(f"Error processing chat message: {e}")
            log_error(traceback.format_exc())
            
    def _build_enhanced_prompt(self, message: str, user_context: dict, relationship: str, metadata: dict) -> str:
        """Build an enhanced prompt with user context and conversation analysis"""
        context_parts = []
        
        # Add user context
        username = user_context.get("username", "User")
        context_parts.append(f"[User: {username}, Relationship: {relationship}]")
        
        if user_context.get("interests"):
            interests = ", ".join(user_context["interests"][-3:])
            context_parts.append(f"[Interests: {interests}]")
        
        # Add conversation style
        context_parts.append(f"[Style: {metadata['style']}]")
        
        # Add sentiment
        context_parts.append(f"[Mood: {metadata['sentiment']}]")
        
        # Combine context with message
        context_string = " ".join(context_parts)
        return f"{context_string}\n\nUser: {message}"

    async def _get_ai_response(self, prompt: str):
        """Get a response from the AI system"""
        try:
            # Send to Oobabooga API
            import API.api_controller as api_controller
            api_controller.send_via_oogabooga(prompt)
            response = api_controller.receive_via_oogabooga()
            
            if response:
                # Clean and format the response
                response = clean_response(response)
                response = add_personality_flavor(response, settings.twitch_personality)
                
                # Validate message safety
                is_safe, safety_msg = validate_message_safety(response, "twitch")
                if not is_safe:
                    log_error(f"Unsafe message blocked: {safety_msg}")
                    return None
                
                return response
            else:
                log_error("No response received from Oobabooga API")
                return None
                
        except Exception as e:
            log_error(f"Error getting AI response: {str(e)}")
            return None

async def run_twitch_bot():
    """Run the Twitch bot"""
    if not TWITCH_TOKEN or not TWITCH_CHANNEL:
        log_error("Missing Twitch credentials. Bot not started.")
        return
        
    try:
        bot = TwitchBot()
        log_info("Starting Twitch bot...")
        await bot.start()
    except Exception as e:
        log_error(f"Failed to start Twitch bot: {str(e)}")
        raise

def start_twitch_bot():
    """Start the Twitch bot in a separate thread"""
    try:
        thread = threading.Thread(target=lambda: asyncio.run(run_twitch_bot()))
        thread.daemon = True
        thread.start()
        log_info("Twitch bot thread started")
    except Exception as e:
        log_error(f"Failed to start Twitch bot thread: {str(e)}")
        raise

def run_z_waif_twitch():
    """Main entry point for the Twitch bot"""
    try:
        log_startup()
        start_twitch_bot()
    except Exception as e:
        log_error(f"Failed to run Z-WAIF Twitch: {str(e)}")
        raise

def clean_response(response: str) -> str:
    """Clean and format the AI response"""
    # Remove any system notes or instructions
    if "[System Note:" in response:
        response = response[response.find("]") + 1:].strip()
    
    # Remove AI: prefix if present
    if response.startswith("AI:"):
        response = response[3:].strip()
    
    # Remove any leading/trailing quotes
    response = response.strip('"')
    
    return response

def add_personality_flavor(response: str, personality: str) -> str:
    """Add personality-specific flavor to the response"""
    if not response:
        return response
        
    personality = personality.lower()
    
    if personality == "friendly":
        # Add friendly emotes occasionally
        import random
        friendly_emotes = ["<3", ":)", "^_^", "=)", ":D"]
        if random.random() < 0.3:  # 30% chance
            response += f" {random.choice(friendly_emotes)}"
    
    elif personality == "professional":
        # Ensure proper punctuation and capitalization
        if not response.endswith((".", "!", "?")):
            response += "."
        response = response[0].upper() + response[1:]
    
    elif personality == "casual":
        # Add casual flair
        import random
        casual_phrases = [" btw", " haha", " tho", " ngl"]
        if random.random() < 0.2:  # 20% chance
            response += random.choice(casual_phrases)
    
    return response

def validate_message_safety(message: str, platform: str) -> tuple[bool, str]:
    """
    Validate if a message is safe to send.
    Returns (is_safe, reason_if_unsafe)
    """
    if not message:
        return False, "Empty message"
    
    # Check message length
    if platform == "twitch" and len(message) > 500:
        return False, "Message too long for Twitch"
    
    # Basic safety checks
    unsafe_patterns = [
        "http://", "https://",  # No raw URLs
        "[System", "[DEBUG",    # No system messages
        "```", "'''",          # No code blocks
        "{", "}"               # No JSON/code
    ]
    
    for pattern in unsafe_patterns:
        if pattern in message:
            return False, f"Contains unsafe pattern: {pattern}"
    
    return True, ""
