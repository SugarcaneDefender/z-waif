import os
# Moved to os-specific files
if os.name == 'nt':
    from .windows.voice import speak_line, check_if_speaking
else: # TODO: linux
    from .mac.voice import speak_line, check_if_speaking


def set_speaking(set):
    global is_speaking
    is_speaking = set

def force_cut_voice():
    global cut_voice
    cut_voice = True
