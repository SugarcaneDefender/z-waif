#
# For running an individual script in .env, I'm using Pycharm so I can just hit play to test stuff
#

import os
from ollama import chat

# from pathlib import Path

# You can also pass in base64 encoded image data
# img = base64.b64encode(Path(path).read_bytes()).decode()
# or the raw bytes
# img = Path(path).read_bytes()

# Os Path how TF that works???

img_str = str(os.path.abspath('..\LiveImage.png'))
print(img_str)

response = chat(
  model='nsheth/llama-3-lumimaid-8b-v0.1-iq-imatrix',
  messages=[
    {
      'role': 'user',
      'content': 'What is in this image? Be concise.',
      'images': [img_str],
    }
  ],
)

print(response.message.content)


