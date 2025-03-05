from ollama import chat
from ollama import ChatResponse
from ollama import generate

import os
import API.api_controller

ollama_model = os.environ.get("ZW_OLLAMA_MODEL")
ollama_model_visual = os.environ.get("ZW_OLLAMA_MODEL_VISUAL")

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



    if temp_level == 0:
        return {"temperature": 1.17, "min_p": 0.0597, "top_p": 0.87, "top_k": 64, "num_ctx": API.api_controller.max_context, "repeat_penalty": 1.09, "stop": stop, "num_predict": max_tokens, "repeat_last_n": -1}

    if temp_level == 1:
        return {"temperature": 1.27, "min_p": 0.0497, "top_p": 0.87, "top_k": 72, "num_ctx": API.api_controller.max_context, "repeat_penalty": 1.12, "stop": stop, "num_predict": max_tokens, "repeat_last_n": -1}

    if temp_level == 2:
        return {"temperature": 1.47, "min_p": 0.0397, "top_p": 0.97, "top_k": 99, "num_ctx": API.api_controller.max_context, "repeat_penalty": 1.19, "stop": stop, "num_predict": max_tokens, "repeat_last_n": -1}

