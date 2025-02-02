import os
from typing import Any

import whisper # type: ignore
import torch
from dotenv import load_dotenv
load_dotenv()

device = "mps" if torch.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"

USER_MODEL = os.environ.get("WHISPER_MODEL", "base.en")

def to_transcribe_original_language(voice: str) -> str:

    nresult: str = ""
    model = whisper.load_model(USER_MODEL)
    result: dict[str, Any] = model.transcribe(voice, language="en", compression_ratio_threshold=1.9, no_speech_threshold=0.1) # type: ignore
    for mem in result["segments"]:
        nresult+=mem['text']+" "

    return nresult


