from ollama import chat
from ollama import ChatResponse
from ollama import generate

import os

ollama_model = os.environ.get("ZW_OLLAMA_MODEL")

def api_standard(history):

    response: ChatResponse = chat(
        model=ollama_model,
        messages=history,
        keep_alive="25h",
    )
    return response.message.content


def api_stream(history):
    stream = chat(
        model=ollama_model,
        messages=history,
        stream=True,
        keep_alive="25h",
    )

    return stream
