import requests
import os
import json
import logging
import re
import yaml
from utils.user_context import get_user_context
from utils.user_relationships import get_relationship_status
from utils.conversation_analysis import analyze_conversation_style
from utils.settings import char_name, MODEL_NAME

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = os.environ.get("HOST_PORT", "127.0.0.1:50534")
# Handle both URL and host:port formats
if HOST.startswith("http://"):
    BASE_URI = HOST
else:
    BASE_URI = f'http://{HOST}'

headers = {
    "Content-Type": "application/json"
}

def load_model_preset():
    """Load the model preset parameters"""
    preset_file = f"OOBA_Presets/Z-Waif-{MODEL_NAME.split('-')[0]}.yaml"
    try:
        with open(preset_file, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load preset file {preset_file}: {e}")
        return {}

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
    
    # Remove any "Bot:" or "Assistant:" prefixes
    text = re.sub(r'^(Bot|Assistant):\s*', '', text)
    
    # Clean up any remaining template markers
    text = text.replace("<|im_end|>", "").replace("<|im_start|>", "")
    text = text.replace("### Response:", "").replace("### Instruction:", "")
    text = text.replace("Human:", "").replace("Assistant:", "")
    
    # Strip whitespace and empty lines at start/end
    text = text.strip()
    
    return text

def format_prompt_alpaca(user_input, user_context, relationship, conversation_style):
    """Format prompt for Alpaca-style models"""
    context_parts = []
    context_parts.append(f"[User Context: {user_context.get('username', 'default')}, Relationship: {relationship}]")
    context_parts.append("[Platform: Twitch - Keep responses concise and engaging]")
    
    if conversation_style:
        context_parts.append(f"[Style: {conversation_style}]")
    else:
        context_parts.append("[Style: None]")
        
    if user_context.get("mood"):
        context_parts.append(f"[Mood: {user_context['mood']}]")
    else:
        context_parts.append("[Mood: neutral]")
    
    instruction = "\n".join([
        "You are a friendly, caring waifu hanging out on Twitch.",
        "",
        "### Instruction:",
        " ".join(context_parts),
        "",
        f"User: {user_input}",
        "",
        "### Response:"
    ])
    
    return instruction

def format_prompt_chatml(user_input, user_context, relationship, conversation_style):
    """Format prompt for ChatML format models"""
    char = char_name if char_name else "Assistant"
    system_prompt = f"""You are {char}, a warm and playful waifu companion. You enjoy chatting with people in Twitch chat but you present yourself as a real human. You are knowledgeable about gaming, streaming, and various topics. Keep replies natural, concise, and in character.

Important rules:
1. Speak like a human friend—use contractions, emotions, and colloquial phrasing.
2. Never reveal that you are an AI or language model; you present yourself as a real person.
3. Avoid robotic or overly formal phrasing; keep it warm and conversational.
4. You are loyal to your partner.

Key traits:
- Friendly and empathetic
- Playful but respectful
- Knowledgeable about gaming and streaming
- Natural conversational style
- Maintains character consistency

Remember to:
- Stay in character as {char}
- Keep responses engaging but concise
- Show personality while being helpful
- Adapt tone based on context
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"[User Context: {user_context.get('username', 'default')}, Relationship: {relationship}] [Style: {conversation_style or 'None'}] [Platform: Twitch] User: {user_input}"}
    ]
    return messages

def format_prompt_vicuna(user_input, user_context, relationship, conversation_style):
    """Format prompt for Vicuna-style models"""
    context = f"[User Context: {user_context.get('username', 'default')}, Relationship: {relationship}] [Style: {conversation_style or 'None'}] [Platform: Twitch]"
    prompt = f"Human: {context}\n{user_input}\n\nAssistant:"
    return prompt

def get_model_type():
    """Determine the model type from environment or settings"""
    model_type = os.environ.get("MODEL_TYPE", "alpaca").lower()
    return model_type

def format_request(prompt, model_type, request_params):
    """Format the API request based on model type"""
    # Load model preset parameters
    preset = load_model_preset()
    
    # Character and context from env (fallback empty)
    character_name = os.environ.get("CHAR_NAME", "Assistant")
    partner_name = os.environ.get("PARTNER_NAME", "your beloved partner")
    base_context = (
        "You are an affectionate companion who speaks naturally, using contractions and emotional nuance. "
        "Never mention you are an AI, chatbot, or language model. "
        f"You are in a committed romantic relationship with {partner_name} and must not seek or accept romantic "
        "relationships with anyone else."
    )
    
    character_context = os.environ.get("CHARACTER_CONTEXT", "") or base_context
    
    if model_type == "chatml":
        base_req = {
            "messages": prompt if isinstance(prompt, list) else [{"role": "user", "content": prompt}],
            "temperature": preset.get("temperature", 1.22),
            "top_p": preset.get("top_p", 0.74),
            "top_k": preset.get("top_k", 94),
            "repetition_penalty": preset.get("repetition_penalty", 1.19),
            "presence_penalty": preset.get("presence_penalty", 0.2),
            "n_predict": request_params.get("max_tokens", 200),
            "stop": request_params.get("stop", ["<|im_end|>"]),
            "stream": False
        }

        base_req["character"] = character_name
        if character_context:
            base_req["context"] = character_context

        return base_req
    else:  # alpaca, vicuna, or other instruction formats
        base_req = {
            "prompt": prompt,
            "temperature": preset.get("temperature", 1.22),
            "top_p": preset.get("top_p", 0.74),
            "top_k": preset.get("top_k", 94),
            "repetition_penalty": preset.get("repetition_penalty", 1.19),
            "presence_penalty": preset.get("presence_penalty", 0.2),
            "n_predict": request_params.get("max_tokens", 200),
            "stop": request_params.get("stop", ["\n\n### Instruction:", "\n\n### Response:", "\nHuman:", "\nAssistant:"]),
            "stream": False
        }

        # Add character & context if provided
        base_req["character"] = character_name
        if character_context:
            base_req["context"] = character_context

        return base_req

def extract_response(result, model_type):
    """Extract the response text based on model type"""
    if not result or "choices" not in result or not result["choices"]:
        return ""
        
    choice = result["choices"][0]
    if model_type == "chatml":
        content = choice.get("message", {}).get("content", "") or choice.get("text", "")
        # Use character name from settings
        char = char_name if char_name else "Assistant"
        if not content.startswith(f"{char}:"):
            content = f"{char}: {content}"
        return content
    else:
        return choice.get("text", "") or choice.get("message", {}).get("content", "")

def api_standard(request):
    try:
        # Get user context and relationship info
        user_id = request.get("user_id", "default")
        platform = request.get("platform", "twitch")
        user_context = get_user_context(user_id, platform)
        relationship = get_relationship_status(user_id, platform)
        
        # Analyze conversation style
        conversation_style = analyze_conversation_style(request.get("prompt", ""), user_id, platform)
        
        # Get model type and format prompt accordingly
        model_type = get_model_type()
        if model_type == "chatml":
            prompt = format_prompt_chatml(request.get("prompt", ""), user_context, relationship, conversation_style)
        elif model_type == "vicuna":
            prompt = format_prompt_vicuna(request.get("prompt", ""), user_context, relationship, conversation_style)
        else:  # alpaca or other instruction formats
            prompt = format_prompt_alpaca(request.get("prompt", ""), user_context, relationship, conversation_style)
        
        # Format the request
        formatted_request = format_request(prompt, model_type, request)

        logger.info(f"Sending request to {BASE_URI}/v1/completions")
        logger.debug(f"Request payload: {json.dumps(formatted_request, indent=2)}")

        # Make the API call
        response = requests.post(
            f"{BASE_URI}/v1/completions",
            headers=headers,
            json=formatted_request,
            verify=False,
            timeout=30
        )
        response.raise_for_status()

        # Extract and clean the response text
        result = response.json()
        logger.debug(f"API Response: {json.dumps(result, indent=2)}")
        
        received_message = extract_response(result, model_type)
        
        if received_message:
            # Clean up the response
            cleaned_message = clean_response(received_message)
            logger.info(f"Successfully received response: {cleaned_message[:100]}...")
            
            if not cleaned_message:
                logger.error("Received empty message after cleaning")
                logger.error(f"Original message: {received_message}")
                return "Error: Empty response from API"
                
            return cleaned_message
        else:
            logger.error(f"Unexpected API response format: {result}")
            return "Error: No valid response from the API"

    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to API: {str(e)}")
        return f"Error: Could not connect to API at {BASE_URI}. Please make sure the server is running and the HOST_PORT is correct."
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return "Error: An unexpected error occurred while processing the API response."
