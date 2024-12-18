import time

import colorama
import humanize, os, threading
import emoji

import utils.audio
import utils.hotkeys
import utils.transcriber_translate
import utils.voice
import utils.vtube_studio
import utils.alarm
import utils.volume_listener
import utils.minecraft
import utils.log_conversion
import utils.cane_lib

import API.Oogabooga_Api_Support

import utils.lorebook
import utils.camera

import utils.z_waif_discord
import utils.web_ui

import utils.settings
import utils.retrospect
import utils.based_rag
import utils.tag_task_controller
import utils.gaming_control

from dotenv import load_dotenv
load_dotenv()

TT_CHOICE = os.environ.get("WHISPER_CHOICE")
char_name = os.environ.get("CHAR_NAME")

stored_transcript = "Issue with message cycling!"

undo_allowed = False
is_live_pipe = False

# Not for sure live pipe... atleast how it is counted now. Unipipes in a few updates will clear this up
# Livepipe is only for the hotkeys actions, that is why... but these are for non-hotkey stuff!
live_pipe_no_speak = False


# noinspection PyBroadException
def main():

    while True:
        print("You" + colorama.Fore.GREEN + colorama.Style.BRIGHT + " (mic) " + colorama.Fore.RESET + ">", end="", flush=True)

        # Stative control depending on what mode we are (gaming, streaming, normal, ect.)
        if utils.settings.is_gaming_loop:
            command = utils.gaming_control.gaming_step()
        else:
            command = utils.hotkeys.chat_input_await()

        # Flag us as running a command now
        global is_live_pipe
        is_live_pipe = True

        if command == "CHAT":
            main_converse()

        elif command == "RATE":
            main_rate()

        elif command == "NEXT":
            main_next()

        elif command == "REDO":
            main_undo()

        elif command == "SOFT_RESET":
            main_soft_reset()

        elif command == "ALARM":
            main_alarm_message()

        elif command == "VIEW":
            main_view_image()

        elif command == "BLANK":
            main_send_blank()

        # Stack wipe any current inputs, to avoid doing multiple in a row
        utils.hotkeys.stack_wipe_inputs()

        # Flag us as no longer running a command
        is_live_pipe = False



def main_converse():
    print(
        "\rYou" + colorama.Fore.GREEN + colorama.Style.BRIGHT + " (mic " + colorama.Fore.YELLOW + "[Recording]" + colorama.Fore.GREEN + ") " + colorama.Fore.RESET + ">",
        end="", flush=True)

    # Actual recording and waiting bit
    audio_buffer = utils.audio.record()


    try:
        tanscribing_log = "\rYou" + colorama.Fore.GREEN + colorama.Style.BRIGHT + " (mic " + colorama.Fore.BLUE + "[Transcribing (" + str(
            humanize.naturalsize(
                os.path.getsize(audio_buffer))) + ")]" + colorama.Fore.GREEN + ") " + colorama.Fore.RESET + "> "
        print(tanscribing_log, end="", flush=True)

        # My own edit- To remove possible transcribing errors
        transcript = "Whoops! The code is having some issues, chill for a second."

        transcript = utils.transcriber_translate.to_transcribe_original_language(audio_buffer)



    except Exception as e:
        print(colorama.Fore.RED + colorama.Style.BRIGHT + "Error: " + str(e))
        return

    # Fix the transcript, to stop any accidental repeats (whisper glitch)
    transcript = utils.cane_lib.remove_repeats(transcript)

    # Print the transcript
    print('\r' + ' ' * len(tanscribing_log), end="")
    print('\r' + colorama.Fore.RED + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
          + "----Me----"
          + colorama.Fore.RED + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)
    print(f"{transcript.strip()}")
    print("\n")

    # Store the message, for cycling purposes
    global stored_transcript
    stored_transcript = transcript


    # Actual sending of the message, waits for reply automatically

    API.Oogabooga_Api_Support.send_via_oogabooga(transcript)


    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function
    main_message_speak()

    # After use, delete the recording.
    try:
        os.remove(audio_buffer)
    except:
        pass


def main_message_speak():
    #
    #   Message is received Here
    #

    message = API.Oogabooga_Api_Support.receive_via_oogabooga()


    # Stop this if the message was streamed- we have already read it!
    if API.Oogabooga_Api_Support.last_message_streamed:
        return

    #
    #   Speak the message now!
    #

    s_message = emoji.replace_emoji(message, replace='')

    utils.voice.set_speaking(True)

    voice_speaker = threading.Thread(target=utils.voice.speak_line(s_message, refuse_pause=False))
    voice_speaker.daemon = True
    voice_speaker.start()

    # Minirest for frame-piercing (race condition as most people call it) for the speaking
    time.sleep(0.01)

    while utils.voice.check_if_speaking():
        time.sleep(0.01)



def message_checks(message):

    #
    # Runs message checks for plugins, such as VTube Studio and Minecraft
    #

    #   Log our message (ONLY if the last chat was NOT streaming)

    if not API.Oogabooga_Api_Support.last_message_streamed:
        print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
              + "----" + char_name + "----"
              + colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)
        print(f"{message}")
        print("\n")

    #
    #   Vtube Studio Emoting
    #

    if utils.settings.vtube_enabled and not API.Oogabooga_Api_Support.last_message_streamed:
        # Feeds the message to our VTube Studio script
        utils.vtube_studio.set_emote_string(message)

        # Check for any emotes on it's end
        vtube_studio_thread = threading.Thread(target=utils.vtube_studio.check_emote_string)
        vtube_studio_thread.daemon = True
        vtube_studio_thread.start()

    #
    # Minecraft API
    #

    if utils.settings.minecraft_enabled:
        utils.minecraft.check_for_command(message)


    #
    # Gaming
    #

    if utils.settings.gaming_enabled:
        utils.gaming_control.message_inputs(message)


    # We can now undo the previous message

    global undo_allowed
    undo_allowed = True


def main_rate():
    # function to rate character messages from main
    # NOTE: NO LONGER VALID

    return



def main_next():

    API.Oogabooga_Api_Support.next_message_oogabooga()

    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function
    main_message_speak()

def main_minecraft_chat(message):

    # This is a shadow chat
    global live_pipe_no_speak
    if (not utils.settings.speak_shadowchats) and utils.settings.stream_chats:
        live_pipe_no_speak = True

    # Limit the amount of tokens allowed to send (minecraft chat limits)
    API.Oogabooga_Api_Support.force_tokens_count(47)

    # Actual sending of the message, waits for reply automatically
    API.Oogabooga_Api_Support.send_via_oogabooga(message)

    # Reply in the craft
    utils.minecraft.minecraft_chat()

    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function, if we are set to speak them (will be spoken otherwise)
    live_pipe_no_speak = False
    if utils.settings.speak_shadowchats and not utils.settings.stream_chats:
        main_message_speak()


def main_discord_chat(message):

    # This is a shadow chat
    global live_pipe_no_speak
    if (not utils.settings.speak_shadowchats) and utils.settings.stream_chats:
        live_pipe_no_speak = True

    # Actual sending of the message, waits for reply automatically
    API.Oogabooga_Api_Support.send_via_oogabooga(message)

    #
    # CHATS WILL BE GRABBED AFTER THIS RUNS!
    #

    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function, if we are set to speak them (will be spoken otherwise)
    live_pipe_no_speak = False
    if utils.settings.speak_shadowchats and not utils.settings.stream_chats:
        main_message_speak()





def main_web_ui_chat(message):

    # This is a shadow chat
    global live_pipe_no_speak
    if (not utils.settings.speak_shadowchats) and utils.settings.stream_chats:
        live_pipe_no_speak = True

    # Actual sending of the message, waits for reply automatically
    API.Oogabooga_Api_Support.send_via_oogabooga(message)

    #
    # CHATS WILL BE GRABBED AFTER THIS RUNS!
    #

    # Cut voice if needed
    utils.voice.force_cut_voice()

    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function, if we are set to speak them (will be spoken otherwise)
    live_pipe_no_speak = False
    if utils.settings.speak_shadowchats and not utils.settings.stream_chats:
        main_message_speak()

def main_web_ui_next():

    # This is a shadow chat
    global live_pipe_no_speak
    global live_pipe_is_webui_regen
    if (not utils.settings.speak_shadowchats) and utils.settings.stream_chats:
        live_pipe_no_speak = True


    # Cut voice if needed
    utils.voice.force_cut_voice()

    # Force end the existing stream (if there is one)
    if API.Oogabooga_Api_Support.is_in_api_request:
        API.Oogabooga_Api_Support.set_force_skip_streaming(True)
        live_pipe_no_speak = False
        return

    API.Oogabooga_Api_Support.next_message_oogabooga()

    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function, if we are set to speak them (will be spoken otherwise)
    live_pipe_no_speak = False
    if utils.settings.speak_shadowchats and not utils.settings.stream_chats:
        main_message_speak()



def main_discord_next():

    # This is a shadow chat
    global live_pipe_no_speak
    if (not utils.settings.speak_shadowchats) and utils.settings.stream_chats:
        live_pipe_no_speak = True

    API.Oogabooga_Api_Support.next_message_oogabooga()

    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function, if we are set to speak them (will be spoken otherwise)
    live_pipe_no_speak = False
    if utils.settings.speak_shadowchats and not utils.settings.stream_chats:
        main_message_speak()


def main_undo():

    global undo_allowed
    if undo_allowed:

        undo_allowed = False

        # Cut voice if needed
        utils.voice.force_cut_voice()

        API.Oogabooga_Api_Support.undo_message()

        print("\nUndoing the previous message!\n")

        time.sleep(0.1)

def main_soft_reset():

    API.Oogabooga_Api_Support.soft_reset()

    # We can noT undo
    global undo_allowed
    undo_allowed = False

    time.sleep(0.1)


def main_alarm_message():

    # Check for the daily memory
    if utils.alarm.random_memories and len(utils.based_rag.history_database) > 100:
        main_memory_proc()

    # Send it!
    API.Oogabooga_Api_Support.send_via_oogabooga(utils.alarm.get_alarm_message())

    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    main_message_speak()

    # Clear the alarm
    utils.alarm.clear_alarm()


def main_memory_proc():
    if len(utils.based_rag.history_database) < 100:
        print("Not enough conversation history for memories!")
        return

    # This is a shadow chat
    global live_pipe_no_speak
    if (not utils.settings.speak_shadowchats) and utils.settings.stream_chats:
        live_pipe_no_speak = True

    # Retrospect and get a random memory
    utils.retrospect.retrospect_random_mem_summary()

    #
    # CHATS WILL BE GRABBED AFTER THIS RUNS!
    #

    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function, if we are set to speak them (will be spoken otherwise)
    live_pipe_no_speak = False
    if utils.settings.speak_shadowchats and not utils.settings.stream_chats:
        main_message_speak()



def main_view_image():

    # Disabled for now! Loading in the multi-modal pipeline puts us overburdened!
    # NOTE: No longer disabled, but please add a toggle for this on/off depending on cam!
    # return

    # Give us some feedback
    print("\n\nViewing the camera! Please wait...\n")

    # Clear the camera inputs
    utils.hotkeys.clear_camera_inputs()

    #
    # Get the image first before any processing.

    #
    # Use the image feed
    if utils.settings.cam_use_image_feed:
        utils.camera.use_image_feed()

    #
    # Screenshot capture
    elif utils.settings.cam_use_screenshot:
        utils.camera.capture_screenshot()

    #
    # Normal camera capture
    else:

        # If we do not want to preview, simply take the image. Else, do the confirmation loop

        if not utils.settings.cam_image_preview:
            utils.camera.capture_pic()

        else:
            break_cam_loop = False

            # Loop to check for if the image is what we want or not
            # NOTE: If image preview is on, then the loop will not even go! Neat!

            while not break_cam_loop:
                utils.hotkeys.clear_camera_inputs()
                utils.camera.capture_pic()

                while not (utils.hotkeys.VIEW_IMAGE_PRESSED or utils.hotkeys.CANCEL_IMAGE_PRESSED):
                    time.sleep(0.05)

                if utils.hotkeys.VIEW_IMAGE_PRESSED:
                    break_cam_loop = True

                utils.hotkeys.clear_camera_inputs()


    print("Image processing...\n")

    # Check if we want to run the MIC or not for direct talk
    direct_talk_transcript = ""

    if utils.settings.cam_direct_talk:
        direct_talk_transcript = view_image_prompt_get()

    # View and process the image, storing the result
    transcript = API.Oogabooga_Api_Support.send_image_via_oobabooga(direct_talk_transcript)

    # Fix up our transcript & show us
    if not utils.settings.stream_chats:
        print("\n" + transcript + "\n")

    # We can now undo the previous message

    global undo_allowed
    undo_allowed = True

    # Check if we need to reply after the image
    if utils.settings.cam_reply_after:
        view_image_after_chat("So, what did you think of the image, " + char_name + "?")



def view_image_prompt_get():
    print(
        "\rYou" + colorama.Fore.GREEN + colorama.Style.BRIGHT + " (mic " + colorama.Fore.YELLOW + "[Recording]" + colorama.Fore.GREEN + ") " + colorama.Fore.RESET + ">",
        end="", flush=True)

    # Manually toggle on the recording of the mic (it is disabled by toggling off. also works with autochat too BTW)
    utils.hotkeys.speak_input_on_from_cam_direct_talk()

    # Actual recording and waiting bit
    audio_buffer = utils.audio.record()


    try:
        tanscribing_log = "\rYou" + colorama.Fore.GREEN + colorama.Style.BRIGHT + " (mic " + colorama.Fore.BLUE + "[Transcribing (" + str(
            humanize.naturalsize(
                os.path.getsize(audio_buffer))) + ")]" + colorama.Fore.GREEN + ") " + colorama.Fore.RESET + "> "
        print(tanscribing_log, end="", flush=True)

        # My own edit- To remove possible transcribing errors
        transcript = "Whoops! The code is having some issues, chill for a second."

        transcript = utils.transcriber_translate.to_transcribe_original_language(audio_buffer)



    except Exception as e:
        print(colorama.Fore.RED + colorama.Style.BRIGHT + "Error: " + str(e))
        return

    # Print the transcript
    print('\r' + ' ' * len(tanscribing_log), end="")
    print('\r' + colorama.Fore.RED + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
          + "----Me----"
          + colorama.Fore.RED + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)
    print(f"{transcript.strip()}")
    print("\n")

    # Return our transcipt of what we have just said
    return transcript

def view_image_after_chat(message):

    # Actual sending of the message, waits for reply automatically
    API.Oogabooga_Api_Support.send_via_oogabooga(message)


    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function
    main_message_speak()


def main_send_blank():

    # Give us some feedback
    print("\nSending blank message...\n")

    transcript = ""

    # Store the message, for cycling purposes
    global stored_transcript
    stored_transcript = transcript


    # Actual sending of the message, waits for reply automatically

    API.Oogabooga_Api_Support.send_via_oogabooga(transcript)

    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)


    # Pipe us to the reply function
    main_message_speak()

def run_program():

    # Announce that the program is running
    print("Welcome back! Loading chat interface...\n\n", end="", flush=True)

    # Load hotkey ON/OFF on boot
    utils.hotkeys.load_hotkey_bootstate()

    # Load the defaults for modules being on/off in the settings
    minecraft_enabled_string = os.environ.get("MODULE_MINECRAFT")
    if minecraft_enabled_string == "ON":
        utils.settings.minecraft_enabled = True
    else:
        utils.settings.minecraft_enabled = False

    alarm_enabled_string = os.environ.get("MODULE_ALARM")
    if alarm_enabled_string == "ON":
        utils.settings.alarm_enabled = True
    else:
        utils.settings.alarm_enabled = False

    vtube_enabled_string = os.environ.get("MODULE_VTUBE")
    if vtube_enabled_string == "ON":
        utils.settings.vtube_enabled = True
    else:
        utils.settings.vtube_enabled = False

    discord_enabled_string = os.environ.get("MODULE_DISCORD")
    if discord_enabled_string == "ON":
        utils.settings.discord_enabled = True
    else:
        utils.settings.discord_enabled = False

    rag_enabled_string = os.environ.get("MODULE_RAG")
    if rag_enabled_string == "ON":
        utils.settings.rag_enabled = True
    else:
        utils.settings.rag_enabled = False

    vision_enabled_string = os.environ.get("MODULE_VISUAL")
    if vision_enabled_string == "ON":
        utils.settings.vision_enabled = True
    else:
        utils.settings.vision_enabled = False

    gaming_enabled_string = os.environ.get("MODULE_GAMING")
    if gaming_enabled_string == "ON":
        utils.settings.gaming_enabled = True
    else:
        utils.settings.gaming_enabled = False


    # Other settings

    utils.settings.eyes_follow = os.environ.get("EYES_FOLLOW")

    newline_cut_enabled_string = os.environ.get("NEWLINE_CUT_BOOT")
    if newline_cut_enabled_string == "ON":
        utils.settings.newline_cut = True
    else:
        utils.settings.newline_cut = False

    rp_sup_enabled_string = os.environ.get("RP_SUP_BOOT")
    if rp_sup_enabled_string == "ON":
        utils.settings.supress_rp = True
    else:
        utils.settings.supress_rp = False

    stream_chats_enabled_string = os.environ.get("API_STREAM_CHATS")
    if stream_chats_enabled_string == "ON":
        utils.settings.stream_chats = True
    else:
        utils.settings.stream_chats = False


    # Load in our char name
    utils.settings.char_name = char_name

    # Load tags and tasks
    utils.tag_task_controller.load_tags_tasks()

    # Run any needed log conversions
    utils.log_conversion.run_conversion()

    # Load the previous chat history
    API.Oogabooga_Api_Support.check_load_past_chat()


    # Start the VTube Studio interaction in a separate thread, we ALWAYS do this FYI
    if utils.settings.vtube_enabled:
        vtube_studio_thread = threading.Thread(target=utils.vtube_studio.run_vtube_studio_connection)
        vtube_studio_thread.daemon = True
        vtube_studio_thread.start()


    # Start another thread for the alarm interaction
    if utils.settings.alarm_enabled:
        alarm_thread = threading.Thread(target=utils.alarm.alarm_loop)
        alarm_thread.daemon = True
        alarm_thread.start()


    # Start another thread for the volume levels, and another for the full auto toggle
    volume_listener = threading.Thread(target=utils.volume_listener.run_volume_listener)
    volume_listener.daemon = True
    volume_listener.start()

    volume_listener_toggle = threading.Thread(target=utils.hotkeys.listener_timer)
    volume_listener_toggle.daemon = True
    volume_listener_toggle.start()


    # Start another thread for the Minecraft watchdog
    if utils.settings.minecraft_enabled:
        minecraft_thread = threading.Thread(target=utils.minecraft.chat_check_loop)
        minecraft_thread.daemon = True
        minecraft_thread.start()

    # Start another thread for Discord
    if utils.settings.discord_enabled:
        discord_thread = threading.Thread(target=utils.z_waif_discord.run_z_waif_discord)
        discord_thread.daemon = True
        discord_thread.start()

    # Start another thread for camera facial track, if we want that
    if utils.settings.eyes_follow == "Faces":
        face_follow_thread = threading.Thread(target=utils.camera.loop_follow_look)
        face_follow_thread.daemon = True
        face_follow_thread.start()
    elif utils.settings.eyes_follow == "Random":
        face_follow_thread = threading.Thread(target=utils.camera.loop_random_look)
        face_follow_thread.daemon = True
        face_follow_thread.start()

    # Start another thread for Gradio
    gradio_thread = threading.Thread(target=utils.web_ui.launch_demo)
    gradio_thread.daemon = True
    gradio_thread.start()




    # Run the primary loop
    main()


if __name__ == "__main__":

    current_directory = os.path.dirname(os.path.abspath(__file__))

    # Create the resource directory path based on the current directory
    resource_directory = os.path.join(current_directory, "utils","resource")
    os.makedirs(resource_directory, exist_ok=True)

    # Create the voice_in and voice_out directory paths
    voice_in_directory = os.path.join(resource_directory, "voice_in")
    voice_out_directory = os.path.join(resource_directory, "voice_out")

    # Create the voice_in and voice_out directories if they don't exist
    os.makedirs(voice_in_directory, exist_ok=True)
    os.makedirs(voice_out_directory, exist_ok=True)


    run_program()

