# import asyncio
from typing import Dict, List, Any, Optional
from utils.zw_logging import log_info, log_error
import API.api_controller as api_controller


class AIHandler:
    def __init__(self):
        self.default_personality = "friendly"
        self.response_cache = {}
        self.max_cache_size = 100

    async def generate_response(
        self, prompt: str, personality: Optional[str] = None, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate AI response using the main API controller"""
        try:
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

            # Generate response using main API
            api_controller.send_via_oogabooga(enhanced_prompt)
            response = api_controller.receive_via_oogabooga()

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

        # Add context if available
        if context:
            if context.get("platform"):
                platform = context["platform"]
                if platform == "twitch":
                    enhanced_parts.append(
                        "This is for Twitch chat - keep responses concise and engaging."
                    )
                elif platform == "discord":
                    enhanced_parts.append(
                        "This is for Discord - you can be more detailed if needed."
                    )

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

    async def generate_contextual_response(
        self, message: str, user_context: Dict[str, Any], memories: List[str] = None
    ) -> str:
        """Generate response with full context"""
        # Build comprehensive context
        context_parts = []

        # Add user context
        if user_context:
            username = user_context.get("username", "User")
            relationship = user_context.get("relationship_level", "stranger")
            platform = user_context.get("platform", "unknown")

            context_parts.append(f"User: {username} (relationship: {relationship})")

            if user_context.get("interests"):
                interests = ", ".join(
                    user_context["interests"][-3:]
                )  # Last 3 interests
                context_parts.append(f"Their interests: {interests}")

            if user_context.get("personality_traits"):
                traits = ", ".join(user_context["personality_traits"])
                context_parts.append(f"Their style: {traits}")

        # Add relevant memories
        if memories:
            memory_context = "Previous relevant conversations:\n" + "\n".join(
                memories[-3:]
            )
            context_parts.append(memory_context)

        # Build full prompt
        context_string = "\n".join(context_parts) if context_parts else ""
        full_prompt = f"{context_string}\n\nCurrent message: {message}"

        # Determine personality based on relationship
        personality = self._get_personality_for_relationship(
            user_context.get("relationship_level", "stranger")
        )

        return await self.generate_response(
            full_prompt,
            personality=personality,
            context={
                "platform": user_context.get("platform"),
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
