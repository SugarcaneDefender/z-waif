import time
import os

import utils.hotkeys
import utils.voice_splitter
import utils.soundboard
import utils.settings
import API.api_controller

assert os.name == "posix" # type: ignore

is_speaking = False
cut_voice = False

def speak_line(s_message: str, refuse_pause: bool):
    global cut_voice #, is_speaking
    cut_voice = False
    chunky_message = utils.voice_splitter.split_into_sentences(s_message)
    
    for chunk in chunky_message:
        #speaker = win32com.client.Dispatch("SAPI.SpVoice")
        #speaker.Speak(chunk)

        # Play soundbaord sounds, if any
        pure_chunk = utils.soundboard.extract_soundboard(chunk)

        # Cut out if we are not speaking unless spoken to!
        if utils.settings.speak_only_spokento and not API.api_controller.last_message_received_has_own_name:
            continue
        
        # Escape the chunk
        banned_char_list = ["\"", "'", "\\", "`", "$", "{", "}", "[", "]", "(", ")", "<", ">", "|"]
        for char in banned_char_list:
            pure_chunk = pure_chunk.replace(char, "\\" + char)
        
        os.system(f"say {pure_chunk} &") # TODO: Use a real tts engine (piper?) instead of system tts

        if not refuse_pause:
            time.sleep(0.05)    # IMPORTANT: Mini-rests between chunks for other calculations in the program to run.
        else:
            time.sleep(0.001)   # Still have a mini-mini rest, even with pauses

        # Break free if we undo/redo, and stop reading
        if utils.hotkeys.NEXT_PRESSED or utils.hotkeys.REDO_PRESSED or cut_voice:
            cut_voice = False
            break




    # Reset the volume cooldown so she don't pickup on herself
    utils.hotkeys.cooldown_listener_timer()

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
