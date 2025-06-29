# Standard library imports
import asyncio
import datetime
import os
import json
import sys
import threading
import time

# Third-party imports
import colorama
import emoji
import humanize
from dotenv import load_dotenv

# Local imports - API modules
import API.api_controller
import API.character_card
import API.task_profiles

# Local imports - Utils modules
from utils import alarm
from utils import audio
from utils import based_rag
from utils import camera
from utils import cane_lib
from utils import console_input
from utils import gaming_control
from utils import hangout
from utils import hotkeys
from utils import log_conversion
from utils import lorebook
from utils import minecraft
from utils import retrospect
from utils import settings
from utils import tag_task_controller
from utils import transcriber_translate
from utils import uni_pipes
from utils import voice
from utils import volume_listener
from utils import vtube_studio
from utils import web_ui
from utils import z_waif_discord
from utils import z_waif_twitch
from utils import zw_logging
from utils.chat_history import add_message_to_history

load_dotenv()

TT_CHOICE = os.environ.get("WHISPER_CHOICE")
char_name = os.environ.get("CHAR_NAME")

stored_transcript = "Issue with message cycling!"

undo_allowed = False
is_live_pipe = False

# Not for sure live pipe... atleast how it is counted now. Unipipes in a few updates will clear this up
# Livepipe is only for the hotkeys actions, that is why... but these are for non-hotkey stuff!
settings.live_pipe_no_speak = False
live_pipe_force_speak_on_response = False
live_pipe_use_streamed_interrupt_watchdog = False

text_chat_input = None

# Command line message input support
startup_message = None

def handle_command_line_args():
    """Handle command line arguments for message input like the release version"""
    global startup_message
    
    # Get command line arguments (skip script name at index 0)
    args = sys.argv[1:]
    
    if len(args) > 0:
        # Join all arguments into a single message
        startup_message = ' '.join(args)
        print(f"\n{colorama.Fore.CYAN}Command line message received: {startup_message}{colorama.Fore.RESET}\n")
        return True
    
    return False

def process_startup_message():
    """Process the startup message if provided"""
    global startup_message
    
    if startup_message:
        print(f"\n{colorama.Fore.GREEN}Processing startup message...{colorama.Fore.RESET}")
        
        # Wait a moment for all systems to be ready
        time.sleep(2)
        
        # Process the message directly without using the global variable
        message = startup_message
        startup_message = None  # Clear it immediately
        
        # Process the message directly like main_text_chat does
        print('\r' + colorama.Fore.RED + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
              + "----Me----"
              + colorama.Fore.RED + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)
        print(f"{message.strip()}")
        print("\n")

        # Store the message, for cycling purposes
        global stored_transcript
        stored_transcript = message

        # Use the improved API run function with anti-streaming personality
        reply_message = API.api_controller.run(message, temp_level=0.7)
        
        if reply_message and reply_message.strip():
            # Apply response cleaning to prevent streaming personality
            clean_reply = clean_twitch_response(reply_message)
            message_checks(clean_reply)

        # Speak the reply
        main_message_speak()
        
        print(f"\n{colorama.Fore.GREEN}Startup message processed. Continuing with normal operation...{colorama.Fore.RESET}\n")

# noinspection PyBroadException
def main():

    while True:
        # -- Non-blocking input handling --

        # 1. Check for console input
        command = None
        
        # Stative control depending on what mode we are (gaming, streaming, normal, ect.)
        if settings.is_gaming_loop:
            command = gaming_control.gaming_step()
        
        else:
            typed_line = console_input.get_line_nonblocking()
            if typed_line is not None:
                typed_line = typed_line.strip()
                lowercase_line = typed_line.lower()

                if lowercase_line in {"/next", "next"}:
                    command = "NEXT"
                elif lowercase_line in {"/redo", "redo"}:
                    command = "REDO"
                elif lowercase_line in {"/soft_reset", "soft reset", "reset"}:
                    command = "SOFT_RESET"
                elif lowercase_line in {"/view", "view"}:
                    command = "VIEW"
                elif lowercase_line in {"/blank", "blank"}:
                    command = "BLANK"
                else:
                    # Treat as a standard chat message
                    global text_chat_input
                    text_chat_input = typed_line
                    command = "TEXT_CHAT"

        # 2. If no console input, check for hotkeys
        if command is None:
            command = hotkeys.get_command_nonblocking()

        # 3. If still no command, check for alarms
        if command is None and alarm.alarm_check():
            command = "ALARM"

        # If any command was found, process it
        if command:
            global is_live_pipe
            is_live_pipe = True

            # Map command to a pipe process
            if command == "CHAT":
                uni_pipes.start_new_pipe(desired_process="Main-Chat", is_main_pipe=True)
            elif command == "TEXT_CHAT":
                uni_pipes.start_new_pipe(desired_process="Main-Text-Chat", is_main_pipe=True)
            elif command == "NEXT":
                uni_pipes.start_new_pipe(desired_process="Main-Next", is_main_pipe=True)
            elif command == "REDO":
                uni_pipes.start_new_pipe(desired_process="Main-Redo", is_main_pipe=True)
            elif command == "SOFT_RESET":
                uni_pipes.start_new_pipe(desired_process="Main-Soft-Reset", is_main_pipe=True)
            elif command == "ALARM":
                uni_pipes.start_new_pipe(desired_process="Main-Alarm", is_main_pipe=True)
            elif command == "VIEW":
                uni_pipes.start_new_pipe(desired_process="Main-View-Image", is_main_pipe=True)
            elif command == "BLANK":
                uni_pipes.start_new_pipe(desired_process="Main-Blank", is_main_pipe=True)
            elif command == "Hangout":
                uni_pipes.start_new_pipe(desired_process="Hangout-Loop", is_main_pipe=True)
            elif command == "Twitch-Chat":
                uni_pipes.start_new_pipe(desired_process="Main-Twitch-Chat", is_main_pipe=True)

            # Wait until the main pipe we have sent is finished
            while uni_pipes.main_pipe_running:
                time.sleep(0.001)

            hotkeys.stack_wipe_inputs()
            if settings.semi_auto_chat:
                hotkeys.speak_input_toggle_from_ui()

            is_live_pipe = False
        
        # Prevent busy-spinning
        time.sleep(0.05)


def main_converse():
    print(
        "\rYou" + colorama.Fore.GREEN + colorama.Style.BRIGHT + " (mic " + colorama.Fore.YELLOW + "[Recording]" + colorama.Fore.GREEN + ") " + colorama.Fore.RESET + ">",
        end="", flush=True)

    # Actual recording and waiting bit
    audio_buffer = audio.record()

    size_string = ""
    try:
        size_string = humanize.naturalsize(os.path.getsize(audio_buffer))
    except Exception as e:
        print(f"Error getting audio buffer size: {e}")
        size_string = str(1 + len(transcriber_translate.transcription_chunks)) + " Chunks"

    try:
        tanscribing_log = "\rYou" + colorama.Fore.GREEN + colorama.Style.BRIGHT + " (mic " + colorama.Fore.BLUE + "[Transcribing (" + size_string + ")]" + colorama.Fore.GREEN + ") " + colorama.Fore.RESET + "> "

        print(tanscribing_log, end="", flush=True)

        while transcriber_translate.chunky_request != None:  # rest to wait for transcription to complete
            time.sleep(0.01)

        # My own edit- To remove possible transcribing errors
        transcript = "Whoops! The code is having some issues, chill for a second."

        # Check for if we are in autochat and the audio is not big enough, then just return and forget about this
        if audio.latest_chat_frame_count < settings.autochat_mininum_chat_frames and hotkeys.get_autochat_toggle():
            print("Audio length too small for autochat - cancelling...")
            zw_logging.update_debug_log("Autochat too small in length. Assuming anomaly and not actual speech...")
            transcriber_translate.clear_transcription_chunks()
            return

        transcript = transcriber_translate.transcribe_voice_to_text(audio_buffer)

        if len(transcript) < 2:
            print("Transcribed chat is blank - cancelling...")
            zw_logging.update_debug_log("Transcribed chat is blank. Assuming anomaly and not actual speech...")
            return


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

    # Store the message, for cycling purposes
    global stored_transcript
    stored_transcript = transcript


    # Actual sending of the message, waits for reply automatically
    # Use the improved API run function with anti-streaming personality
    reply_message = API.api_controller.run(transcript, temp_level=0.7)
    
    if reply_message and reply_message.strip():
        # Apply response cleaning to prevent streaming personality
        clean_reply = clean_twitch_response(reply_message)
        message_checks(clean_reply)

    # Pipe us to the reply function
    main_message_speak()

    # After use, delete the recording.
    try:
        os.remove(audio_buffer)
    except Exception as e:
        print(f"Error deleting audio buffer file {audio_buffer}: {e}")


def main_message_speak():
    """Handle speaking messages (voice + plugin checks)"""
    global live_pipe_force_speak_on_response

    # Message is received here
    message = API.api_controller.receive_via_oogabooga()

    # Stop if the message was streamed—we already spoke it, unless a force-speak was queued
    if API.api_controller.last_message_streamed and not live_pipe_force_speak_on_response:
        live_pipe_force_speak_on_response = False
        return

    # Strip emojis for clearer TTS
    s_message = emoji.replace_emoji(message or "", replace="")

    if s_message.strip():
        t = threading.Thread(target=voice.speak_line, args=(s_message,), kwargs={"refuse_pause": False})
        t.daemon = True
        t.start()

        # Wait until speaking finishes to prevent overlap with next TTS
        while voice.check_if_speaking():
            time.sleep(0.01)

    # Process message checks even if nothing was spoken (so logs/plugins run)
    if message and message.strip():
        message_checks(message)

        # Force speak if specifically requested (e.g., hangout interrupt)
        if live_pipe_force_speak_on_response:
            voice.speak(message)
            live_pipe_force_speak_on_response = False



def message_checks(message):
    """Run post-response tasks: logging, plugin hooks, prints, etc."""

    if not message or message.strip() == "":
        return

    # Log message only if it was NOT streamed
    if not API.api_controller.last_message_streamed:
        # Use debug log since update_chat_log doesn't exist
        zw_logging.update_debug_log(f"Message from {char_name if char_name else 'Assistant'}: {message}")

    # Print banner + text only if not streamed (streamed path prints in real-time)
    if not API.api_controller.last_message_streamed:
        banner_name = char_name if char_name else 'Assistant'
        print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
              + f"----{banner_name}----"
              + colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)
        print(message.strip())
        print()

    # Speak in shadow-chat configuration (non-streamed)
    # if settings.speak_shadowchats and not API.api_controller.last_message_streamed:
    #     # voice.speak(message)  # Function doesn't exist in this version
    #     pass

    # Plugin checks
    if settings.minecraft_enabled:
        minecraft.check_for_command(message)
        minecraft.check_message(message)

    if settings.vtube_enabled and not API.api_controller.last_message_streamed:
        vtube_studio.set_emote_string(message)
        vtube_thread = threading.Thread(target=vtube_studio.check_emote_string)
        vtube_thread.daemon = True
        vtube_thread.start()

    if settings.gaming_enabled:
        gaming_control.message_inputs(message)

    # if settings.rag_enabled:
    #     # based_rag.check_message(message)  # Function doesn't exist in this version
    #     pass

    # Handle kill-word
    if "/ripout/" in message.lower():
        print("\n\nBot is knowingly closing the program! This is typically done as a last resort! Please re-evaluate your actions! :(\n\n")
        sys.exit("Closing…")

    # Allow undo
    global undo_allowed
    undo_allowed = True


def main_rate():
    # function to rate character messages from main
    # NOTE: NO LONGER VALID

    return



def main_next():

    API.api_controller.next_message_oogabooga()

    # Run our message checks
    reply_message = API.api_controller.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function
    main_message_speak()

def main_minecraft_chat(message):
    """Handle incoming Minecraft game chat (shadow chat)"""

    # Flag that we are in a non-spoken shadow chat if shadow-speech is disabled while streaming
    # global settings.live_pipe_no_speak - not needed since settings is a module
    if (not settings.speak_shadowchats) and settings.stream_chats:
        settings.live_pipe_no_speak = True

    # Minecraft chat box can only hold so many characters – force the token count low
    API.api_controller.force_tokens_count(47)

    # Send the player's message to the LLM
    API.api_controller.send_via_oogabooga(message)

    # Push the assistant reply back into the game chat window
    minecraft.minecraft_chat()

    # Standard post-processing (logging, plugin hooks, prints, etc.)
    reply_message = API.api_controller.receive_via_oogabooga()
    message_checks(reply_message)

    # If we're configured to speak shadow chats and we aren't streaming, speak the line aloud
    settings.live_pipe_no_speak = False
    if settings.speak_shadowchats and not settings.stream_chats:
        main_message_speak()

def main_discord_chat(message):
    """Handle Discord chat messages (shadow chat)"""

    # Shadow-chat voice suppression when streaming
    # global settings.live_pipe_no_speak - not needed since settings is a module
    if (not settings.speak_shadowchats) and settings.stream_chats:
        settings.live_pipe_no_speak = True

    # Send the Discord message to the LLM
    API.api_controller.send_via_oogabooga(message)

    # Fetch and process the assistant reply
    reply_message = API.api_controller.receive_via_oogabooga()
    message_checks(reply_message)

    # Speak it if configured
    settings.live_pipe_no_speak = False
    if settings.speak_shadowchats and not settings.stream_chats:
        main_message_speak()

def main_twitch_chat(message):
    """Handle Twitch chat messages as personal conversations (NOT streaming)"""
    
    # Parse the Twitch message format: "username: message"
    if ": " in message:
        username, user_message = message.split(": ", 1)
        
        print(f"[Twitch] {username}: {user_message}")
        
        # Log the user message to chat history
        try:
            from utils.chat_history import add_message_to_history
            add_message_to_history(username, "user", user_message, "twitch")
        except Exception as e:
            print(f"[Twitch] Could not log to chat history: {e}")
        
        # Send the message to the API
        API.api_controller.send_via_oogabooga(user_message)
        
        # Get the raw response
        reply_message = API.api_controller.receive_via_oogabooga()
        
        if reply_message and reply_message.strip():
            # Clean the response to remove streaming artifacts and ensure personal conversation tone
            clean_reply = clean_twitch_response(reply_message)
            
            # Update the history with the cleaned response instead of the raw one
            if len(API.api_controller.ooga_history) > 0:
                # Replace the last response in history with the cleaned version
                API.api_controller.ooga_history[-1][1] = clean_reply
                # Save the updated history
                API.api_controller.save_histories()
            
            # Log the assistant response to chat history
            try:
                from utils.chat_history import add_message_to_history
                add_message_to_history(username, "assistant", clean_reply, "twitch")
            except Exception as e:
                print(f"[Twitch] Could not log assistant response to chat history: {e}")
            
            # Run message checks and speak if enabled
            message_checks(clean_reply)
            main_message_speak()
            
            print(f"[Twitch Response] {clean_reply}")
            return clean_reply  # Return the cleaned response for Twitch bot to send
        return ""  # Return empty string if no response
    else:
        # Fallback for malformed messages
        print(f"[Twitch] Malformed message: {message}")
        API.api_controller.send_via_oogabooga(message)
        reply_message = API.api_controller.receive_via_oogabooga()
        if reply_message and reply_message.strip():
            clean_reply = clean_twitch_response(reply_message)
            
            # Update the history with the cleaned response
            if len(API.api_controller.ooga_history) > 0:
                API.api_controller.ooga_history[-1][1] = clean_reply
                API.api_controller.save_histories()
            
            message_checks(clean_reply)
            main_message_speak()
            return clean_reply  # Return the cleaned response for Twitch bot to send
        return ""  # Return empty string if no response

def clean_twitch_response(response):
    """Clean Twitch responses to ensure personal conversation tone and remove streaming artifacts"""
    if not response:
        return ""
    
    clean_reply = response.strip()
    
    # Remove character name prefix if present
    if clean_reply.startswith("Alexcia:"):
        clean_reply = clean_reply[8:].strip()
    elif clean_reply.startswith("Assistant:"):
        clean_reply = clean_reply[10:].strip()
    
    # Remove streaming context and roleplay actions
    streaming_contexts = [
        "*The stream has just ended",
        "*chatting with viewers",
        "*in the chat*",
        "*stream*",
        "*viewers*",
        "*chat*",
        "*streaming*",
        "*on stream*",
        "*live*"
    ]
    
    for context in streaming_contexts:
        if context.lower() in clean_reply.lower():
            # Remove the entire streaming context
            clean_reply = ""
            break
    
    # If we cleared the response due to streaming context, provide a natural alternative
    if not clean_reply or clean_reply.strip() == "":
        return "Hey there! How's it going?"
    
    # Remove streaming personality artifacts (more comprehensive)
    streaming_phrases = [
        "Thanks for watching",
        "enjoying the stream",
        "Welcome to my stream",
        "Don't forget to follow",
        "Hey viewers",
        "Welcome to the stream", 
        "Thanks for the follow",
        "Appreciate the subscription",
        "Welcome everyone",
        "Hey stream",
        "What's up chat",
        "Hello viewers",
        "Thanks for being here",
        "Welcome back to the stream",
        "stream has just ended",
        "chatting with viewers",
        "glad you're enjoying the stream",
        "thanks for watching",
        "quiet in chat",
        "interacting online"
    ]
    
    # Check for streaming language and replace entire response if found
    for phrase in streaming_phrases:
        if phrase.lower() in clean_reply.lower():
            # If streaming language detected, replace with personal conversation
            return "Hey! How are you doing today? What's been going on with you?"
    
    # Additional check for streaming context words
    streaming_context_words = [
        "streaming", "stream", "viewers", "gameplay", "joining us", 
        "blast streaming", "new viewers", "send me a message"
    ]
    
    for word in streaming_context_words:
        if word.lower() in clean_reply.lower():
            # Replace streaming response with personal conversation
            return "Hey there! How's your day going? What's on your mind?"
    
    # Remove action text in asterisks
    import re
    clean_reply = re.sub(r'\*[^*]*\*', '', clean_reply).strip()
    
    # Remove any "You:" or "Response:" artifacts
    if "You:" in clean_reply:
        clean_reply = clean_reply.split("You:")[0].strip()
    if "Response:" in clean_reply:
        clean_reply = clean_reply.split("Response:")[0].strip()
    
    # Remove fake conversation artifacts
    lines = clean_reply.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        # Skip lines that look like fake conversations
        if ':' in line and any(indicator in line.lower() for indicator in ['you:', 'user:', 'response:', 'assistant:']):
            continue
        if line:
            cleaned_lines.append(line)
    
    if cleaned_lines:
        clean_reply = ' '.join(cleaned_lines)
    
    # Final fallback if response is empty or just whitespace
    if not clean_reply or clean_reply.strip() == "":
        return "Hi! Nice to see you!"
    
    return clean_reply

def main_twitch_next():
    """Handle Twitch chat regeneration command (shadow chat)"""

    # global settings.live_pipe_no_speak - not needed since settings is a module
    if (not settings.speak_shadowchats) and settings.stream_chats:
        settings.live_pipe_no_speak = True

    API.api_controller.next_message_oogabooga()

    reply_message = API.api_controller.receive_via_oogabooga()
    message_checks(reply_message)

    settings.live_pipe_no_speak = False
    if settings.speak_shadowchats and not settings.stream_chats:
        main_message_speak()

def main_web_ui_chat(message):
    """Handle chat messages from the web UI by spawning a worker thread."""
    
    # This function is now just a trigger.
    # The actual work is done in a separate thread to avoid blocking the UI.
    
    chat_thread = threading.Thread(target=main_web_ui_chat_worker, args=(message,))
    chat_thread.daemon = True
    chat_thread.start()

def main_web_ui_chat_worker(message):
    """The actual logic for handling web UI chat, runs in a background thread."""
    
    # If the message is blank, use the dedicated function for that
    if message == "":
        main_send_blank()
        return
    
    # Web UI messages should use the same improved API as Twitch for consistent personality
    # global settings.live_pipe_no_speak - not needed since settings is a module
    if (not settings.speak_shadowchats) and settings.stream_chats:
        settings.live_pipe_no_speak = True

    # Send the message to the API
    API.api_controller.send_via_oogabooga(message)

    # Get the raw response
    reply_message = API.api_controller.receive_via_oogabooga()
    
    if reply_message and reply_message.strip():
        # Apply the same response cleaning as Twitch to prevent streaming personality
        clean_reply = clean_twitch_response(reply_message)
        
        # Update the history with the cleaned response instead of the raw one
        if len(API.api_controller.ooga_history) > 0:
            # Replace the last response in history with the cleaned version
            API.api_controller.ooga_history[-1][1] = clean_reply
            # Save the updated history
            API.api_controller.save_histories()
        
        message_checks(clean_reply)

    # Reset suppression flag and run speech pipeline like other shadow chats
    settings.live_pipe_no_speak = False
    if settings.speak_shadowchats and not settings.stream_chats:
        main_message_speak()

def main_web_ui_next():
    """Handle regeneration requests from the web UI"""
    # Shadow chat regeneration
    # global settings.live_pipe_no_speak - not needed since settings is a module
    if (not settings.speak_shadowchats) and settings.stream_chats:
        settings.live_pipe_no_speak = True

    # Cut voice if needed
    voice.force_cut_voice()

    # If a generation is already running, request skip and exit early
    if API.api_controller.is_in_api_request:
        API.api_controller.set_force_skip_streaming(True)
        settings.live_pipe_no_speak = False
        return

    # Generate new response
    API.api_controller.next_message_oogabooga()

    # Get and process the response
    reply_message = API.api_controller.receive_via_oogabooga()
    if reply_message and reply_message.strip():
        message_checks(reply_message)

        if settings.speak_shadowchats and not settings.stream_chats:
            voice.speak(reply_message)

    settings.live_pipe_no_speak = False
    if settings.speak_shadowchats and not settings.stream_chats:
        main_message_speak()

def main_discord_next():

    # This is a shadow chat
    # global settings.live_pipe_no_speak - not needed since settings is a module
    if (not settings.speak_shadowchats) and settings.stream_chats:
        settings.live_pipe_no_speak = True

    API.api_controller.next_message_oogabooga()

    # Run our message checks
    reply_message = API.api_controller.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function, if we are set to speak them (will be spoken otherwise)
    settings.live_pipe_no_speak = False
    if settings.speak_shadowchats and not settings.stream_chats:
        main_message_speak()


def main_undo():

    global undo_allowed
    if undo_allowed:

        undo_allowed = False

        # Cut voice if needed
        voice.force_cut_voice()

        API.api_controller.undo_message()

        print("\nUndoing the previous message!\n")

        time.sleep(0.1)

def main_soft_reset():

    API.api_controller.soft_reset()

    # We can noT undo
    global undo_allowed
    undo_allowed = False

    time.sleep(0.1)


def main_alarm_message():

    # Check for the daily memory
    if alarm.random_memories and len(based_rag.history_database) > 100:
        main_memory_proc()

    # Send it!
    API.api_controller.send_via_oogabooga(alarm.get_alarm_message())

    # Run our message checks
    reply_message = API.api_controller.receive_via_oogabooga()
    message_checks(reply_message)

    main_message_speak()

    # Clear the alarm
    alarm.clear_alarm()


def main_memory_proc():
    if len(based_rag.history_database) < 100:
        print("Not enough conversation history for memories!")
        return

    # This is a shadow chat
    # global settings.live_pipe_no_speak - not needed since settings is a module
    if (not settings.speak_shadowchats) and settings.stream_chats:
        settings.live_pipe_no_speak = True

    # Retrospect and get a random memory
    retrospect.retrospect_random_mem_summary()

    #
    # CHATS WILL BE GRABBED AFTER THIS RUNS!
    #

    # Run our message checks
    reply_message = API.api_controller.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function, if we are set to speak them (will be spoken otherwise)
    # settings.live_pipe_no_speak moved to settings.py to avoid circular import
    if settings.speak_shadowchats and not settings.stream_chats:
        main_message_speak()



def main_view_image():

    # Give us some feedback
    print("\n\nViewing the camera! Please wait...\n")

    # Clear the camera inputs
    hotkeys.clear_camera_inputs()

    #
    # Get the image first before any processing.

    #
    # Use the image feed
    if settings.cam_use_image_feed:
        camera.use_image_feed()

    #
    # Screenshot capture
    elif settings.cam_use_screenshot:
        camera.capture_screenshot()

    #
    # Normal camera capture
    else:

        # If we do not want to preview, simply take the image. Else, do the confirmation loop

        if not settings.cam_image_preview:
            camera.capture_pic()

        else:
            break_cam_loop = False

            # Loop to check for if the image is what we want or not
            # NOTE: If image preview is on, then the loop will not even go! Neat!

            while not break_cam_loop:
                hotkeys.clear_camera_inputs()
                camera.capture_pic()

                while not (hotkeys.VIEW_IMAGE_PRESSED or hotkeys.CANCEL_IMAGE_PRESSED):
                    time.sleep(0.05)

                if hotkeys.VIEW_IMAGE_PRESSED:
                    break_cam_loop = True

                hotkeys.clear_camera_inputs()


    print("Image processing...\n")

    # Check if we want to run the MIC or not for direct talk
    direct_talk_transcript = ""

    if settings.cam_direct_talk:
        direct_talk_transcript = view_image_prompt_get()

    # View and process the image, storing the result
    transcript = API.api_controller.send_image_via_oobabooga(direct_talk_transcript)

    # Headers and checks
    message_checks(transcript)

    # Speak!
    main_message_speak()

    # We can now undo the previous message

    global undo_allowed
    undo_allowed = True

    # Check if we need to reply after the image
    # NOTE: Depriciated!
    #
    # if settings.cam_reply_after:
    #     view_image_after_chat("So, what did you think of the image, " + char_name + "?")



def view_image_prompt_get():
    print(
        "\rYou" + colorama.Fore.GREEN + colorama.Style.BRIGHT + " (mic " + colorama.Fore.YELLOW + "[Recording]" + colorama.Fore.GREEN + ") " + colorama.Fore.RESET + ">",
        end="", flush=True)

    # Manually toggle on the recording of the mic (it is disabled by toggling off. also works with autochat too BTW)
    hotkeys.speak_input_on_from_cam_direct_talk()

    # Actual recording and waiting bit
    audio_buffer = audio.record()


    size_string = ""
    try:
         size_string = humanize.naturalsize(os.path.getsize(audio_buffer))
    except Exception as e:
        size_string = str(1 + len(transcriber_translate.transcription_chunks)) + " Chunks"

    try:
        tanscribing_log = "\rYou" + colorama.Fore.GREEN + colorama.Style.BRIGHT + " (mic " + colorama.Fore.BLUE + "[Transcribing (" + size_string + ")]" + colorama.Fore.GREEN + ") " + colorama.Fore.RESET + "> "
        print(tanscribing_log, end="", flush=True)

        while transcriber_translate.chunky_request != None:  # rest to wait for transcription to complete
            time.sleep(0.01)

        # My own edit- To remove possible transcribing errors
        transcript = "Whoops! The code is having some issues, chill for a second."

        transcript = transcriber_translate.transcribe_voice_to_text(audio_buffer)



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
    API.api_controller.send_via_oogabooga(message)


    # Run our message checks
    reply_message = API.api_controller.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function
    main_message_speak()


def main_send_blank():
    """Handle sending blank messages"""
    # Give us some feedback
    print("\nSending blank message...\n")

    # Send a blank message (convert to listening placeholder for AI)
    blank_placeholder = "*listens attentively*"
    API.api_controller.send_via_oogabooga(blank_placeholder)

    # Get the response
    reply_message = API.api_controller.receive_via_oogabooga()
    
    # Always process the response, even if it's empty
    # This ensures the interaction gets added to chat history for web UI
    if reply_message and reply_message.strip():
        message_checks(reply_message)
        # Speak the response if shadow chats are enabled
        if settings.speak_shadowchats:
            voice.speak(reply_message)
    else:
        # Even with empty response, run message_checks to ensure proper logging
        message_checks(reply_message or "*nods quietly*")
        # Manually ensure the interaction is in history for web UI
        if len(API.api_controller.ooga_history) == 0 or API.api_controller.ooga_history[-1][0] != blank_placeholder:
            # Add the interaction to history if it wasn't added by the API
            API.api_controller.ooga_history.append([
                blank_placeholder, 
                reply_message or "*nods quietly*", 
                settings.cur_tags.copy(), 
                "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())
            ])
            API.api_controller.save_histories()

#
# Defs for main hangout functions
#

def hangout_converse():
    print(
        "\rYou" + colorama.Fore.GREEN + colorama.Style.BRIGHT + " (mic " + colorama.Fore.YELLOW + "[Recording]" + colorama.Fore.GREEN + ") " + colorama.Fore.RESET + ">",
        end="", flush=True)

    # Actual recording and waiting bit
    audio_buffer = audio.record()
    size_string = ""
    try:
         size_string = humanize.naturalsize(os.path.getsize(audio_buffer))
    except Exception as e:
        size_string = str(1 + len(transcriber_translate.transcription_chunks)) + " Chunks"

    try:
        tanscribing_log = "\rYou" + colorama.Fore.GREEN + colorama.Style.BRIGHT + " (mic " + colorama.Fore.BLUE + "[Transcribing (" + size_string + ")]" + colorama.Fore.GREEN + ") " + colorama.Fore.RESET + "> "
        print(tanscribing_log, end="", flush=True)

        while transcriber_translate.chunky_request != None:  # rest to wait for transcription to complete
            time.sleep(0.01)

        # My own edit- To remove possible transcribing errors
        transcript = "Whoops! The code is having some issues, chill for a second."

        # Check for if we are in autochat and the audio is not big enough, then just return and forget about this
        # This will cause us to re-loop! Awesome!
        if audio.latest_chat_frame_count < settings.autochat_mininum_chat_frames and hotkeys.get_autochat_toggle():
            print("Audio length too small for autochat - cancelling...")
            zw_logging.update_debug_log("Autochat too small in length. Assuming anomaly and not actual speech...")
            transcriber_translate.clear_transcription_chunks()
            return "Audio too short!"

        transcript = transcriber_translate.transcribe_voice_to_text(audio_buffer)

        if len(transcript) < 2:
            print("Transcribed chat is blank - cancelling...")
            zw_logging.update_debug_log("Transcribed chat is blank. Assuming anomaly and not actual speech...")
            return "Audio too short!"



    except Exception as e:
        print(colorama.Fore.RED + colorama.Style.BRIGHT + "Error: " + str(e))
        return "Audio error!"

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

    # After use, delete the recording.
    try:
        os.remove(audio_buffer)
    except Exception as e:
        print(f"Error deleting audio buffer file {audio_buffer}: {e}")

    return transcript

def hangout_reply(transcript):

    # Bit here for interruption (only if needed)
    if hangout.use_interruptable_chat:
        hangout_interruptable = threading.Thread(target=hangout_interrupt_audio_recordable)
        hangout_interruptable.daemon = True
        hangout_interruptable.start()

    # Actual sending of the message, waits for reply automatically
    API.api_controller.send_via_oogabooga(transcript)

    # Run our message checks
    reply_message = API.api_controller.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function
    main_message_speak()

    # Clear our appendables (hangout)
    hangout.clear_appendables()

def hangout_wait_reply_waitportion(transcript):
    # Send our request, be sure to not read it aloud
    global live_pipe_use_streamed_interrupt_watchdog
    # Note: settings.live_pipe_no_speak doesn't need global declaration
    settings.live_pipe_no_speak = True
    live_pipe_use_streamed_interrupt_watchdog = True

    API.api_controller.send_via_oogabooga(transcript)

    live_pipe_use_streamed_interrupt_watchdog = False
    settings.live_pipe_no_speak = False

def hangout_wait_reply_replyportion():

    # wait for gen to finish
    while API.api_controller.is_in_api_request:
        time.sleep(0.01)

    # Run our message checks
    reply_message = API.api_controller.receive_via_oogabooga()
    message_checks(reply_message)

    # Set it so that we speak on response
    global live_pipe_force_speak_on_response
    live_pipe_force_speak_on_response = True

    # Pipe us to the reply function
    main_message_speak()

    # Clear our appendables (hangout)
    hangout.clear_appendables()

    live_pipe_force_speak_on_response = False


def hangout_view_image_reply(transcript, dont_speak_aloud):
    # global settings.live_pipe_no_speak - not needed since settings is a module

    # Give us some feedback
    print("\n\nViewing the camera! Please wait...\n")

    # Clear the camera inputs
    hotkeys.clear_camera_inputs()

    #
    # Get the image first before any processing.
    #
    # Screenshot capture
    if settings.cam_use_screenshot:
        camera.capture_screenshot()

    #
    # Normal camera capture
    else:

        # Just take the image, we do not confirm the image input with this version
        camera.capture_pic()



    print("Image processing...\n")

    # Append what was talked about recently
    direct_talk_transcript = transcript

    # Set us speaking aloud or not (controls are in the API script for streamed update handler
    settings.live_pipe_no_speak = dont_speak_aloud

    # View and process the image, storing the result
    transcript = API.api_controller.send_image_via_oobabooga_hangout(direct_talk_transcript)


    # Run our required message checks
    message_checks(transcript)

    settings.live_pipe_no_speak = False

    # Clear our appendables (hangout)
    hangout.clear_appendables()

# For interrupting in hangout mode. Flagged as "Ordus" for recording and transcribing, needs its own methods
def hangout_interrupt_audio_recordable():

    # Minirest to allow the API to start requesting
    time.sleep(2)

    not_run_yet = True

    # Auto-close when the api is in an request
    while API.api_controller.is_in_api_request or not_run_yet:

        time.sleep(0.01)

        # Actual recording and waiting bit
        audio_buffer = audio.record_ordus()
        ordus_transcript = transcriber_translate.ordus_transcribe_voice_to_text(audio_buffer)

        # All the things you can say to get your waifu to stop talking
        interrupt_messages = ["wait " + char_name, char_name + " wait", "wait, " + char_name, "wait. " + char_name, char_name + ", wait", char_name + ". wait"]

        # Flag
        not_run_yet = False

        if cane_lib.keyword_check(ordus_transcript, interrupt_messages):

            # Force the interrupt
            API.api_controller.flag_end_streaming = True

            # Info
            zw_logging.update_debug_log("Forcing generation to end - name detected!")

            # We can exit now
            return

def main_text_chat():
    """Handle chat messages from the text input"""
    global text_chat_input
    if text_chat_input is None:
        print("Error: No text chat input was provided.")
        return

    # Use the text input from the global variable
    transcript = text_chat_input
    text_chat_input = None  # Clear it after use

    # Print the transcript
    print('\r' + colorama.Fore.RED + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
          + "----Me----"
          + colorama.Fore.RED + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)
    print(f"{transcript.strip()}")
    print("\n")

    # Store the message, for cycling purposes
    global stored_transcript
    stored_transcript = transcript

    # Actual sending of the message, waits for reply automatically
    API.api_controller.send_via_oogabooga(transcript)

    # Run our message checks
    reply_message = API.api_controller.receive_via_oogabooga()
    message_checks(reply_message)

    # Pipe us to the reply function
    main_message_speak()

def run_program():
    """Main program startup function with proper error handling"""
    try:
        # Initialize colorama for cross-platform colored output
        colorama.init()
        
        print(f"{colorama.Fore.CYAN}Z-WAIF System Initializing...{colorama.Fore.RESET}")
        
        # Set up basic error logging (after colorama init)
        try:
            zw_logging.log_startup()
        except Exception as log_error:
            print(f"Warning: Logging initialization failed: {log_error}")
        
    except Exception as e:
        print(f"FATAL: Failed to initialize basic systems: {e}")
        input("Press Enter to exit...")
        return

    #
    # Startup Prep
    #

    # Load any available character cards
    API.character_card.load_char_card()

    # Load any available task profiles
    API.task_profiles.load_task_profiles()

    # Load hotkey ON/OFF on boot
    hotkeys.load_hotkey_bootstate()

    # Load the defaults for modules being on/off in the settings
    minecraft_enabled_string = os.environ.get("MODULE_MINECRAFT")
    settings.minecraft_enabled = minecraft_enabled_string == "ON" and os.name != "posix"

    alarm_enabled_string = os.environ.get("MODULE_ALARM")
    if alarm_enabled_string == "ON":
        settings.alarm_enabled = True
    else:
        settings.alarm_enabled = False

    vtube_enabled_string = os.environ.get("MODULE_VTUBE")
    if vtube_enabled_string == "ON":
        settings.vtube_enabled = True
    else:
        settings.vtube_enabled = False

    discord_enabled_string = os.environ.get("MODULE_DISCORD")
    if discord_enabled_string == "ON":
        settings.discord_enabled = True
    else:
        settings.discord_enabled = False

    twitch_enabled_string = os.environ.get("MODULE_TWITCH")
    if twitch_enabled_string == "ON":
        settings.twitch_enabled = True
    else:
        settings.twitch_enabled = False

    rag_enabled_string = os.environ.get("MODULE_RAG")
    if rag_enabled_string == "ON":
        settings.rag_enabled = True
    else:
        settings.rag_enabled = False

    vision_enabled_string = os.environ.get("MODULE_VISUAL")
    if vision_enabled_string == "ON":
        settings.vision_enabled = True
    else:
        settings.vision_enabled = False

    gaming_enabled_string = os.environ.get("MODULE_GAMING")
    if gaming_enabled_string == "ON":
        settings.gaming_enabled = True
    else:
        settings.gaming_enabled = False


    # Other settings

    settings.eyes_follow = os.environ.get("EYES_FOLLOW")
    settings.autochat_mininum_chat_frames = int(os.environ.get("AUTOCHAT_MIN_LENGTH", "400"))

    silero_string = os.environ.get("SILERO_VAD")
    if silero_string == "ON":
        settings.use_silero_vad = True
    else:
        settings.use_silero_vad = False

    newline_cut_enabled_string = os.environ.get("NEWLINE_CUT_BOOT")
    if newline_cut_enabled_string == "ON":
        settings.newline_cut = True
    else:
        settings.newline_cut = False

    rp_sup_enabled_string = os.environ.get("RP_SUP_BOOT")
    if rp_sup_enabled_string == "ON":
        settings.supress_rp = True
    else:
        settings.supress_rp = False

    stream_chats_enabled_string = os.environ.get("API_STREAM_CHATS")
    if stream_chats_enabled_string == "ON":
        settings.stream_chats = True
    else:
        settings.stream_chats = False


    # Load in our char name
    settings.char_name = char_name

    # Load tags and tasks
    tag_task_controller.load_tags_tasks()

    # Run any needed log conversions
    log_conversion.run_conversion()

    # Load the previous chat history, and make a backup of it
    API.api_controller.check_load_past_chat()

    # Load in our chatpops
    chatpops_enabled_string = os.environ.get("USE_CHATPOPS")
    if chatpops_enabled_string == "ON":
        settings.use_chatpops = True
    else:
        settings.use_chatpops = False

    with open("Configurables/Chatpops.json", 'r') as openfile:
        settings.chatpop_phrases = json.load(openfile)


    # Start the VTube Studio interaction in a separate thread, we ALWAYS do this FYI
    if settings.vtube_enabled:
        vtube_studio_thread = threading.Thread(target=vtube_studio.run_vtube_studio_connection)
        vtube_studio_thread.daemon = True
        vtube_studio_thread.start()

        # Emote loop as well
        vtube_studio_thread = threading.Thread(target=vtube_studio.emote_runner_loop)
        vtube_studio_thread.daemon = True
        vtube_studio_thread.start()


    # Start another thread for the alarm interaction
    if settings.alarm_enabled:
        alarm_thread = threading.Thread(target=alarm.alarm_loop)
        alarm_thread.daemon = True
        alarm_thread.start()


    # Start another thread for the different voice detections
    volume_listener_thread = threading.Thread(target=volume_listener.run_volume_listener)
    volume_listener_thread.daemon = True
    volume_listener_thread.start()

    vad_listener = threading.Thread(target=audio.record_vad_loop)
    vad_listener.daemon = True
    vad_listener.start()

    listener_toggle = threading.Thread(target=hotkeys.listener_timer)
    listener_toggle.daemon = True
    listener_toggle.start()


    # Buffer loop
    chat_recording_buffer = threading.Thread(target=audio.autochat_audio_buffer_record)
    chat_recording_buffer.daemon = True
    chat_recording_buffer.start()


    # Start another thread for the Minecraft watchdog
    if settings.minecraft_enabled:
        minecraft_thread = threading.Thread(target=minecraft.chat_check_loop)
        minecraft_thread.daemon = True
        minecraft_thread.start()

    # Start another thread for Discord
    if settings.discord_enabled:
        discord_thread = threading.Thread(target=z_waif_discord.run_z_waif_discord)
        discord_thread.daemon = True
        discord_thread.start()

    # Start another thread for Twitch
    if settings.twitch_enabled:
        twitch_thread = threading.Thread(target=z_waif_twitch.run_z_waif_twitch)
        twitch_thread.daemon = True
        twitch_thread.start()



    # Start another thread for camera facial track, if we want that
    if settings.eyes_follow == "Faces":
        face_follow_thread = threading.Thread(target=camera.loop_follow_look)
        face_follow_thread.daemon = True
        face_follow_thread.start()
    elif settings.eyes_follow == "Random":
        face_follow_thread = threading.Thread(target=camera.loop_random_look)
        face_follow_thread.daemon = True
        face_follow_thread.start()

    # Start a chunky transcription thread
    # NOTE: While I could add a check to see if we need to, it really doesn't matter, since no requests come in anyway!
    chunky_transcription = threading.Thread(target=transcriber_translate.chunky_transcription_loop)
    chunky_transcription.daemon = True
    chunky_transcription.start()

    # Start another thread for Gradio
    gradio_thread = threading.Thread(target=web_ui.launch_demo)
    gradio_thread.daemon = True
    gradio_thread.start()

    # Line to manually crash the software (y'know, testing and whatnot)
    # calculated_test = 0 / 0

    # Load our character card and task files (for Ollama)
    API.character_card.load_char_card()
    API.task_profiles.load_task_profiles()

    # Handle command line arguments for message input
    handle_command_line_args()

    # Kick off the console reader so typed input works alongside hotkeys/voice
    console_input.start_console_reader()

    # Announce that the program is running
    print(f"{colorama.Fore.GREEN}Welcome back! Loading chat interface...{colorama.Fore.RESET}\n")
    
    # Process startup message if provided (after all systems are ready)
    if startup_message:
        try:
            process_startup_message()
        except Exception as e:
            print(f"{colorama.Fore.RED}Error processing startup message: {e}{colorama.Fore.RESET}")
            zw_logging.log_error(f"Startup message error: {e}")

    # Run the primary loop with error handling
    try:
        print(f"{colorama.Fore.CYAN}Z-WAIF is ready! Type messages or use hotkeys...{colorama.Fore.RESET}\n")
        main()
    except KeyboardInterrupt:
        print(f"\n{colorama.Fore.YELLOW}Shutdown requested by user{colorama.Fore.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{colorama.Fore.RED}Critical error in main loop: {e}{colorama.Fore.RESET}")
        zw_logging.log_error(f"Main loop critical error: {e}")
        print("Check log.txt for details")
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    try:
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

        # Run the main program
        run_program()
        
    except Exception as e:
        # Final catch-all error handler
        print(f"\nFATAL ERROR: {e}")
        print("Z-WAIF failed to start properly.")
        print("Please check your configuration and requirements.")
        input("Press Enter to exit...")
        sys.exit(1)

