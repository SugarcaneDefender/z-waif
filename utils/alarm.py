import time
import datetime
from utils import settings
import os
import json

ALARM_TRIGGERED: bool = False
ALARM_READY: bool = False
ALARM_MESSAGE: str = (
    "[System Message] There was an issue with the alarm system... whoops!"
)

random_memories: bool = True

# Load the configurable alarm message (talomere, comes after the date)
with open("Configurables/AlarmMessage.json", "r") as openfile:
    alarm_talomere: str = json.load(openfile)


def alarm_loop():
    global ALARM_TRIGGERED, ALARM_READY, ALARM_MESSAGE

    while True:
        # Loop every 10 seconds
        time.sleep(10)

        # Get the time string
        current_time = datetime.datetime.now()
        cur_time_string = current_time.strftime("%H:%M")

        # Reset the alarm just after midnight every night
        if cur_time_string == "00:01":
            ALARM_TRIGGERED = False

        # Run our alarm here if we are at the specified time
        if cur_time_string == settings.alarm_time and ALARM_TRIGGERED == False:

            # Flag
            ALARM_TRIGGERED = True

            # Get name (can't declair at the start, donno why, don't care!)
            char_name = os.environ.get("CHAR_NAME")

            # Make our message
            cur_date_string = current_time.strftime("%B/%d/%Y")
            cur_day_of_week_string = current_time.strftime("%A")

            # TODO: combine?
            alarm_message = f"[System A] Good morning, {char_name}! It's {cur_day_of_week_string}, {cur_date_string}, at {cur_time_string}. {alarm_talomere}"

            ALARM_MESSAGE = alarm_message

            # Flag us, we can be picked up by main
            ALARM_READY = True


def alarm_check() -> bool:
    return ALARM_READY


def clear_alarm():
    global ALARM_READY
    ALARM_READY = False


def get_alarm_message() -> str:
    return ALARM_MESSAGE
