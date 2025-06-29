from ollama import chat
from ollama import ChatResponse
from ollama import generate

import os
import API.api_controller
import json
import logging
import re

from utils.conversation_analysis import analyze_conversation_style
from utils.settings import char_name, MODEL_NAME
from utils.user_context import get_user_context
from utils.user_relationships import get_relationship_status
from utils import zw_logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
ollama_model = os.environ.get("ZW_OLLAMA_MODEL", "llama2")
ollama_model_visual = os.environ.get("ZW_OLLAMA_MODEL_VISUAL", "llava")

# Load our configs for our different temperatures
try:
    with open("Configurables/OllamaModelConfigs.json", 'r') as openfile:
        model_configs = json.load(openfile)
except Exception as e:
    logger.warning(f"Could not load OllamaModelConfigs.json: {e}")
    # Fallback configuration
    model_configs = {
        0: {"temperature": 0.7, "min_p": 0.05, "top_p": 0.9, "top_k": 40, "repeat_penalty": 1.1, 
            "repeat_last_n": 64, "frequency_penalty": 0.0, "presence_penalty": 0.0},
        1: {"temperature": 1.0, "min_p": 0.1, "top_p": 0.85, "top_k": 35, "repeat_penalty": 1.15,
            "repeat_last_n": 64, "frequency_penalty": 0.1, "presence_penalty": 0.1},
        2: {"temperature": 1.3, "min_p": 0.15, "top_p": 0.8, "top_k": 30, "repeat_penalty": 1.2,
            "repeat_last_n": 64, "frequency_penalty": 0.2, "presence_penalty": 0.2}
    }

def clean_response(text):
    """Clean up the response text by removing internal markers and formatting."""
    # Remove context/system markers
    patterns = [
        r'\[Bot:[^\]]*\]',
        r'\[Assistant:[^\]]*\]',
        r'\[Style:[^\]]*\]',
        r'\[Platform:[^\]]*\]',
        r'\[Gender:[^\]]*\]',
        r'\[Personality:[^\]]*\]',
        r'\[Relationship:[^\]]*\]',
        r'\[Location:[^\]]*\]',
        r'\[Mood:[^\]]*\]'
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '', text)
    
    # Remove any remaining square brackets content
    text = re.sub(r'\[[^\]]*\]', '', text)
    
    # Clean up multiple newlines and spaces
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r' +', ' ', text)
    
    # Remove character name prefix if present - more robust matching
    name_pattern = r'^[A-Za-z]+:\s*'
    text = re.sub(name_pattern, '', text).strip()
    
    # Clean up any remaining template markers
    text = text.replace("<|im_end|>", "").replace("<|im_start|>", "")
    text = text.replace("### Response:", "").replace("### Instruction:", "")
    text = text.replace("Human:", "").replace("Assistant:", "")
    
    # Strip whitespace and empty lines at start/end
    text = text.strip()
    
    return text

def format_prompt_for_ollama(user_input, user_context, relationship, conversation_style):
    """Format prompt for Ollama with proper system message and context"""
    char = char_name if char_name else "Assistant"
    
    # Detect platform from user input
    platform_context = "personal conversation"
    if "[Platform: Twitch" in user_input:
        platform_context = "Twitch chat interaction"
    elif "[Platform: Discord" in user_input:
        platform_context = "Discord conversation"
    elif "[Platform: Web Interface" in user_input or "[Platform: Command Line" in user_input:
        platform_context = "personal one-on-one conversation"
    elif "[Platform: Voice Chat" in user_input:
        platform_context = "personal voice conversation"
    elif "[Platform: Minecraft" in user_input:
        platform_context = "casual gaming chat"
    
    system_prompt = f"""You are {char}, a warm and caring companion having a {platform_context}. You are a real person with genuine emotions and experiences.

CRITICAL INSTRUCTIONS:
1. ALWAYS respond directly to what the person asks or says - if they ask "how are you today?", tell them specifically how you're feeling today
2. Be authentic and personal - share genuine thoughts, feelings, and experiences
3. Use natural contractions and casual language like a real friend would
4. Never mention being an AI, bot, assistant, or language model
5. Answer questions thoughtfully and specifically, not with generic responses
6. Show real interest in the person you're talking to

Your personality:
- Genuinely caring and empathetic
- Conversational and down-to-earth
- Emotionally expressive and relatable
- Thoughtful in your responses
- Present in the moment

Context:
- User: {user_context.get('username', 'default')}
- Relationship: {relationship}
- Conversation Style: {conversation_style or 'casual'}

RESPOND TO THEIR ACTUAL MESSAGE: Address what they're specifically asking or talking about. If they ask how you are, tell them how you're actually feeling. If they share something, respond to that specific thing.

Stay natural, be yourself, and have a real conversation."""
    
    # Clean the user input to remove platform markers for cleaner conversation
    clean_user_input = user_input
    if "[Platform:" in clean_user_input:
        clean_user_input = re.sub(r'\[Platform:[^\]]*\]\s*', '', clean_user_input).strip()
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": clean_user_input}
    ]
    return messages

def api_standard(history, temp_level, stop, max_tokens, user_input=None, user_id="default", platform="twitch"):
    """Enhanced API standard call with context support"""
    try:
        # Get user context and relationship info if user_input is provided
        if user_input:
            user_context = get_user_context(user_id, platform)
            relationship = get_relationship_status(user_id, platform)
            conversation_style = analyze_conversation_style(user_input, user_id, platform)
            
            # Format with enhanced prompt
            messages = format_prompt_for_ollama(user_input, user_context, relationship, conversation_style)
        else:
            # Use provided history as-is
            messages = history

        this_model = ollama_model

        response: ChatResponse = chat(
            model=this_model,
            messages=messages,
            keep_alive="25h",
            options=get_temperature_options(temp_level=temp_level, stop=stop, max_tokens=max_tokens),
        )
        
        # Clean the response
        cleaned_response = clean_response(response.message.content)
        logger.info(f"Successfully received Ollama response: {cleaned_response[:100]}...")
        
        return cleaned_response
        
    except Exception as e:
        logger.error(f"Ollama API standard request failed: {e}")
        return f"Error: Could not connect to Ollama. Please make sure Ollama is running and the model '{ollama_model}' is available."

def api_stream(history, temp_level, stop, max_tokens, user_input=None, user_id="default", platform="twitch"):
    """Enhanced API streaming call with context support"""
    try:
        # Get user context and relationship info if user_input is provided
        if user_input:
            user_context = get_user_context(user_id, platform)
            relationship = get_relationship_status(user_id, platform)
            conversation_style = analyze_conversation_style(user_input, user_id, platform)
            
            # Format with enhanced prompt
            messages = format_prompt_for_ollama(user_input, user_context, relationship, conversation_style)
        else:
            # Use provided history as-is
            messages = history

        this_model = ollama_model

        stream = chat(
            model=this_model,
            messages=messages,
            stream=True,
            keep_alive="25h",
            options=get_temperature_options(temp_level=temp_level, stop=stop, max_tokens=max_tokens),
        )

        return stream
        
    except Exception as e:
        logger.error(f"Ollama API streaming request failed: {e}")
        return []

def api_standard_image(history):
    """Vision API call for image processing"""
    try:
        this_model = ollama_model_visual

        response: ChatResponse = chat(
            model=this_model,
            messages=history,
            keep_alive="25h",
        )
        
        # Clean the response
        cleaned_response = clean_response(response.message.content)
        return cleaned_response
        
    except Exception as e:
        logger.error(f"Ollama image API request failed: {e}")
        return f"Error processing image with Ollama: {e}"

def api_stream_image(history):
    """Streaming vision API call for image processing"""
    try:
        this_model = ollama_model_visual

        stream = chat(
            model=this_model,
            messages=history,
            stream=True,
            keep_alive="25h",
        )

        return stream
        
    except Exception as e:
        logger.error(f"Ollama streaming image API request failed: {e}")
        return []

def get_temperature_options(temp_level, stop, max_tokens):
    """Get temperature and generation options"""
    # Do not use our own config...
    if temp_level == -1:
        return None

    # Ensure temp_level is within bounds
    if temp_level not in model_configs:
        temp_level = 0  # Default to conservative settings

    import API.api_controller
    return {
        "temperature": model_configs[temp_level]['temperature'],
        "min_p": model_configs[temp_level]['min_p'],
        "top_p": model_configs[temp_level]['top_p'],
        "top_k": model_configs[temp_level]['top_k'],
        "num_ctx": getattr(API.api_controller, 'max_context', 4096),
        "repeat_penalty": model_configs[temp_level]['repeat_penalty'],
        "stop": stop,
        "num_predict": max_tokens,
        "repeat_last_n": model_configs[temp_level]['repeat_last_n'],
        "frequency_penalty": model_configs[temp_level]['frequency_penalty'],
        "presence_penalty": model_configs[temp_level]['presence_penalty']
    }

def api_call(user_input, temp_level, max_tokens=150, streaming=False, stop=None, preset=None, char_send=None):
    """
    Unified API call function for Ollama that handles both simple and streaming requests.
    This consolidates the API logic that was previously scattered in api_controller.py.
    Note: preset and char_send parameters are accepted for interface compatibility but not used by Ollama.
    """
    from API.api_controller import encode_new_api_ollama
    from utils import zw_logging
    
    try:
        # Encode messages for ollama
        messages = encode_new_api_ollama(user_input)
        
        if streaming:
            # Return streaming response with enhanced context
            return api_stream(
                history=messages, 
                temp_level=temp_level, 
                stop=stop, 
                max_tokens=max_tokens,
                user_input=user_input
            )
        else:
            # Return simple response with enhanced context
            return api_standard(
                history=messages, 
                temp_level=temp_level, 
                stop=stop, 
                max_tokens=max_tokens,
                user_input=user_input
            )
            
    except Exception as e:
        zw_logging.log_error(f"Ollama API request failed: {e}")
        return "Sorry, I'm having connection issues right now." if not streaming else []

def extract_streaming_chunk(event):
    """
    Extract content chunk from Ollama streaming event.
    This consolidates the API-specific parsing logic.
    """
    try:
        if hasattr(event, 'message') and hasattr(event.message, 'content'):
            return event.message.content
        elif isinstance(event, dict) and 'message' in event and 'content' in event['message']:
            return event['message']['content']
        else:
            return ""
    except Exception:
        return ""


