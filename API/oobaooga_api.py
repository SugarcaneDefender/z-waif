import requests
import os
import json
import logging
import re
from utils.user_context import get_user_context
from utils.user_relationships import get_relationship_status
from utils.conversation_analysis import analyze_conversation_style

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = os.environ.get("HOST_PORT", "127.0.0.1:50534")  # Using llama.cpp server port
# Handle both URL and host:port formats
if HOST.startswith("http://"):
    BASE_URI = HOST
else:
    BASE_URI = f'http://{HOST}'

headers = {
    "Content-Type": "application/json"
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
    
    # Remove any "Bot:" or "Assistant:" prefixes
    text = re.sub(r'^(Bot|Assistant):\s*', '', text)
    
    # Clean up any remaining template markers
    text = text.replace("<|im_end|>", "").replace("<|im_start|>", "")
    
    # Strip whitespace and empty lines at start/end
    text = text.strip()
    
    return text

def format_prompt(user_input, user_context, relationship, conversation_style):
    """Format the prompt with context in a cleaner way."""
    system_prompt = "You are a friendly and engaging Twitch chatbot. Keep responses natural and concise."
    
    # Format user context without brackets
    context_parts = []
    
    if user_context.get("interests"):
        interests = ", ".join(user_context["interests"][-3:])
        context_parts.append(f"User interests: {interests}")
    
    # Add platform-specific guidance
    context_parts.append("Platform: Twitch - Keep responses concise and engaging")
    
    # Format the messages for the chat template
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    
    return messages

def api_standard(request):
    try:
        # Get user context and relationship info
        user_id = request.get("user_id", "default")
        platform = request.get("platform", "twitch")
        user_context = get_user_context(user_id, platform)
        relationship = get_relationship_status(user_id, platform)
        
        # Analyze conversation style
        conversation_style = analyze_conversation_style(request.get("prompt", ""), user_id, platform)
        
        # Format messages with clean context
        messages = format_prompt(
            request.get("prompt", ""),
            user_context,
            relationship,
            conversation_style
        )
        
        # Format the request for llama.cpp server
        formatted_request = {
            "messages": messages,
            "temperature": 0.7,
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "max_tokens": request.get("max_tokens", 200),
            "stop": request.get("stop", ["<|im_end|>", "\n\n### Instruction:", "\n\n### Response:"])
        }

        logger.info(f"Sending request to {BASE_URI}/v1/chat/completions")
        logger.debug(f"Request payload: {json.dumps(formatted_request, indent=2)}")

        # Make the API call
        response = requests.post(
            f"{BASE_URI}/v1/chat/completions",
            headers=headers,
            json=formatted_request,
            verify=False,
            timeout=30
        )
        response.raise_for_status()

        # Extract and clean the response text
        result = response.json()
        logger.debug(f"API Response: {json.dumps(result, indent=2)}")
        
        if result and "choices" in result and len(result["choices"]) > 0:
            received_message = result["choices"][0]["message"]["content"]
            # Clean up the response
            cleaned_message = clean_response(received_message)
            logger.info(f"Successfully received response: {cleaned_message[:100]}...")
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
