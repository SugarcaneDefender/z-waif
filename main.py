import time

import colorama
import humanize, os, threading
import emoji

import utils.audio
import utils.hotkeys
import utils.transcriber_translate
import win32com.client
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


from dotenv import load_dotenv
load_dotenv()

TT_CHOICE = os.environ.get("WHISPER_CHOICE")
char_name = os.environ.get("CHAR_NAME")

stored_transcript = "Issue with message cycling!"

undo_allowed = False


# noinspection PyBroadException
def main():

    while True:
        print("You" + colorama.Fore.GREEN + colorama.Style.BRIGHT + " (mic) " + colorama.Fore.RESET + ">", end="", flush=True)

        command = utils.hotkeys.chat_input_await()


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


    #
    #   Speak the message now!
    #

    s_message = emoji.replace_emoji(message, replace='')


    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    speaker.Speak(s_message)


    # Reset the volume cooldown so she don't pickup on herself
    utils.hotkeys.cooldown_listener_timer()


def message_checks(message):

    #
    # Runs message checks for plugins, such as VTube Studio and Minecraft
    #

    #   Log our message

    print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
          + "----" + char_name + "----"
          + colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)
    print(f"{message}")
    print("\n")

    #
    #   Vtube Studio Emoting
    #

    if utils.settings.vtube_enabled:
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

    # Limit the amount of tokens allowed to send (minecraft chat limits)
    API.Oogabooga_Api_Support.force_tokens_count(47)

    # Actual sending of the message, waits for reply automatically
    API.Oogabooga_Api_Support.send_via_oogabooga(message)

    # Reply in the craft
    utils.minecraft.minecraft_chat()

    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function, if we are set to speak them
    if utils.settings.speak_shadowchats:
        main_message_speak()


def main_discord_chat(message):

    # Actual sending of the message, waits for reply automatically
    API.Oogabooga_Api_Support.send_via_oogabooga(message)

    #
    # CHATS WILL BE GRABBED AFTER THIS RUNS!
    #

    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function, if we are set to speak them (NOTE: THIS WILL SLOW THE REPLY PROCESS, AS SHE WILL HAVE TO SPEAK THE WHOLE REPLY FIRST)
    if utils.settings.speak_shadowchats:
        main_message_speak()




def main_web_ui_chat(message):

    # Actual sending of the message, waits for reply automatically
    API.Oogabooga_Api_Support.send_via_oogabooga(message)

    #
    # CHATS WILL BE GRABBED AFTER THIS RUNS!
    #

    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function, if we are set to speak them (NOTE: THIS WILL SLOW THE REPLY PROCESS, AS SHE WILL HAVE TO SPEAK THE WHOLE REPLY FIRST)
    if utils.settings.speak_shadowchats:
        main_message_speak()

def main_web_ui_next():

    API.Oogabooga_Api_Support.next_message_oogabooga()

    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function, if we are set to speak them (NOTE: THIS WILL SLOW THE REPLY PROCESS, AS SHE WILL HAVE TO SPEAK THE WHOLE REPLY FIRST)
    if utils.settings.speak_shadowchats:
        main_message_speak()



def main_discord_next():

    API.Oogabooga_Api_Support.next_message_oogabooga()

    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function, if we are set to speak them (NOTE: THIS WILL SLOW THE REPLY PROCESS, AS SHE WILL HAVE TO SPEAK THE WHOLE REPLY FIRST)
    if utils.settings.speak_shadowchats:
        main_message_speak()


def main_undo():

    global undo_allowed
    if undo_allowed:

        undo_allowed = False

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

    # Retrospect and get a random memory
    utils.retrospect.retrospect_random_mem_summary()

    #
    # CHATS WILL BE GRABBED AFTER THIS RUNS!
    #

    # Run our message checks
    reply_message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function, if we are set to speak them (NOTE: THIS WILL SLOW THE REPLY PROCESS, AS SHE WILL HAVE TO SPEAK THE WHOLE REPLY FIRST)
    if utils.settings.speak_shadowchats:
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
    # Get the image first before any processing. Decide if we take a new image or feed
    if not utils.settings.cam_use_image_feed:

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




    else:
        utils.camera.use_image_feed()

    print("Image processing...\n")

    # Check if we want to run the MIC or not for direct talk
    direct_talk_transcript = ""

    if utils.settings.cam_direct_talk:
        direct_talk_transcript = view_image_prompt_get()

    # View and process the image, storing the result
    transcript = API.Oogabooga_Api_Support.view_image(direct_talk_transcript)

    # Fix up our transcript & show us
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

    utils.settings.eyes_follow = os.environ.get("EYES_FOLLOW")


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

