import numpy as np
import sounddevice as sd
from numba.cuda.libdevice import trunc
from sympy import false

duration = 10 #in seconds

global VOL_LISTENER_LEVEL
VOL_LISTENER_LEVEL = 0.01

global SPEAKING_DETECTED
global SPEAKING_TIMER
SPEAKING_DETECTED = False
SPEAKING_TIMER = 0

no_mic = False


def audio_callback(indata, frames, time, status):
    global VOL_LISTENER_LEVEL

    if no_mic:
        VOL_LISTENER_LEVEL = 0

    volume_norm = np.linalg.norm(indata) * 10

    # for reference, 0-2 is quiet background, 20 - 30 is non direct talking, 40+ is identified talking
    # take a rolling average, be more aggressive for if the sound is louder

    if (volume_norm > VOL_LISTENER_LEVEL):
        VOL_LISTENER_LEVEL = (VOL_LISTENER_LEVEL + volume_norm + 2) / 2
    else:
        VOL_LISTENER_LEVEL = ((VOL_LISTENER_LEVEL * 5) + volume_norm) / 6


def get_vol_level():
    return VOL_LISTENER_LEVEL



def run_volume_listener():

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
