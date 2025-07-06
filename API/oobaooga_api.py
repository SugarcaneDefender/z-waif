# Standard library imports
import json
import logging
import os
import re

# Third-party imports
import requests
import yaml
import sseclient

# Local imports - Utils modules
from utils.conversation_analysis import analyze_conversation_style
from utils.settings import char_name, MODEL_NAME
from utils.user_context import get_user_context
from utils.user_relationships import get_relationship_status
from utils import zw_logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = os.environ.get("HOST_PORT", "127.0.0.1:49493")
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
    
    # Detect platform from user input
    platform_instruction = "Keep responses natural and conversational"
    if "[Platform: Twitch" in user_input:
        platform_instruction = "Keep responses concise and engaging for chat"
    elif "[Platform: Web Interface" in user_input or "[Platform: Command Line" in user_input:
        platform_instruction = "Focus on personal one-on-one conversation"
    elif "[Platform: Voice Chat" in user_input:
        platform_instruction = "Respond naturally for voice conversation"
    elif "[Platform: Discord" in user_input:
        platform_instruction = "Keep responses casual and friendly"
    
    context_parts = []
    context_parts.append(f"[User Context: {user_context.get('username', 'default')}, Relationship: {relationship}]")
    context_parts.append(f"[Platform Instructions: {platform_instruction}]")
    
    if conversation_style:
        context_parts.append(f"[Style: {conversation_style}]")
    else:
        context_parts.append("[Style: None]")
        
    if user_context.get("mood"):
        context_parts.append(f"[Mood: {user_context['mood']}]")
    else:
        context_parts.append("[Mood: neutral]")
    
    instruction = "\n".join([
        "You are a friendly, caring companion having a conversation. Present yourself as a real person, never as an AI or assistant.",
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

RESPOND TO THEIR ACTUAL MESSAGE: Address what they're specifically asking or talking about. If they ask how you are, tell them how you're actually feeling. If they share something, respond to that specific thing.

Stay natural, be yourself, and have a real conversation."""
    
    # Clean the user input to remove platform markers for cleaner conversation
    clean_user_input = user_input
    if "[Platform:" in clean_user_input:
        import re
        clean_user_input = re.sub(r'\[Platform:[^\]]*\]\s*', '', clean_user_input).strip()
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": clean_user_input}
    ]
    return messages

def format_prompt_vicuna(user_input, user_context, relationship, conversation_style):
    """Format prompt for Vicuna-style models"""
    
    # Extract actual platform from user input instead of hardcoding Twitch
    platform_info = "Personal Chat"
    if "[Platform: Twitch" in user_input:
        platform_info = "Twitch"
    elif "[Platform: Discord" in user_input:
        platform_info = "Discord"
    elif "[Platform: Web Interface" in user_input:
        platform_info = "Personal Web Chat"
    elif "[Platform: Voice Chat" in user_input:
        platform_info = "Voice Conversation"
    elif "[Platform: Command Line" in user_input:
        platform_info = "Personal Chat"
    
    context = f"[User Context: {user_context.get('username', 'default')}, Relationship: {relationship}] [Style: {conversation_style or 'None'}] [Platform: {platform_info}]"
    prompt = f"Human: {context}\n{user_input}\n\nAssistant:"
    return prompt

def get_model_type():
    """Determine the model type from environment or settings"""
    # Default to chatml for modern models that support ChatML format
    model_type = os.environ.get("MODEL_TYPE", "chatml").lower()
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
    
    # Use API-specific context if available, otherwise fall back to CHARACTER_CONTEXT, then base_context
    api_context = os.environ.get("API_CHARACTER_CONTEXT", "")
    if api_context:
        character_context = api_context
    else:
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
    
    # Handle chat completions format (has message.content)
    if "message" in choice and "content" in choice["message"]:
        content = choice["message"]["content"]
    # Handle completions format (has text)
    elif "text" in choice:
        content = choice["text"]
    else:
        return ""
    
    if not content or not content.strip():
        return ""
        
    return content.strip()

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

        # Determine the correct endpoint based on the request format
        endpoint = "/v1/chat/completions" if "messages" in formatted_request else "/v1/completions"
        
        logger.info(f"Sending request to {BASE_URI}{endpoint}")
        logger.debug(f"Request payload: {json.dumps(formatted_request, indent=2)}")

        # Make the API call
        response = requests.post(
            BASE_URI + endpoint,
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

def api_call(user_input, temp_level, max_tokens=450, streaming=False, preset=None, char_send=None, stop=None):
    """
    Unified API call function for Oobabooga that handles both simple and streaming requests.
    This consolidates the API logic that was previously scattered in api_controller.py.
    """
    import requests
    import sseclient
    from utils import zw_logging
    import API.character_card
    
    # Always log API calls regardless of debug mode
    print(f"[API] api_call() invoked with user_input: {repr(user_input[:50])}...")
    
    try:
        # Load platform-separated conversation history
        try:
            # Extract platform from user input for context separation
            platform = "personal"  # Default
            user_id = "default"    # Default user ID
            
            if "[Platform: Twitch Chat]" in user_input:
                platform = "twitch"
                user_id = "twitch_user"  # Could be extracted from user_input if needed
            elif "[Platform: Discord]" in user_input:
                platform = "discord"
                user_id = "discord_user"
            elif "[Platform: Web Interface" in user_input:
                platform = "webui"
                user_id = "webui_user"
            elif "[Platform: Command Line" in user_input:
                platform = "cmd"
                user_id = "cmd_user"
            elif "[Platform: Voice Chat" in user_input:
                platform = "voice"
                user_id = "voice_user"
            elif "[Platform: Minecraft" in user_input:
                platform = "minecraft"
                user_id = "minecraft_user"
            elif "[Platform: Hangout" in user_input:
                platform = "hangout"
                user_id = "hangout_user"
            
            # Get platform-specific conversation history
            from utils.chat_history import get_chat_history
            chat_history = get_chat_history(user_id, platform, limit=10)  # Last 10 exchanges
            
            # Convert to the format expected by the API (list of [user, assistant] pairs)
            ooga_history = []
            for i in range(0, len(chat_history), 2):
                if i + 1 < len(chat_history):
                    user_msg = chat_history[i].get('content', '') if chat_history[i].get('role') == 'user' else ''
                    assistant_msg = chat_history[i + 1].get('content', '') if chat_history[i + 1].get('role') == 'assistant' else ''
                    if user_msg and assistant_msg:
                        ooga_history.append([user_msg, assistant_msg])
            
            # If no platform-specific history, use minimal default
            if not ooga_history:
                ooga_history = [["Hello, I am back!", "Welcome back! *smiles*"]]
                
        except Exception as e:
            print(f"[API] Error loading platform history: {e}")
            ooga_history = [["Hello, I am back!", "Welcome back! *smiles*"]]
        
        # Build messages array with character card and history
        messages = []
        
        # Detect platform from user input for context
        platform_context = ""
        if "[Platform: Web Interface - Personal Chat]" in user_input:
            platform_context = "\n\nCONTEXT: This is a personal one-on-one conversation through a web interface. Be warm, caring, and authentic. Focus on meaningful personal interaction."
        elif "[Platform: Twitch Chat]" in user_input:
            platform_context = "\n\nCONTEXT: You are chatting on Twitch. Keep responses casual, engaging, and chat-friendly. Avoid streaming references but maintain a conversational tone. Be authentic and relatable. IMPORTANT: Respond with actual words and sentences, not just emoji. Have real conversations with people."
        elif "[Platform: Discord]" in user_input:
            platform_context = "\n\nCONTEXT: You are chatting on Discord. Be casual, fun, and engaging. You can use emojis and informal language. Keep the social energy up."
        elif "[Platform: Command Line - Personal Chat]" in user_input:
            platform_context = "\n\nCONTEXT: This is a personal conversation through command line. Be direct but friendly. Keep responses clear and engaging."
        elif "[Platform: Voice Chat - Personal Conversation]" in user_input:
            platform_context = "\n\nCONTEXT: This is a voice conversation. Be natural and conversational as if speaking aloud. Use natural speech patterns and be expressive."
        elif "[Platform: Minecraft Game Chat]" in user_input:
            platform_context = "\n\nCONTEXT: You are chatting in Minecraft. Keep responses short, game-appropriate, and fun. Be supportive of gameplay activities."
        elif "[Platform: Alarm/Reminder System]" in user_input:
            platform_context = "\n\nCONTEXT: This is an alarm or reminder. Be helpful, direct, and supportive. Focus on being encouraging and useful."
        elif "[Platform: Hangout Mode - Casual Conversation]" in user_input:
            platform_context = "\n\nCONTEXT: This is casual hangout mode. Be relaxed, fun, and spontaneous. Focus on creating a comfortable, enjoyable atmosphere."
        
        # Add character card as system message with platform context
        if API.character_card.character_card and isinstance(API.character_card.character_card, str):
            enhanced_character_card = API.character_card.character_card.strip() + platform_context
            messages.append({"role": "system", "content": enhanced_character_card})
            print(f"[API] Platform detected: {platform_context.split(':')[1].split('.')[0] if platform_context else 'Personal'}")

        # Add recent history (last 10 exchanges like release version)
        recent_history = ooga_history[-10:] if len(ooga_history) > 10 else ooga_history
        
        for entry in recent_history:
            # Handle both old format (2 elements) and new format (4+ elements)
            if len(entry) >= 2:
                user_msg = entry[0]
                assistant_msg = entry[1]
                
                if user_msg:
                    messages.append({"role": "user", "content": str(user_msg)})
                if assistant_msg:
                    messages.append({"role": "assistant", "content": str(assistant_msg)})

        # Add current user input
        if user_input:
            messages.append({"role": "user", "content": str(user_input)})
        
        # Always show what we're sending
        print(f"[API] Sending {len(messages)} messages to backend")
        for i, msg in enumerate(messages):
            content_preview = msg.get('content', '')[:100] + ('...' if len(msg.get('content', '')) > 100 else '')
            print(f"[API] Message {i+1} ({msg.get('role', 'unknown')}): {content_preview}")
        
        # Debug: Show the full system message to verify character card content
        if messages and messages[0].get('role') == 'system':
            print(f"[API] DEBUG: System message length: {len(messages[0]['content'])} characters")
            print(f"[API] DEBUG: System message preview: {messages[0]['content'][:200]}...")
        
        # Build the request - Keep full functionality but use supported parameters only
        HOST = os.environ.get("HOST_PORT", "127.0.0.1:5000")
        if HOST.startswith("http"):
            uri = f'{HOST}/v1/chat/completions'
        else:
            uri = f'http://{HOST}/v1/chat/completions'
        request = {
            "messages": messages,
            "mode": "chat",
            "character": None,  # Disable character to use our system messages
            "max_tokens": max_tokens,
            "temperature": max(temp_level, 0.7),  # Ensure minimum temperature for creativity
            "top_p": 0.9,  # Add top_p for better generation
            "top_k": 40,   # Add top_k to prevent repetitive responses
            "repetition_penalty": 1.1,  # Prevent repetitive emoji responses
            "do_sample": True,
            "stream": streaming,
            "truncation_length": 4096,  # Keep context length
            "min_length": 10,  # Force minimum response length
            "no_repeat_ngram_size": 2,  # Prevent immediate repetition
        }
        
        # Add preset if specified
        if preset:
            request["preset"] = preset
            
        # Add stopping criteria if specified
        if stop:
            request["stop"] = stop
        
        print(f"[API] Request details: max_tokens={max_tokens}, temp={temp_level}, streaming={streaming}, char_send={char_send}")
        
        # Add debugging for request content
        print(f"[API] Request JSON size: {len(str(request))} characters")
        
        # Define headers
        headers = {"Content-Type": "application/json"}
        
        if streaming:
            # Handle streaming request
            print(f"[API] Making streaming request to {uri}")
            response = requests.post(uri, headers=headers, json=request, stream=True, verify=False, timeout=30)
            response.raise_for_status()
            return sseclient.SSEClient(response)
        else:
            # Make direct API call for non-streaming with the proper conversation context
            print(f"[API] Making non-streaming request to {uri}")
            
            try:
                response = requests.post(uri, headers=headers, json=request, verify=False, timeout=30)
                print(f"[API] Response status code: {response.status_code}")
                response.raise_for_status()
                
                result = response.json()
                print(f"[API] Received response with keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
                
                # Extract the response content
                if 'choices' in result and result['choices']:
                    choice = result['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        response_content = choice['message']['content']
                        print(f"[API] Extracted response content: {repr(response_content[:100])}...")
                        
                        # Check for emoji-only responses and provide fallback
                        import re
                        # Remove common emoji and check if anything substantial remains
                        text_only = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251\U0001F900-\U0001F9FF]+', '', response_content).strip()
                        
                        if len(text_only) < 3:  # If response is mostly/only emoji
                            print(f"[API] Warning: Detected emoji-only response '{response_content}', providing fallback")
                            # Provide contextual fallback based on platform
                            if "[Platform: Twitch Chat]" in str(messages):
                                response_content = "Hey! How's it going? What's up?"
                            elif "[Platform: Discord]" in str(messages):
                                response_content = "Hey there! What's on your mind?"
                            else:
                                response_content = "Hi! How are you doing today?"
                        
                        return response_content
                    elif 'text' in choice:
                        response_content = choice['text']
                        print(f"[API] Extracted response text: {repr(response_content[:100])}...")
                        return response_content
                    else:
                        print(f"[API] Unexpected choice format: {choice}")
                        return "I'm having trouble with my response format."
                else:
                    print(f"[API] No choices in response: {result}")
                    return "I'm having trouble generating a response."
                    
            except requests.exceptions.Timeout:
                print(f"[API] Request timed out after 30 seconds")
                return "Sorry, the request timed out. Please try again."
            except requests.exceptions.ConnectionError as e:
                print(f"[API] Connection error: {e}")
                return "Sorry, I can't connect to the AI backend right now."
            except requests.exceptions.HTTPError as e:
                print(f"[API] HTTP error {response.status_code}: {e}")
                if response.status_code == 422:
                    print(f"[API] Validation error - check if parameters are supported")
                return f"Sorry, there was an API error (status {response.status_code})."
            except Exception as e:
                print(f"[API] Unexpected error during request: {e}")
                return "Sorry, something unexpected went wrong with the request."
                
    except requests.exceptions.RequestException as e:
        print(f"[API] Request failed: {e}")
        zw_logging.log_error(f"API request failed: {e}")
        return "Sorry, I'm having connection issues right now."
    except Exception as e:
        print(f"[API] Unexpected error: {e}")
        zw_logging.log_error(f"Unexpected API error: {e}")
        return "I'm having trouble responding right now."

def extract_streaming_chunk(event):
    """
    Extract content chunk from Oobabooga streaming event.
    This consolidates the API-specific parsing logic.
    """
    try:
        # Handle chat-style SSE events
        if event.data:
            payload = json.loads(event.data)
            if 'choices' in payload and payload['choices']:
                delta = payload['choices'][0].get('delta', {})
                return delta.get('content', '')
    except json.JSONDecodeError:
        # Fallback for older/different formats, though less likely now
        pass
    return ""
