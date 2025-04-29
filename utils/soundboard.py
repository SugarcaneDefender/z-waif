#
# Watchdog to check for soundboard sounds
#

import os
import random

from pydub import AudioSegment
from pydub.playback import play
import time

def extract_soundboard(input_string):

    input_string = input_string.replace("/Soundboard/", "/soundboard/")

    # If the very start of this is a soundboard sound, as some dummy spaces behind it so it splits fine
    if input_string.startswith("/soundboard/"):
        input_string = " " + input_string

    # Split it based on number of soundboard objects
    soundboard_split = input_string.split("/soundboard/")

    # If there is no soundboard object, return right away
    if len(soundboard_split) < 2:
        return input_string

    # Begin our cancatonatoed (cantonese) message, so we can remove the sound headers
    cantonese_message = soundboard_split[0]

    # We have sounds in here, play them
    sound_counter = 1                       # Start at 1, 0 will always be no sound

    time.sleep(0.27) # Mini-rest to stop her speach from affecting the

    while sound_counter < len(soundboard_split):
        sound_trace = soundboard_split[sound_counter].split("/")[0]

        # Play the sound!
        soundboard_playsound(sound_trace)

        cantonese_message += str(soundboard_split[sound_counter].split("/")[1])   # latter half addition
        sound_counter += 1

    return cantonese_message

def soundboard_playsound(sound_name):
    # Plays the given sound. try/except for if it tries to play a sound that doesn't exist / other jank

    try:
        sound = AudioSegment.from_wav("Configurables/Soundboard/" + sound_name + ".wav")
        play(sound)

    except:
        return

