from http.client import responses

import lmstudio as lms

import os
import API.api_controller
import json

lmstudio_model = os.environ.get("ZW_LMSTUDIO_MODEL")
lmstudio_model_visual = os.environ.get("ZW_LMSTUDIO_MODEL_VISUAL")

# Load our configs for our different temperatures
with open("Configurables/LMStudioModelConfigs.json", 'r') as openfile:
    model_configs = json.load(openfile)

def api_standard(history, temp_level, stop, max_tokens):

    # Model needed?

    model = lms.llm(lmstudio_model)

    history_as_dict = dict(messages=history)
    chat = lms.Chat.from_history(history_as_dict)

    response = model.respond(chat, config=get_temperature_options(temp_level, stop, max_tokens))


    return response.content


def api_stream(history, temp_level, stop, max_tokens):

    model = lms.llm(lmstudio_model)

    history_as_dict = dict(messages=history)
    chat = lms.Chat.from_history(history_as_dict)

    return model.respond_stream(chat, config=get_temperature_options(temp_level, stop, max_tokens))

def api_standard_image(history, text_input, temp_level, stop, max_tokens):

    model = lms.llm(lmstudio_model)

    history_as_dict = dict(messages=history)
    chat = lms.Chat.from_history(history_as_dict)

    img_path = 'LiveImage.png'
    image_handle = lms.prepare_image(img_path)
    chat.add_user_message(text_input, images=[image_handle])

    response = model.respond(chat, config=get_temperature_options(temp_level, stop, max_tokens))

    return response

def api_stream_image(history, text_input, temp_level, stop, max_tokens):

    model = lms.llm(lmstudio_model)

    history_as_dict = dict(messages=history)
    chat = lms.Chat.from_history(history_as_dict)

    img_path = 'LiveImage.png'
    image_handle = lms.prepare_image(img_path)
    chat.add_user_message(text_input, images=[image_handle])

    return model.respond_stream(chat, config=get_temperature_options(temp_level, stop, max_tokens))


def get_temperature_options(temp_level, stop, max_tokens):

    # Do not use our own config...
    if temp_level == -1:
        return None


    return {"temperature": model_configs[temp_level]['temperature'],
            "minPSampling": model_configs[temp_level]['min_p'],
            "topKSampling": model_configs[temp_level]['top_k'],
            "repeatPenalty": model_configs[temp_level]['repeat_penalty'],
            "stopStrings": stop,
            "maxTokens": max_tokens,
            }




