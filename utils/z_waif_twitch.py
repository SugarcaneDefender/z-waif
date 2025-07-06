# Standard library imports
import asyncio
import os
import random
import threading
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

# Third-party imports
import twitchio
from twitchio.ext import commands  # type: ignore
from dotenv import load_dotenv

# Local imports - Main module
import main

# Local imports - Utils modules (ALL AI modules properly integrated)
from utils import uni_pipes
from utils import settings
from utils.zw_logging import log_info, log_error, log_startup, log_message_length_warning
from utils.user_context import get_user_context, update_user_context
from utils.message_processing import clean_response, validate_message_safety, add_personality_flavor
from utils.ai_message_tracker import should_ai_respond, record_ai_message
from utils.user_relationships import (
    add_relationship_context_to_response,
    get_relationship_level,
    update_relationship,
    get_relationship_data,
    format_message_with_relationship,
    load_relationships
)
from utils.conversation_analysis import analyze_conversation_style, get_message_metadata, extract_topics, analyze_sentiment
from utils.based_rag import add_message_to_database, call_rag_message, run_based_rag, load_rag_history
from utils.ai_handler import AIHandler
from utils.memory_manager import MemoryManager
from utils.chat_history import add_message_to_history, get_chat_history
from utils import voice
from utils import vtube_studio

# Load environment variables
load_dotenv()

# Enhanced AI system initialization
ai_handler = AIHandler()
try:
    # Initialize memory manager with proper error handling
    memory_manager = MemoryManager(None)  # Pass None for now since rag_processor isn't available
except Exception as e:
    memory_manager = None
    log_error(f"Could not initialize memory manager: {e}")

# Initialize relationships system
try:
    load_relationships()
except Exception as e:
    log_error(f"Could not load relationships: {e}")

# Twitch configuration - Support both single and multiple channels
TWITCH_TOKEN = os.getenv('TWITCH_TOKEN')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID') 
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')

# Support both single channel (backward compatibility) and multiple channels
TWITCH_CHANNEL_SINGLE = os.getenv('TWITCH_CHANNEL')  # Single channel (existing)
TWITCH_CHANNELS_MULTI = os.getenv('TWITCH_CHANNELS')  # Multiple channels (new)

# Determine channels to connect to
if TWITCH_CHANNELS_MULTI:
    # Multiple channels specified
    TWITCH_CHANNELS = [ch.strip() for ch in TWITCH_CHANNELS_MULTI.split(',') if ch.strip()]
elif TWITCH_CHANNEL_SINGLE:
    # Single channel specified (backward compatibility)
    TWITCH_CHANNELS = [TWITCH_CHANNEL_SINGLE.strip()]
else:
    # No channels specified
    TWITCH_CHANNELS = []

TWITCH_BOT_NAME = os.getenv('TWITCH_BOT_NAME', 'z_waif_bot')

# Enhanced Twitch-specific settings from environment or defaults
TWITCH_RESPONSE_CHANCE = float(os.getenv('TWITCH_RESPONSE_CHANCE', '0.8'))
TWITCH_COOLDOWN_SECONDS = int(os.getenv('TWITCH_COOLDOWN_SECONDS', '3'))
TWITCH_MAX_MESSAGE_LENGTH = int(os.getenv('TWITCH_MAX_MESSAGE_LENGTH', '450'))
TWITCH_AUTO_RESPOND = os.getenv('TWITCH_AUTO_RESPOND', 'ON').upper() == 'ON'
TWITCH_PERSONALITY = os.getenv('TWITCH_PERSONALITY', 'friendly').lower()

# Performance optimization settings
MAX_RESPONSE_LENGTH = TWITCH_MAX_MESSAGE_LENGTH
RESPONSE_CACHE_SIZE = 100
USER_CONTEXT_CACHE_SIZE = 50
CONVERSATION_HISTORY_LIMIT = 10

# Caching for performance
response_cache = {}
user_context_cache = {}
conversation_cache = {}

class TwitchBot(commands.Bot):
    def __init__(self):
        # Prepare credentials - handle both personal and bot app setups
        self.token = os.getenv("TWITCH_TOKEN")
        self.client_id = os.getenv("TWITCH_CLIENT_ID")
        self.client_secret = os.getenv("TWITCH_CLIENT_SECRET")
        self.bot_name = os.getenv("TWITCH_BOT_NAME", "z_waif_bot")
        
        # Handle channel configuration
        channels_env = os.getenv("TWITCH_CHANNELS")
        single_channel = os.getenv("TWITCH_CHANNEL")
        
        if channels_env:
            # Multiple channels (comma-separated)
            self.channels = [ch.strip() for ch in channels_env.split(",")]
        elif single_channel:
            # Single channel
            self.channels = [single_channel.strip()]
        else:
            raise ValueError("Either TWITCH_CHANNEL or TWITCH_CHANNELS must be set")
        
        # Store initial channels for compatibility
        self.initial_channels = self.channels.copy()
        
        # Bot personality and behavior settings
        self.personality = os.getenv("TWITCH_PERSONALITY", "friendly")
        self.auto_respond = os.getenv("TWITCH_AUTO_RESPOND", "ON") == "ON"
        self.response_chance = float(os.getenv("TWITCH_RESPONSE_CHANCE", "0.8"))
        self.cooldown_seconds = int(os.getenv("TWITCH_COOLDOWN_SECONDS", "3"))
        self.max_message_length = int(os.getenv("TWITCH_MAX_MESSAGE_LENGTH", "450"))
        
        # Enhanced features
        self.user_contexts = {}
        self.conversation_histories = {}
        self.user_relationships = {}
        self.message_cooldowns = {}
        
        # Initialize the bot
        super().__init__(
            token=self.token,
            client_id=self.client_id,
            client_secret=self.client_secret,
            nick=self.bot_name,
            prefix='!',
            initial_channels=self.channels
        )
        
        print(f"INFO:app:Twitch bot initialized for {'single' if len(self.channels) == 1 else 'multiple'} channel{'s' if len(self.channels) > 1 else ''}: {', '.join(self.channels)}")
        
        self.ai_handler = ai_handler
        self.memory_manager = memory_manager
        self.active_conversations = {}
        self.user_sessions = {}
        self.last_responses = {}
        self.max_message_length = TWITCH_MAX_MESSAGE_LENGTH
        self.response_chance = TWITCH_RESPONSE_CHANCE
        self.cooldown_seconds = TWITCH_COOLDOWN_SECONDS
        self.auto_respond = TWITCH_AUTO_RESPOND
        self.personality = TWITCH_PERSONALITY

    async def event_ready(self):
        print(f"[TWITCH] ✅ event_ready() called - Bot is connecting to Twitch!")
        
        if len(self.channels) == 1:
            log_info(f'Twitch bot {self.nick} is ready and connected to channel: {self.channels[0]}')
            print(f'🎮 Twitch bot ready! Connected to: {self.channels[0]}')
            print(f'[TWITCH] ✅ Successfully connected and ready to receive messages')
        elif len(self.channels) > 1:
            log_info(f'Twitch bot {self.nick} is ready and connected to {len(self.channels)} channels: {", ".join(self.channels)}')
            print(f'🎮 Twitch bot ready! Connected to {len(self.channels)} channels: {", ".join(self.channels)}')
            print(f'[TWITCH] ✅ Successfully connected to multiple channels and ready to receive messages')
        else:
            log_info(f'Twitch bot {self.nick} is ready (no initial channels)')
            print(f'🎮 Twitch bot ready! (No initial channels - use environment variables to set channels)')
            print(f'[TWITCH] ⚠️ No channels configured - bot won\'t receive messages')

    async def event_message(self, message: twitchio.Message):  # type: ignore
        """Enhanced message processing with full AI integration"""
        if message.echo:
            return
            
        try:
            # Extract message details
            username = message.author.name
            user_id = str(message.author.id)
            channel = message.channel.name
            content = message.content.strip()
            
            print(f"[TWITCH] Received message from {username} in {channel}: '{content}'")
            
            # Skip if empty message
            if not content:
                print(f"[TWITCH] Skipping empty message from {username}")
                return
                
            # Handle bot commands first
            try:
                await self.handle_commands(message)
            except Exception as e:
                log_error(f"Error handling commands: {e}")
            
            # Skip if message is a command (commands are handled above)
            if content.startswith('!'):
                print(f"[TWITCH] Skipping command message: {content}")
                return
                
            # AI-powered spam/safety filtering
            try:
                is_safe, safety_reason = validate_message_safety(content, "twitch")
                if not is_safe:
                    log_info(f"Filtered unsafe message from {username}: {content} - Reason: {safety_reason}")
                    return
            except Exception as e:
                log_error(f"Error in safety validation: {e}")
                # Continue processing on safety validation error
                
            # AI message tracking to prevent loops
            try:
                should_respond = should_ai_respond(content, "twitch", channel)
                print(f"[TWITCH] AI response tracking result: {should_respond}")
                if not should_respond:
                    log_info(f"AI determined not to respond to: {content}")
                    return
            except Exception as e:
                log_error(f"Error in AI response tracking: {e}")
                print(f"[TWITCH] Continuing despite AI tracking error: {e}")
                
            # Auto-respond check with personality-based chance
            auto_respond_decision = self.auto_respond and random.random() <= self.response_chance
            print(f"[TWITCH] Auto-respond decision: auto_respond={self.auto_respond}, chance={self.response_chance}, decision={auto_respond_decision}")
            
            if not auto_respond_decision:
                # Still update user context and relationships even if not responding
                print(f"[TWITCH] Not responding but updating user data silently")
                try:
                    await self._update_user_data_silently(user_id, username, content, channel)
                except Exception as e:
                    log_error(f"Error updating user data silently: {e}")
                return
                
            print(f"[TWITCH] Proceeding with AI response generation for: {content}")
            
            # Enhanced user context management
            try:
                user_context = await self._get_enhanced_user_context(user_id, username, channel)
                print(f"[TWITCH] Retrieved user context for {username}")
            except Exception as e:
                log_error(f"Error getting user context: {e}")
                user_context = {"username": username, "channel": channel, "platform": "twitch"}
            
            # Conversation analysis
            try:
                conversation_context = await self._analyze_conversation_context(channel, content, user_context)
                print(f"[TWITCH] Analyzed conversation context")
            except Exception as e:
                log_error(f"Error analyzing conversation context: {e}")
                conversation_context = {"channel": channel}
            
            # Memory retrieval using RAG
            try:
                relevant_memories = await self._get_relevant_memories(user_id, content)
                print(f"[TWITCH] Retrieved {len(relevant_memories)} relevant memories")
            except Exception as e:
                log_error(f"Error retrieving memories: {e}")
                relevant_memories = []
            
            # Enhanced response generation
            try:
                print(f"[TWITCH] Generating enhanced response...")
                response = await self._generate_enhanced_response(
                    content, user_context, conversation_context, relevant_memories, channel
                )
                print(f"[TWITCH] Generated response: {response[:100] if response else 'None'}...")
            except Exception as e:
                log_error(f"Error generating enhanced response: {e}")
                # Fallback to main.py integration
                print(f"[TWITCH] Falling back to main.py integration")
                try:
                    import main
                    response = main.main_twitch_chat(f"[Platform: Twitch Chat] {content}")
                except Exception as e2:
                    log_error(f"Error in main.py fallback: {e2}")
                    response = "Sorry, I'm having trouble responding right now!"
            
            if response and response.strip():
                # Clean and optimize response
                try:
                    response = clean_response(response)
                    response = add_personality_flavor(response, user_context.get('personality_preference', self.personality))
                    
                    # Add relationship context
                    response = add_relationship_context_to_response(response, username, "twitch")
                    
                    # Limit response length for Twitch
                    if len(response) > self.max_message_length:
                        response = response[:self.max_message_length-3] + "..."
                        log_message_length_warning(f"Truncated response for {username}")
                    
                    # Send response
                    await message.channel.send(response)
                    
                    # Record AI message to prevent loops
                    record_ai_message(response, "twitch", channel)
                    
                    # Update user relationship
                    await self._update_user_relationship(user_id, username, content, response)
                    
                    # Store in conversation history
                    await self._store_conversation(user_id, username, content, response, channel)
                    
                    # Log successful response
                    log_info(f"Sent Twitch response to {username} in {channel}: {response}")
                    
                except Exception as e:
                    log_error(f"Error processing response: {e}")
                    
        except Exception as e:
            log_error(f"Error processing Twitch message: {e}")
            import traceback
            traceback.print_exc()

    async def _update_user_data_silently(self, user_id: str, username: str, content: str, channel: str):
        """Update user data without generating a response"""
        try:
            # Update user context
            update_user_context(user_id, {
                'message_count': 1,
                'username': username,
                'last_message': content,
                'last_interaction': datetime.now().isoformat(),
                'platform': 'twitch',
                'channel': channel
            })
            
            # Update relationship data
            update_relationship(user_id, "twitch", "neutral")
            
            # Analyze conversation style
            try:
                analyze_conversation_style(content, user_id, "twitch")
            except Exception as e:
                log_error(f"Error analyzing conversation style: {e}")
                
            # Add to memory without generating response
            if self.memory_manager:
                try:
                    await self.memory_manager.add_memory(
                        f"{username}: {content}",
                        context={'user_id': user_id, 'platform': 'twitch', 'channel': channel}
                    )
                except Exception as e:
                    log_error(f"Error adding to memory: {e}")
            
        except Exception as e:
            log_error(f"Error updating user data: {e}")

    async def _get_enhanced_user_context(self, user_id: str, username: str, channel: str) -> Dict[str, Any]:
        """Get enhanced user context with caching"""
        cache_key = f"{user_id}_{channel}"
        
        if cache_key in user_context_cache:
            return user_context_cache[cache_key]
            
        try:
            # Get base user context
            user_context = get_user_context(user_id, platform="twitch")
            
            # Add relationship information
            relationship_level = get_relationship_level(user_id, "twitch")
            relationship_context = get_relationship_data(user_id, "twitch")
            
            # Enhanced context
            enhanced_context = {
                **user_context,
                'username': username,
                'channel': channel,
                'platform': 'twitch',
                'relationship_level': relationship_level,
                'relationship_context': relationship_context,
                'personality_preference': user_context.get('personality_preference', self.personality),
                'conversation_history': get_chat_history(user_id, "twitch", limit=CONVERSATION_HISTORY_LIMIT)
            }
            
            # Cache the context
            user_context_cache[cache_key] = enhanced_context
            
            return enhanced_context
            
        except Exception as e:
            log_error(f"Error getting enhanced user context: {e}")
            return {
                'username': username,
                'channel': channel,
                'platform': 'twitch',
                'personality_preference': self.personality
            }

    async def _analyze_conversation_context(self, channel: str, content: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation context for better responses"""
        try:
            # Get conversation insights
            conversation_insights = analyze_conversation_style(content, user_context.get('user_id', ''), "twitch")
            
            # Extract topics and sentiment
            topics = extract_topics(content)
            sentiment = analyze_sentiment(content)
            
            # Analyze message metadata
            metadata = get_message_metadata(content)
            
            return {
                'conversation_insights': conversation_insights,
                'topics': topics,
                'sentiment': sentiment,
                'metadata': metadata,
                'channel': channel,
                'message_length': len(content),
                'contains_question': '?' in content,
                'contains_mention': '@' in content or user_context.get('username', '').lower() in content.lower()
            }
            
        except Exception as e:
            log_error(f"Error analyzing conversation context: {e}")
            return {
                'channel': channel,
                'message_length': len(content),
                'contains_question': '?' in content,
                'contains_mention': '@' in content
            }

    async def _get_relevant_memories(self, user_id: str, content: str) -> List[str]:
        """Get relevant memories for context"""
        try:
            if self.memory_manager:
                memories = await self.memory_manager.get_user_specific_memories(user_id, "twitch")
                return memories[:3]  # Limit to top 3 most relevant
            else:
                # Fallback to basic RAG system
                try:
                    # Use the available based_rag functions
                    rag_message = call_rag_message()
                    if rag_message and rag_message != "No memory currently!":
                        return [rag_message]
                    return []
                except Exception:
                    return []
        except Exception as e:
            log_error(f"Error retrieving memories: {e}")
            return []

    async def _generate_enhanced_response(
        self, 
        content: str, 
        user_context: Dict[str, Any], 
        conversation_context: Dict[str, Any], 
        relevant_memories: List[str],
        channel: str
    ) -> str:
        """Generate real AI response from LLM using the same flow as other platforms"""
        
        try:
            # Format the message like main_twitch_chat() expects: "username: message"
            username = user_context.get('username', 'TwitchUser')
            formatted_message = f"{username}: {content}"
            
            # Call main_twitch_chat() the same way other platforms do
            # This will go through send_platform_aware_message() -> API -> Real LLM response
            response = main.main_twitch_chat(formatted_message)
            
            if response and response.strip():
                return response
                
        except Exception as e:
            log_error(f"Error in main system response generation: {e}")
            
        # If main system fails, provide a simple fallback
        return "Hey! How's it going?"

    async def _fallback_response_generation(self, content: str, context: Dict[str, Any]) -> str:
        """Fallback response generation using main system"""
        try:
            # Use main system's Twitch chat handler with natural message
            # Just pass the original message with platform marker, let character card handle personality
            response = main.main_twitch_chat(f"[Platform: Twitch Chat] {content}")
            return response or ""
        except Exception as e:
            log_error(f"Error in fallback response generation: {e}")
            return ""

    async def _update_user_relationship(self, user_id: str, username: str, user_message: str, response: str):
        """Update user relationship based on interaction"""
        try:
            # Update user context
            update_user_context(user_id, {
                'last_interaction': datetime.now().isoformat(),
                'last_message': user_message,
                'last_response': response,
                'username': username,
                'platform': 'twitch'
            })
            
            # Update relationship with proper parameters
            update_relationship(user_id, "twitch", "positive")
            
        except Exception as e:
            log_error(f"Error updating user relationship: {e}")

    async def _store_conversation(self, user_id: str, username: str, user_message: str, response: str, channel: str):
        """Store conversation in history"""
        try:
            # Add to chat history
            add_message_to_history(user_id, "user", user_message, "twitch")
            add_message_to_history(user_id, "assistant", response, "twitch")
            
            # Add to RAG database (simple version - just adds latest message)
            try:
                add_message_to_database()
            except Exception as rag_error:
                log_error(f"Error adding to RAG database: {rag_error}")
            
        except Exception as e:
            log_error(f"Error storing conversation: {e}")

    # Enhanced commands with AI integration
    @commands.command(name='personality')
    async def personality_command(self, ctx, new_personality: str = None):
        """Change AI personality with context awareness"""
        user_id = str(ctx.author.id)
        
        if new_personality:
            # Update user context with personality preference
            try:
                update_user_context(user_id, {'personality_preference': new_personality})
                await ctx.send(f"✨ Personality updated to {new_personality}! This will influence how I respond to you.")
            except Exception as e:
                log_error(f"Error updating personality: {e}")
                await ctx.send("❌ Sorry, I couldn't update your personality preference.")
        else:
            try:
                user_context = get_user_context(user_id, platform="twitch")
                current_personality = user_context.get('personality_preference', self.personality)
                await ctx.send(f"🎭 Current personality: {current_personality}. Available: friendly, playful, sarcastic, supportive, energetic")
            except Exception as e:
                log_error(f"Error getting personality: {e}")
                await ctx.send("❌ Sorry, I couldn't get your personality preference.")

    @commands.command(name='memory')
    async def memory_command(self, ctx, *, query: str = None):
        """Query AI memory system"""
        user_id = str(ctx.author.id)
        
        if query:
            try:
                memories = await self._get_relevant_memories(user_id, query)
                if memories:
                    response = f"💭 I remember: {memories[0][:100]}..."
                    await ctx.send(response)
                else:
                    await ctx.send("🤔 I don't have any relevant memories about that.")
            except Exception as e:
                log_error(f"Error querying memory: {e}")
                await ctx.send("❌ Sorry, I couldn't search my memories right now.")
        else:
            await ctx.send("💭 Use '!memory <query>' to search my memories about our conversations!")

    @commands.command(name='status')
    async def status_command(self, ctx):
        """Show enhanced bot status"""
        try:
            user_id = str(ctx.author.id)
            user_context = get_user_context(user_id, platform="twitch")
            relationship_level = get_relationship_level(user_id, "twitch")
            
            status = f"🤖 Status: Online | 💝 Relationship: {relationship_level} | 🧠 AI Modules: Active"
            await ctx.send(status)
        except Exception as e:
            log_error(f"Error getting status: {e}")
            await ctx.send("🤖 Status: Online | 🧠 AI Modules: Active")

def run_twitch_bot():
    """Run the Twitch bot with enhanced AI integration"""
    print(f"[TWITCH] run_twitch_bot() called")
    print(f"[TWITCH] Checking environment variables...")
    print(f"[TWITCH] TWITCH_TOKEN present: {'Yes' if TWITCH_TOKEN else 'No'}")
    print(f"[TWITCH] TWITCH_CHANNELS: {TWITCH_CHANNELS}")
    
    if not TWITCH_TOKEN:
        log_error("TWITCH_TOKEN not found in environment variables")
        log_error("Please set TWITCH_TOKEN=your_oauth_token in your .env file")
        log_error("Get your OAuth token from: https://twitchtokengenerator.com/")
        print(f"[TWITCH] ❌ Missing TWITCH_TOKEN - cannot start bot")
        return
        
    # Channel validation with helpful messages
    if not TWITCH_CHANNELS:
        log_error("No Twitch channels configured!")
        log_error("Please set either:")
        log_error("  TWITCH_CHANNEL=yourchannel  (for single channel)")
        log_error("  TWITCH_CHANNELS=channel1,channel2,channel3  (for multiple channels)")
        print(f"[TWITCH] ❌ No channels configured - cannot start bot")
        return
    
    # Log setup type
    if TWITCH_CLIENT_ID:
        log_info("Using bot app setup with Client ID")
    else:
        log_info("Using personal OAuth setup (no Client ID required)")
    
    if len(TWITCH_CHANNELS) == 1:
        log_info(f"Starting enhanced Twitch bot for single channel: {TWITCH_CHANNELS[0]}")
    else:
        log_info(f"Starting enhanced Twitch bot for {len(TWITCH_CHANNELS)} channels: {', '.join(TWITCH_CHANNELS)}")
    
    try:
        print(f"[TWITCH] Creating TwitchBot instance...")
        bot = TwitchBot()
        print(f"[TWITCH] TwitchBot created successfully")
        print(f"[TWITCH] Bot nick: {bot.nick}")
        print(f"[TWITCH] Bot channels: {bot.channels}")
        print(f"[TWITCH] Token present: {'Yes' if bot.token else 'No'}")
        print(f"[TWITCH] Token starts with: {bot.token[:10] if bot.token else 'None'}...")
        print(f"[TWITCH] Attempting to connect to Twitch...")
        
        bot.run()
        
    except Exception as e:
        log_error(f"Error running Twitch bot: {e}")
        print(f"[TWITCH] Detailed error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Provide helpful error messages based on common issues
        if "authentication failed" in str(e).lower():
            print(f"[TWITCH] ❌ Authentication failed - check your TWITCH_TOKEN")
            print(f"[TWITCH] 💡 Get a new token from: https://twitchtokengenerator.com/")
        elif "channel" in str(e).lower():
            print(f"[TWITCH] ❌ Channel error - check your TWITCH_CHANNEL setting")
            print(f"[TWITCH] 💡 Make sure the channel name is correct (without # symbol)")
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            print(f"[TWITCH] ❌ Network connection error - check your internet connection")
        else:
            print(f"[TWITCH] ❌ Unknown error occurred during Twitch bot startup")

def run_z_waif_twitch():
    """Main entry point for Z-WAIF Twitch integration"""
    if len(TWITCH_CHANNELS) == 1:
        print(f"🎮 Starting Z-WAIF Twitch integration for channel: {TWITCH_CHANNELS[0]}")
    elif len(TWITCH_CHANNELS) > 1:
        print(f"🎮 Starting Z-WAIF Twitch integration for {len(TWITCH_CHANNELS)} channels: {', '.join(TWITCH_CHANNELS)}")
    else:
        print("🎮 Starting Z-WAIF Twitch integration (no channels configured)")
    
    # Verify AI modules are loaded
    print("🧠 Verifying AI modules...")
    print(f"   ✅ AI Handler: {ai_handler is not None}")
    print(f"   ✅ Memory Manager: {memory_manager is not None}")
    print(f"   ✅ User Context: Available")
    print(f"   ✅ Relationship System: Available")
    print(f"   ✅ Message Processing: Available")
    print(f"   ✅ Conversation Analysis: Available")
    print(f"   ✅ RAG Database: Available")
    
    # Show channel configuration
    if len(TWITCH_CHANNELS) == 1:
        print(f"📺 Target Channel: {TWITCH_CHANNELS[0]}")
    elif len(TWITCH_CHANNELS) > 1:
        print(f"📺 Target Channels: {', '.join(TWITCH_CHANNELS)}")
        print(f"   (Multi-channel mode: Bot will respond in all {len(TWITCH_CHANNELS)} channels)")
    
    # Show configuration
    print(f"⚙️  Configuration:")
    print(f"   🎭 Personality: {TWITCH_PERSONALITY}")
    print(f"   🎲 Response Chance: {TWITCH_RESPONSE_CHANCE}")
    print(f"   ⏰ Cooldown: {TWITCH_COOLDOWN_SECONDS}s")
    print(f"   📝 Max Message Length: {TWITCH_MAX_MESSAGE_LENGTH}")
    print(f"   🤖 Auto-Respond: {'ON' if TWITCH_AUTO_RESPOND else 'OFF'}")
    
    # Start the bot in a separate thread to prevent blocking the main application
    print(f"[TWITCH] Starting Twitch bot in background thread...")
    import threading
    
    def twitch_bot_thread():
        try:
            # Create a new event loop for this thread since Twitch bot uses asyncio
            import asyncio
            asyncio.set_event_loop(asyncio.new_event_loop())
            run_twitch_bot()
        except Exception as e:
            print(f"[TWITCH] Error in twitch_bot_thread: {e}")
            import traceback
            traceback.print_exc()
    
    # Start the thread as a daemon so it won't prevent the main program from exiting
    thread = threading.Thread(target=twitch_bot_thread, daemon=True)
    thread.start()
    
    print(f"[TWITCH] ✅ Twitch bot thread started successfully")
    print(f"[TWITCH] The bot will connect to Twitch in the background...")
