#
# Script is for the TTS, since it is now going to be threaded
#
import time

import win32com.client
import utils.hotkeys
import utils.voice_splitter

is_speaking = False
cut_voice = False

def speak_line(s_message):

    global cut_voice
    cut_voice = False

    chunky_message = utils.voice_splitter.split_into_sentences(s_message)

    for chunk in chunky_message:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Speak(chunk)

        time.sleep(0.05)    # IMPORTANT: Mini-rests between chunks for other calculations in the program to run.

        # Break free if we undo/redo, and stop reading
        if utils.hotkeys.NEXT_PRESSED or utils.hotkeys.REDO_PRESSED or cut_voice:
            cut_voice = False
            break




    # Reset the volume cooldown so she don't pickup on herself
    utils.hotkeys.cooldown_listener_timer()

    set_speaking(False)

    return

# Midspeaking (still processing whole message)
def check_if_speaking():
    return is_speaking

def set_speaking(set):
    global is_speaking
    is_speaking = set

def force_cut_voice():
    global cut_voice
    cut_voice = True
