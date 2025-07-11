import numpy as np
import sounddevice as sd
#from numba.cuda.libdevice import trunc
#from sympy import false

from utils import settings
from utils import audio
from utils import voice

duration = 10 #in seconds

global VOL_LISTENER_LEVEL
VOL_LISTENER_LEVEL = 0.01

global SPEAKING_DETECTED
global SPEAKING_TIMER
SPEAKING_DETECTED = False
SPEAKING_TIMER = 0

no_mic = False

# Add missing attributes that other modules are trying to access
VAD_RESULT = False
speaking = False

def audio_callback(indata, frames, time, status):
    global VOL_LISTENER_LEVEL

    if no_mic:
        VOL_LISTENER_LEVEL = 0

    # volume_norm = our current volume value
    volume_norm = np.linalg.norm(indata) * 10

    # for reference, 0-2 is quiet background, 20 - 30 is non direct talking, 40+ is identified talking
    # take a rolling average, be more aggressive for if the sound is louder
    
    # Get sensitivity value without circular import
    try:
        from utils import hotkeys
        sensitivity = hotkeys.SPEAKING_VOLUME_SENSITIVITY
    except (ImportError, AttributeError):
        sensitivity = 16  # Default value

    if (volume_norm > VOL_LISTENER_LEVEL):
        VOL_LISTENER_LEVEL = (VOL_LISTENER_LEVEL + volume_norm + (0.024 * sensitivity) + 0.01) / 2
    else:
        VOL_LISTENER_LEVEL = ((VOL_LISTENER_LEVEL * 8) + volume_norm - (0.0044 * sensitivity)) / 9


def get_vol_level():
    return VOL_LISTENER_LEVEL


def update_vad_result():
    """Update VAD_RESULT based on current VAD state"""
    global VAD_RESULT
    VAD_RESULT = audio.get_vad_voice_detected()


def update_speaking_state():
    """Update speaking state based on voice module"""
    global speaking
    speaking = voice.is_speaking


def run_volume_listener():

    # Do not run this if we are using Silero VAD instead!
    if settings.use_silero_vad == True:
        return

    allow_mic = False

    sound_query = sd.query_devices()
    for devices in sound_query:
        if devices['max_input_channels'] != 0:
            allow_mic = True

    if not allow_mic:
        print("No mic detected!")

        global no_mic
        no_mic = True

        global VOL_LISTENER_LEVEL
        VOL_LISTENER_LEVEL = 0

        return

    while True:
        # Update VAD and speaking states
        update_vad_result()
        update_speaking_state()
        
        # Run Stream
        stream = sd.InputStream(callback=audio_callback)


        # Wait up!
        with stream:
            sd.sleep(duration * 1000)
