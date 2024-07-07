import os

import whisper
import torch
from dotenv import load_dotenv
load_dotenv()

device = "cuda" if torch.cuda.is_available() else "cpu"

USER_MODEL = os.environ.get("WHISPER_MODEL")

def to_transcribe_original_language(voice):

    nresult=""
    model = whisper.load_model(USER_MODEL)
    result = model.transcribe(voice, language="en", compression_ratio_threshold=1.9, no_speech_threshold=0.1)
    for mem in result["segments"]:
        nresult+=mem['text']+" "

    return nresult


