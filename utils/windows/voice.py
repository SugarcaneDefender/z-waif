import time
import os
import requests
import json
import logging
import tempfile
from pathlib import Path

assert os.name == 'nt' # type: ignore

import win32com.client
import winsound
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
    """Speak a line using RVC voice conversion with proper Windows TTS fallback"""
    global cut_voice, is_speaking
    cut_voice = False
    is_speaking = True

    try:
        chunky_message = voice_splitter.split_into_sentences(s_message)

        for chunk in chunky_message:
            try:
                # Play soundboard sounds, if any
                pure_chunk = soundboard.extract_soundboard(chunk)

                # Cut out if we are not speaking unless spoken to!
                if settings.speak_only_spokento and not API.api_controller.last_message_received_has_own_name:
                    continue

                # Clean up the text for speech
                pure_chunk = pure_chunk.replace("*", "")
                pure_chunk = pure_chunk.replace("!!", "!").replace("!!!", "!").replace("!!!!", "!").replace("!!!!!", "!")

                # Skip empty chunks
                if not pure_chunk.strip():
                    continue

                # Try RVC first
                rvc_success = False
                try:
                    response = requests.post(
                        RVC_URI,
                        json={
                            "text": pure_chunk,
                            "model": getattr(settings, 'rvc_model', 'default'),
                            "speaker": getattr(settings, 'rvc_speaker', 'default'),
                            "pitch": getattr(settings, 'rvc_pitch', 1.0),
                            "speed": getattr(settings, 'rvc_speed', 1.0)
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        audio_data = response.content
                        if audio_data:
                            # Save to temporary file with proper cleanup
                            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                                temp_file.write(audio_data)
                                temp_file_path = temp_file.name
                            
                            try:
                                # Play audio using Windows sound system
                                winsound.PlaySound(temp_file_path, winsound.SND_FILENAME)
                                rvc_success = True
                            except Exception as play_error:
                                logger.error(f"Error playing RVC audio: {play_error}")
                            finally:
                                # Clean up temp file
                                try:
                                    os.unlink(temp_file_path)
                                except:
                                    pass
                    else:
                        logger.warning(f"RVC server returned status code: {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"RVC request failed: {e}")
                except Exception as e:
                    logger.error(f"RVC error: {e}")

                # Fallback to Windows SAPI if RVC failed
                if not rvc_success:
                    logger.info("Falling back to Windows SAPI TTS")
                    _speak_line_sapi(pure_chunk)

                # Timing control
                if not refuse_pause:
                    time.sleep(0.05)    # IMPORTANT: Mini-rests between chunks for other calculations in the program to run.
                else:
                    time.sleep(0.001)   # Still have a mini-mini rest, even with pauses

                # Break free if we undo/redo, and stop reading
                if hotkeys.NEXT_PRESSED or hotkeys.REDO_PRESSED or cut_voice:
                    cut_voice = False
                    break

            except Exception as e:
                logger.error(f"Voice chunk error: {e}")
                zw_logging.update_debug_log(f"Error with voice chunk: {e}")

    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        zw_logging.update_debug_log(f"Error with voice processing: {e}")
    finally:
        # Reset the volume cooldown so she don't pickup on herself
        try:
            hotkeys.cooldown_listener_timer()
        except:
            pass
        is_speaking = False

# Improved SAPI-based TTS with better error handling
def _speak_line_sapi(pure_chunk):
    """Speak using Windows SAPI with improved error handling"""
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        
        # Set voice properties for better quality
        voices = speaker.GetVoices()
        if voices.Count > 0:
            # Try to find a high-quality voice
            for i in range(voices.Count):
                voice = voices.Item(i)
                if "enhanced" in voice.GetDescription().lower() or "premium" in voice.GetDescription().lower():
                    speaker.Voice = voice
                    break
        
        # Speak the text
        speaker.Speak(pure_chunk)
        
    except Exception as e:
        logger.error(f"SAPI TTS error: {e}")
        # Final fallback - just print the text
        print(f"[Voice Error - Text]: {pure_chunk}")

def speak_line(s_message, refuse_pause):
    """Speak a line using RVC if enabled, else fallback to Windows SAPI"""
    # Check if RVC is enabled in settings
    use_rvc = getattr(settings, 'use_rvc', False)
    
    if use_rvc:
        speak_line_rvc(s_message, refuse_pause)
        return

    global cut_voice, is_speaking
    cut_voice = False
    is_speaking = True

    try:
        for chunk in voice_splitter.split_into_sentences(s_message):
            try:
                pure_chunk = soundboard.extract_soundboard(chunk)

                if settings.speak_only_spokento and not API.api_controller.last_message_received_has_own_name:
                    continue

                pure_chunk = pure_chunk.replace("*", "").replace("!!", "!").replace("!!!", "!").replace("!!!!", "!").replace("!!!!!", "!")

                if pure_chunk.strip():
                    _speak_line_sapi(pure_chunk)

                time.sleep(0.001 if refuse_pause else 0.05)

                if hotkeys.NEXT_PRESSED or hotkeys.REDO_PRESSED or cut_voice:
                    cut_voice = False
                    break

            except Exception as e:
                logger.error(f"Voice chunk error: {e}")
                zw_logging.update_debug_log(f"Error with voice chunk: {e}")

    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        zw_logging.update_debug_log(f"Error with voice processing: {e}")
    finally:
        try:
            hotkeys.cooldown_listener_timer()
        except:
            pass
        is_speaking = False

# Midspeaking (still processing whole message)
def check_if_speaking() -> bool:
    return is_speaking

def set_speaking(set_val: bool):
    global is_speaking
    is_speaking = set_val

def force_cut_voice():
    global cut_voice
    cut_voice = True
