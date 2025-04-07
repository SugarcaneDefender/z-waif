import os

import keyboard
# import mouse
import time
import threading
import utils.alarm
import utils.volume_listener
import utils.settings
import json
import utils.zw_logging
import utils.audio


RATE_PRESSED = False

RATE_LEVEL = 0

NEXT_PRESSED = False

REDO_PRESSED = False


BACKSLASH_PRESSED = False

SPEAK_TOGGLED = False
general_listener_speaking_detected = False

FULL_AUTO_TOGGLED = False
SPEAKING_TIMER = 0
SPEAKING_TIMER_COOLDOWN = 0
SPEAKING_VOLUME_SENSITIVITY = 16
SPEAKING_VOLUME_SENSITIVITY_PRESSED = False


SOFT_RESET_PRESSED = False

VIEW_IMAGE_PRESSED = False
CANCEL_IMAGE_PRESSED = False

BLANK_MESSAGE_PRESSED = False


# Rating Inputs
#keyboard.on_press_key("1", lambda _:rate_input(0))
#keyboard.on_press_key("2", lambda _:rate_input(1))
#keyboard.on_press_key("3", lambda _:rate_input(2))
#keyboard.on_press_key("4", lambda _:rate_input(3))

# Options for right click to speak
# mouse.on_right_click(callback= lambda _:speak_input_toggle(), args="_")

# Legacy Input Bindings
# keyboard.on_press_key("RIGHT_ARROW", lambda _:next_input())
# keyboard.on_press_key("UP_ARROW", lambda _:redo_input())
# keyboard.on_press_key("GRAVE", lambda _:lock_inputs())
# keyboard.on_press_key("BACKSLASH", lambda _:input_lock_backslash())
# keyboard.on_press_key("RIGHT_CTRL", lambda _:speak_input_toggle())
# keyboard.on_press_key("A", lambda _:input_toggle_autochat())
# keyboard.on_press_key("S", lambda _:input_change_listener_sensitivity())
# keyboard.on_press_key("R", lambda _:input_soft_reset())
# keyboard.on_press_key("C", lambda _:input_view_image())
# keyboard.on_press_key("X", lambda _:input_cancel_image())
# keyboard.on_press_key("B", lambda _:input_send_blank())

def load_hotkey_bootstate():

    HOTKEYS_BOOT = os.environ.get("HOTKEYS_BOOT")

    if HOTKEYS_BOOT == "ON":
        utils.settings.hotkeys_locked = False

    if HOTKEYS_BOOT == "OFF":
        utils.settings.hotkeys_locked = True
        print("\nInput System Lock Set To " + str(utils.settings.hotkeys_locked) + " !")

    # Also bind all of our needed hotkeys at this point
    bind_all_hotkeys()

def bind_all_hotkeys():

    # Load in our hotkeys
    with open("Configurables/Keybinds.json", 'r') as openfile:
        keybinds = json.load(openfile)

    # Table for text to function. We use the function name without the () to store it as a variable, then pass it as the bindable
    options = {
        "Next" : next_input,
        "Undo" : redo_input,
        "Input Lock 1" : lock_inputs,
        "Input Lock 2" : input_lock_backslash,
        "Speak Toggle" : speak_input_toggle,
        "Autochat" : input_toggle_autochat,
        "Autochat Sensitivity" : input_change_listener_sensitivity,
        "Soft Reset" : input_soft_reset,
        "View Image" : input_view_image,
        "Cancel Image" : input_cancel_image,
        "Send Blank" : input_send_blank,

        "Semi Auto Chat" : input_toggle_semi_autochat,
        "Toggle Hangout Mode" : input_toggle_hangout_mode
    }

    # Cycle through, dictionary define
    for keybind in keybinds:
        bind_hotkey(keybind[0], options[keybind[1]])


def bind_hotkey(binding, input_action):

    try:
        keyboard.on_press_key(binding, lambda _: input_action())
    except:
        print("Issue binding to hotkey " + binding + "!")
        utils.zw_logging.update_debug_log("Issue binding to hotkey " + binding + "!")


def rate_input(rating):

    if utils.settings.hotkeys_locked:
        return

    global RATE_PRESSED
    global RATE_LEVEL

    RATE_PRESSED = True
    RATE_LEVEL = rating

def next_input():
    if utils.settings.hotkeys_locked:
        return

    global NEXT_PRESSED

    NEXT_PRESSED = True

def redo_input():

    if utils.settings.hotkeys_locked:
        return

    global REDO_PRESSED

    #   Ensure we sent a message to redo, so we don't clear past 1 ever

    REDO_PRESSED = True

def get_speak_input():
    if SPEAKING_TIMER_COOLDOWN > 0:
        return False

    return SPEAK_TOGGLED

def speak_input_toggle():
    if utils.settings.hotkeys_locked:
        return

    global SPEAK_TOGGLED

    SPEAK_TOGGLED = not SPEAK_TOGGLED

def speak_input_toggle_from_ui():
    global SPEAK_TOGGLED

    SPEAK_TOGGLED = not SPEAK_TOGGLED

def speak_input_on_from_cam_direct_talk():
    global SPEAK_TOGGLED

    SPEAK_TOGGLED = True


def lock_inputs():

    # Await and run on another thread
    locking_thread = threading.Thread(target=run_lock_inputs)
    locking_thread.daemon = True
    locking_thread.start()



def run_lock_inputs():
    global BACKSLASH_PRESSED

    # Check for if we press the backslash key in time
    BACKSLASH_PRESSED = False

    time.sleep(0.9)

    if BACKSLASH_PRESSED:
        utils.settings.hotkeys_locked = not utils.settings.hotkeys_locked
        print("\nInput System Lock Set To " + str(utils.settings.hotkeys_locked) + " !")


def input_lock_backslash():
    global BACKSLASH_PRESSED

    BACKSLASH_PRESSED = True


def input_view_image():
    global VIEW_IMAGE_PRESSED

    # additional lockout for if the vision system is offline
    if utils.settings.hotkeys_locked or utils.settings.vision_enabled == False:
        return

    VIEW_IMAGE_PRESSED = True

def input_cancel_image():
    global CANCEL_IMAGE_PRESSED

    # additional lockout for if the vision system is offline
    if utils.settings.hotkeys_locked or utils.settings.vision_enabled == False:
        return

    CANCEL_IMAGE_PRESSED = True

def view_image_from_ui():
    global VIEW_IMAGE_PRESSED

    VIEW_IMAGE_PRESSED = True

def cancel_image_from_ui():
    global CANCEL_IMAGE_PRESSED

    CANCEL_IMAGE_PRESSED = True

def clear_camera_inputs():
    global CANCEL_IMAGE_PRESSED, VIEW_IMAGE_PRESSED

    CANCEL_IMAGE_PRESSED = False
    VIEW_IMAGE_PRESSED = False



def input_send_blank():
    global BLANK_MESSAGE_PRESSED

    if utils.settings.hotkeys_locked:
        return

    BLANK_MESSAGE_PRESSED = True


def get_autochat_toggle():
    return FULL_AUTO_TOGGLED

def input_toggle_autochat():
    global FULL_AUTO_TOGGLED

    if utils.settings.hotkeys_locked:
        return

    if utils.settings.hangout_mode:
        return

    FULL_AUTO_TOGGLED = not FULL_AUTO_TOGGLED
    print("\nFull Auto Set To " + str(FULL_AUTO_TOGGLED) + " !")

    # Disable semi-auto
    utils.settings.semi_auto_chat = False



# For when semi-auto chat is turned on
def disable_autochat():
    global FULL_AUTO_TOGGLED
    FULL_AUTO_TOGGLED = False

def input_toggle_autochat_from_ui():
    global FULL_AUTO_TOGGLED

    FULL_AUTO_TOGGLED = not FULL_AUTO_TOGGLED
    print("\nFull Auto Set To " + str(FULL_AUTO_TOGGLED) + " !")

    # Disable semi-auto
    utils.settings.semi_auto_chat = False


# From keyboard
def input_toggle_semi_autochat():

    if utils.settings.hotkeys_locked:
        return

    if utils.settings.hangout_mode:
        return

    # Mutually exclusive
    disable_autochat()

    utils.settings.semi_auto_chat = not utils.settings.semi_auto_chat

    print("\nSemi-Auto Chat set to " + str(utils.settings.semi_auto_chat) + " !")

def input_toggle_hangout_mode():
    global FULL_AUTO_TOGGLED

    if utils.settings.hotkeys_locked:
        return

    if utils.settings.stream_chats is False:
        return  # Not allowed if our chats are not streamed

    # It's on rn, disable
    if utils.settings.hangout_mode is True:
        utils.settings.hangout_mode = False
        utils.settings.semi_auto_chat = False
        FULL_AUTO_TOGGLED = False

    # It's off rn, enable
    elif utils.settings.hangout_mode is False:
        utils.settings.hangout_mode = True
        utils.settings.semi_auto_chat = False
        FULL_AUTO_TOGGLED = True

    print("Hangout mode toggled to " + str(utils.settings.hangout_mode))
    utils.zw_logging.update_debug_log("Hangout mode toggled to " + str(utils.settings.hangout_mode))

# From webui.
# Note: Yes, this code is getting a bit jungle like and excessive. But, I want to grow first, and this isn't too bad
# I mean, it's the Hotkey script; why the hell is the UI toggle here??? But again, it makes sense cause we have toggles in here
# Z-Waif will grow bigger and bigger until a great reforge is needed. By then, we will have good waifus, and they can do the code for us.
# I know that this is literally describing the singularity, but well, thought has a physical component. You ever think of that?
# Thinking takes electricity - for us and them - for anyone (unless you have some kind of device with light or water using kinetic energy)
# So it takes physical space to think. And so, the singularity will simply be improvements over time, since it can't become
# "all knowing". There is a literal physical limit, we live in a physical world.
# That's like, the whole point of the local AI Waifu; they are right there with you. They are physically present.
# We are simply giving them senses.
# Okay, I think this scrawl has gone on long enough... back to the coding mines.
def web_ui_toggle_hangout_mode():
    global FULL_AUTO_TOGGLED

    if utils.settings.stream_chats is False:
        return  # Not allowed if our chats are not streamed

    # It's on rn, disable
    if utils.settings.hangout_mode is True:
        utils.settings.hangout_mode = False
        utils.settings.semi_auto_chat = False
        FULL_AUTO_TOGGLED = False

    # It's off rn, enable
    elif utils.settings.hangout_mode is False:
        utils.settings.hangout_mode = True
        utils.settings.semi_auto_chat = False
        FULL_AUTO_TOGGLED = True

    print("Hangout mode toggled to " + str(utils.settings.hangout_mode))
    utils.zw_logging.update_debug_log("Hangout mode toggled to " + str(utils.settings.hangout_mode))

def listener_timer():
    global SPEAK_TOGGLED
    global general_listener_speaking_detected
    global SPEAKING_TIMER
    global SPEAKING_TIMER_COOLDOWN


    while True:
        vol_listener_level = utils.volume_listener.get_vol_level()

        # If we are speaking, add to counter, if not remove from it
        if (vol_listener_level > SPEAKING_VOLUME_SENSITIVITY) and (SPEAKING_TIMER_COOLDOWN == 0):
            SPEAKING_TIMER += 40
            if SPEAKING_TIMER > 109:
                SPEAKING_TIMER = 109

        else:
            SPEAKING_TIMER -= 1
            if SPEAKING_TIMER < 0:
                SPEAKING_TIMER = 0



        # No full auto indoors! Check to see if we need to flop it lmao
        if FULL_AUTO_TOGGLED:
            if (SPEAKING_TIMER == 0 or SPEAKING_TIMER_COOLDOWN > 0) and SPEAK_TOGGLED == True:
                SPEAK_TOGGLED = False

            elif SPEAKING_TIMER > 0 and SPEAK_TOGGLED == False:
                SPEAK_TOGGLED = True

        # Same thing here, but with endpoints for hangout mode to detect with
        if (SPEAKING_TIMER == 0 or SPEAKING_TIMER_COOLDOWN > 0) and SPEAK_TOGGLED == True:
            general_listener_speaking_detected = False

        elif SPEAKING_TIMER > 0 and SPEAK_TOGGLED == False:
            general_listener_speaking_detected = True


        # End of loop, clock cycle time
        SPEAKING_TIMER_COOLDOWN -= 0.02
        if SPEAKING_TIMER_COOLDOWN < 0:
            SPEAKING_TIMER_COOLDOWN = 0

        time.sleep(0.02)


def cooldown_listener_timer():
    global SPEAKING_TIMER
    global SPEAKING_TIMER_COOLDOWN

    SPEAKING_TIMER = 0
    SPEAKING_TIMER_COOLDOWN = 0.47


def input_change_listener_sensitivity():
    global SPEAKING_VOLUME_SENSITIVITY

    if utils.settings.hotkeys_locked:
        return

    if SPEAKING_VOLUME_SENSITIVITY <= 9:
        SPEAKING_VOLUME_SENSITIVITY = 16
    elif SPEAKING_VOLUME_SENSITIVITY <= 16:
        SPEAKING_VOLUME_SENSITIVITY = 27
    elif SPEAKING_VOLUME_SENSITIVITY <= 27:
        SPEAKING_VOLUME_SENSITIVITY = 57
    elif SPEAKING_VOLUME_SENSITIVITY <= 57:
        SPEAKING_VOLUME_SENSITIVITY = 104
    elif SPEAKING_VOLUME_SENSITIVITY >= 104:
        SPEAKING_VOLUME_SENSITIVITY = 9
    print("\nSensitivity Set To " + str(SPEAKING_VOLUME_SENSITIVITY) + "!")


def input_change_listener_sensitivity_from_ui(value):
    global SPEAKING_VOLUME_SENSITIVITY

    SPEAKING_VOLUME_SENSITIVITY = value

    print("\nSensitivity Set To " + str(SPEAKING_VOLUME_SENSITIVITY) + "!")



def input_soft_reset():
    global SOFT_RESET_PRESSED

    if utils.settings.hotkeys_locked:
        return

    SOFT_RESET_PRESSED = True

# Used to detect, and then clear a next input press. "Pulls" the input, making it eat it.
def pull_next_press_input():
    global NEXT_PRESSED

    if NEXT_PRESSED:
        NEXT_PRESSED = False    # Cleaning
        return True             # We pressed it bro

    return False

# Set to true
def do_next_press_input():
    global NEXT_PRESSED
    NEXT_PRESSED = True

# Turns all inputs off
def stack_wipe_inputs():
    global RATE_PRESSED, NEXT_PRESSED, REDO_PRESSED, SOFT_RESET_PRESSED, VIEW_IMAGE_PRESSED, BLANK_MESSAGE_PRESSED, SPEAK_TOGGLED

    RATE_PRESSED = False
    NEXT_PRESSED = False
    REDO_PRESSED = False
    SOFT_RESET_PRESSED = False
    VIEW_IMAGE_PRESSED = False
    BLANK_MESSAGE_PRESSED = False
    SPEAK_TOGGLED = False

def chat_input_await():
    input_found = False

    while not input_found:
        global RATE_PRESSED, NEXT_PRESSED, REDO_PRESSED, SOFT_RESET_PRESSED, VIEW_IMAGE_PRESSED, BLANK_MESSAGE_PRESSED

        # Breakout if gaming started
        if utils.settings.is_gaming_loop:
            break

        # Most important is the hangout loop: run that first
        if utils.settings.hangout_mode:
            return "Hangout"

        if get_speak_input():

            return "CHAT"

        elif RATE_PRESSED:
            RATE_PRESSED = False
            return "RATE"


        elif NEXT_PRESSED:
            NEXT_PRESSED = False
            return "NEXT"


        elif REDO_PRESSED:
            REDO_PRESSED = False
            return "REDO"

        elif SOFT_RESET_PRESSED:
            SOFT_RESET_PRESSED = False
            return "SOFT_RESET"

        # NOTE: Well want to have a central awaiting system later, but right now I'm just adding to here
        elif utils.alarm.alarm_check():
            return "ALARM"


        elif VIEW_IMAGE_PRESSED:
            VIEW_IMAGE_PRESSED = False
            return "VIEW"

        elif BLANK_MESSAGE_PRESSED:
            BLANK_MESSAGE_PRESSED = False
            return "BLANK"

        else:
            time.sleep(0.01)

