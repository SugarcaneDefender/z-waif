from twitchio.ext import commands
import os
import asyncio
import random
from dotenv import load_dotenv
from utils import settings
import logging
from utils.zw_logging import log_info, log_error
import threading
import time
import API.api_controller as api_controller
from user_context import get_user_context, update_user_context
from chat_history import get_chat_history, update_chat_history, add_message_to_history
from message_processing import clean_response, validate_message_safety, add_personality_flavor
from utils.ai_message_tracker import should_ai_respond, record_ai_message
from user_relationships import (
    format_message_with_relationship, 
    add_relationship_context_to_response,
    update_relationship,
    analyze_conversation_style
)
from memory_manager import MemoryManager, MultiprocessRAG
from utils.ai_handler import AIHandler
from sentence_transformers import SentenceTransformer
import main

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")

if not TWITCH_TOKEN or not TWITCH_CHANNEL:
    log_error("TWITCH_TOKEN or TWITCH_CHANNEL not found. Twitch module disabled.")
else:
    log_info("Twitch credentials loaded successfully.")

class TwitchBot(commands.Bot):
    def __init__(self):
        log_info("Initializing Twitch Bot with enhanced AI capabilities...")
        
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
            
        print(f"\n=== Initializing Enhanced Twitch Bot ===")
        print(f"Channel: {channel}")
        print(f"Token Status: {'Valid' if token else 'Missing'}")
        print(f"Client ID Status: {'Valid' if client_id else 'Missing'}")
        print(f"AI Memory System: Loaded")
        print(f"Relationship Tracking: Active")
        print(f"Message Safety: Enabled")
        
        super().__init__(
            token=token,
            client_id=client_id,
            nick=channel,
            prefix='!',
            initial_channels=[channel]
        )
        logging.info("Enhanced Twitch Bot initialized with AI capabilities.")
        
    async def event_ready(self):
        print(f"\n=== Enhanced Twitch Bot Ready! ===")
        print(f"Connected as: {self.nick}")
        print(f"User ID: {self.user_id}")
        print(f"AI Systems: Online")
        print(f"Personality: {settings.twitch_personality}")
        print(f"Auto-respond: {'Enabled' if settings.twitch_auto_respond else 'Disabled'}")
        log_info("Enhanced Twitch Bot is ready and all AI systems are online!")

    async def event_message(self, message):
        if message.echo:
            return
            
        log_info(f"Twitch message from {message.author.name}: {message.content}")
        
        # Handle bot commands first
        await self.handle_commands(message)
        
        # Check if we should respond to this message (prevents self-response loops)
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
        
        try:
            # Process the message with full AI capabilities
            await self._process_chat_message(message, user_id, username, user_message)
            
        except Exception as e:
            log_error(f"Error processing Twitch message: {e}")
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
            log_error(f"Error updating user data: {e}")
    
    async def _process_chat_message(self, message, user_id: str, username: str, user_message: str):
        """Process chat message with full AI capabilities"""
        
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
        
        # Get user context and enhance it
        user_context = get_user_context(user_id, "twitch")
        user_context['username'] = username
        user_context['platform'] = 'twitch'
        
        # Update user context with current interaction
        update_user_context(user_id, {
            "message_count": 1,
            "username": username
        }, "twitch")
        
        # Update relationship data
        update_relationship(user_id, "twitch", "neutral")
        analyze_conversation_style(user_message, user_id, "twitch")
        
        # Get relevant memories
        relevant_memories = await self.memory_manager.retrieve_relevant_memories(user_message)
        user_specific_memories = await self.memory_manager.get_user_specific_memories(user_id, "twitch")
        
        # Combine all memories
        all_memories = relevant_memories + user_specific_memories
        
        # Generate AI response with full context
        # Option 1: Use local AI handler (current method)
        ai_response = await self.ai_handler.generate_contextual_response(
            user_message, 
            user_context, 
            all_memories
        )
        
        # Option 2: Use main shadow chat (alternative method - uncomment if needed)
        # main.main_twitch_chat(user_message)
        # ai_response = api_controller.receive_via_oogabooga()
        
        if ai_response:
            # Add relationship-specific enhancements
            enhanced_response = add_relationship_context_to_response(ai_response, username, "twitch")
            
            # Add personality flavor based on settings
            personality_response = add_personality_flavor(enhanced_response, settings.twitch_personality)
            
            # Clean and validate the response
            cleaned_response = clean_response(personality_response, "twitch")
            final_response = f"@{username} {cleaned_response}"
            
            # Final safety check
            is_safe, safety_msg = validate_message_safety(final_response, "twitch")
            
            if is_safe:
                await message.channel.send(final_response)
                
                # Record the sent message to prevent self-response
                record_ai_message(cleaned_response, "twitch", str(message.channel))
                
                log_info(f"AI responded to {username} on Twitch: {cleaned_response[:50]}...")
                
                # Add to chat history
                add_message_to_history(user_id, "user", user_message, "twitch", 
                                     {"username": username, "channel": str(message.channel)})
                add_message_to_history(user_id, "assistant", cleaned_response, "twitch")
                
                # Add to memory for future context
                await self.memory_manager.add_memory(
                    f"{username}: {user_message}\nAI: {cleaned_response}",
                    context={'user_id': user_id, 'platform': 'twitch', 'interaction_type': 'chat'}
                )
                
            else:
                log_error(f"Unsafe response blocked: {safety_msg}")
                # Send a safe fallback instead
                fallback = "I'd love to chat but I'm having trouble finding the right words! 😅"
                await message.channel.send(f"@{username} {fallback}")
                record_ai_message(fallback, "twitch", str(message.channel))
        else:
            log_error("No AI response generated")
    
    async def _handle_regeneration(self, message):
        """Handle regeneration commands using main shadow chat functions"""
        try:
            username = message.author.name
            
            # Use main shadow chat function for regeneration
            main.main_twitch_next()
            
            # Get the response from the API
            message_reply = api_controller.receive_via_oogabooga()
            
            if message_reply:
                cleaned_response = clean_response(message_reply, "twitch")
                final_response = f"@{username} {cleaned_response}"
                
                # Safety check
                is_safe, safety_msg = validate_message_safety(final_response, "twitch")
                if is_safe:
                    await message.channel.send(final_response)
                    record_ai_message(cleaned_response, "twitch", str(message.channel))
                else:
                    await message.channel.send(f"@{username} ✅ Regenerated (but kept it safe!)")
            else:
                await message.channel.send(f"@{username} ✅ Regenerated")
                
        except Exception as e:
            log_error(f"Error processing regeneration: {e}")
            await message.channel.send(f"@{message.author.name} ❌ Error processing regeneration")
    
    # @commands.command(name='stats')
    # async def stats_command(self, ctx):
    #     """Show AI statistics"""
    #     try:
    #         memory_stats = await self.memory_manager.get_memory_stats()
    #         user_stats = get_user_stats("twitch")
    #
    #         stats_msg = f"🤖 AI Stats: {memory_stats['total_memories']} memories, {user_stats['total_users']} users tracked"
    #         await ctx.send(stats_msg)
    #     except Exception as e:
    #         log_error(f"Error getting stats: {e}")
    #         await ctx.send("❌ Error getting stats")
    
    @commands.command(name='personality')
    async def personality_command(self, ctx, new_personality: str = None):
        """Change or check AI personality"""
        try:
            if new_personality:
                valid_personalities = ["friendly", "enthusiastic", "sarcastic", "supportive", "casual", "playful"]
                if new_personality.lower() in valid_personalities:
                    settings.twitch_personality = new_personality.lower()
                    await ctx.send(f"🎭 Personality changed to: {new_personality}")
                else:
                    await ctx.send(f"❌ Invalid personality. Valid options: {', '.join(valid_personalities)}")
            else:
                await ctx.send(f"🎭 Current personality: {settings.twitch_personality}")
        except Exception as e:
            log_error(f"Error changing personality: {e}")
            await ctx.send("❌ Error changing personality")

async def run_twitch_bot():
    if not TWITCH_TOKEN or not TWITCH_CHANNEL:
        log_error("Cannot start Twitch bot without credentials.")
        return
    log_info("Starting Twitch bot...")
    if not settings.TWITCH_ENABLED:
        log_error("Twitch bot is disabled in settings.")
        return
    try:
        bot = TwitchBot()
        while True:
            try:
                await bot.start()
                log_info("Twitch bot started successfully.")
                break
            except Exception as e:
                log_error(f"Twitch bot crashed: {e}")
                log_info("Attempting to restart Twitch bot in 10 seconds...")
                await asyncio.sleep(10)  # Use async sleep
    except Exception as e:
        log_error(f"Failed to start Twitch bot: {e}")

def start_twitch_bot():
    log_info("Entry point for starting the Twitch bot.")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_twitch_bot())
    except Exception as e:
        log_error(f"Failed to start Twitch bot: {e}")

def run_twitch():
    """Main entry point called by main.py"""
    log_info("Starting Z-WAIF Twitch integration...")
    start_twitch_bot()
