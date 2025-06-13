import time
import os
import requests
import json
import logging
from pathlib import Path

assert os.name == 'nt' # type: ignore

import win32com.client
from utils import hotkeys
from utils import voice_splitter
from utils import zw_logging
from utils import soundboard
from utils import settings
import API.api_controller

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

is_speaking = False
cut_voice = False

# RVC Configuration
RVC_HOST = os.environ.get("RVC_HOST", "127.0.0.1")
RVC_PORT = os.environ.get("RVC_PORT", "7897")
RVC_URI = f"http://{RVC_HOST}:{RVC_PORT}/voice"

def speak_line_rvc(s_message, refuse_pause=False):
    """Speak a line using RVC voice conversion"""
    global cut_voice
    cut_voice = False

    chunky_message = voice_splitter.split_into_sentences(s_message)

    for chunk in chunky_message:
        try:
            # Play soundboard sounds, if any
            pure_chunk = soundboard.extract_soundboard(chunk)

            # Cut out if we are not speaking unless spoken to!
            if settings.speak_only_spokento and not API.api_controller.last_message_received_has_own_name:
                continue

            # Remove any asterisks from being spoken
            pure_chunk = pure_chunk.replace("*", "")

            # Change any !!! or other multi-exclamations to single use
            pure_chunk = pure_chunk.replace("!!", "!")
            pure_chunk = pure_chunk.replace("!!!", "!")
            pure_chunk = pure_chunk.replace("!!!!", "!")
            pure_chunk = pure_chunk.replace("!!!!!", "!")

            # Send to RVC server
            try:
                response = requests.post(
                    RVC_URI,
                    json={
                        "text": pure_chunk,
                        "model": settings.rvc_model,
                        "speaker": settings.rvc_speaker,
                        "pitch": settings.rvc_pitch,
                        "speed": settings.rvc_speed
                    },
                    timeout=10
                )
                response.raise_for_status()

                # Get audio data and play
                audio_data = response.content
                if audio_data:
                    # Save temporary audio file
                    temp_file = Path("temp_voice.wav")
                    temp_file.write_bytes(audio_data)
                    
                    # Play audio using default audio player
                    import winsound
                    winsound.PlaySound(str(temp_file), winsound.SND_FILENAME)
                    
                    # Clean up temp file
                    temp_file.unlink()
                
            except Exception as e:
                logger.error(f"RVC error: {str(e)}")
                # Fallback to default voice
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Speak(pure_chunk)

            if not refuse_pause:
                time.sleep(0.05)    # IMPORTANT: Mini-rests between chunks for other calculations in the program to run.
            else:
                time.sleep(0.001)   # Still have a mini-mini rest, even with pauses

            # Break free if we undo/redo, and stop reading
            if hotkeys.NEXT_PRESSED or hotkeys.REDO_PRESSED or cut_voice:
                cut_voice = False
                break

        except Exception as e:
            logger.error(f"Voice error: {str(e)}")
            zw_logging.update_debug_log("Error with voice!")

    # Reset the volume cooldown so she don't pickup on herself
    hotkeys.cooldown_listener_timer()
    set_speaking(False)
    return

def speak_line(s_message, refuse_pause):
    """Original speak_line function using Windows SAPI"""
    global cut_voice
    cut_voice = False

    chunky_message = voice_splitter.split_into_sentences(s_message)

    for chunk in chunky_message:
        try:
            # Play soundbaord sounds, if any
            pure_chunk = soundboard.extract_soundboard(chunk)

            # Cut out if we are not speaking unless spoken to!
            if settings.speak_only_spokento and not API.api_controller.last_message_received_has_own_name:
                continue

            # Remove any asterisks from being spoken
            pure_chunk = pure_chunk.replace("*", "")

            # Change any !!! or other multi-exclamations to single use
            pure_chunk = pure_chunk.replace("!!", "!")
            pure_chunk = pure_chunk.replace("!!!", "!")
            pure_chunk = pure_chunk.replace("!!!!", "!")
            pure_chunk = pure_chunk.replace("!!!!!", "!")

            # Speak
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak(pure_chunk)

            if not refuse_pause:
                time.sleep(0.05)    # IMPORTANT: Mini-rests between chunks for other calculations in the program to run.
            else:
                time.sleep(0.001)   # Still have a mini-mini rest, even with pauses

            # Break free if we undo/redo, and stop reading
            if hotkeys.NEXT_PRESSED or hotkeys.REDO_PRESSED or cut_voice:
                cut_voice = False
                break

        except:
            zw_logging.update_debug_log("Error with voice!")

    # Reset the volume cooldown so she don't pickup on herself
    hotkeys.cooldown_listener_timer()
    set_speaking(False)
    return

# Midspeaking (still processing whole message)
def check_if_speaking() -> bool:
    return is_speaking

def set_speaking(set: bool):
    global is_speaking
    is_speaking = set

def force_cut_voice():
    global cut_voice
    cut_voice = True
