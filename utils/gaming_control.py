import time

import keyboard
from utils import tag_task_controller as tag
from utils import settings
import re
from utils import zw_logging
import json

#
# This script is for your AI to interact with games.
#


# What primarily controls it
def gaming_step():

    # Ensure we have all the settings prepared here
    settings.cam_use_image_feed = False
    settings.cam_direct_talk = False
    settings.cam_reply_after = True
    settings.cam_image_preview = False
    settings.cam_reply_after = True

    # Run this VIEW in loop
    return "VIEW"



def message_inputs(message):

    cur_game = tag.get_pure_task()

    # Parse all presses
    these_presses = re.findall(r'\(.*?\)', message)

    # Cycle through all the button presses
    for press in these_presses:

        # Send the button presses
        do_button_press(press, tag.get_pure_task())

        # Cancel the loop if RIPOUT is sent (This is for if your bot has a crisis and wants to stop experiencing (humane))
        if press == "(ripout)":
            settings.is_gaming_loop = False




def do_button_press(press, game):

    # Get out mappings from JSON
    with open("Configurables/GamingInputs/" + game + ".json", 'r') as openfile:
        mappings = json.load(openfile)

    # Cycle through all of the button mappings. If one is found, press and wait
    for buttons in mappings:
        if buttons[0] == str.lower(press):

            keyboard.press(buttons[1])
            zw_logging.update_debug_log("Pressed " + buttons[1] + "!")
            time.sleep(0.07)
            keyboard.release(buttons[1])
            time.sleep(0.67)

