import os
import time

import whisper
from faster_whisper import WhisperModel
import torch
from dotenv import load_dotenv
load_dotenv()

device = "cuda" if torch.cuda.is_available() else "cpu"

FORCE_CPU = os.environ.get("WHISPER_TURBO_CPU_TRANSCRIPTION")
if FORCE_CPU == "ON":
    device = "cpu"

USER_MODEL = os.environ.get("WHISPER_MODEL")
WHISPER_TURBO = os.environ.get("WHISPER_TURBO")

CHUNKY_TRANSCRIPTION = os.environ.get("WHISPER_CHUNKY")

# Chunky Info
transcription_chunks = []
chunky_request = None



#
# Main Calls

def transcribe_voice_to_text(voice):

    # Pull from our chunklad if we are in chunking mode
    if CHUNKY_TRANSCRIPTION == "ON":
        return chunky_get_merge()

    #
    # whisper-turbo or normal Whisper

    if WHISPER_TURBO == "ON":
        return faster_transcribe(voice)

    else:
        return classical_transcribe(voice)


# Transcription for the interruptable chat (which is ran continually)
def ordus_transcribe_voice_to_text(voice):

    #
    # whisper-turbo or normal Whisper. No chunklad option- it is basically already chunked

    if WHISPER_TURBO == "ON":
        return faster_transcribe(voice)

    else:
        return classical_transcribe(voice)




#
# Transcriptions

# Awesome transcription, uses whisper-turbo
def faster_transcribe(voice):
    nresult = ""
    model_size = USER_MODEL

    if device == "cuda":
        # Run on GPU with FP16
        model = WhisperModel(model_size, device="cuda", compute_type="float16")

    else:
        # or run on CPU with INT8
        model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, info = model.transcribe(voice, beam_size=5,  compression_ratio_threshold=1.9, no_speech_threshold=0.1)

    # Return the combined text
    for segment in segments:
        nresult += segment.text + " "
    return nresult

# Normal transcription, uses whisper
def classical_transcribe(voice):
    nresult=""
    model = whisper.load_model(USER_MODEL)
    result = model.transcribe(voice, language="en", compression_ratio_threshold=1.9, no_speech_threshold=0.1)

    # Return the combined text
    for mem in result["segments"]:
        nresult += mem['text']+" "
    return nresult



#
# Chunky Handlers

# Chunky whisper-turbo (for "live" transcription). This is the input call.
def chunky_transcribe(voice_clip):
    global transcription_chunks

    if WHISPER_TURBO == "ON":
        transcription_chunks.append(str(faster_transcribe(voice_clip)))

    else:
        transcription_chunks.append(str(classical_transcribe(voice_clip)))


# Runs thread/loop for chunky transcript requests
def chunky_transcription_loop():
    global chunky_request

    while True:
        time.sleep(0.001)
        if chunky_request != None:
            chunky_transcribe(voice_clip=chunky_request)
            chunky_request = None

# Give request for the chunky loop
def give_chunky_request(voice_clip):
    global chunky_request

    chunky_request = voice_clip

def clear_transcription_chunks():
    global transcription_chunks
    transcription_chunks = []

# Chunky whisper-turbo (for "live" transcription). This is the call to get our combined, complete transcript
def chunky_get_merge():

    global transcription_chunks
    final_chunky_message = ""

    # Add the rest of the chunks
    for chunk in transcription_chunks:
        final_chunky_message += chunk

    # NOTE: We could add in a method to stitch together words with overlapping timings and whatnot.
    # Like if a word is repeated, and increase the ammount of audio overlap per chunk.
    # That would be a good low-hanging fruit for any future programmer looking at this!
    # I also had it collecting the actual segments, not just text, but it was giving wierd errors
    # Although, whisper-turbo is plenty fast...

    transcription_chunks = []   # reset it
    return final_chunky_message
