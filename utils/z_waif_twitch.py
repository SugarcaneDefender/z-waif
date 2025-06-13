from twitchio.ext import commands # type: ignore
import os
import asyncio
import random
from dotenv import load_dotenv
from utils import settings
from zw_logging import (
    log_info, log_error, log_startup, log_message_length_warning,
)
import threading
from user_context import get_user_context, update_user_context
from message_processing import clean_response, validate_message_safety, add_personality_flavor
from ai_message_tracker import should_ai_respond, record_ai_message
from user_relationships import (
    add_relationship_context_to_response,
    update_relationship,
    analyze_conversation_style
)
from memory_manager import MemoryManager, MultiprocessRAG
from ai_handler import AIHandler
from sentence_transformers import SentenceTransformer
# import main

load_dotenv()

TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")

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
            token = TWITCH_TOKEN
            channel = TWITCH_CHANNEL
            client_id = os.environ.get('TWITCH_CLIENT_ID')
            
            if not token.startswith('oauth:'):
                token = f'oauth:{token}'
                
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

    async def event_message(self, message):
        if message.echo:
            return
            
        try:
            # Check message length
            if len(message.content) > 2000:
                log_message_length_warning(message.content, len(message.content), "Twitch")
                return
                
            log_info(f"Twitch message from {message.author.name}: {message.content}")
            
            # Handle bot commands first
            await self.handle_commands(message)
            
            # Check if we should respond to this message
            if not should_ai_respond(message.content, "twitch", str(message.channel)):
                log_info(f"Skipping Twitch message (own message or cooldown): {message.content[:50]}...")
                return
            
            # Get user information
            user_id = str(message.author.id)
            username = message.author.name
            user_message = message.content
            
            # Skip if message is just a command without content
            if user_message.strip() in ['!chat', '!ai'] or (user_message.startswith('!') and len(user_message.strip()) <= 10):
                return
            
            # Check if auto-respond is enabled and apply response chance
            if not settings.twitch_auto_respond or random.random() > settings.twitch_response_chance:
                # Still update user context and relationships even if not responding
                await self._update_user_data_only(user_id, username, user_message)
                return
            
            # Process the message with full AI capabilities
            await self._process_chat_message(message, user_id, username, user_message)
            
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
            update_relationship(user_id, "twitch", "neutral")
            analyze_conversation_style(message, user_id, "twitch")
            
            # Add to memory without generating response
            await self.memory_manager.add_memory(
                f"{username}: {message}",
                context={'user_id': user_id, 'platform': 'twitch'}
            )
            
        except Exception as e:
            log_error(f"Error updating user data: {str(e)}")

    async def _process_chat_message(self, message, user_id: str, username: str, user_message: str):
        """Process chat message with full AI capabilities"""
        try:
            # Handle special regeneration commands
            if user_message.lower() in ['!regen', '!reroll', '!redo']:
                await self._handle_regeneration(message)
                return
            
            # Handle special AI commands
            if user_message.lower().startswith('!'):
                command_parts = user_message[1:].split()
                command = command_parts[0].lower()
                args = command_parts[1:] if len(command_parts) > 1 else []
                
                if command in ['help', 'about', 'status', 'joke', 'quote']:
                    user_context = get_user_context(user_id, "twitch")
                    user_context['username'] = username
                    user_context['platform'] = 'twitch'
                    
                    response = await self.ai_handler.process_command(command, args, user_context)
                    final_response = f"@{username} {response}"
                    
                    # Validate message safety
                    is_safe, safety_msg = validate_message_safety(final_response, "twitch")
                    if is_safe:
                        await message.channel.send(final_response)
                        record_ai_message(response, "twitch", str(message.channel))
                    else:
                        log_error(f"Unsafe message blocked: {safety_msg}")
                    return
            
            # Regular chat message processing
            user_context = get_user_context(user_id, "twitch")
            user_context['username'] = username
            user_context['platform'] = 'twitch'
            
            # Update user context and relationship data
            update_user_context(user_id, {
                "message_count": 1,
                "username": username
            }, "twitch")
            update_relationship(user_id, "twitch", "neutral")
            analyze_conversation_style(user_message, user_id, "twitch")
            
            # Get relevant memories
            relevant_memories = await self.memory_manager.retrieve_relevant_memories(user_message)
            user_specific_memories = await self.memory_manager.get_user_specific_memories(user_id, "twitch")
            
            # Combine memories and generate response
            all_memories = relevant_memories + user_specific_memories
            ai_response = await self.ai_handler.generate_contextual_response(
                user_message,
                user_context,
                all_memories
            )
            
            # Process and send response
            if ai_response:
                final_response = clean_response(ai_response)
                final_response = add_personality_flavor(final_response, settings.twitch_personality)
                final_response = add_relationship_context_to_response(final_response, user_id, "twitch")
                final_response = f"@{username} {final_response}"
                
                # Validate and send
                is_safe, safety_msg = validate_message_safety(final_response, "twitch")
                if is_safe:
                    await message.channel.send(final_response) # type: ignore
                    record_ai_message(ai_response, "twitch", str(message.channel)) # type: ignore
                else:
                    log_error(f"Unsafe message blocked: {safety_msg}")
            
        except Exception as e:
            log_error(f"Error processing chat message: {str(e)}")

    async def _handle_regeneration(self, message):
        """Handle regeneration requests"""
        try:
            # Implementation of regeneration logic
            pass
        except Exception as e:
            log_error(f"Error processing regeneration: {str(e)}")
            await message.channel.send(f"@{message.author.name} ❌ Error processing regeneration") # type: ignore

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
