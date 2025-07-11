# Standard library imports
import asyncio
import datetime
import os
import json
import sys
import threading
import time

# Ensure project root is in sys.path for module resolution
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"[Main] Added project root {project_root} to sys.path")

# Third-party imports
import colorama
import emoji
import humanize
from dotenv import load_dotenv

# Local imports - API modules
import API.api_controller
import API.character_card as character_card
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
        
        print(f"[DEBUG] Processing startup message: {repr(message)}")
        
        # Process the message directly like main_text_chat does
        print('\r' + colorama.Fore.RED + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
              + "----Me----"
              + colorama.Fore.RED + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)
        print(f"{message.strip()}")
        print("\n")

        # Store the message, for cycling purposes
        global stored_transcript
        stored_transcript = message

        print(f"[DEBUG] About to call send_platform_aware_message")
        # Use the enhanced platform-aware messaging system
        clean_reply = send_platform_aware_message(message, platform="cmd")
        print(f"[DEBUG] send_platform_aware_message returned: {repr(clean_reply)}")
        
        if clean_reply and clean_reply.strip():
            print(f"[DEBUG] About to call message_checks")
            message_checks(clean_reply)
            print(f"[DEBUG] message_checks completed")

        # Speak the reply
        print(f"[DEBUG] About to call main_message_speak")
        main_message_speak()
        print(f"[DEBUG] main_message_speak completed")
        
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
        # Reset the old history system to just the default greeting
        fresh_history = [["Hello, I am back!", "Welcome back! *smiles*"]]
        
        # Save to LiveLog.json (old system)
        import json
        with open("LiveLog.json", 'w') as outfile:
            json.dump(fresh_history, outfile, indent=4)
        
        # Clear the in-memory old history
        API.api_controller.ooga_history = fresh_history
        
        # Clear the new platform-separated chat histories
        from utils.chat_history import clear_all_histories
        clear_all_histories()
        
        print(f"{colorama.Fore.GREEN}✅ Conversation history cleared successfully!")
        print(f"🔄 Chat has been reset to fresh start")
        print(f"🗑️ Cleared both old and platform-separated histories{colorama.Fore.RESET}")
        
    except Exception as e:
        print(f"{colorama.Fore.RED}❌ Error clearing history: {e}{colorama.Fore.RESET}")
        import traceback
        traceback.print_exc()


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
        # Use thread pool to prevent thread leak - only start if no emote processing is active
        if not hasattr(vtube_studio, '_emote_thread_active') or not vtube_studio._emote_thread_active:
            vtube_studio._emote_thread_active = True
            vtube_thread = threading.Thread(target=_safe_vtube_emote_check)
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


def _safe_vtube_emote_check():
    """Thread-safe wrapper for vtube emote checking to prevent thread leaks"""
    try:
        vtube_studio.check_emote_string()
    except Exception as e:
        print(f"Error in vtube emote check: {e}")
        zw_logging.log_error(f"VTube emote check error: {e}")
    finally:
        # Always reset the flag to allow future threads
        vtube_studio._emote_thread_active = False


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
            
            # Run message checks which handles speaking automatically
            message_checks(clean_reply)
            # Note: Removed main_message_speak() call to prevent double speaking
            
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
            
            # Run message checks which handles speaking automatically  
            message_checks(clean_reply)
            # Note: Removed main_message_speak() call to prevent double speaking
            return clean_reply  # Return the cleaned response for Twitch bot to send
        return ""  # Return empty string if no response

def send_platform_aware_message(message, platform="cmd"):
    """Send a message with platform context"""
    from API.api_controller import run
    
    # Map platform names to the format expected by API controller
    platform_mapping = {
        "cmd": "Command Line",
        "webui": "Web Interface",
        "twitch": "Twitch Chat",
        "discord": "Discord",
        "voice": "Voice Chat",
        "minecraft": "Minecraft",
        "hangout": "Hangout Mode - Casual Conversation",
        "alarm": "Alarm/Reminder System"
    }
    
    mapped_platform = platform_mapping.get(platform, platform)
    platform_message = f"[Platform: {mapped_platform}] {message}"
    print(f"[DEBUG] send_platform_aware_message calling run with: {repr(platform_message)}")
    try:
        result = run(platform_message, settings.temp_level)
        print(f"[DEBUG] run returned: {repr(result)}")
        return result
    except Exception as e:
        print(f"[DEBUG] run threw exception: {e}")
        raise e

def main_web_ui_chat(message):
    """Handle chat messages from web UI"""
    from utils.web_ui import process_web_input
    return process_web_input(message, user_id="webui_user")

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
            banner_name = settings.char_name if settings.char_name else 'Assistant'
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
        colorama.init(autoreset=True)
        
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

    # ------------------------------------------------------------------
    # Automatic environment / daemon detection (mirrors upstream logic)
    # ------------------------------------------------------------------
    print(f"{colorama.Fore.CYAN}🔧 [PRE] Auto-configuring environment...{colorama.Fore.RESET}")
    try:
        settings.auto_detect_flash_attn_compatibility()
        settings.auto_detect_model_name()
        settings.auto_detect_vtube()
        settings.auto_detect_img()
        settings.auto_detect_character_names()
        settings.ensure_ollama_host()
        settings.auto_detect_and_set_ollama_model()
        settings.auto_detect_oobabooga()
        settings.ensure_daemons_running()
        settings.auto_configure_api_priority()
        settings.check_all_daemons_and_print_status()
        print(f"{colorama.Fore.GREEN}✅ [PRE] Auto-configuration complete{colorama.Fore.RESET}")
    except Exception as e:
        print(f"{colorama.Fore.YELLOW}⚠️ Auto-configuration had some issues: {e}{colorama.Fore.RESET}")
        print(f"{colorama.Fore.CYAN}Continuing with manual configuration...{colorama.Fore.RESET}")

    #
    # Startup Prep
    #

    # Load any available character cards
    character_card.load_char_card()

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
    settings.autochat_mininum_chat_frames = int(os.environ.get("AUTOCHAT_MIN_LENGTH", "100"))

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
    chunky_transcription = threading.Thread(target=transcriber_translate.chunky_transcription_loop)
    chunky_transcription.daemon = True
    chunky_transcription.start()

    # Start another thread for Gradio
    gradio_thread = threading.Thread(target=web_ui.launch_demo)
    gradio_thread.daemon = True
    gradio_thread.start()

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
        # Cleanup HTTP sessions to prevent resource leaks
        try:
            from API.oobaooga_api import close_http_session
            close_http_session()
            print("HTTP sessions closed cleanly")
        except ImportError:
            pass  # Module might not be available
        sys.exit(0)
    except Exception as e:
        print(f"{colorama.Fore.RED}Critical error in main loop: {e}{colorama.Fore.RESET}")
        zw_logging.log_error(f"Main loop critical error: {e}")
        # Cleanup HTTP sessions even on error
        try:
            from API.oobaooga_api import close_http_session
            close_http_session()
        except ImportError:
            pass  # Module might not be available
        print("Check log.txt for details")
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    try:
        # Initialize settings early
        from utils import settings
        settings.initialize_settings()

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
