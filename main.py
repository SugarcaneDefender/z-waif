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

# Import enhanced AI handler for better integration
from utils.ai_handler import AIHandler

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

# Debug mode toggle
debug_mode = False

# Initialize enhanced AI handler for better integration
enhanced_ai_handler = AIHandler()

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

def verify_system_integration():
    """Verify that all enhanced components are working together"""
    print(f"{colorama.Fore.CYAN}🔧 Verifying enhanced system integration...{colorama.Fore.RESET}")
    
    # Check AI handler
    try:
        test_chatpop = enhanced_ai_handler.get_contextual_chatpop({"platform": "personal"}, "Hello")
        print(f"{colorama.Fore.GREEN}✅ Enhanced AI handler working - Sample chatpop: '{test_chatpop}'{colorama.Fore.RESET}")
    except Exception as e:
        print(f"{colorama.Fore.RED}❌ AI handler issue: {e}{colorama.Fore.RESET}")
    
    # Check chatpops configuration
    try:
        # Re-import settings to ensure we have the latest state
        from utils import settings
        chatpop_count = len(settings.chatpop_phrases) if hasattr(settings, 'chatpop_phrases') else 0
        
        if settings.use_chatpops and chatpop_count > 0:
            print(f"{colorama.Fore.GREEN}✅ Chatpops enabled with {chatpop_count} phrases{colorama.Fore.RESET}")
        elif not settings.use_chatpops:
            print(f"{colorama.Fore.YELLOW}⚠️ Chatpops disabled in settings{colorama.Fore.RESET}")
        else:
            print(f"{colorama.Fore.YELLOW}⚠️ Chatpops enabled but no phrases loaded (found {chatpop_count}){colorama.Fore.RESET}")
    except Exception as e:
        print(f"{colorama.Fore.RED}❌ Chatpops configuration issue: {e}{colorama.Fore.RESET}")
    
    # Check API controller integration
    try:
        if hasattr(API.api_controller, 'ai_handler'):
            print(f"{colorama.Fore.GREEN}✅ API controller has enhanced AI handler{colorama.Fore.RESET}")
        else:
            print(f"{colorama.Fore.YELLOW}⚠️ API controller using standard chatpops{colorama.Fore.RESET}")
    except Exception as e:
        print(f"{colorama.Fore.RED}❌ API controller integration issue: {e}{colorama.Fore.RESET}")
    
    print(f"{colorama.Fore.CYAN}🔧 System verification complete!{colorama.Fore.RESET}\n")

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

        # Use the enhanced platform-aware messaging system
        clean_reply = send_platform_aware_message(message, platform="cmd")
        
        if clean_reply and clean_reply.strip():
            message_checks(clean_reply)

        # Speak the reply
        main_message_speak()
        
        print(f"\n{colorama.Fore.GREEN}Startup message processed. Continuing with normal operation...{colorama.Fore.RESET}\n")

# noinspection PyBroadException
def print_console_help():
    """Display available console commands"""
    help_text = f"""
{colorama.Fore.CYAN}═══════════════════════════════════════════════════════════════════════════════
                              Z-WAIF CONSOLE COMMANDS
═══════════════════════════════════════════════════════════════════════════════{colorama.Fore.RESET}

{colorama.Fore.GREEN}Chat Commands:{colorama.Fore.RESET}
  • Type any message                    → Send as chat to AI
  • /blank, blank                       → Send blank message (AI will self-talk)

{colorama.Fore.YELLOW}Control Commands:{colorama.Fore.RESET}
  • /next, next                         → Generate next response
  • /redo, redo                         → Regenerate last response
  • /soft_reset, reset                  → Reset conversation context
  • /view, view                         → Take/send image (if vision enabled)

{colorama.Fore.BLUE}System Commands:{colorama.Fore.RESET}
  • /help, help, /?                     → Show this help
  • /status, status                     → Show current system status
  • /clear, clear_history               → Clear conversation history
  • /debug, debug_toggle                → Toggle debug mode on/off
  • /quit, exit                         → Shutdown Z-WAIF

{colorama.Fore.YELLOW}Hotkey Commands:{colorama.Fore.RESET}
  • Ctrl+A                              → Toggle Auto-Chat
  • Ctrl+B                              → Send Blank Message
  • Ctrl+R                              → Soft Reset
  • Ctrl+S                              → Change Autochat Sensitivity
  • Right Arrow                         → Next Response
  • Up Arrow                            → Redo Last Response

{colorama.Fore.MAGENTA}Note:{colorama.Fore.RESET} All commands work while other functions are running!
{colorama.Fore.GREEN}✅ Console typing now works without hotkey interference!{colorama.Fore.RESET}
{colorama.Fore.CYAN}═══════════════════════════════════════════════════════════════════════════════{colorama.Fore.RESET}
"""
    print(help_text)


def clear_conversation_history():
    """Clear conversation history and reset to fresh start"""
    try:
        # Reset the history to just the default greeting
        fresh_history = [["Hello, I am back!", "Welcome back! *smiles*"]]
        
        # Save to LiveLog.json
        import json
        with open("LiveLog.json", 'w') as outfile:
            json.dump(fresh_history, outfile, indent=4)
        
        # Clear the in-memory history
        API.api_controller.ooga_history = fresh_history
        
        print(f"{colorama.Fore.GREEN}✅ Conversation history cleared successfully!")
        print(f"🔄 Chat has been reset to fresh start{colorama.Fore.RESET}")
        
    except Exception as e:
        print(f"{colorama.Fore.RED}❌ Error clearing history: {e}{colorama.Fore.RESET}")


def toggle_debug_mode():
    """Toggle debug mode on/off"""
    global debug_mode
    debug_mode = not debug_mode
    status = "ON" if debug_mode else "OFF"
    print(f"{colorama.Fore.CYAN}🐛 Debug mode: {status}{colorama.Fore.RESET}")


def print_status_info():
    """Display current system status"""
    history_length = len(API.api_controller.ooga_history) if hasattr(API.api_controller, 'ooga_history') else 0
    
    status_text = f"""
{colorama.Fore.CYAN}═══════════════════════════════════════════════════════════════════════════════
                                Z-WAIF STATUS
═══════════════════════════════════════════════════════════════════════════════{colorama.Fore.RESET}

{colorama.Fore.GREEN}🎤 Recording:{colorama.Fore.RESET}          {'ON' if hotkeys.get_speak_input() else 'OFF'}
{colorama.Fore.GREEN}🤖 Auto-Chat:{colorama.Fore.RESET}         {'ON' if hotkeys.get_autochat_toggle() else 'OFF'}
{colorama.Fore.GREEN}📱 Semi-Auto Chat:{colorama.Fore.RESET}    {'ON' if settings.semi_auto_chat else 'OFF'}
{colorama.Fore.GREEN}🏠 Hangout Mode:{colorama.Fore.RESET}      {'ON' if settings.hangout_mode else 'OFF'}
{colorama.Fore.GREEN}🎮 Gaming Mode:{colorama.Fore.RESET}       {'ON' if settings.is_gaming_loop else 'OFF'}
{colorama.Fore.GREEN}🔒 Hotkeys Locked:{colorama.Fore.RESET}    {'YES' if settings.hotkeys_locked else 'NO'}
{colorama.Fore.GREEN}👁️ Vision:{colorama.Fore.RESET}           {'ON' if settings.vision_enabled else 'OFF'}
{colorama.Fore.GREEN}🎯 Sensitivity:{colorama.Fore.RESET}       {hotkeys.get_autochat_sensitivity()}
{colorama.Fore.GREEN}💬 History Length:{colorama.Fore.RESET}    {history_length} messages
{colorama.Fore.GREEN}📊 Current Mode:{colorama.Fore.RESET}      {'Live Pipe' if is_live_pipe else 'Waiting for Input'}

{colorama.Fore.CYAN}═══════════════════════════════════════════════════════════════════════════════{colorama.Fore.RESET}
"""
    print(status_text)


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
                    print("⏭️ Processing NEXT command...")
                    command = "NEXT"
                elif lowercase_line in {"/redo", "redo"}:
                    print("🔄 Processing REDO command...")
                    command = "REDO"
                elif lowercase_line in {"/soft_reset", "soft reset", "reset"}:
                    print("🔄 Processing SOFT RESET command...")
                    command = "SOFT_RESET"
                elif lowercase_line in {"/view", "view"}:
                    print("👁️ Processing VIEW IMAGE command...")
                    command = "VIEW"
                elif lowercase_line in {"/blank", "blank"}:
                    print("📝 Processing BLANK MESSAGE command...")
                    command = "BLANK"
                elif lowercase_line in {"/help", "help", "/?"}:
                    print_console_help()
                    command = None  # Don't process as command, just show help
                elif lowercase_line in {"/status", "status"}:
                    print_status_info()
                    command = None  # Don't process as command, just show status
                elif lowercase_line in {"/clear", "clear", "/clear_history", "clear_history"}:
                    clear_conversation_history()
                    command = None  # Don't process as command, just clear history
                elif lowercase_line in {"/debug", "debug", "/debug_toggle", "debug_toggle"}:
                    toggle_debug_mode()
                    command = None  # Don't process as command, just toggle debug
                elif lowercase_line in {"/quit", "quit", "exit", "/exit"}:
                    print("👋 Shutting down Z-WAIF...")
                    sys.exit(0)
                else:
                    # Treat as a standard chat message
                    print(f"💬 Processing text chat: '{typed_line}'")
                    # Pass the message directly to the pipe instead of using global variable
                    uni_pipes.start_new_pipe(desired_process="Main-Text-Chat", is_main_pipe=True, data=typed_line)
                    command = None  # Don't process through normal command flow

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


    # Use platform-aware messaging for voice chat
    clean_reply = send_platform_aware_message(transcript, platform="voice")
    
    if clean_reply and clean_reply.strip():
        # Update the history with the cleaned response
        if len(API.api_controller.ooga_history) > 0:
            API.api_controller.ooga_history[-1][1] = clean_reply
            API.api_controller.save_histories()
        
        message_checks(clean_reply)

    # Pipe us to the reply function
    main_message_speak()

    # After use, delete the recording.
    try:
        os.remove(audio_buffer)
    except Exception as e:
        print(f"Error deleting audio buffer file {audio_buffer}: {e}")


def main_message_speak(skip_message_checks=False):
    """Handle speaking messages (voice + plugin checks)"""
    global live_pipe_force_speak_on_response
    
    if debug_mode:
        print(f"[DEBUG] main_message_speak() called with skip_message_checks={skip_message_checks}")

    # Message is received here
    message = API.api_controller.receive_via_oogabooga()
    if debug_mode:
        print(f"[DEBUG] main_message_speak() received: {repr(message)}")

    # Stop if the message was streamed—we already spoke it, unless a force-speak was queued
    if API.api_controller.last_message_streamed and not live_pipe_force_speak_on_response:
        live_pipe_force_speak_on_response = False
        return

    # Clean the message for TTS (remove character name prefix)
    clean_message = message or ""
    if settings.char_name and clean_message.startswith(f"{settings.char_name}:"):
        clean_message = clean_message[len(settings.char_name)+1:].strip()
    elif clean_message.startswith("Assistant:"):
        clean_message = clean_message[10:].strip()
    
    # Strip emojis for clearer TTS
    s_message = emoji.replace_emoji(clean_message, replace="")

    if s_message.strip():
        t = threading.Thread(target=voice.speak_line, args=(s_message,), kwargs={"refuse_pause": False})
        t.daemon = True
        t.start()

        # Wait until speaking finishes to prevent overlap with next TTS
        while voice.check_if_speaking():
            time.sleep(0.01)

    # Process message checks even if nothing was spoken (so logs/plugins run)
    # But skip if the caller has already handled message_checks
    if message and message.strip() and not skip_message_checks:
        message_checks(message)

        # Force speak if specifically requested (e.g., hangout interrupt)
        if live_pipe_force_speak_on_response:
            # Also clean the force speak message
            force_speak_clean = message
            if settings.char_name and force_speak_clean.startswith(f"{settings.char_name}:"):
                force_speak_clean = force_speak_clean[len(settings.char_name)+1:].strip()
            elif force_speak_clean.startswith("Assistant:"):
                force_speak_clean = force_speak_clean[10:].strip()
            voice.speak(force_speak_clean)
            live_pipe_force_speak_on_response = False



def message_checks(message, skip_print=False):
    """Run post-response tasks: logging, plugin hooks, prints, etc."""
    
    try:
        if debug_mode:
            print(f"[DEBUG] message_checks() called with skip_print={skip_print}, message: {repr(message[:50])}...")
    except:
        pass
    
    if not message or message.strip() == "":
        return

    # Log message only if it was NOT streamed
    if not API.api_controller.last_message_streamed:
        # Use debug log since update_chat_log doesn't exist
        zw_logging.update_debug_log(f"Message from {settings.char_name if settings.char_name else 'Assistant'}: {message}")

        # Handle printing - skip_print=True completely prevents printing
        if skip_print:
            # Skip all printing when skip_print is True
            pass
        elif not API.api_controller.last_message_streamed:
            # Print banner + text only if not streamed (streamed path prints in real-time)
            banner_name = settings.char_name if settings.char_name else 'Assistant'
            print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
                  + f"----{banner_name}----"
                  + colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)
            
            # Clean the message for display (remove character name prefix)
            display_message = message
            if settings.char_name and display_message.startswith(f"{settings.char_name}:"):
                display_message = display_message[len(settings.char_name)+1:].strip()
            elif display_message.startswith("Assistant:"):
                display_message = display_message[10:].strip()
            
            print(display_message.strip())
            print()

    # Plugin checks (run regardless of printing)
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

    # Use platform-aware messaging for Minecraft
    clean_reply = send_platform_aware_message(message, platform="minecraft")

    # Push the assistant reply back into the game chat window
    minecraft.minecraft_chat()

    # Standard post-processing (logging, plugin hooks, prints, etc.)
    if clean_reply and clean_reply.strip():
        # Update the history with the cleaned response
        if len(API.api_controller.ooga_history) > 0:
            API.api_controller.ooga_history[-1][1] = clean_reply
            API.api_controller.save_histories()
        
        message_checks(clean_reply)

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

    # Use platform-aware messaging for Discord
    clean_reply = send_platform_aware_message(message, platform="discord")

    # Fetch and process the assistant reply
    if clean_reply and clean_reply.strip():
        # Update the history with the cleaned response
        if len(API.api_controller.ooga_history) > 0:
            API.api_controller.ooga_history[-1][1] = clean_reply
            API.api_controller.save_histories()
        
        message_checks(clean_reply)

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
        
        # Use platform-aware messaging for Twitch
        clean_reply = send_platform_aware_message(user_message, platform="twitch")
        
        if clean_reply and clean_reply.strip():
            # Update the history with the cleaned response
            if len(API.api_controller.ooga_history) > 0:
                API.api_controller.ooga_history[-1][1] = clean_reply
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
        clean_reply = send_platform_aware_message(message, platform="twitch")
        if clean_reply and clean_reply.strip():
            # Update the history with the cleaned response
            if len(API.api_controller.ooga_history) > 0:
                API.api_controller.ooga_history[-1][1] = clean_reply
                API.api_controller.save_histories()
            
            message_checks(clean_reply)
            main_message_speak()
            return clean_reply  # Return the cleaned response for Twitch bot to send
        return ""  # Return empty string if no response

def send_platform_aware_message(user_input, platform="personal"):
    """Send a message with platform context to get appropriate responses"""
    
    # Add platform context to the user input for the AI to understand
    if platform == "twitch":
        contextual_input = f"[Platform: Twitch Chat] {user_input}"
    elif platform == "discord":
        contextual_input = f"[Platform: Discord] {user_input}"
    elif platform == "webui":
        contextual_input = f"[Platform: Web Interface - Personal Chat] {user_input}"
    elif platform == "cmd":
        contextual_input = f"[Platform: Command Line - Personal Chat] {user_input}"
    elif platform == "voice":
        contextual_input = f"[Platform: Voice Chat - Personal Conversation] {user_input}"
    elif platform == "minecraft":
        contextual_input = f"[Platform: Minecraft Game Chat] {user_input}"
    elif platform == "alarm":
        contextual_input = f"[Platform: Alarm/Reminder System] {user_input}"
    elif platform == "hangout":
        contextual_input = f"[Platform: Hangout Mode - Casual Conversation] {user_input}"
    else:
        contextual_input = user_input
    
    # Send the message with context
    API.api_controller.send_via_oogabooga(contextual_input)
    
    # Get the response
    reply_message = API.api_controller.receive_via_oogabooga()
    
    # Clean the response based on platform
    if platform == "twitch":
        return clean_twitch_response(reply_message)
    elif platform == "discord":
        return clean_discord_response(reply_message)
    elif platform == "voice":
        return clean_voice_response(reply_message)
    elif platform == "minecraft":
        return clean_minecraft_response(reply_message)
    elif platform == "alarm":
        return clean_alarm_response(reply_message)
    elif platform == "hangout":
        return clean_hangout_response(reply_message)
    elif platform in ["webui", "cmd"]:
        return clean_personal_response(reply_message)
    else:
        return clean_personal_response(reply_message)

def clean_personal_response(response):
    """Clean responses for personal conversations (Web UI, CMD)"""
    if not response:
        return ""
    
    clean_reply = response.strip()
    
    # Remove character name prefix if present - more robust matching
    import re
    from utils import settings
    
    # First, try to remove the configured character name specifically
    if settings.char_name and clean_reply.startswith(f"{settings.char_name}:"):
        clean_reply = clean_reply[len(settings.char_name)+1:].strip()
    
    # Then, catch any other name patterns (like "Assistant:", etc.)
    name_pattern = r'^[A-Za-z]+:\s*'
    clean_reply = re.sub(name_pattern, '', clean_reply).strip()
    
    # Remove streaming language completely for personal conversations
    streaming_phrases = [
        "Thanks for watching", "enjoying the stream", "Welcome to my stream",
        "Don't forget to follow", "Hey viewers", "Welcome to the stream", 
        "Thanks for the follow", "Appreciate the subscription", "Welcome everyone",
        "Hey stream", "What's up chat", "Hello viewers", "Thanks for being here",
        "Welcome back to the stream", "stream has just ended", "chatting with viewers",
        "glad you're enjoying the stream", "thanks for watching", "quiet in chat",
        "interacting online", "streaming", "stream", "viewers", "gameplay", 
        "joining us", "blast streaming", "new viewers", "send me a message"
    ]
    
    # Check for streaming language and replace entire response if found
    for phrase in streaming_phrases:
        if phrase.lower() in clean_reply.lower():
            return "Hey! How are you doing? What's on your mind?"
    
    # Remove action text in asterisks
    clean_reply = re.sub(r'\*[^*]*\*', '', clean_reply).strip()
    
    # Remove platform context markers
    clean_reply = re.sub(r'\[Platform:[^\]]*\]', '', clean_reply).strip()
    
    # Final fallback if response is empty
    if not clean_reply or clean_reply.strip() == "":
        return "Hi! Nice to chat with you!"
    
    return clean_reply

def clean_discord_response(response):
    """Clean responses for Discord conversations"""
    if not response:
        return ""
    
    clean_reply = response.strip()
    
    # Remove character name prefix if present - more robust matching
    import re
    from utils import settings
    
    # First, try to remove the configured character name specifically
    if settings.char_name and clean_reply.startswith(f"{settings.char_name}:"):
        clean_reply = clean_reply[len(settings.char_name)+1:].strip()
    
    # Then, catch any other name patterns (like "Assistant:", etc.)
    name_pattern = r'^[A-Za-z]+:\s*'
    clean_reply = re.sub(name_pattern, '', clean_reply).strip()
    
    # Remove platform context markers
    clean_reply = re.sub(r'\[Platform:[^\]]*\]', '', clean_reply).strip()
    
    # Keep Discord-appropriate language (casual, fun, emojis OK)
    # But remove streaming references
    streaming_phrases = [
        "Thanks for watching", "enjoying the stream", "Welcome to my stream",
        "Don't forget to follow", "stream has just ended", "chatting with viewers",
        "glad you're enjoying the stream", "thanks for watching"
    ]
    
    for phrase in streaming_phrases:
        if phrase.lower() in clean_reply.lower():
            return "Hey! What's up? 😊"
    
    # Final fallback if response is empty
    if not clean_reply or clean_reply.strip() == "":
        return "Hey there! 👋"
    
    return clean_reply

def clean_twitch_response(response):
    """Clean Twitch responses to ensure personal conversation tone and remove streaming artifacts"""
    if not response:
        return ""
    
    clean_reply = response.strip()
    
    # Remove character name prefix if present - more robust matching
    import re
    from utils import settings
    
    # First, try to remove the configured character name specifically
    if settings.char_name and clean_reply.startswith(f"{settings.char_name}:"):
        clean_reply = clean_reply[len(settings.char_name)+1:].strip()
    
    # Then, catch any other name patterns (like "Assistant:", etc.)
    name_pattern = r'^[A-Za-z]+:\s*'
    clean_reply = re.sub(name_pattern, '', clean_reply).strip()
    
    # Remove platform context markers
    clean_reply = re.sub(r'\[Platform:[^\]]*\]', '', clean_reply).strip()
    
    # For Twitch, we want to keep it conversational but not overly streaming-focused
    # Remove heavy streaming language but keep casual chat
    streaming_phrases = [
        "Thanks for watching", "Don't forget to follow", "Welcome to my stream",
        "Thanks for the follow", "Appreciate the subscription", "Welcome to the stream",
        "Welcome back to the stream", "stream has just ended", "thanks for watching"
    ]
    
    for phrase in streaming_phrases:
        if phrase.lower() in clean_reply.lower():
            return "Hey! How's it going?"
    
    # Remove action text in asterisks
    clean_reply = re.sub(r'\*[^*]*\*', '', clean_reply).strip()
    
    # Final fallback if response is empty
    if not clean_reply or clean_reply.strip() == "":
        return "Hi! Nice to see you!"
    
    return clean_reply

def clean_voice_response(response):
    """Clean responses for voice conversations (more natural, conversational)"""
    if not response:
        return ""
    
    clean_reply = response.strip()
    
    # Remove character name prefix if present - more robust matching
    import re
    from utils import settings
    
    # First, try to remove the configured character name specifically
    if settings.char_name and clean_reply.startswith(f"{settings.char_name}:"):
        clean_reply = clean_reply[len(settings.char_name)+1:].strip()
    
    # Then, catch any other name patterns (like "Assistant:", etc.)
    name_pattern = r'^[A-Za-z]+:\s*'
    clean_reply = re.sub(name_pattern, '', clean_reply).strip()
    
    # Remove platform context markers
    clean_reply = re.sub(r'\[Platform:[^\]]*\]', '', clean_reply).strip()
    
    # Remove streaming language completely for voice conversations
    streaming_phrases = [
        "Thanks for watching", "enjoying the stream", "Welcome to my stream",
        "Don't forget to follow", "Hey viewers", "Welcome to the stream", 
        "Thanks for the follow", "Appreciate the subscription", "Welcome everyone",
        "Hey stream", "What's up chat", "Hello viewers", "Thanks for being here",
        "Welcome back to the stream", "stream has just ended", "chatting with viewers",
        "glad you're enjoying the stream", "thanks for watching", "quiet in chat",
        "interacting online", "streaming", "stream", "viewers", "gameplay", 
        "joining us", "blast streaming", "new viewers"
    ]
    
    # Check for streaming language and replace entire response if found
    for phrase in streaming_phrases:
        if phrase.lower() in clean_reply.lower():
            return "Hey! How are you feeling today?"
    
    # Remove action text in asterisks for cleaner voice
    clean_reply = re.sub(r'\*[^*]*\*', '', clean_reply).strip()
    
    # Final fallback if response is empty
    if not clean_reply or clean_reply.strip() == "":
        return "Hey there! What's on your mind?"
    
    return clean_reply

def clean_minecraft_response(response):
    """Clean responses for Minecraft game chat (short, game-appropriate)"""
    if not response:
        return ""
    
    clean_reply = response.strip()
    
    # Remove character name prefix if present - more robust matching
    import re
    from utils import settings
    
    # First, try to remove the configured character name specifically
    if settings.char_name and clean_reply.startswith(f"{settings.char_name}:"):
        clean_reply = clean_reply[len(settings.char_name)+1:].strip()
    
    # Then, catch any other name patterns (like "Assistant:", etc.)
    name_pattern = r'^[A-Za-z]+:\s*'
    clean_reply = re.sub(name_pattern, '', clean_reply).strip()
    
    # Remove platform context markers
    clean_reply = re.sub(r'\[Platform:[^\]]*\]', '', clean_reply).strip()
    
    # Keep responses short for Minecraft chat (character limit)
    if len(clean_reply) > 100:
        clean_reply = clean_reply[:97] + "..."
    
    # Remove streaming language
    streaming_phrases = ["streaming", "stream", "viewers", "follow", "subscribe"]
    for phrase in streaming_phrases:
        if phrase.lower() in clean_reply.lower():
            return "Hey! What's up in the game?"
    
    # Final fallback if response is empty
    if not clean_reply or clean_reply.strip() == "":
        return "Hi! How's the game going?"
    
    return clean_reply

def clean_alarm_response(response):
    """Clean responses for alarm/reminder system (helpful, direct)"""
    if not response:
        return ""
    
    clean_reply = response.strip()
    
    # Remove character name prefix if present - more robust matching
    import re
    from utils import settings
    
    # First, try to remove the configured character name specifically
    if settings.char_name and clean_reply.startswith(f"{settings.char_name}:"):
        clean_reply = clean_reply[len(settings.char_name)+1:].strip()
    
    # Then, catch any other name patterns (like "Assistant:", etc.)
    name_pattern = r'^[A-Za-z]+:\s*'
    clean_reply = re.sub(name_pattern, '', clean_reply).strip()
    
    # Remove platform context markers
    clean_reply = re.sub(r'\[Platform:[^\]]*\]', '', clean_reply).strip()
    
    # Remove streaming language completely for alarms
    streaming_phrases = ["streaming", "stream", "viewers", "follow", "subscribe", "watching"]
    for phrase in streaming_phrases:
        if phrase.lower() in clean_reply.lower():
            return "Hey! Just wanted to remind you about something!"
    
    # Final fallback if response is empty
    if not clean_reply or clean_reply.strip() == "":
        return "Time for your reminder!"
    
    return clean_reply

def clean_hangout_response(response):
    """Clean responses for hangout mode (relaxed, casual, friendly)"""
    if not response:
        return ""
    
    clean_reply = response.strip()
    
    # Remove character name prefix if present - more robust matching
    import re
    from utils import settings
    
    # First, try to remove the configured character name specifically
    if settings.char_name and clean_reply.startswith(f"{settings.char_name}:"):
        clean_reply = clean_reply[len(settings.char_name)+1:].strip()
    
    # Then, catch any other name patterns (like "Assistant:", etc.)
    name_pattern = r'^[A-Za-z]+:\s*'
    clean_reply = re.sub(name_pattern, '', clean_reply).strip()
    
    # Remove platform context markers
    clean_reply = re.sub(r'\[Platform:[^\]]*\]', '', clean_reply).strip()
    
    # Remove streaming language but keep casual tone
    streaming_phrases = [
        "Thanks for watching", "Don't forget to follow", "Welcome to my stream",
        "Thanks for the follow", "Appreciate the subscription", "Welcome to the stream",
        "stream has just ended", "thanks for watching"
    ]
    
    for phrase in streaming_phrases:
        if phrase.lower() in clean_reply.lower():
            return "Hey! Just hanging out and chatting with you!"
    
    # Final fallback if response is empty
    if not clean_reply or clean_reply.strip() == "":
        return "Just chilling! What's up?"
    
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

    # Debug logging for tracking double printing
    try:
        if debug_mode:
            print(f"[DEBUG] main_web_ui_chat_worker starting with message: '{message}'")
    except:
        pass

    # Use platform-aware messaging for web UI
    clean_reply = send_platform_aware_message(message, platform="webui")
    
    if clean_reply and clean_reply.strip():
        # Update the history with the cleaned response
        if len(API.api_controller.ooga_history) > 0:
            API.api_controller.ooga_history[-1][1] = clean_reply
            API.api_controller.save_histories()
        
        # Debug logging before printing
        try:
            if debug_mode:
                print(f"[DEBUG] About to print clean_reply: '{clean_reply}'")
        except:
            pass
        
        # Print the cleaned response directly like main_text_chat does to avoid double printing
        banner_name = settings.char_name if settings.char_name else 'Assistant'
        print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
              + f"----{banner_name}----"
              + colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)
        print(clean_reply.strip())
        print()
        
        # Run plugin checks without the printing (using skip_print flag)
        message_checks(clean_reply, skip_print=True)

    # Reset suppression flag and run speech pipeline like other shadow chats
    settings.live_pipe_no_speak = False
    if settings.speak_shadowchats and not settings.stream_chats:
        main_message_speak(skip_message_checks=True)

def main_web_ui_next():
    """Handle regeneration requests from the web UI"""
    print("Generating Replacement Message!")
    
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

    # Generate new response using the same approach as initial messages
    try:
        # Get the last user message from history to regenerate response
        if len(API.api_controller.ooga_history) > 0:
            last_entry = API.api_controller.ooga_history[-1]
            last_user_message = last_entry[0] if len(last_entry) > 0 else ""
            
            if last_user_message:
                # Use the same platform-aware messaging as the original chat
                clean_reply = send_platform_aware_message(last_user_message, platform="webui")
                
                if clean_reply and clean_reply.strip():
                    # Update the history with the new response
                    API.api_controller.ooga_history[-1][1] = clean_reply
                    API.api_controller.save_histories()
                    
                    # Print the new response with banner
                    banner_name = settings.char_name if settings.char_name else 'Assistant'
                    print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
                          + f"----{banner_name}----"
                          + colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)
                    print(clean_reply.strip())
                    print()
                    
                    # Run plugin checks without additional printing
                    message_checks(clean_reply, skip_print=True)
                    
                    # Handle speech if configured
                    if settings.speak_shadowchats and not settings.stream_chats:
                        voice.speak(clean_reply)
            else:
                print("No previous message found to regenerate!")
    except Exception as e:
        print(f"Error during regeneration: {e}")
        
    # Reset suppression flag and run speech pipeline
    settings.live_pipe_no_speak = False
    if settings.speak_shadowchats and not settings.stream_chats:
        main_message_speak(skip_message_checks=True)

def main_discord_next():

    # This is a shadow chat
    # global settings.live_pipe_no_speak - not needed since settings is a module
    if (not settings.speak_shadowchats) and settings.stream_chats:
        settings.live_pipe_no_speak = True

    API.api_controller.next_message_oogabooga()

    # Run our message checks with Discord platform awareness
    reply_message = API.api_controller.receive_via_oogabooga()
    if reply_message and reply_message.strip():
        # Clean the response for Discord platform
        clean_reply = clean_discord_response(reply_message)
        
        # Update the history with the cleaned response
        if len(API.api_controller.ooga_history) > 0:
            API.api_controller.ooga_history[-1][1] = clean_reply
            API.api_controller.save_histories()
        
        message_checks(clean_reply)

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

    # Use platform-aware messaging for alarms
    clean_reply = send_platform_aware_message(alarm.get_alarm_message(), platform="alarm")

    # Run our message checks
    if clean_reply and clean_reply.strip():
        # Update the history with the cleaned response
        if len(API.api_controller.ooga_history) > 0:
            API.api_controller.ooga_history[-1][1] = clean_reply
            API.api_controller.save_histories()
        
        message_checks(clean_reply)

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

    # Use platform-aware messaging for image follow-up chat (voice context)
    clean_reply = send_platform_aware_message(message, platform="voice")

    # Run our message checks
    if clean_reply and clean_reply.strip():
        # Update the history with the cleaned response
        if len(API.api_controller.ooga_history) > 0:
            API.api_controller.ooga_history[-1][1] = clean_reply
            API.api_controller.save_histories()
        
        message_checks(clean_reply)

    # Pipe us to the reply function
    main_message_speak()


def main_send_blank():
    """Handle sending blank messages"""
    # Give us some feedback
    print("\nSending blank message...\n")

    # Send the actual blank message
    API.api_controller.send_via_oogabooga("")

    # Get the response
    reply_message = API.api_controller.receive_via_oogabooga()
    
    # Always process the response, even if it's empty
    # This ensures the interaction gets added to chat history for web UI
    if reply_message and reply_message.strip():
        # Clean the response for personal conversation (web UI/CMD context)
        clean_reply = clean_personal_response(reply_message)
        
        # Update the history with the cleaned response
        if len(API.api_controller.ooga_history) > 0:
            API.api_controller.ooga_history[-1][1] = clean_reply
            API.api_controller.save_histories()
        
        message_checks(clean_reply)
        # Speak the response if shadow chats are enabled
        if settings.speak_shadowchats:
            voice.speak(clean_reply)
    else:
        # Even with empty response, run message_checks to ensure proper logging
        message_checks(reply_message or "*nods quietly*")
        # Manually ensure the interaction is in history for web UI with blank input
        if len(API.api_controller.ooga_history) == 0 or API.api_controller.ooga_history[-1][0] != "":
            # Add the interaction to history if it wasn't added by the API
            API.api_controller.ooga_history.append([
                "", 
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

    # Use platform-aware messaging for hangout mode
    clean_reply = send_platform_aware_message(transcript, platform="hangout")

    # Run our message checks
    if clean_reply and clean_reply.strip():
        # Update the history with the cleaned response
        if len(API.api_controller.ooga_history) > 0:
            API.api_controller.ooga_history[-1][1] = clean_reply
            API.api_controller.save_histories()
        
        message_checks(clean_reply)

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

    # Use platform-aware messaging for hangout mode (but don't get response yet)
    API.api_controller.send_via_oogabooga(f"[Platform: Hangout Mode - Casual Conversation] {transcript}")

    live_pipe_use_streamed_interrupt_watchdog = False
    settings.live_pipe_no_speak = False

def hangout_wait_reply_replyportion():

    # wait for gen to finish
    while API.api_controller.is_in_api_request:
        time.sleep(0.01)

    # Run our message checks with hangout platform cleaning
    reply_message = API.api_controller.receive_via_oogabooga()
    if reply_message and reply_message.strip():
        # Clean the response for hangout platform
        clean_reply = clean_hangout_response(reply_message)
        
        # Update the history with the cleaned response
        if len(API.api_controller.ooga_history) > 0:
            API.api_controller.ooga_history[-1][1] = clean_reply
            API.api_controller.save_histories()
        
        message_checks(clean_reply)

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

def main_text_chat(transcript=None):
    """Handle chat messages from the text input"""
    
    # If no transcript passed as parameter, try the global variable (fallback)
    if transcript is None:
        global text_chat_input
        if debug_mode:
            print(f"[DEBUG] main_text_chat called with no parameter, text_chat_input = {repr(text_chat_input)}")
        
        if text_chat_input is None:
            print("Error: No text chat input was provided.")
            return
        
        transcript = text_chat_input
        text_chat_input = None  # Clear it immediately after capturing
    else:
        if debug_mode:
            print(f"[DEBUG] main_text_chat called with parameter: {repr(transcript)}")
    
    # Validate we have actual content
    if not transcript or not transcript.strip():
        print("Error: Text chat input was empty.")
        return

    # Print the transcript
    print('\r' + colorama.Fore.RED + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
          + "----Me----"
          + colorama.Fore.RED + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)
    print(f"{transcript.strip()}")
    print("\n")

    # Store the message, for cycling purposes
    global stored_transcript
    stored_transcript = transcript

    try:
        # Send the message with CMD platform context
        clean_reply = send_platform_aware_message(transcript, platform="cmd")
        
        if clean_reply and clean_reply.strip():
            # Print the cleaned response directly (no double output via message_checks)
            banner_name = char_name if char_name else 'Assistant'
            print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
                  + f"----{banner_name}----"
                  + colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)
            print(clean_reply.strip())
            print()
            
            # Run plugin checks without the printing (using skip_print flag)
            message_checks(clean_reply, skip_print=True)
            
            # Handle TTS directly with the already cleaned message
            if clean_reply.strip():
                s_message = emoji.replace_emoji(clean_reply, replace="")
                if s_message.strip():
                    t = threading.Thread(target=voice.speak_line, args=(s_message,), kwargs={"refuse_pause": False})
                    t.daemon = True
                    t.start()
                    
                    # Wait until speaking finishes to prevent overlap with next TTS
                    while voice.check_if_speaking():
                        time.sleep(0.01)
        
    except Exception as e:
        print(f"{colorama.Fore.RED}Error processing text chat: {e}{colorama.Fore.RESET}")
        zw_logging.log_error(f"Text chat processing error: {e}")

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

    # Load in our chatpops - use environment variable to potentially override
    chatpops_enabled_string = os.environ.get("USE_CHATPOPS")
    if chatpops_enabled_string == "ON":
        settings.use_chatpops = True
    elif chatpops_enabled_string == "OFF":
        settings.use_chatpops = False
    # If not set in environment, keep the current setting from settings.py
    
    # Chatpops are already loaded in settings.py, no need to reload them here
    # The loading in settings.py handles the JSON file properly with error handling


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

    # Announce that the program is running and verify system integration
    print(f"{colorama.Fore.GREEN}Welcome back! Loading chat interface...{colorama.Fore.RESET}\n")
    
    # Verify that all enhanced components are working together
    verify_system_integration()
    
    # Process startup message if provided (after all systems are ready)
    if startup_message:
        try:
            process_startup_message()
        except Exception as e:
            print(f"{colorama.Fore.RED}Error processing startup message: {e}{colorama.Fore.RESET}")
            zw_logging.log_error(f"Startup message error: {e}")

    # Run the primary loop with error handling
    try:
        print(f"{colorama.Fore.CYAN}Z-WAIF is ready with enhanced natural chatpops!{colorama.Fore.RESET}")
        print(f"{colorama.Fore.GREEN}💬 Type messages to chat with AI")
        print(f"🎛️ Use /help for console commands")
        print(f"⌨️ Hotkeys use Ctrl+letter or Alt+letter combinations")
        print(f"🗣️ Enhanced contextual chatpops will make conversations more natural")
        print(f"🔓 Console typing now works without hotkey interference!{colorama.Fore.RESET}\n")
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

