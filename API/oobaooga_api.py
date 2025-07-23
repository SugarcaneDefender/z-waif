import requests
import os

HOST = os.environ.get("HOST_PORT")
URI = f'http://{HOST}/v1/chat/completions'
URL_MODEL = f'http://{HOST}/v1/engines/'

headers = {
    "Content-Type": "application/json"
}

# Send using the non-streaming API
def api_standard(request):

    response = requests.post(URI, headers=headers, json=request, verify=False)

    received_message = response.json()['choices'][0]['message']['content']

    return received_message
