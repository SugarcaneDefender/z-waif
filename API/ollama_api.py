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


