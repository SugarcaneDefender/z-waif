import time
import os

import utils.hotkeys
import utils.voice_splitter

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
        
        # Escape the chunk
        banned_char_list = ["\"", "'", "\\", "`", "$", "{", "}", "[", "]", "(", ")", "<", ">", "|"]
        for char in banned_char_list:
            chunk = chunk.replace(char, "\\" + char)
        
        os.system(f"say {chunk} &") # TODO: Use a real tts engine (piper?) instead of system tts

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
