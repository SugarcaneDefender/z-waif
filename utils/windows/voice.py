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
RVC_PORT = os.environ.get("RVC_PORT", "18888")  # Updated to match the actual RVC server port
# Fix: Use the correct RVC API endpoint - most RVC servers use /api/tts or /tts
RVC_URI = f"http://{RVC_HOST}:{RVC_PORT}/api/tts"

def speak_line_rvc(s_message, refuse_pause=False):
    """Speak a line using RVC voice conversion with proper Windows TTS fallback"""
    print(f"[DEBUG] speak_line_rvc called with: {repr(s_message)}")
    global cut_voice, is_speaking
    cut_voice = False
    is_speaking = True
    print(f"[DEBUG] speak_line_rvc: starting RVC processing")
    
    # Quick check if RVC server is running and has TTS capabilities
    try:
        test_response = requests.get(f"http://{RVC_HOST}:{RVC_PORT}/", timeout=2)
        print(f"[DEBUG] RVC server check: {test_response.status_code}")
        
        # Check if this RVC server has TTS endpoints
        tts_test = requests.get(f"http://{RVC_HOST}:{RVC_PORT}/tts", timeout=2)
        if tts_test.status_code == 404:
            print(f"[DEBUG] RVC server running but no TTS endpoints available")
            print(f"[DEBUG] Falling back to Windows SAPI immediately")
            _speak_line_sapi(s_message)
            return
            
    except Exception as e:
        print(f"[DEBUG] RVC server not responding: {e}")
        print(f"[DEBUG] Falling back to Windows SAPI immediately")
        _speak_line_sapi(s_message)
        return

    try:
        print(f"[DEBUG] speak_line_rvc: splitting message into sentences")
        chunky_message = voice_splitter.split_into_sentences(s_message)
        print(f"[DEBUG] speak_line_rvc: got {len(chunky_message)} sentences")

        for i, chunk in enumerate(chunky_message):
            print(f"[DEBUG] speak_line_rvc: processing chunk {i+1}/{len(chunky_message)}: {repr(chunk)}")
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
                print(f"[DEBUG] speak_line_rvc: trying RVC endpoints")
                
                # List of common RVC endpoints to try (updated for modern RVC API)
                rvc_endpoints = [
                    f"http://{RVC_HOST}:{RVC_PORT}/tts",
                    f"http://{RVC_HOST}:{RVC_PORT}/api/tts",
                    f"http://{RVC_HOST}:{RVC_PORT}/synthesize",
                    f"http://{RVC_HOST}:{RVC_PORT}/api/synthesize",
                    f"http://{RVC_HOST}:{RVC_PORT}/voice",
                    f"http://{RVC_HOST}:{RVC_PORT}/api/voice"
                ]
                print(f"[DEBUG] speak_line_rvc: RVC endpoints to try: {rvc_endpoints}")
                
                for endpoint in rvc_endpoints:
                    print(f"[DEBUG] speak_line_rvc: trying endpoint: {endpoint}")
                    try:
                        # Updated RVC request format to match modern RVC API
                        rvc_payload = {
                            "text": pure_chunk,
                            "model": getattr(settings, 'rvc_model', 'default'),
                            "speaker_id": int(getattr(settings, 'rvc_speaker', '0')),
                            "pitch_adjust": float(getattr(settings, 'rvc_pitch', '0.0')),
                            "speed": float(getattr(settings, 'rvc_speed', '1.0')),
                            "emotion": "Happy",  # Default emotion
                            "language": "en"     # Default language
                        }
                        
                        # Alternative payload format for different RVC implementations
                        rvc_payload_alt = {
                            "text": pure_chunk,
                            "voice": getattr(settings, 'rvc_model', 'default'),
                            "speaker": int(getattr(settings, 'rvc_speaker', '0')),
                            "pitch": float(getattr(settings, 'rvc_pitch', '0.0')),
                            "speed": float(getattr(settings, 'rvc_speed', '1.0'))
                        }
                        print(f"[DEBUG] speak_line_rvc: sending payload to {endpoint}: {rvc_payload}")
                        
                        # Try primary payload format first
                        response = requests.post(
                            endpoint,
                            json=rvc_payload,
                            timeout=10
                        )
                        
                        # If that fails, try alternative format
                        if response.status_code != 200:
                            print(f"[DEBUG] speak_line_rvc: trying alternative payload format for {endpoint}")
                            response = requests.post(
                                endpoint,
                                json=rvc_payload_alt,
                                timeout=10
                            )
                        print(f"[DEBUG] speak_line_rvc: got response from {endpoint}, status: {response.status_code}")
                        
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
                                    logger.info(f"RVC success using endpoint: {endpoint}")
                                    break  # Success, exit the endpoint loop
                                except Exception as play_error:
                                    logger.error(f"Error playing RVC audio: {play_error}")
                                finally:
                                    # Clean up temp file
                                    try:
                                        os.unlink(temp_file_path)
                                    except:
                                        pass
                        else:
                            logger.warning(f"RVC server returned status code: {response.status_code} for endpoint: {endpoint}")
                            
                    except requests.exceptions.RequestException as e:
                        logger.debug(f"RVC request failed for endpoint {endpoint}: {e}")
                    except Exception as e:
                        logger.debug(f"RVC error for endpoint {endpoint}: {e}")
                
                # If no endpoint worked, log it and fallback immediately
                if not rvc_success:
                    logger.warning("All RVC endpoints failed, falling back to Windows SAPI TTS")
                    print(f"[DEBUG] RVC failed, using Windows SAPI fallback")
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
    print(f"[DEBUG] _speak_line_sapi called with: {repr(pure_chunk)}")
    try:
        print(f"[DEBUG] Creating SAPI SpVoice object")
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        print(f"[DEBUG] SAPI SpVoice object created")
        
        # Set voice properties for better quality
        print(f"[DEBUG] Getting voices")
        voices = speaker.GetVoices()
        print(f"[DEBUG] Found {voices.Count} voices")
        if voices.Count > 0:
            # Try to find a high-quality voice
            for i in range(voices.Count):
                voice = voices.Item(i)
                if "enhanced" in voice.GetDescription().lower() or "premium" in voice.GetDescription().lower():
                    speaker.Voice = voice
                    print(f"[DEBUG] Set enhanced voice: {voice.GetDescription()}")
                    break
        
        # Speak the text
        print(f"[DEBUG] About to call speaker.Speak()")
        speaker.Speak(pure_chunk)
        print(f"[DEBUG] speaker.Speak() completed")
        
    except Exception as e:
        print(f"[DEBUG] SAPI TTS error: {e}")
        logger.error(f"SAPI TTS error: {e}")
        # Final fallback - just print the text
        print(f"[Voice Error - Text]: {pure_chunk}")
    print(f"[DEBUG] _speak_line_sapi function completed")

def speak_line(s_message, refuse_pause):
    """Speak a line using RVC if enabled, else fallback to Windows SAPI"""
    print(f"[DEBUG] Windows speak_line called with: {repr(s_message)}")
    # Check if RVC is enabled in settings
    use_rvc = getattr(settings, 'use_rvc', False)
    print(f"[DEBUG] RVC enabled: {use_rvc}")
    
    if use_rvc:
        print(f"[DEBUG] Using RVC speak_line_rvc")
        speak_line_rvc(s_message, refuse_pause)
        return

    global cut_voice, is_speaking
    cut_voice = False
    is_speaking = True
    print(f"[DEBUG] Using Windows SAPI TTS")

    try:
        for chunk in voice_splitter.split_into_sentences(s_message):
            try:
                pure_chunk = soundboard.extract_soundboard(chunk)

                if settings.speak_only_spokento and not API.api_controller.last_message_received_has_own_name:
                    continue

                pure_chunk = pure_chunk.replace("*", "").replace("!!", "!").replace("!!!", "!").replace("!!!!", "!").replace("!!!!!", "!")

                if pure_chunk.strip():
                    print(f"[DEBUG] About to call _speak_line_sapi with: {repr(pure_chunk)}")
                    _speak_line_sapi(pure_chunk)
                    print(f"[DEBUG] _speak_line_sapi completed")

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
        print(f"[DEBUG] Windows speak_line completed")

# Midspeaking (still processing whole message)
def check_if_speaking() -> bool:
    return is_speaking

def set_speaking(set_val: bool):
    global is_speaking
    is_speaking = set_val

def force_cut_voice():
    global cut_voice
    cut_voice = True
