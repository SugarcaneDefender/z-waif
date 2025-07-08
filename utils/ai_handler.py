# import asyncio
from typing import Dict, List, Any, Optional
import random
from utils.zw_logging import log_info, log_error


class AIHandler:
    def __init__(self):
        self.default_personality = "friendly"
        self.response_cache = {}
        self.max_cache_size = 100
        
        # Enhanced chatpops organized by context
        self.chatpops = {
            "greeting": [
                "Oh, hey there!", "Well, hello!", "Oh, hi!", "Hey there!", 
                "Oh, nice to see you!", "Well, hey!", "Oh, what's up?"
            ],
            "thinking": [
                "Hmm, let me think", "Let me see...", "Hmm, interesting", 
                "Oh, that's a good question", "Hmm, you know what", "Let me think about that"
            ],
            "agreement": [
                "Oh, absolutely", "Yeah, totally", "Oh, for sure", "Yeah, exactly", 
                "That's so true", "Oh, definitely", "I hear you", "Hmm, I agree"
            ],
            "positive": [
                "Oh, I love that", "Oh, awesome", "That's great", "Oh, amazing", 
                "That's wonderful", "Oh, fantastic", "Oh, brilliant", "That's so cool"
            ],
            "casual": [
                "Oh, yeah", "Yeah, well", "Hmm, okay", "Oh, right", "Yeah, I see", 
                "That's fair", "Oh, I see", "Yeah, of course"
            ],
            "surprise": [
                "Oh, wow", "Oh, really?", "That's interesting", "Oh, nice", 
                "Oh, cool", "Hmm, interesting", "Oh, sweet"
            ],
            "gaming": [
                "Oh, nice move!", "That's epic!", "Oh, awesome!", "Yeah, let's go!", 
                "That's so cool!", "Oh, perfect!", "Hmm, interesting strategy"
            ],
            "personal": [
                "Oh, that's sweet", "I hear you", "That makes sense", "Oh, I get it", 
                "That's really nice", "Oh, I understand", "That's so thoughtful"
            ]
        }

    def get_contextual_chatpop(self, context: Dict[str, Any] = None, message: str = "") -> str:
        """Get a contextually appropriate chatpop"""
        if not context:
            context = {}
            
        platform = context.get("platform", "personal")
        personality = context.get("personality", "friendly")
        
        # Determine context based on message content and platform
        message_lower = message.lower()
        
        # Gaming context
        if platform == "minecraft" or "game" in message_lower or "play" in message_lower:
            return random.choice(self.chatpops["gaming"])
        
        # Greeting context
        if any(word in message_lower for word in ["hello", "hi", "hey", "morning", "evening"]):
            return random.choice(self.chatpops["greeting"])
            
        # Question context (thinking)
        if "?" in message or any(word in message_lower for word in ["what", "how", "why", "when", "where"]):
            return random.choice(self.chatpops["thinking"])
            
        # Positive context
        if any(word in message_lower for word in ["love", "awesome", "great", "amazing", "cool", "nice"]):
            return random.choice(self.chatpops["positive"])
            
        # Agreement context
        if any(word in message_lower for word in ["yes", "agree", "right", "exactly", "true"]):
            return random.choice(self.chatpops["agreement"])
            
        # Surprise context
        if any(word in message_lower for word in ["wow", "really", "seriously", "no way"]):
            return random.choice(self.chatpops["surprise"])
            
        # Personal conversation context
        if platform in ["voice", "webui", "cmd"] or any(word in message_lower for word in ["feel", "think", "believe"]):
            return random.choice(self.chatpops["personal"])
        
        # Default to casual
        return random.choice(self.chatpops["casual"])

    async def generate_response(
        self, prompt: str, personality: Optional[str] = None, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate AI response using the main API controller"""
        try:
            # Import only when needed to avoid circular imports
            import API.api_controller as api_controller
            
            # Use provided personality or default
            current_personality = personality or self.default_personality

            # Add personality context to prompt if needed
            enhanced_prompt = self._enhance_prompt_with_personality(
                prompt, current_personality, context
            )

            # Check cache first
            cache_key = hash(enhanced_prompt)
            if cache_key in self.response_cache:
                log_info("Using cached response")
                return self.response_cache[cache_key]

            # Generate response using main API with platform context
            api_controller.send_via_oogabooga(enhanced_prompt)
            response = api_controller.receive_via_oogabooga()
            
            # Clean response based on platform if context provided
            if context and context.get("platform"):
                response = self._clean_response_for_platform(response, context["platform"])

            if response:
                # Cache the response
                self._add_to_cache(cache_key, response)
                log_info(f"Generated AI response: {response[:50]}...")
                return response
            else:
                log_error("No response received from API")
                return self._get_fallback_response(current_personality)

        except Exception as e:
            log_error(f"Error generating AI response: {e}")
            return self._get_fallback_response(personality or self.default_personality)

    def _enhance_prompt_with_personality(
        self, prompt: str, personality: str, context: Dict[str, Any] = None
    ) -> str:
        """Enhance prompt with personality and context"""
        personality_instructions = {
            "friendly": "Respond in a warm, friendly, and approachable manner.",
            "enthusiastic": "Respond with high energy and excitement!",
            "sarcastic": "Respond with subtle wit and sarcasm (but keep it playful).",
            "supportive": "Respond with empathy and encouragement.",
            "casual": "Respond in a relaxed, informal way like talking to a friend.",
            "professional": "Respond in a polite and professional manner.",
            "playful": "Respond with humor and playfulness.",
        }

        personality_instruction = personality_instructions.get(
            personality, personality_instructions["friendly"]
        )

        # Build enhanced prompt
        enhanced_parts = [personality_instruction]

        # Add platform context if available
        if context:
            if context.get("platform"):
                platform = context["platform"]
                # Add standardized platform context tags
                if platform == "twitch":
                    enhanced_parts.insert(0, "[Platform: Twitch Chat]")
                    enhanced_parts.append("Keep responses concise and engaging for Twitch chat.")
                elif platform == "discord":
                    enhanced_parts.insert(0, "[Platform: Discord]")
                    enhanced_parts.append("This is for Discord - you can be casual and use emojis.")
                elif platform == "voice":
                    enhanced_parts.insert(0, "[Platform: Voice Chat - Personal Conversation]")
                    enhanced_parts.append("This is a personal voice conversation.")
                elif platform == "webui":
                    enhanced_parts.insert(0, "[Platform: Web Interface - Personal Chat]")
                    enhanced_parts.append("This is a personal chat through the web interface.")
                elif platform == "cmd":
                    enhanced_parts.insert(0, "[Platform: Command Line - Personal Chat]")
                    enhanced_parts.append("This is a personal chat through the command line.")
                elif platform == "minecraft":
                    enhanced_parts.insert(0, "[Platform: Minecraft Game Chat]")
                    enhanced_parts.append("Keep responses short for Minecraft game chat.")
                else:
                    enhanced_parts.insert(0, f"[Platform: {platform}]")

            if context.get("user_relationship"):
                relationship = context["user_relationship"]
                relationship_instructions = {
                    "stranger": "Be polite and welcoming to this new person.",
                    "acquaintance": "Be friendly - you've chatted with them before.",
                    "friend": "Be casual and warm - they're a regular here.",
                    "close_friend": "Be enthusiastic - they're one of your favorites!",
                    "vip": "Be excited - this is a special member of the community!",
                }
                if relationship in relationship_instructions:
                    enhanced_parts.append(relationship_instructions[relationship])

        enhanced_parts.append(f"\nUser message: {prompt}")

        return " ".join(enhanced_parts)

    def _add_to_cache(self, key: str|int, response: str):
        """Add response to cache with size management"""
        if len(self.response_cache) >= self.max_cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.response_cache))
            del self.response_cache[oldest_key]

        self.response_cache[key] = response

    def _get_fallback_response(self, personality: str) -> str:
        """Get fallback response when AI generation fails"""
        fallback_responses = {
            "friendly": "I'm having trouble thinking of a response right now, but thanks for chatting! 😊",
            "enthusiastic": "Oops! My brain had a little hiccup there! But I'm still excited to chat! 🎉",
            "sarcastic": "Well, this is awkward... my witty response generator just broke. How convenient.",
            "supportive": "I'm sorry, I'm having a technical moment. But I'm here for you! 💜",
            "casual": "Hmm, drawing a blank here. That's weird. What were we talking about again?",
            "professional": "I apologize, but I'm experiencing a technical difficulty. Please try again.",
            "playful": "Oopsie! My brain.exe stopped working for a second there! 🤪",
        }

        return fallback_responses.get(personality, fallback_responses["friendly"])

    def _clean_response_for_platform(self, response: str, platform: str) -> str:
        """Clean response based on platform requirements"""
        if not response:
            return ""
        
        import re
        
        clean_reply = response.strip()
        
        # Remove platform context markers
        clean_reply = re.sub(r'\[Platform:[^\]]*\]', '', clean_reply).strip()
        
        # Platform-specific cleaning
        if platform == "twitch":
            return self._clean_twitch_response(clean_reply)
        elif platform == "discord":
            return self._clean_discord_response(clean_reply)
        elif platform in ["voice", "webui", "cmd"]:
            return self._clean_personal_response(clean_reply)
        elif platform == "minecraft":
            return self._clean_minecraft_response(clean_reply)
        else:
            return self._clean_personal_response(clean_reply)
    
    def _clean_personal_response(self, response: str) -> str:
        """Clean for personal conversations"""
        import re
        streaming_phrases = [
            "Thanks for watching", "enjoying the stream", "Welcome to my stream",
            "Don't forget to follow", "Hey viewers", "streaming", "stream", "viewers"
        ]
        for phrase in streaming_phrases:
            if phrase.lower() in response.lower():
                return "Hey! How are you doing? What's on your mind?"
        
        clean_reply = re.sub(r'\*[^*]*\*', '', response).strip()
        return clean_reply if clean_reply else "Hi! Nice to chat with you!"
    
    def _clean_twitch_response(self, response: str) -> str:
        """Clean for Twitch conversations"""
        import re
        streaming_phrases = ["Thanks for watching", "Don't forget to follow", "Welcome to my stream"]
        for phrase in streaming_phrases:
            if phrase.lower() in response.lower():
                return "Hey! How's it going?"
        
        clean_reply = re.sub(r'\*[^*]*\*', '', response).strip()
        return clean_reply if clean_reply else "Hi! Nice to see you!"
    
    def _clean_discord_response(self, response: str) -> str:
        """Clean for Discord conversations"""
        import re
        streaming_phrases = ["Thanks for watching", "stream has just ended"]
        for phrase in streaming_phrases:
            if phrase.lower() in response.lower():
                return "Hey! What's up? 😊"
        
        return response if response else "Hey there! 👋"
    
    def _clean_minecraft_response(self, response: str) -> str:
        """Clean for Minecraft conversations"""
        if len(response) > 100:
            response = response[:97] + "..."
        return response if response else "Hi! How's the game going?"

    async def generate_contextual_response(
        self, message: str, user_context: Dict[str, Any], memories: List[str] = None
    ) -> str:
        """Generate response with full context - simplified for natural conversation"""
        
        # Use a natural approach for all platforms
        # Let the character card and main system handle the personality
        platform = user_context.get("platform", "unknown")
        username = user_context.get("username", "")
        
        # Create a natural conversational prompt without formal structure
        if username and username.lower() not in message.lower():
            # Only add name context if it's not already in the message
            natural_prompt = f"{username} says: {message}"
        else:
            natural_prompt = message
        
        # Determine personality based on relationship
        personality = self._get_personality_for_relationship(
            user_context.get("relationship_level", "stranger")
        )

        return await self.generate_response(
            natural_prompt,
            personality=personality,
            context={
                "platform": platform,
                "user_relationship": user_context.get("relationship_level"),
            },
        )

    def _get_personality_for_relationship(self, relationship_level: str) -> str:
        """Get appropriate personality for relationship level"""
        personality_map = {
            "stranger": "friendly",
            "acquaintance": "friendly",
            "friend": "casual",
            "close_friend": "enthusiastic",
            "vip": "enthusiastic",
        }
        return personality_map.get(relationship_level, "friendly")

    async def generate_greeting(self, user_context: Dict[str, Any]) -> str:
        """Generate appropriate greeting for user"""
        relationship = user_context.get("relationship_level", "stranger")
        username = user_context.get("username", "there")

        greeting_prompts = {
            "stranger": f"Generate a friendly greeting for a new person named {username}",
            "acquaintance": f"Generate a welcoming greeting for {username} who has visited before",
            "friend": f"Generate a casual greeting for your friend {username}",
            "close_friend": f"Generate an enthusiastic greeting for your good friend {username}",
            "vip": f"Generate an excited greeting for VIP member {username}",
        }

        prompt = greeting_prompts.get(relationship, greeting_prompts["stranger"])
        personality = self._get_personality_for_relationship(relationship)

        return await self.generate_response(prompt, personality=personality)

    async def process_command(
        self, command: str, args: List[str], user_context: Dict[str, Any]
    ) -> str:
        """Process special commands"""
        command = command.lower()

        if command == "help":
            return self._get_help_response(user_context.get("platform"))
        elif command == "about":
            return "I'm an AI assistant here to chat and help out! Feel free to ask me anything! 😊"
        elif command == "status":
            return f"I'm doing great! Thanks for asking, {user_context.get('username', 'friend')}! 🌟"
        elif command == "joke":
            prompt = (
                "Tell a clean, family-friendly joke that would be appropriate for chat"
            )
            return await self.generate_response(prompt, personality="playful")
        elif command == "quote":
            prompt = "Share an inspiring or motivational quote"
            return await self.generate_response(prompt, personality="supportive")
        else:
            return f"I don't recognize the command '{command}'. Type 'help' for available commands!"

    def _get_help_response(self, platform: str) -> str:
        """Get help response for platform"""
        base_help = """Available commands:
• help - Show this help
• about - Learn about me
• status - Check how I'm doing
• joke - Get a random joke
• quote - Get an inspiring quote"""

        if platform == "twitch":
            return base_help + "\n• !regen - Regenerate last response"

        return base_help

    def clear_cache(self):
        """Clear response cache"""
        self.response_cache.clear()
        log_info("AI response cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.response_cache),
            "max_cache_size": self.max_cache_size,
            "cache_usage": len(self.response_cache) / self.max_cache_size,
        }
