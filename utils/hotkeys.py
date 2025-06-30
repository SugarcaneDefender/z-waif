# Standard library imports
import json
import os
import threading
import time

# Third-party imports
import keyboard
# import mouse

# Local imports - Utils modules
from utils import alarm
from utils import audio
from utils import settings
from utils import volume_listener
from utils import zw_logging


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
        settings.hotkeys_locked = False

    if HOTKEYS_BOOT == "OFF":
        settings.hotkeys_locked = True
        print("\nInput System Lock Set To " + str(settings.hotkeys_locked) + " !")

    # Also bind all of our needed hotkeys at this point
    bind_all_hotkeys()

def unbind_all_hotkeys():
    """Clear all existing hotkey bindings"""
    try:
        # Try the newer method first
        keyboard.unhook_all_hotkeys()
        keyboard.unhook_all()
        print("🧹 Cleared all existing hotkeys")
    except AttributeError:
        # Fallback for older keyboard library versions
        try:
            keyboard.clear_all_hotkeys()
            print("🧹 Cleared all existing hotkeys (fallback method)")
        except AttributeError:
            # Final fallback - just continue without clearing
            print("⚠️ Could not clear existing hotkeys - continuing anyway")
    except Exception as e:
        # Handle any other errors gracefully
        print(f"⚠️ Warning clearing hotkeys: {e} - continuing anyway")

def bind_all_hotkeys():

    # Clear any existing bindings first
    unbind_all_hotkeys()

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
    """Bind hotkey with proper action handling"""
    
    def safe_hotkey_action():
        # Skip hotkey if hotkeys are locked
        if settings.hotkeys_locked:
            return
            
        # Execute the hotkey action
        input_action()

    try:
        # Check if it's a modifier combination (contains + sign)
        if '+' in binding:
            # Use add_hotkey for modifier combinations (convert to lowercase format)
            hotkey_combo = binding.lower()
            keyboard.add_hotkey(hotkey_combo, safe_hotkey_action)
            print(f"✅ Bound combination hotkey: {binding} ({hotkey_combo})")
        else:
            # Use on_press_key for single keys
            keyboard.on_press_key(binding, lambda _: safe_hotkey_action())
            print(f"✅ Bound single hotkey: {binding}")
    except Exception as e:
        print(f"❌ Issue binding hotkey {binding}: {e}")
        zw_logging.update_debug_log(f"Issue binding to hotkey {binding}: {e}")


def rate_input(rating):

    if settings.hotkeys_locked:
        return

    global RATE_PRESSED
    global RATE_LEVEL

    RATE_PRESSED = True
    RATE_LEVEL = rating

def next_input():
    if settings.hotkeys_locked:
        return

    global NEXT_PRESSED

    NEXT_PRESSED = True

def redo_input():

    if settings.hotkeys_locked:
        return

    global REDO_PRESSED

    #   Ensure we sent a message to redo, so we don't clear past 1 ever

    REDO_PRESSED = True

def get_speak_input():
    if SPEAKING_TIMER_COOLDOWN > 0:
        return False

    return SPEAK_TOGGLED

def speak_input_toggle():
    if settings.hotkeys_locked:
        return

    global SPEAK_TOGGLED

    SPEAK_TOGGLED = not SPEAK_TOGGLED
    
    # Log the toggle
    if SPEAK_TOGGLED:
        print("Microphone Recording toggled ON")
    else:
        print("Microphone Recording toggled OFF")

def speak_input_toggle_from_ui():
    global SPEAK_TOGGLED

    SPEAK_TOGGLED = not SPEAK_TOGGLED
    
    # Log the toggle for UI tracking
    if SPEAK_TOGGLED:
        print("Microphone Recording toggled ON (Web UI)")
    else:
        print("Microphone Recording toggled OFF (Web UI)")

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
        settings.hotkeys_locked = not settings.hotkeys_locked
        print("\nInput System Lock Set To " + str(settings.hotkeys_locked) + " !")


def input_lock_backslash():
    global BACKSLASH_PRESSED

    BACKSLASH_PRESSED = True


def input_view_image():
    global VIEW_IMAGE_PRESSED

    # additional lockout for if the vision system is offline
    if settings.hotkeys_locked or settings.vision_enabled == False:
        return

    VIEW_IMAGE_PRESSED = True

def input_cancel_image():
    global CANCEL_IMAGE_PRESSED

    # additional lockout for if the vision system is offline
    if settings.hotkeys_locked or settings.vision_enabled == False:
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

    if settings.hotkeys_locked:
        return

    BLANK_MESSAGE_PRESSED = True


def get_autochat_toggle():
    return FULL_AUTO_TOGGLED

def input_toggle_autochat():
    global FULL_AUTO_TOGGLED

    FULL_AUTO_TOGGLED = not FULL_AUTO_TOGGLED

    # If we are toggling on, print to the user that we are doing so
    if FULL_AUTO_TOGGLED:
        print("Auto-Chat toggled ON")

    if not FULL_AUTO_TOGGLED:
        print("Auto-Chat toggled OFF")


def input_toggle_autochat_from_ui():
    global FULL_AUTO_TOGGLED

    FULL_AUTO_TOGGLED = not FULL_AUTO_TOGGLED

    # Log the toggle for UI tracking
    if FULL_AUTO_TOGGLED:
        print("Auto-Chat toggled ON (Web UI)")
    else:
        print("Auto-Chat toggled OFF (Web UI)")


def disable_autochat():
    global FULL_AUTO_TOGGLED

    FULL_AUTO_TOGGLED = False

def get_autochat_sensitivity():
    global SPEAKING_VOLUME_SENSITIVITY
    return SPEAKING_VOLUME_SENSITIVITY


def input_change_listener_sensitivity():
    global SPEAKING_VOLUME_SENSITIVITY_PRESSED

    if settings.hotkeys_locked:
        return

    SPEAKING_VOLUME_SENSITIVITY_PRESSED = True


def input_change_listener_sensitivity_from_ui(sensitivity_level):
    global SPEAKING_VOLUME_SENSITIVITY

    SPEAKING_VOLUME_SENSITIVITY = sensitivity_level


def chat_input_await():
    #
    # Used to await for any input from the user (hotkeys, alarms, ect.)
    #

    # Loop to check for our inputs
    while True:

        # Check for our alarm
        if alarm.alarm_check():
            return "ALARM"

        # Check for our autochat
        elif FULL_AUTO_TOGGLED and SPEAK_TOGGLED and volume_listener.VAD_RESULT:
            return "CHAT"

        # Check for our normal hotkeys
        elif NEXT_PRESSED:
            return "NEXT"

        elif REDO_PRESSED:
            return "REDO"

        elif SPEAK_TOGGLED:
            return "CHAT"

        elif SOFT_RESET_PRESSED:
            return "SOFT_RESET"

        elif VIEW_IMAGE_PRESSED:
            return "VIEW"

        elif BLANK_MESSAGE_PRESSED:
            return "BLANK"

        elif settings.hangout_mode:
            return "Hangout"

        time.sleep(0.01)

def get_command_nonblocking():
    """Check for hotkey presses without blocking."""
    global NEXT_PRESSED, REDO_PRESSED, SOFT_RESET_PRESSED, VIEW_IMAGE_PRESSED, BLANK_MESSAGE_PRESSED

    # Check for our alarm first, as it's highest priority
    if alarm.alarm_check():
        return "ALARM"

    # Check for autochat
    if FULL_AUTO_TOGGLED and SPEAK_TOGGLED and volume_listener.VAD_RESULT:
        return "CHAT"

    # Check for standard hotkeys
    if NEXT_PRESSED:
        NEXT_PRESSED = False
        return "NEXT"
    if REDO_PRESSED:
        REDO_PRESSED = False
        return "REDO"
    if SPEAK_TOGGLED:
        # This is a special case. We don't want to consume the toggle,
        # just report that it's active. The main loop will handle the rest.
        return "CHAT"
    if SOFT_RESET_PRESSED:
        SOFT_RESET_PRESSED = False
        return "SOFT_RESET"
    if VIEW_IMAGE_PRESSED:
        VIEW_IMAGE_PRESSED = False
        return "VIEW"
    if BLANK_MESSAGE_PRESSED:
        BLANK_MESSAGE_PRESSED = False
        return "BLANK"
    if settings.hangout_mode:
        # Similar to SPEAK_TOGGLED, we just report the mode is active.
        return "Hangout"
        
    return None

def stack_wipe_inputs():

    global NEXT_PRESSED
    global REDO_PRESSED
    global SPEAK_TOGGLED
    global SOFT_RESET_PRESSED
    global VIEW_IMAGE_PRESSED
    global BLANK_MESSAGE_PRESSED

    NEXT_PRESSED = False
    REDO_PRESSED = False
    SPEAK_TOGGLED = False
    SOFT_RESET_PRESSED = False
    VIEW_IMAGE_PRESSED = False
    BLANK_MESSAGE_PRESSED = False


def input_soft_reset():
    if settings.hotkeys_locked:
        return

    global SOFT_RESET_PRESSED

    SOFT_RESET_PRESSED = True


def pull_next_press_input():
    if NEXT_PRESSED:
        return True
    else:
        return False


def listener_timer():

    global SPEAKING_TIMER
    global SPEAKING_TIMER_COOLDOWN
    global FULL_AUTO_TOGGLED
    global SPEAKING_VOLUME_SENSITIVITY_PRESSED
    global SPEAKING_VOLUME_SENSITIVITY

    while True:

        # Check for sensitivity button, start a listener if so
        if SPEAKING_VOLUME_SENSITIVITY_PRESSED:
            SPEAKING_VOLUME_SENSITIVITY_PRESSED = False
            get_sensitivity_thread = threading.Thread(target=get_sensitivity_input)
            get_sensitivity_thread.daemon = True
            get_sensitivity_thread.start()


        # Timer for speaking with mic
        if SPEAK_TOGGLED and volume_listener.speaking and not FULL_AUTO_TOGGLED:
            SPEAKING_TIMER = SPEAKING_TIMER + 1

        else:
            SPEAKING_TIMER = 0

        # Cooldown timer
        if SPEAKING_TIMER_COOLDOWN > 0:
            SPEAKING_TIMER_COOLDOWN = SPEAKING_TIMER_COOLDOWN - 1


        # If we speak long enough, then we can do our thing
        if SPEAKING_TIMER > 20 and SPEAKING_TIMER_COOLDOWN == 0:
            SPEAKING_TIMER = 0
            SPEAKING_TIMER_COOLDOWN = 140
            general_listener_speaking_detected = True


        time.sleep(0.02)


def cooldown_listener_timer():
    """Reset the volume cooldown so the AI doesn't pick up on its own voice"""
    global SPEAKING_TIMER_COOLDOWN
    SPEAKING_TIMER_COOLDOWN = 140  # Set cooldown to prevent self-pickup


def get_sensitivity_input():
    global SPEAKING_VOLUME_SENSITIVITY
    from utils import console_input

    print("\n\nPlease enter a new sensitivity value! (1-200)")
    print("You can type other commands while waiting...")
    
    # Use non-blocking input instead of blocking input()
    start_time = time.time()
    while True:
        # Check for console input non-blockingly
        new_sens_str = console_input.get_line_nonblocking()
        if new_sens_str is not None:
            try:
                new_sens = int(new_sens_str.strip())
                if new_sens < 1:
                    new_sens = 1
                if new_sens > 200:
                    new_sens = 200

                SPEAKING_VOLUME_SENSITIVITY = new_sens
                print(f"Sensitivity set to {new_sens}!")
                return
            except ValueError:
                print(f"'{new_sens_str}' is not a valid number! Please enter a whole number (1-200)")
                continue
        
        # Timeout after 30 seconds to prevent infinite waiting
        if time.time() - start_time > 30:
            print("Sensitivity input timeout. Keeping current value.")
            return
            
        time.sleep(0.1)  # Small delay to prevent busy waiting

def input_toggle_semi_autochat():
    # No toggle in hangout mode
    if settings.hangout_mode:
        return

    # Toggle
    settings.semi_auto_chat = not settings.semi_auto_chat

    # Log the toggle
    if settings.semi_auto_chat:
        print("Semi-Auto Chat toggled ON")
    else:
        print("Semi-Auto Chat toggled OFF")

    # Disable
    disable_autochat()

def input_toggle_hangout_mode():
    settings.hangout_mode = not settings.hangout_mode
    zw_logging.update_debug_log(f"Hangout mode toggled to {settings.hangout_mode}")

    # If we are toggling on, print to the user that we are doing so
    if settings.hangout_mode:
        print("Hangout mode toggled ON")
    else:
        print("Hangout mode toggled OFF")

def web_ui_toggle_hangout_mode():
    input_toggle_hangout_mode()

