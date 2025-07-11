import numpy as np
import sounddevice as sd
#from numba.cuda.libdevice import trunc
#from sympy import false

from utils import hotkeys
from utils import settings

duration = 10 #in seconds

global VOL_LISTENER_LEVEL
VOL_LISTENER_LEVEL = 0.01

global SPEAKING_DETECTED
global SPEAKING_TIMER
SPEAKING_DETECTED = False
SPEAKING_TIMER = 0

no_mic = False

# Add missing constants that hotkeys module expects
SPEAKING_VOLUME_THRESHOLD = 35.0  # Volume threshold for speaking detection
SPEAKING_TIMER_MAX = 50  # Maximum timer value for speaking detection


def audio_callback(indata, frames, time, status):
    global VOL_LISTENER_LEVEL

    if no_mic:
        VOL_LISTENER_LEVEL = 0

    # volume_norm = our current volume value
    volume_norm = np.linalg.norm(indata) * 10

    # for reference, 0-2 is quiet background, 20 - 30 is non direct talking, 40+ is identified talking
    # take a rolling average, be more aggressive for if the sound is louder

    if (volume_norm > VOL_LISTENER_LEVEL):
        VOL_LISTENER_LEVEL = (VOL_LISTENER_LEVEL + volume_norm + (0.024 * hotkeys.SPEAKING_VOLUME_SENSITIVITY) + 0.01) / 2
    else:
        VOL_LISTENER_LEVEL = ((VOL_LISTENER_LEVEL * 8) + volume_norm - (0.0044 * hotkeys.SPEAKING_VOLUME_SENSITIVITY)) / 9


def get_vol_level():
    return VOL_LISTENER_LEVEL


def update_vad_result():
    """Update the VAD (Voice Activity Detection) result based on volume level."""
    global SPEAKING_DETECTED, SPEAKING_TIMER, VOL_LISTENER_LEVEL
    
    # Skip if using Silero VAD
    if settings.use_silero_vad:
        return
        
    # Check if volume exceeds speaking threshold
    threshold = getattr(hotkeys, 'SPEAKING_VOLUME_THRESHOLD', SPEAKING_VOLUME_THRESHOLD)
    if VOL_LISTENER_LEVEL > threshold:
        SPEAKING_DETECTED = True
        SPEAKING_TIMER = getattr(hotkeys, 'SPEAKING_TIMER_MAX', SPEAKING_TIMER_MAX)
    elif SPEAKING_TIMER > 0:
        SPEAKING_TIMER -= 1
    else:
        SPEAKING_DETECTED = False


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
        # Run Stream
        stream = sd.InputStream(callback=audio_callback)


        # Wait up!
        with stream:
            sd.sleep(duration * 1000)
