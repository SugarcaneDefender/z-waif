import os

import keyboard
import mouse
import time
import threading
import utils.alarm
import utils.volume_listener
import utils.settings


RATE_PRESSED = False

RATE_LEVEL = 0

NEXT_PRESSED = False

REDO_PRESSED = False


BACKSLASH_PRESSED = False

SPEAK_TOGGLED = False

FULL_AUTO_TOGGLED = False
SPEAKING_TIMER = 0
SPEAKING_TIMER_COOLDOWN = 0
SPEAKING_VOLUME_SENSITIVITY = 20
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


# Next Input

keyboard.on_press_key("RIGHT_ARROW", lambda _:next_input())


# Undo Message Input

keyboard.on_press_key("UP_ARROW", lambda _:redo_input())


#Locking Input

keyboard.on_press_key("GRAVE", lambda _:lock_inputs())
keyboard.on_press_key("BACKSLASH", lambda _:input_lock_backslash())


keyboard.on_press_key("RIGHT_CTRL", lambda _:speak_input_toggle())

# Options for right click to speak
# mouse.on_right_click(callback= lambda _:speak_input_toggle(), args="_")

keyboard.on_press_key("A", lambda _:input_toggle_autochat())
keyboard.on_press_key("S", lambda _:input_change_listener_sensitivity())

keyboard.on_press_key("R", lambda _:input_soft_reset())

keyboard.on_press_key("C", lambda _:input_view_image())
keyboard.on_press_key("X", lambda _:input_cancel_image())

keyboard.on_press_key("B", lambda _:input_send_blank())

def load_hotkey_bootstate():

    HOTKEYS_BOOT = os.environ.get("HOTKEYS_BOOT")

    if HOTKEYS_BOOT == "ON":
        utils.settings.hotkeys_locked = False

    if HOTKEYS_BOOT == "OFF":
        utils.settings.hotkeys_locked = True
        print("\nInput System Lock Set To " + str(utils.settings.hotkeys_locked) + " !")



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

    FULL_AUTO_TOGGLED = not FULL_AUTO_TOGGLED
    print("\nFull Auto Set To " + str(FULL_AUTO_TOGGLED) + " !")

def input_toggle_autochat_from_ui():
    global FULL_AUTO_TOGGLED

    FULL_AUTO_TOGGLED = not FULL_AUTO_TOGGLED
    print("\nFull Auto Set To " + str(FULL_AUTO_TOGGLED) + " !")


def listener_timer():
    global SPEAK_TOGGLED
    global SPEAKING_TIMER
    global SPEAKING_TIMER_COOLDOWN


    while True:
        vol_listener_level = utils.volume_listener.get_vol_level()

        # If we are speaking, add to counter, if not remove from it
        if (vol_listener_level > SPEAKING_VOLUME_SENSITIVITY) and (SPEAKING_TIMER_COOLDOWN == 0):
            SPEAKING_TIMER += 50
            if SPEAKING_TIMER > 99:
                SPEAKING_TIMER = 99

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
        SPEAKING_VOLUME_SENSITIVITY = 20
    elif SPEAKING_VOLUME_SENSITIVITY <= 20:
        SPEAKING_VOLUME_SENSITIVITY = 37
    elif SPEAKING_VOLUME_SENSITIVITY <= 37:
        SPEAKING_VOLUME_SENSITIVITY = 67
    elif SPEAKING_VOLUME_SENSITIVITY <= 67:
        SPEAKING_VOLUME_SENSITIVITY = 104
    elif SPEAKING_VOLUME_SENSITIVITY >= 104:
        SPEAKING_VOLUME_SENSITIVITY = 9
    print("\nSensitivity Set To " + str(SPEAKING_VOLUME_SENSITIVITY) + " !")


def input_change_listener_sensitivity_from_ui(value):
    global SPEAKING_VOLUME_SENSITIVITY

    SPEAKING_VOLUME_SENSITIVITY = value

    print("\nSensitivity Set To " + str(SPEAKING_VOLUME_SENSITIVITY) + " !")



def input_soft_reset():
    global SOFT_RESET_PRESSED

    if utils.settings.hotkeys_locked:
        return

    SOFT_RESET_PRESSED = True


def chat_input_await():
    input_found = False

    while not input_found:
        global RATE_PRESSED, NEXT_PRESSED, REDO_PRESSED, SOFT_RESET_PRESSED, VIEW_IMAGE_PRESSED, BLANK_MESSAGE_PRESSED


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
            time.sleep(0.02)

