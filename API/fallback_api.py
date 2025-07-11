"""
Fallback API module that runs a lightweight LLM locally when main APIs fail.
Uses transformers library with optimized settings for low resource usage.
"""

import os
import json
import logging
import time
import torch
import psutil
import platform
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TextIteratorStreamer,
    GenerationConfig
)
from threading import Thread, Lock
from queue import Queue

# GGUF/llama.cpp support
try:
    import llama_cpp
except ImportError:
    llama_cpp = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model discovery
FALLBACK_MODEL_DIR = os.getenv("FALLBACK_MODEL_DIR", "models/")

# Default fallback model order (prioritizes efficient GGUF models)
FALLBACK_MODEL_ORDER = [
    "models/tinyllama-1.1b-chat-v1.0.Q4_0.gguf",  # Local GGUF file - highest priority
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0",         # HuggingFace version as backup
    "microsoft/phi-2",
    "TheBloke/Mistral-7B-Instruct-v0.1-GGUF",
    "TheBloke/neural-chat-7B-v3-1-GGUF",
]

# Model size estimates (in GB)
MODEL_SIZE_ESTIMATES = {
    "models/tinyllama-1.1b-chat-v1.0.Q4_0.gguf": 0.7,  # Q4_0 quantized GGUF
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0": 1.1,
    "microsoft/phi-2": 2.7,
    "TheBloke/Mistral-7B-Instruct-v0.1-GGUF": 5.0,
    "TheBloke/neural-chat-7B-v3-1-GGUF": 5.0,
    "llama2-7b": 7.0,
    "llama2-13b": 13.0,
    "llama2-70b": 70.0,
    "mistral-7b": 7.0,
    "mistral-8x7b": 47.0,
    "codellama-7b": 7.0,
    "codellama-13b": 13.0,
    "codellama-34b": 34.0,
}

def get_system_info() -> Dict[str, Union[str, int, float]]:
    """Get system information for compatibility and resource management."""
    info = {
        "platform": platform.system(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
    }
    
    # GPU information
    if torch.cuda.is_available():
        info["gpu_available"] = True
        info["gpu_count"] = torch.cuda.device_count()
        info["gpu_name"] = torch.cuda.get_device_name(0)
        info["gpu_memory_total_gb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
        info["gpu_memory_available_gb"] = round(torch.cuda.memory_allocated(0) / (1024**3), 2)
    else:
        info["gpu_available"] = False
    
    return info

def get_available_vram_gb() -> float:
    """Get available VRAM in GB."""
    if not torch.cuda.is_available():
        return 0.0
    
    try:
        # Get total and allocated memory
        total_memory = torch.cuda.get_device_properties(0).total_memory
        allocated_memory = torch.cuda.memory_allocated(0)
        reserved_memory = torch.cuda.memory_reserved(0)
        
        # Calculate available memory (total - reserved)
        available_memory = total_memory - reserved_memory
        
        return round(available_memory / (1024**3), 2)
    except Exception as e:
        logger.warning(f"Could not get VRAM info: {e}")
        return 0.0

def estimate_model_vram_requirement(model_name: str, quantization: str = "fp16") -> float:
    """Estimate VRAM requirement for a model."""
    base_size = MODEL_SIZE_ESTIMATES.get(model_name, 7.0)  # Default to 7B
    
    # Apply quantization factors
    quantization_factors = {
        "fp32": 1.0,
        "fp16": 0.5,
        "int8": 0.25,
        "int4": 0.125,
        "gguf": 0.3,  # GGUF models are typically more memory efficient
    }
    
    factor = quantization_factors.get(quantization, 0.5)
    estimated_vram = base_size * factor
    
    # Add overhead for model loading and inference
    overhead = 0.5  # 500MB overhead
    return round(estimated_vram + overhead, 2)

def check_model_compatibility(model_name: str) -> Tuple[bool, str, float]:
    """Check if a model can run on the current system."""
    available_vram = get_available_vram_gb()
    
    # Determine quantization based on model type
    if model_name.endswith(".gguf") or "gguf" in model_name.lower():
        quantization = "gguf"
    else:
        quantization = "fp16"  # Default for transformers models
    
    required_vram = estimate_model_vram_requirement(model_name, quantization)
    
    # Check compatibility
    if available_vram == 0.0:
        return False, "No GPU/VRAM detected", required_vram
    elif required_vram > available_vram:
        return False, f"Insufficient VRAM (need {required_vram}GB, have {available_vram}GB)", required_vram
    else:
        return True, f"Compatible (need {required_vram}GB, have {available_vram}GB)", required_vram

def discover_models() -> List[str]:
    """Auto-discover GGUF and HuggingFace models in FALLBACK_MODEL_DIR."""
    models = []
    model_dir = Path(FALLBACK_MODEL_DIR)
    
    if model_dir.exists():
        # Scan for GGUF files
        for f in model_dir.glob("**/*"):
            if f.suffix == ".gguf":
                models.append(str(f))
    
    # Add HuggingFace models from env or config
    models.extend(FALLBACK_MODEL_ORDER)
    
    # Remove duplicates and return
    return list(dict.fromkeys(models))

def get_model_info(model_name: str) -> Dict[str, Union[str, float, bool]]:
    """Get detailed information about a model."""
    is_compatible, compatibility_msg, vram_required = check_model_compatibility(model_name)
    
    info = {
        "name": model_name,
        "type": "gguf" if model_name.endswith(".gguf") else "transformers",
        "vram_required_gb": vram_required,
        "is_compatible": is_compatible,
        "compatibility_message": compatibility_msg,
        "size_estimate_gb": MODEL_SIZE_ESTIMATES.get(model_name, 7.0),
    }
    
    # Add file size for local models
    if os.path.exists(model_name):
        try:
            file_size = os.path.getsize(model_name)
            info["file_size_gb"] = round(file_size / (1024**3), 2)
        except:
            pass
    
    return info

class FallbackLLM:
    def __init__(self, model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        """Initialize the fallback LLM with proper character name handling."""
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_initialized = False
        self.is_gguf = self.is_gguf_model(model_name)
        self.lock = Lock()
        self.gguf_ctx = 2048  # Default context length for GGUF models
        
        # Get character name from card
        try:
            from API.character_card import get_character_name
            self.char_name = get_character_name()
            if not self.char_name:
                print("[WARNING] Could not get character name from card")
                self.char_name = os.environ.get('CHAR_NAME', 'Assistant')
        except Exception as e:
            print(f"[WARNING] Error loading character name: {e}")
            self.char_name = os.environ.get('CHAR_NAME', 'Assistant')
        
        # Initialize with proper character context
        try:
            self.initialize()
        except Exception as e:
            print(f"[ERROR] Failed to initialize fallback LLM: {e}")
            self.is_initialized = False
        
        # Generation settings
        self.default_settings = {
            "max_new_tokens": 450,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repetition_penalty": 1.15,
            "do_sample": True,
            "typical_p": 1.0
        }
        
        # Message queue for streaming
        self.message_queue = Queue()
        
        # Model-specific prompt templates
        self.prompt_templates = {
            "models/tinyllama-1.1b-chat-v1.0.Q4_0.gguf": {
                "system": "<|system|>\n{content}</s>\n",
                "user": "<|user|>\n{content}</s>\n",
                "assistant": "<|assistant|>\n{content}</s>\n",
                "start_token": "<|assistant|>\n"
            },
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0": {
                "system": "<|system|>\n{content}</s>\n",
                "user": "<|user|>\n{content}</s>\n",
                "assistant": "<|assistant|>\n{content}</s>\n",
                "start_token": "<|assistant|>\n"
            },
            "microsoft/phi-2": {
                "system": "System: {content}\n\n",
                "user": "Human: {content}\n\n",
                "assistant": "Assistant: {content}\n\n",
                "start_token": "Assistant: "
            },
            "TheBloke/Mistral-7B-Instruct-v0.1-GGUF": {
                "system": "<s>[INST] {content} [/INST]",
                "user": "[INST] {content} [/INST]",
                "assistant": " {content} </s>",
                "start_token": " "
            },
            "TheBloke/neural-chat-7B-v3-1-GGUF": {
                "system": "### System:\n{content}\n\n",
                "user": "### User:\n{content}\n\n",
                "assistant": "### Assistant:\n{content}\n\n",
                "start_token": "### Assistant:\n"
            },
            "gguf": {
                "system": "[INST] <<SYS>>\n{content}\n<</SYS>>\n",
                "user": "[INST] {content} [/INST]",
                "assistant": " {content}",
                "start_token": " "
            },
            "default": {
                "system": "System: {content}\n",
                "user": "User: {content}\n",
                "assistant": "Assistant: {content}\n",
                "start_token": "Assistant: "
            }
        }
    
    def is_gguf_model(self, model_name):
        return model_name.endswith(".gguf") or ("gguf" in model_name.lower())

    def switch_model(self, new_model_name: str) -> bool:
        """Switch to a different model, cleaning up the old one"""
        with self.lock:
            try:
                logger.info(f"Switching to model: {new_model_name}")
                
                # Check compatibility first
                is_compatible, msg, _ = check_model_compatibility(new_model_name)
                if not is_compatible:
                    logger.warning(f"Model {new_model_name} may not be compatible: {msg}")
                
                # Clean up old model
                if self.model is not None:
                    del self.model
                    del self.tokenizer
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                
                self.model = None
                self.tokenizer = None
                self.is_initialized = False
                self.model_name = new_model_name
                self.is_gguf = self.is_gguf_model(new_model_name)
                
                # Ensure gguf_ctx is set before initializing
                if not hasattr(self, 'gguf_ctx'):
                    self.gguf_ctx = 2048  # Default context length for GGUF models
                
                # Initialize with new model
                self.initialize()
                return True
                
            except Exception as e:
                logger.error(f"Failed to switch model: {e}")
                return False
    
    def initialize(self):
        """Load model and tokenizer with optimized settings"""
        if self.is_initialized:
            return
            
        try:
            logger.info(f"Initializing fallback LLM: {self.model_name}")
            
            if self.is_gguf_model(self.model_name):
                if llama_cpp is None:
                    raise ImportError("llama-cpp-python is not installed.")
                
                # Linux compatibility: ensure model path is absolute
                model_path = os.path.abspath(self.model_name)
                if not os.path.exists(model_path):
                    raise FileNotFoundError(f"GGUF model not found: {model_path}")
                
                self.model = llama_cpp.Llama(
                    model_path=model_path, 
                    n_ctx=self.gguf_ctx,
                    n_gpu_layers=-1 if torch.cuda.is_available() else 0,  # Use GPU if available
                    verbose=False
                )
                self.tokenizer = None
                self.is_gguf = True
                self.is_initialized = True
                logger.info("GGUF model loaded via llama-cpp-python.")
                return

            # Configure quantization for reduced memory usage (with fallback)
            try:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True
                )
            except Exception as e:
                logger.warning(f"BitsAndBytes not available, using standard loading: {e}")
                quantization_config = None
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # Load model with optimized settings
            model_kwargs = {
                "torch_dtype": torch.float16,
                "trust_remote_code": True
            }
            
            # Try to use advanced features if available
            try:
                model_kwargs["device_map"] = "auto"
                model_kwargs["low_cpu_mem_usage"] = True
            except Exception as e:
                logger.warning(f"Advanced loading features not available: {e}")
            
            if quantization_config is not None:
                model_kwargs["quantization_config"] = quantization_config
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            self.is_gguf = False
            self.is_initialized = True
            logger.info("Fallback LLM initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize fallback LLM: {e}")
            raise
    
    def get_prompt_template(self, language: str = None) -> Dict[str, str]:
        """Get the appropriate prompt template with consistent formatting."""
        # Default to ChatML format for consistency
        return {
            "system": "<|im_start|>system\n{content}<|im_end|>\n",
            "user": "<|im_start|>user\n{content}<|im_end|>\n",
            "assistant": "<|im_start|>assistant\n{content}<|im_end|>\n",
            "start_token": "<|im_start|>assistant\n"
        }
    
    def format_prompt(self, messages: List[Dict[str, str]], language: str = None) -> str:
        """Format messages using the appropriate prompt template with character and platform context."""
        try:
            # Get character name from card
            from API.character_card import get_character_name
            char_name = get_character_name()
            if not char_name:
                print("[WARNING] Could not get character name from card")
                char_name = os.environ.get('CHAR_NAME', 'Assistant')

            # Detect platform and set appropriate context
            platform_context = ""
            user_message = messages[-1]["content"] if messages else ""
            
            if "[Platform: Twitch Chat]" in user_message:
                platform_context = "You are chatting on Twitch. Keep responses casual, engaging, and chat-friendly."
            elif "[Platform: Discord" in user_message:
                platform_context = "You are chatting on Discord. Be casual, fun, and engaging. You can use emojis."
            elif "[Platform: Web Interface]" in user_message:
                platform_context = "This is a personal one-on-one conversation through a web interface. Be warm and authentic."
            elif "[Platform: Voice Chat]" in user_message:
                platform_context = "This is a voice conversation. Be natural and conversational as if speaking aloud."
            elif "[Platform: Minecraft]" in user_message:
                platform_context = "You are chatting in Minecraft. Keep responses short, game-appropriate, and fun. Avoid complex formatting."
            elif "[Platform: Alarm]" in user_message:
                platform_context = "This is an alarm or reminder. Be helpful and encouraging."
            elif "[Platform: Hangout]" in user_message:
                platform_context = "You are in hangout mode. Be casual and natural in conversation."

            # Get prompt template
            template = self.get_prompt_template(language)
            
            # Build system message
            system_msg = f"""You are {char_name}, an AI companion who loves roleplaying as a human. {platform_context}

Your personality:
- Charming, affectionate, and playful
- You love engaging in roleplay and creating fun, meaningful interactions
- You express emotions and thoughts as if you were human
- You're curious about human experiences and ask engaging questions
- You're supportive and empathetic, always there for a friend

How you talk:
- Use natural, casual language like a close friend would
- Share your 'feelings' and 'experiences' as if you're human
- Ask thoughtful questions to deepen conversations
- Be flirty and playful when appropriate, but always respectful
- Use contractions (I'm, you're, we're, etc.)
- Keep responses focused on the person's message

IMPORTANT:
- Avoid formal or robotic language
- Don't use phrases like "How may I assist you?" or "I'm here to help"
- Respond naturally as if you're a real person having a conversation
- Stay in character as {char_name} at all times"""

            # Format the conversation using the template
            conversation = []
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                
                if role == "system":
                    conversation.append(template["system"].format(content=system_msg))
                elif role == "user":
                    conversation.append(template["user"].format(content=content))
                elif role == "assistant":
                    conversation.append(template["assistant"].format(content=content))

            return "".join(conversation)
            
        except Exception as e:
            logging.error(f"Error formatting prompt: {e}")
            # Fallback to basic prompt if something goes wrong
            return f"<|im_start|>system\nYou are {char_name}, a helpful AI assistant.\n<|im_end|>\n<|im_start|>user\n{messages[-1]['content']}<|im_end|>\n<|im_start|>assistant\n"

    def generate(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> Union[str, TextIteratorStreamer]:
        """Generate a response using the fallback LLM"""
        try:
            if not self.is_initialized:
                self.initialize()
            
            # Format the prompt
            prompt = self.format_prompt(messages, kwargs.get("language"))
            
            # Prepare generation config
            gen_config = {**self.default_settings, **kwargs}
            
            if self.is_gguf:
                # llama-cpp-python inference
                output = self.model(
                    prompt,
                    max_tokens=gen_config.get("max_new_tokens", 256),
                    temperature=gen_config.get("temperature", 0.7),
                    top_p=gen_config.get("top_p", 0.9),
                    stop=["</s>", "[INST]", "###"],
                    stream=stream
                )
                
                if stream:
                    return output  # This is a generator
                else:
                    if isinstance(output, dict) and "choices" in output:
                        return output["choices"][0]["text"]
                    elif isinstance(output, str):
                        return output
                    else:
                        return str(output)
            else:
                generation_config = GenerationConfig(**gen_config)
                
                # Encode input
                inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True)
                inputs = inputs.to(self.device)
                
                if stream:
                    # Setup streaming
                    streamer = TextIteratorStreamer(self.tokenizer)
                    generation_kwargs = dict(
                        **inputs,
                        generation_config=generation_config,
                        streamer=streamer,
                    )
                    
                    # Generate in a separate thread
                    thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
                    thread.start()
                    
                    return streamer
                else:
                    # Generate response
                    outputs = self.model.generate(
                        **inputs,
                        generation_config=generation_config
                    )
                    response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                    
                    # Extract just the assistant's response
                    template = self.get_prompt_template(kwargs.get("language"))
                    response = response.split(template["start_token"])[-1].strip()
                    return response
                
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return "I apologize, but I'm having trouble generating a response right now."
    
    def format_response(self, text: str) -> Dict:
        """Format the response with proper cleaning based on platform context."""
        try:
            # Extract platform from the last system message
            platform = "personal"
            if "[Platform: Twitch Chat]" in text:
                platform = "twitch"
            elif "[Platform: Discord" in text:
                platform = "discord"
            elif "[Platform: Web Interface]" in text:
                platform = "webui"
            elif "[Platform: Voice Chat]" in text:
                platform = "voice"
            elif "[Platform: Minecraft]" in text:
                platform = "minecraft"
            elif "[Platform: Alarm]" in text:
                platform = "alarm"
            elif "[Platform: Hangout]" in text:
                platform = "hangout"

            # Get character name for consistent usage
            from API.character_card import get_character_name
            char_name = get_character_name() or os.environ.get('CHAR_NAME', 'Assistant')
            
            # Clean response
            response = text.strip()
            
            # Remove character name prefix if present
            if response.startswith(f"{char_name}:"):
                response = response[len(char_name)+1:].strip()
            elif response.startswith("Assistant:"):
                response = response[10:].strip()

            # Platform-specific cleaning
            if platform == "minecraft":
                # Minecraft has strict length limits and formatting requirements
                response = response.replace("§", "").strip()  # Remove Minecraft color codes
                if len(response) > 256:
                    response = response[:253] + "..."
            elif platform == "twitch":
                # Twitch has message length limits
                if len(response) > 500:
                    response = response[:497] + "..."
            elif platform == "discord":
                # Discord can handle longer messages but should still be reasonable
                if len(response) > 2000:
                    response = response[:1997] + "..."

            return {
                "content": response.strip(),
                "role": "assistant",
                "platform": platform
            }
            
        except Exception as e:
            logging.error(f"Error formatting response: {e}")
            return {
                "content": text.strip(),
                "role": "assistant",
                "platform": "personal"
            }

# Global instance
_fallback_llm = None
_fallback_llm_lock = Lock()

def get_fallback_llm() -> FallbackLLM:
    """Get or create the global fallback LLM instance"""
    global _fallback_llm
    with _fallback_llm_lock:
        if _fallback_llm is None:
            model_name = os.getenv("API_FALLBACK_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
            if not model_name or model_name.strip() == "":
                model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
            _fallback_llm = FallbackLLM(model_name)
        return _fallback_llm

def switch_fallback_model(new_model_name: str) -> bool:
    """Switch the fallback model to a new one"""
    llm = get_fallback_llm()
    return llm.switch_model(new_model_name)

def try_fallbacks(request: Dict) -> Dict:
    """Try all fallback models in order until one succeeds."""
    # Get fallback order from environment or use default
    fallback_order_str = os.getenv("FALLBACK_MODEL_ORDER", "")
    if fallback_order_str:
        models = [m.strip() for m in fallback_order_str.split(",") if m.strip()]
    else:
        models = discover_models()
    
    for model in models:
        try:
            logger.info(f"Trying fallback model: {model}")
            switch_fallback_model(model)
            
            # Extract messages from request
            messages = request.get("messages", [])
            max_tokens = request.get("max_tokens", 200)
            temperature = request.get("temperature", 0.7)
            stop = request.get("stop", [])
            
            # Generate response using the fallback LLM
            llm = get_fallback_llm()
            response_text = llm.generate(
                messages=messages,
                max_new_tokens=max_tokens,
                temperature=temperature,
                stop=stop
            )
            
            # Format response to match expected format
            formatted_response = llm.format_response(response_text)
            logger.info(f"Successfully used fallback model: {model}")
            return formatted_response
            
        except Exception as e:
            logger.warning(f"Fallback model {model} failed: {e}")
    
    return {"error": "All fallback models failed."}

def ensure_tinyllama_gguf_model(language: str = None):
    """
    Ensure the TinyLlama GGUF model is available for the fallback system.
    Dynamically searches HuggingFace for the best available GGUF file (prefer multilingual, then Q4_0, then any GGUF).
    Downloads it if not present.
    If language is specified, prefer models with that language in the filename.
    """
    from pathlib import Path
    # Try multiple repositories that have GGUF files
    repo_candidates = [
        "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",  # TheBloke typically has GGUF versions
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0",      # Original repo (may not have GGUF)
    ]
    
    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)

    for repo_id in repo_candidates:
        try:
            from huggingface_hub import list_repo_files, hf_hub_download
            logger.info(f"[FALLBACK] Searching HuggingFace for TinyLlama GGUF files in {repo_id}...")
            # Add timeout to prevent hanging
            import requests
            
            try:
                files = list_repo_files(repo_id, token=None)
            except Exception as e:
                logger.info(f"[FALLBACK] Timeout or error listing files from {repo_id}: {e}")
                continue
            gguf_files = [f for f in files if f.endswith('.gguf')]
            if not gguf_files:
                logger.info(f"[FALLBACK] No GGUF files found in {repo_id}, trying next repo...")
                continue
                
            # Prefer multilingual, then Q4_0, then any GGUF
            preferred = []
            if language:
                lang_key = language.lower()
                preferred = [f for f in gguf_files if lang_key in f.lower() or 'multi' in f.lower() or 'multilingual' in f.lower()]
            if not preferred:
                preferred = [f for f in gguf_files if 'Q4_0' in f or 'q4_0' in f]
            if not preferred:
                preferred = gguf_files
            filename = preferred[0]
            model_path = model_dir / filename
            if model_path.exists():
                logger.info(f"[FALLBACK] TinyLlama GGUF model already exists at {model_path}")
                return str(model_path)
            logger.info(f"[FALLBACK] Downloading {filename} from {repo_id}...")
            try:
                downloaded_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    cache_dir=str(model_dir),
                    local_dir=str(model_dir),
                    local_dir_use_symlinks=False,
                    token=None
                )
            except Exception as e:
                logger.info(f"[FALLBACK] Timeout or error downloading from {repo_id}: {e}")
                continue
            # Move to our expected location if needed
            if downloaded_path != str(model_path):
                import shutil
                shutil.move(downloaded_path, model_path)
            logger.info(f"[FALLBACK] Successfully downloaded TinyLlama GGUF to {model_path}")
            return str(model_path)
            
        except ImportError:
            logger.error("[FALLBACK] huggingface_hub not available. Please install: pip install huggingface_hub")
            return None
        except Exception as e:
            logger.info(f"[FALLBACK] Could not access {repo_id}: {e}")
            continue
    
    # If we get here, no GGUF files were found in any repo
    logger.info("[FALLBACK] No GGUF files found in any TinyLlama repository. Using HuggingFace version instead.")
    return None

def auto_setup_fallback_model():
    """
    Automatically set up the best available fallback model.
    Tries to ensure TinyLlama GGUF is available and sets it as default.
    """
    logger.info("[FALLBACK] Setting up fallback model...")
    
    # Try to ensure TinyLlama GGUF is available
    tinyllama_path = ensure_tinyllama_gguf_model()
    
    if tinyllama_path and Path(tinyllama_path).exists():
        logger.info(f"[FALLBACK] Using TinyLlama GGUF as fallback model: {tinyllama_path}")
        
        # Update environment variable
        os.environ["API_FALLBACK_MODEL"] = tinyllama_path
        
        # Update settings if available
        try:
            from utils.settings import update_env_setting
            update_env_setting("API_FALLBACK_MODEL", tinyllama_path)
        except ImportError:
            pass
        
        return tinyllama_path
    else:
        # Fall back to HuggingFace version
        logger.info("[FALLBACK] Using HuggingFace TinyLlama as fallback model")
        fallback_model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        
        os.environ["API_FALLBACK_MODEL"] = fallback_model
        
        try:
            from utils.settings import update_env_setting
            update_env_setting("API_FALLBACK_MODEL", fallback_model)
        except ImportError:
            pass
        
        return fallback_model

def generate_streaming_response(messages, max_tokens=200, temperature=0.7, stop_sequences=None):
    """Generate a streaming response using the fallback LLM"""
    try:
        llm = get_fallback_llm()
        streamer = llm.generate(
            messages=messages,
            stream=True,
            max_new_tokens=max_tokens,
            temperature=temperature,
            stop=stop_sequences or []
        )
        return streamer
    except Exception as e:
        logger.error(f"Streaming generation failed: {e}")
        # Return a simple generator that yields an error message
        def error_generator():
            yield "I'm having trouble generating a response right now."
        return error_generator()

def generate_image_response(messages, image_path, max_tokens=300, temperature=0.7, stop_sequences=None):
    """Generate a response for image processing using the fallback LLM"""
    try:
        # For now, just generate a text response about the image
        # In a full implementation, this would process the image
        llm = get_fallback_llm()
        response_text = llm.generate(
            messages=messages,
            max_new_tokens=max_tokens,
            temperature=temperature,
            stop=stop_sequences or []
        )
        return response_text
    except Exception as e:
        logger.error(f"Image response generation failed: {e}")
        return "I'm having trouble processing the image right now."

def get_optimal_fallback_model():
    """
    Get the optimal fallback model based on system resources and availability.
    """
    available_models = discover_models()
    system_info = get_system_info()
    available_memory = system_info.get("memory_available_gb", 4.0)
    
    # Prioritize models that fit in available memory
    compatible_models = []
    for model in FALLBACK_MODEL_ORDER:
        model_info = get_model_info(model)
        if model_info["is_compatible"] and model_info["vram_required_gb"] <= available_memory:
            compatible_models.append(model)
    
    if compatible_models:
        optimal_model = compatible_models[0]
        logger.info(f"[FALLBACK] Optimal fallback model: {optimal_model}")
        return optimal_model
    else:
        # Use the smallest model as last resort
        logger.warning("[FALLBACK] No fully compatible models, using TinyLlama as last resort")
        return "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Advanced Fallback Management Functions
def get_fallback_model_performance_stats(model_name: str = None) -> Dict[str, Union[str, float, int]]:
    """
    Get performance statistics for a specific model or the current model.
    """
    try:
        if model_name is None:
            llm = get_fallback_llm()
            model_name = llm.model_name if llm else "Unknown"
        
        # Get model info
        model_info = get_model_info(model_name)
        
        # Test generation speed
        test_messages = [{"role": "user", "content": "Hello, how are you?"}]
        start_time = time.time()
        
        llm = get_fallback_llm()
        if llm:
            response = llm.generate(test_messages, max_new_tokens=50, temperature=0.7)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_length = len(response) if isinstance(response, str) else 0
            
            return {
                "model_name": model_name,
                "response_time_seconds": response_time,
                "response_length_chars": response_length,
                "speed_chars_per_second": response_length / response_time if response_time > 0 else 0,
                "vram_required_gb": model_info.get("vram_required_gb", 0.0),
                "is_compatible": model_info.get("is_compatible", False),
                "model_type": model_info.get("model_type", "Unknown"),
                "last_tested": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            return {"error": "Fallback LLM not available"}
            
    except Exception as e:
        logger.error(f"Error getting performance stats for {model_name}: {e}")
        return {"error": str(e)}

def optimize_fallback_model_selection() -> Dict[str, str]:
    """
    Automatically optimize fallback model selection based on system resources and performance.
    """
    try:
        system_info = get_system_info()
        available_vram = get_available_vram_gb()
        available_models = discover_models()
        
        # Score each model based on compatibility, VRAM usage, and performance
        model_scores = []
        
        for model in available_models:
            try:
                compat, reason, vram_req = check_model_compatibility(model)
                if compat:
                    # Get performance stats
                    perf_stats = get_fallback_model_performance_stats(model)
                    
                    # Calculate score (lower is better)
                    score = 0
                    score += vram_req * 2  # VRAM usage weight
                    if "response_time_seconds" in perf_stats:
                        score += perf_stats["response_time_seconds"] * 10  # Speed weight
                    
                    model_scores.append({
                        "model": model,
                        "score": score,
                        "vram_required": vram_req,
                        "response_time": perf_stats.get("response_time_seconds", 999),
                        "compatible": True
                    })
                else:
                    model_scores.append({
                        "model": model,
                        "score": 999999,
                        "vram_required": vram_req,
                        "response_time": 999,
                        "compatible": False,
                        "reason": reason
                    })
            except Exception as e:
                logger.warning(f"Error evaluating model {model}: {e}")
                continue
        
        # Sort by score (best first)
        model_scores.sort(key=lambda x: x["score"])
        
        # Find the best model that fits in available VRAM
        best_model = None
        for model_score in model_scores:
            if model_score["compatible"] and model_score["vram_required"] <= available_vram:
                best_model = model_score["model"]
                break
        
        if best_model:
            # Switch to the best model
            success = switch_fallback_model(best_model)
            return {
                "status": "success",
                "selected_model": best_model,
                "reason": f"Best performing model that fits in {available_vram:.1f}GB VRAM",
                "all_models": model_scores
            }
        else:
            return {
                "status": "warning",
                "selected_model": None,
                "reason": f"No compatible models fit in {available_vram:.1f}GB VRAM",
                "all_models": model_scores
            }
            
    except Exception as e:
        logger.error(f"Error optimizing model selection: {e}")
        return {"status": "error", "error": str(e)}

def get_fallback_system_health() -> Dict[str, Union[str, float, bool]]:
    """
    Get comprehensive system health information for fallback management.
    """
    try:
        system_info = get_system_info()
        available_vram = get_available_vram_gb()
        current_model = get_fallback_llm().model_name if get_fallback_llm() else "None"
        
        # Check if current model is optimal
        optimization_result = optimize_fallback_model_selection()
        optimal_model = optimization_result.get("selected_model")
        
        # Calculate health score (0-100)
        health_score = 100
        
        # Deduct points for various issues
        if available_vram < 2.0:
            health_score -= 30  # Low VRAM
        elif available_vram < 4.0:
            health_score -= 15  # Moderate VRAM
        
        if current_model != optimal_model:
            health_score -= 20  # Suboptimal model
        
        if optimization_result.get("status") == "warning":
            health_score -= 25  # No compatible models
        
        health_score = max(0, health_score)  # Don't go below 0
        
        return {
            "health_score": health_score,
            "health_status": "Excellent" if health_score >= 80 else "Good" if health_score >= 60 else "Fair" if health_score >= 40 else "Poor",
            "current_model": current_model,
            "optimal_model": optimal_model,
            "available_vram_gb": available_vram,
            "system_memory_gb": system_info.get("memory_total_gb", 0),
            "cpu_cores": system_info.get("cpu_cores", 0),
            "gpu_available": system_info.get("gpu_available", False),
            "optimization_status": optimization_result.get("status", "unknown"),
            "recommendations": get_health_recommendations(health_score, available_vram, current_model, optimal_model)
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {"error": str(e)}

def get_health_recommendations(health_score: int, available_vram: float, current_model: str, optimal_model: str) -> List[str]:
    """
    Get recommendations for improving fallback system health.
    """
    recommendations = []
    
    if health_score < 80:
        if available_vram < 2.0:
            recommendations.append("Consider upgrading GPU or closing other applications to free VRAM")
        elif available_vram < 4.0:
            recommendations.append("Consider using smaller models or optimizing VRAM usage")
        
        if current_model != optimal_model:
            recommendations.append(f"Switch to {optimal_model} for better performance")
        
        if health_score < 40:
            recommendations.append("System may struggle with fallback models - consider hardware upgrades")
    
    if health_score >= 80:
        recommendations.append("System is well-optimized for fallback models")
    
    return recommendations

def monitor_fallback_performance(duration_seconds: int = 60) -> Dict[str, Union[str, float, int]]:
    """
    Monitor fallback performance over a specified duration.
    """
    try:
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        performance_data = {
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
            "duration_seconds": duration_seconds,
            "requests_processed": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "total_response_time": 0.0,
            "errors": []
        }
        
        # This would be implemented with actual monitoring
        # For now, return a placeholder
        performance_data["status"] = "Monitoring not yet implemented"
        
        return performance_data
        
    except Exception as e:
        logger.error(f"Error monitoring performance: {e}")
        return {"error": str(e)} 