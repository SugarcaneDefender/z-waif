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
import re
import json
import logging
from typing import Optional, Dict, Any
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
            update_user_context(user_id, "twitch", {
                "interaction_count": 1,
                "username": username
            })
            
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
            
            # If the primary path returns nothing, fall back to a direct Oobabooga call (non-streaming)
            if not response or len(str(response).strip()) == 0 or str(response).startswith("Error:"):
                log_info("Primary AI request returned empty – falling back to direct API call…")

                from API.oobaooga_api import api_standard

                fallback_request = {
                    "prompt": prompt,
                    "max_tokens": settings.max_tokens,
                    "truncation_length": api_controller.max_context,
                    "stop": settings.stopping_strings,
                    "character": api_controller.CHARACTER_CARD,
                }

                response = api_standard(fallback_request)

            if response and not str(response).startswith("Error:"):
                # Clean and format the response
                response = clean_response(response)
                response = add_personality_flavor(response, settings.twitch_personality)

                # Validate for safety before sending
                is_safe, reason = await validate_message_safety(response, "twitch")
                if not is_safe:
                    log_error(f"AI response blocked for safety reasons: {reason}")
                    return None

                return response

            log_error("Fallback AI request also failed or returned no usable content")
            return None
                
        except Exception as e:
            log_error(f"Error getting AI response: {str(e)}")
            return None

async def run_twitch_bot():
    """Initializes and runs the Twitch bot."""
    bot = TwitchBot()
    try:
        await bot.start()
    except twitchio.errors.AuthenticationError as e:
        log_error(f"Failed to start Twitch bot: {e}")
    except Exception as e:
        log_error(f"An unexpected error occurred in Twitch bot: {e}")


def start_twitch_bot():
    asyncio.run(run_twitch_bot())


def run_z_waif_twitch():
    twitch_thread = threading.Thread(target=start_twitch_bot)
    twitch_thread.daemon = True
    twitch_thread.start()
    log_info("Twitch bot thread started")


def clean_response(response: str) -> str:
    """Clean the AI response by removing unwanted artifacts"""
    # Remove anything that looks like a Discord invite
    response = re.sub(r'discord.gg/([a-zA-Z0-9]+)', '[link removed]', response)
    # Remove any extra newlines or whitespace
    response = ' '.join(response.split())
    # Limit response length
    if len(response) > settings.twitch_max_message_length:
        response = response[:settings.twitch_max_message_length]
    return response

def add_personality_flavor(response: str, personality: str) -> str:
    """Add personality to the response based on settings"""
    if personality == "friendly":
        # Add a friendly emoji if one isn't already there
        if not any(char in response for char in ["😊", "😄", "👋"]):
            response += f" {random.choice(['😊', '😄', '👋'])}"
    elif personality == "edgy":
        # Add a more cynical or edgy flavor
        if random.random() < 0.2:
            response += f" ...or whatever."
    # Can add more personalities here
    return response

async def validate_message_safety(message: str, platform: str) -> tuple[bool, str]:
    """
    Validate the message for safety and appropriateness.
    
    Returns:
        tuple[bool, str]: (is_safe, reason)
    """
    # Placeholder for safety validation logic
    # Example: Check for banned words, spam, etc.
    if "some_banned_word" in message:
        return (False, "Contains banned content")
    
    return (True, "")
