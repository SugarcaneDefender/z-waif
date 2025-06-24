from ollama import chat
from ollama import ChatResponse
from ollama import generate

import os
import API.api_controller
import json

ollama_model = os.environ.get("ZW_OLLAMA_MODEL")
ollama_model_visual = os.environ.get("ZW_OLLAMA_MODEL_VISUAL")

# Load our configs for our different temperatures
with open("Configurables/OllamaModelConfigs.json", 'r') as openfile:
    model_configs = json.load(openfile)

def api_standard(history, temp_level, stop, max_tokens):

    # Model needed?
    this_model = ollama_model

    response: ChatResponse = chat(
        model=this_model,
        messages=history,
        keep_alive="25h",
        options=get_temperature_options(temp_level=temp_level, stop=stop, max_tokens=max_tokens),
    )
    return response.message.content


def api_stream(history, temp_level, stop, max_tokens):

    # Model needed?
    this_model = ollama_model

    stream = chat(
        model=this_model,
        messages=history,
        stream=True,
        keep_alive="25h",
        options=get_temperature_options(temp_level=temp_level, stop=stop, max_tokens=max_tokens),
    )

    return stream

def api_standard_image(history):

    # Vision needed?
    this_model = ollama_model_visual

    response: ChatResponse = chat(
        model=this_model,
        messages=history,
        keep_alive="25h",
    )
    return response.message.content

def api_stream_image(history):

    # Vision needed?
    this_model = ollama_model_visual

    stream = chat(
        model=this_model,
        messages=history,
        stream=True,
        keep_alive="25h",
    )

    return stream

def get_temperature_options(temp_level, stop, max_tokens):

    # Do not use our own config...
    if temp_level == -1:
        return None


    return {"temperature": model_configs[temp_level]['temperature'],
            "min_p": model_configs[temp_level]['min_p'],
            "top_p": model_configs[temp_level]['top_p'],
            "top_k": model_configs[temp_level]['top_k'],
            "num_ctx": API.api_controller.max_context,
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
            # Return streaming response
            return api_stream(
                history=messages, 
                temp_level=temp_level, 
                stop=stop, 
                max_tokens=max_tokens
            )
        else:
            # Return simple response
            return api_standard(
                history=messages, 
                temp_level=temp_level, 
                stop=stop, 
                max_tokens=max_tokens
            )
            
    except Exception as e:
        zw_logging.log_error(f"Ollama API request failed: {e}")
        return "Sorry, I'm having connection issues right now." if not streaming else []

def extract_streaming_chunk(event):
    """
    Extract content chunk from Ollama streaming event.
    This consolidates the API-specific parsing logic.
    """
    return event['message']['content']


