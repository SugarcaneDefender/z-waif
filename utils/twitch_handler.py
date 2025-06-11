from utils.ai_handler import AIHandler
from utils.memory_manager import MemoryManager, MultiprocessRAG
from sentence_transformers import SentenceTransformer
import logging
from utils.logging import log_info, log_error

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TwitchHandler:
    def __init__(self):
        log_info("Initializing TwitchHandler.")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        rag_processor = MultiprocessRAG(embedding_model)
        self.memory_manager = MemoryManager(rag_processor)
        self.ai = AIHandler()
        self.speak_shadowchats = True
        
    async def process(self, message_data):
        log_info(f"Processing message data: {message_data}")
        if message_data.get('needs_ai_response', False):
            # Get relevant memories
            relevant_memories = await self.memory_manager.retrieve_relevant_memories(
                message_data['content']
            )
            
            # Add current interaction to memories
            await self.memory_manager.add_memory(
                message_data['content'],
                context={'user_id': message_data['user_id']}
            )
            
            # Create context-aware prompt
            prompt = self._format_prompt(
                content=message_data['content'],
                memories=relevant_memories,
                username=message_data.get('username', 'User')
            )
            
            response = await self.ai.generate_response(prompt)
            if self.speak_shadowchats:
                await self.speak_message(message_data['content'])
            return response
        return None
        
    def _format_prompt(self, content, memories, username):
        memory_context = "\n".join(memories) if memories else "No relevant memories."
        return f"""Context: You are a Twitch chat AI assistant.
Relevant memories:
{memory_context}

Current interaction:
{username}: {content}
Assistant: """ 

    async def speak_message(self, message):
        print(f"Speaking message: {message}")
        
    async def handle_message(self, message):
        log_info(f"Handling message: {message}.")
        