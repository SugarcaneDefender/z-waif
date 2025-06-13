import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from utils.zw_logging import log_info, log_error

class MemoryManager:
    def __init__(self, rag_processor=None):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.rag_processor = rag_processor
        self.memories_file = "Configurables/ai_memories.json"
        self.memories = []
        self.memory_embeddings = []
        self.max_memories = 1000
        self.similarity_threshold = 0.7
        
        self.load_memories()
    
    def load_memories(self):
        """Load memories from file"""
        try:
            if os.path.exists(self.memories_file):
                with open(self.memories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memories = data.get('memories', [])
                    
                # Regenerate embeddings for loaded memories
                if self.memories:
                    self._generate_embeddings()
                    
                log_info(f"Loaded {len(self.memories)} memories")
            else:
                self.memories = []
                log_info("No existing memories file found, starting fresh")
        except Exception as e:
            log_error(f"Error loading memories: {e}")
            self.memories = []
    
    def save_memories(self):
        """Save memories to file"""
        try:
            os.makedirs(os.path.dirname(self.memories_file), exist_ok=True)
            data = {
                'memories': self.memories,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.memories_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log_error(f"Error saving memories: {e}")
    
    async def add_memory(self, content: str, context: Dict[str, Any] = None):
        """Add a new memory"""
        memory = {
            'id': len(self.memories),
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'context': context or {},
            'access_count': 0,
            'importance': self._calculate_importance(content, context)
        }
        
        self.memories.append(memory)
        
        # Regenerate embeddings with new memory
        self._generate_embeddings()
        
        # Prune old memories if needed
        if len(self.memories) > self.max_memories:
            self._prune_memories()
        
        self.save_memories()
        log_info(f"Added memory: {content[:50]}...")
    
    def _calculate_importance(self, content: str, context: Dict[str, Any]) -> float:
        """Calculate importance score for a memory"""
        importance = 0.5  # Base importance
        
        # Higher importance for longer content
        importance += min(len(content) / 500, 0.3)
        
        # Higher importance for user interactions
        if context and context.get('user_id'):
            importance += 0.2
        
        # Higher importance for questions
        if '?' in content:
            importance += 0.1
        
        # Higher importance for emotional content
        emotion_words = ['love', 'hate', 'excited', 'sad', 'happy', 'angry', 'frustrated', 'amazing']
        if any(word in content.lower() for word in emotion_words):
            importance += 0.2
        
        return min(importance, 1.0)
    
    def _generate_embeddings(self):
        """Generate embeddings for all memories"""
        if not self.memories:
            self.memory_embeddings = []
            return
        
        contents = [memory['content'] for memory in self.memories]
        try:
            self.memory_embeddings = self.embedding_model.encode(contents)
            log_info(f"Generated embeddings for {len(contents)} memories")
        except Exception as e:
            log_error(f"Error generating embeddings: {e}")
            self.memory_embeddings = []
    
    async def retrieve_relevant_memories(self, query: str, max_memories: int = 5) -> List[str]:
        """Retrieve memories relevant to the query"""
        if not self.memories or not self.memory_embeddings:
            return []
        
        try:
            # Generate embedding for query
            query_embedding = self.embedding_model.encode([query])
            
            # Calculate similarities
            similarities = np.dot(self.memory_embeddings, query_embedding.T).flatten()
            
            # Get indices of most similar memories
            similar_indices = np.argsort(similarities)[::-1]
            
            # Filter by threshold and limit
            relevant_memories = []
            for idx in similar_indices[:max_memories]:
                if similarities[idx] >= self.similarity_threshold:
                    memory = self.memories[idx]
                    memory['access_count'] += 1  # Track access
                    relevant_memories.append(memory['content'])
            
            if relevant_memories:
                self.save_memories()  # Save updated access counts
                log_info(f"Retrieved {len(relevant_memories)} relevant memories for query")
            
            return relevant_memories
            
        except Exception as e:
            log_error(f"Error retrieving memories: {e}")
            return []
    
    def _prune_memories(self):
        """Remove old or less important memories"""
        # Sort by importance and last access
        current_time = datetime.now()
        
        for memory in self.memories:
            memory_time = datetime.fromisoformat(memory['timestamp'])
            days_old = (current_time - memory_time).days
            
            # Reduce importance over time
            age_factor = max(0.1, 1.0 - (days_old / 365))
            access_factor = min(1.0, memory['access_count'] / 10)
            
            memory['effective_importance'] = (
                memory['importance'] * age_factor * 0.7 + 
                access_factor * 0.3
            )
        
        # Sort by effective importance and keep top memories
        self.memories.sort(key=lambda x: x['effective_importance'], reverse=True)
        removed_count = len(self.memories) - self.max_memories
        self.memories = self.memories[:self.max_memories]
        
        # Regenerate embeddings after pruning
        self._generate_embeddings()
        
        log_info(f"Pruned {removed_count} memories, keeping {len(self.memories)}")
    
    async def get_user_specific_memories(self, user_id: str, platform: str, max_memories: int = 3) -> List[str]:
        """Get memories specific to a user"""
        user_memories = []
        
        for memory in self.memories:
            context = memory.get('context', {})
            if (context.get('user_id') == user_id and 
                context.get('platform') == platform):
                user_memories.append(memory)
        
        # Sort by recency and importance
        user_memories.sort(
            key=lambda x: (x['importance'], x['timestamp']), 
            reverse=True
        )
        
        return [memory['content'] for memory in user_memories[:max_memories]]
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about memories"""
        if not self.memories:
            return {
                'total_memories': 0,
                'avg_importance': 0,
                'oldest_memory': None,
                'newest_memory': None,
                'by_platform': {}
            }
        
        platforms = {}
        importances = []
        
        for memory in self.memories:
            importances.append(memory['importance'])
            
            context = memory.get('context', {})
            platform = context.get('platform', 'unknown')
            platforms[platform] = platforms.get(platform, 0) + 1
        
        return {
            'total_memories': len(self.memories),
            'avg_importance': sum(importances) / len(importances),
            'oldest_memory': min(self.memories, key=lambda x: x['timestamp'])['timestamp'],
            'newest_memory': max(self.memories, key=lambda x: x['timestamp'])['timestamp'],
            'by_platform': platforms,
            'avg_access_count': sum(m['access_count'] for m in self.memories) / len(self.memories)
        }
    
    async def search_memories(self, query: str, platform: str = None, 
                            user_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories with filters"""
        results = []
        
        # Filter memories
        filtered_memories = []
        for memory in self.memories:
            context = memory.get('context', {})
            
            # Apply filters
            if platform and context.get('platform') != platform:
                continue
            if user_id and context.get('user_id') != user_id:
                continue
            
            # Check if query matches content
            if query.lower() in memory['content'].lower():
                filtered_memories.append(memory)
        
        # Sort by relevance (combination of importance and recency)
        filtered_memories.sort(
            key=lambda x: (x['importance'], x['timestamp']), 
            reverse=True
        )
        
        return filtered_memories[:limit]
    
    async def cleanup_old_memories(self, days_old: int = 30):
        """Remove very old memories"""
        cutoff_time = datetime.now() - timedelta(days=days_old)
        
        old_memories = []
        for memory in self.memories:
            memory_time = datetime.fromisoformat(memory['timestamp'])
            if memory_time < cutoff_time and memory['importance'] < 0.5:
                old_memories.append(memory)
        
        # Remove old memories
        for memory in old_memories:
            self.memories.remove(memory)
        
        if old_memories:
            self._generate_embeddings()
            self.save_memories()
            log_info(f"Cleaned up {len(old_memories)} old memories")

class MultiprocessRAG:
    """Simplified RAG processor for multiprocess compatibility"""
    
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.documents = []
        self.embeddings = []
    
    def add_document(self, content: str, metadata: Dict[str, Any] = None):
        """Add a document to the RAG index"""
        doc = {
            'content': content,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        self.documents.append(doc)
        
        # Regenerate embeddings
        self._update_embeddings()
    
    def _update_embeddings(self):
        """Update embeddings for all documents"""
        if not self.documents:
            self.embeddings = []
            return
        
        contents = [doc['content'] for doc in self.documents]
        try:
            self.embeddings = self.embedding_model.encode(contents)
        except Exception as e:
            log_error(f"Error updating RAG embeddings: {e}")
            self.embeddings = []
    
    def search(self, query: str, top_k: int = 5) -> List[str]:
        """Search for relevant documents"""
        if not self.documents or not self.embeddings:
            return []
        
        try:
            query_embedding = self.embedding_model.encode([query])
            similarities = np.dot(self.embeddings, query_embedding.T).flatten()
            
            top_indices = np.argsort(similarities)[::-1][:top_k]
            return [self.documents[i]['content'] for i in top_indices]
            
        except Exception as e:
            log_error(f"Error searching RAG: {e}")
            return [] 