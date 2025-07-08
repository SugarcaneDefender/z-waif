# Standard library imports
import base64
import datetime
import html
import json
import os
import random
import threading
import time
from pathlib import Path

# Third-party imports
import colorama
import emoji
import requests
import sseclient
from dotenv import load_dotenv
from ollama import chat, ChatResponse

# Local imports - API modules
import API.character_card as character_card

# Dynamic API import based on API_TYPE
load_dotenv()  # Load environment variables first
API_TYPE = os.environ.get("API_TYPE", "Oobabooga")

if API_TYPE == "Ollama":
    import API.ollama_api as API
else:  # Default to Oobabooga
    import API.oobaooga_api as API

# Local imports - Main module
import main

# Local imports - Utils modules
from utils import based_rag
from utils import cane_lib
from utils import hangout
from utils import hotkeys
from utils import lorebook
from utils import retrospect
from utils import settings
from utils import tag_task_controller
from utils import voice
from utils import voice_splitter
from utils import vtube_studio
from utils import zw_logging

# Import enhanced AI handler
from utils.ai_handler import AIHandler

HOST = os.environ.get("HOST_PORT", "127.0.0.1:49493")
# Handle both URL and host:port formats (http only, no https support yet)
if HOST.startswith("http://"):
    URI = f'{HOST}/v1/chat/completions'
    URL_MODEL = f'{HOST}/v1/engines/'
else:
    URI = f'http://{HOST}/v1/chat/completions'
    URL_MODEL = f'http://{HOST}/v1/engines/'

IMG_HOST = os.environ.get("IMG_HOST", "127.0.0.1")
IMG_PORT = os.environ.get("IMG_PORT", "5007")
IMG_URI = f'http://{IMG_HOST}:{IMG_PORT}/v1/chat/completions'
IMG_URL_MODEL = f'http://{IMG_HOST}:{IMG_PORT}/v1/engines/'

received_message = ""
# Use environment character card setting or None to use system messages
CHARACTER_CARD = os.environ.get("CHARACTER_CARD", None)
YOUR_NAME = os.environ.get("YOUR_NAME")

API_TYPE = os.environ.get("API_TYPE")
API_TYPE_VISUAL = os.environ.get("API_TYPE_VISUAL")

history_loaded = False

ooga_history = [ ["Hello, I am back!", "Welcome back! *smiles*"] ]

headers = {
    "Content-Type": "application/json"
}

max_context = int(os.environ.get("TOKEN_LIMIT", "4096"))
marker_length = int(os.environ.get("MESSAGE_PAIR_LIMIT", "30"))

force_token_count = False
forced_token_level = 120

stored_received_message = "None!"
currently_sending_message = ""
currently_streaming_message = ""
last_message_received_has_own_name = False
last_message_streamed = False
streaming_sentences_ticker = 0

regenerate_requests_count = 0
regenerate_requests_limit = 5

force_skip_streaming = False
flag_end_streaming = False

is_in_api_request = False

ENCODE_TIME = os.environ.get("TIME_IN_ENCODING")

OOBA_VISUAL_CHARACTER_NAME = os.environ.get("VISUAL_CHARACTER_NAME")
OOBA_VISUAL_PRESET_NAME = os.environ.get("VISUAL_PRESET_NAME")

OLLAMA_VISUAL_ENCODE_GUIDANCE = os.environ.get("OLLAMA_VISUAL_ENCODE_GUIDANCE")
OLLAMA_VISUAL_CARD = os.environ.get("OLLAMA_VISUAL_CARD")

vision_guidance_message = "There is an image attached to this message! Describe what details you see, and comment on what you think of the features, while keeping in role and continuing the conversation!"

# Initialize enhanced AI handler
ai_handler = AIHandler()

# Load in the configurable SoftReset message
with open("Configurables/SoftReset.json", 'r') as openfile:
    soft_reset_message = json.load(openfile)

# Load in the stopping strings
with open("Configurables/StoppingStrings.json", 'r') as openfile:
    settings.stopping_strings = json.load(openfile)


def run(user_input, temp_level):
    global received_message
    global ooga_history
    global is_in_api_request

    # Force character card reload before each API call
    print("[API] Checking character card status...")
    character_card.load_char_card()
    
    # Handle blank input - allow blank messages to be sent as blank messages
    original_user_input = user_input
    if not user_input or user_input.strip() == "":
        zw_logging.update_debug_log("API 'run' received blank input. Sending blank message.")
        # Allow blank messages to be processed normally 

    # We are starting our API request!
    is_in_api_request = True
    
    try:
        # Extract platform from user input to get the correct conversation history
        platform = "personal"
        user_id = "default"
        
        if "[Platform: Twitch Chat]" in original_user_input:
            platform = "twitch"
            user_id = "twitch_user"
        elif "[Platform: Discord]" in original_user_input:
            platform = "discord"
            user_id = "discord_user"
        elif "[Platform: Web Interface" in original_user_input:
            platform = "webui"
            user_id = "webui_user"
        elif "[Platform: Command Line" in original_user_input:
            platform = "cmd"
            user_id = "cmd_user"
        elif "[Platform: Voice Chat" in original_user_input:
            platform = "voice"
            user_id = "voice_user"
        elif "[Platform: Minecraft" in original_user_input:
            platform = "minecraft"
            user_id = "minecraft_user"
        elif "[Platform: Hangout" in original_user_input:
            platform = "hangout"
            user_id = "hangout_user"
        
        # Load platform-specific conversation history instead of old LiveLog.json
        try:
            from utils.chat_history import get_chat_history
            platform_history = get_chat_history(user_id, platform, limit=20)  # Get last 20 messages
            
            # Convert platform history to old format for backward compatibility
            ooga_history = []
            current_pair = [None, None]
            
            for msg in platform_history:
                if msg["role"] == "user":
                    if current_pair[0] is not None:
                        # Save incomplete pair and start new one
                        ooga_history.append([current_pair[0], current_pair[1] or ""])
                    current_pair = [msg["content"], None]
                elif msg["role"] == "assistant":
                    current_pair[1] = msg["content"]
                    ooga_history.append([current_pair[0] or "", current_pair[1]])
                    current_pair = [None, None]
            
            # Add any incomplete pair
            if current_pair[0] is not None:
                ooga_history.append([current_pair[0], current_pair[1] or ""])
            
            # Ensure we have at least the default greeting if history is empty
            if not ooga_history:
                ooga_history = [["Hello, I am back!", "Welcome back! *smiles*"]]
                
            print(f"[API] Loaded {len(ooga_history)} conversation pairs from platform-separated history ({platform})")
            
        except Exception as e:
            print(f"[API] Warning: Could not load platform history, falling back to LiveLog.json: {e}")
            # Fallback to old method
            try:
                with open("LiveLog.json", 'r') as openfile:
                    ooga_history = json.load(openfile)
            except Exception as e2:
                zw_logging.log_error(f"Failed to load LiveLog.json: {e2}")
                ooga_history = [["Hello, I am back!", "Welcome back! *smiles*"]]

        # Debug: Check character card status
        try:
            import main
            if main.debug_mode:
                zw_logging.update_debug_log(f"Character card status: {character_card.character_card[:100]}...")
                zw_logging.update_debug_log(f"API_TYPE: {API_TYPE}")
                zw_logging.update_debug_log(f"Using API module: {API.__name__}")
        except (ImportError, AttributeError):
            pass

        # Check for name in message
        check_for_name_in_message(user_input)
        
        # Enhanced Contextual Chatpop Check for non-streaming mode
        chatpop_prefix = ""  # Store chatpop to include in response text
        if settings.use_chatpops and not settings.live_pipe_no_speak:
            # Determine platform context from the currently sending message
            platform_context = {"platform": "personal"}  # Default
            if "[Platform: Twitch Chat]" in user_input:
                platform_context["platform"] = "twitch"
            elif "[Platform: Discord]" in user_input:
                platform_context["platform"] = "discord"
            elif "[Platform: Minecraft Game Chat]" in user_input:
                platform_context["platform"] = "minecraft"
            elif "[Platform: Voice Chat" in user_input:
                platform_context["platform"] = "voice"
            elif "[Platform: Web Interface" in user_input:
                platform_context["platform"] = "webui"
            elif "[Platform: Command Line" in user_input:
                platform_context["platform"] = "cmd"
            
            # Get contextual chatpop based on user input and platform
            this_chatpop = ai_handler.get_contextual_chatpop(platform_context, user_input)
            print(f"[API] Generated chatpop: '{this_chatpop}'")
            
            # Store chatpop to include in response text (but don't speak it immediately)
            chatpop_prefix = this_chatpop
            
            # REMOVED: voice.speak_line(this_chatpop, refuse_pause=True) - Let calling code handle speech
        
        # Debug: Show connection info
        print(f"[API] HOST: {HOST}")
        print(f"[API] API_TYPE: {API_TYPE}")
        print(f"[API] URI would be: http://{HOST}/v1/chat/completions")
        
        # Simple API call using unified interface
        try:
            print(f"[API] About to call API.api_call with user_input: '{user_input[:50]}...'")
            
            # Use the module-level API import directly
            received_message = API.api_call(
                user_input=user_input,
                temp_level=temp_level,
                max_tokens=settings.max_tokens,  # Use configurable value instead of hard-coding
                streaming=False
            )
            
            print(f"[API] API.api_call returned: '{received_message[:50] if received_message else 'None'}...'")
        except Exception as e:
            print(f"[API] Exception in API.api_call: {e}")
            zw_logging.log_error(f"API request failed: {e}")
            received_message = "Sorry, I'm having connection issues right now."

        # Simple post-processing
        if received_message:
            received_message = html.unescape(received_message)
            if settings.supress_rp:
                received_message = supress_rp_as_others(received_message)
            
            # Add chatpop prefix to the response if we generated one
            if chatpop_prefix:
                received_message = f"{chatpop_prefix} {received_message}"
                print(f"[API] Added chatpop prefix to response: '{received_message[:100]}...'")
            
            # Note: Don't speak here in non-streaming mode - let the calling code handle speech
            # to prevent double speaking. The calling functions (main_web_ui_chat_worker, etc.)
            # will handle speaking appropriately for their context.
            
            # Reset volume cooldown to prevent AI from picking up on its own voice
            try:
                hotkeys.cooldown_listener_timer()
            except AttributeError:
                pass  # Function might not exist in some configurations
        else:
            received_message = "I'm having trouble responding right now."

        # Save to platform-separated history (already extracted platform info above)
        try:
            # Save to platform-separated history (save the full response with chatpop)
            from utils.chat_history import add_message_to_history
            
            # Clean the user input by removing platform markers for cleaner history
            clean_user_input = original_user_input
            if "[Platform:" in clean_user_input:
                import re
                clean_user_input = re.sub(r'\[Platform:[^\]]*\]\s*', '', clean_user_input).strip()
            
            add_message_to_history(user_id, "user", clean_user_input, platform)
            add_message_to_history(user_id, "assistant", received_message, platform)
            
            print(f"[API] Saved conversation to platform-separated history: {platform}")
            
            # Also save to old format for backward compatibility (but use the new data)
            ooga_history.append([original_user_input, received_message])
            save_histories()
            
        except Exception as e:
            print(f"[API] Error saving to platform history: {e}")
            # Fallback to original method if platform history fails
            ooga_history.append([original_user_input, received_message])
            save_histories()
    
    finally:
        # CRITICAL: Always reset the flag, even if exceptions occur
        is_in_api_request = False

    return received_message

#
# For the new streaming chats, runs it continually to grab data as it comes in from Oobabooga. Should run faster
#
def run_streaming(user_input, temp_level, recursion_depth=0):

    global received_message
    global ooga_history
    global forced_token_level
    global force_token_count
    global currently_sending_message
    global currently_streaming_message
    global last_message_streamed
    global streaming_sentences_ticker
    global force_skip_streaming
    global is_in_api_request

    # SAFETY: Prevent infinite recursion
    MAX_RECURSION_DEPTH = 3
    if recursion_depth >= MAX_RECURSION_DEPTH:
        print(f"[API] WARNING: Maximum recursion depth ({MAX_RECURSION_DEPTH}) reached, stopping recursion")
        zw_logging.log_error(f"Maximum streaming recursion depth reached: {recursion_depth}")
        is_in_api_request = False
        return "I'm having trouble generating a response right now."

    # Handle blank input - allow blank messages to be sent as blank messages
    original_user_input = user_input
    if not user_input or user_input.strip() == "":
        zw_logging.update_debug_log("API 'run_streaming' received blank input. Sending blank message.")
        # Allow blank messages to be processed normally 

    # We are starting our API request!
    is_in_api_request = True

    try:
        # Ensure the streamed_api_stringpuller variable exists even if the API request fails to initialize.
        streamed_api_stringpuller = []

        # Clear possible streaming endflag
        global flag_end_streaming
        flag_end_streaming = False

        # Message that is currently being sent
        currently_sending_message = user_input

        # Clear the old streaming message
        currently_streaming_message = ""
        last_message_streamed = True

        # Did the last message we got contain our name?
        check_for_name_in_message(user_input)

        # Load the history from JSON, to clean up the quotation marks
        with open("LiveLog.json", 'r') as openfile:
            ooga_history = json.load(openfile)

        # Determine what preset we want to load in with
        preset = 'Z-Waif-ADEF-Standard'
        if random.random() > 0.77:
            preset = 'Z-Waif-ADEF-Tempered'
        if random.random() > 0.99:
            preset = 'Z-Waif-ADEF-Blazing'

        if temp_level == 1:
            preset = 'Z-Waif-ADEF-Tempered'
            if random.random() > 0.7:
                preset = 'Z-Waif-ADEF-Blazing'
        if temp_level == 2:
            preset = 'Z-Waif-ADEF-Blazing'

        if settings.model_preset != "Default":
            preset = settings.model_preset

        zw_logging.kelvin_log = preset

        # Set what char/task we are sending to - force None to use our character card
        char_send = settings.cur_task_char
        if char_send == "None":
            char_send = None  # Don't use backend character, use our system messages

        # Forced tokens check
        cur_tokens_required = settings.max_tokens
        if force_token_count:
            cur_tokens_required = forced_token_level

        # Set the stop right
        stop = settings.stopping_strings.copy()
        if settings.newline_cut:
            stop.append("\n")
        if settings.asterisk_ban:
            stop.append("*")

        # We will print the header only when we receive the first chunk,
        # avoiding an empty name banner if the request fails.
        header_printed = False

        # Reset the ticker (starts counting at 1)
        streaming_sentences_ticker = 1

        # Send the actual API Request using unified interface
        streamed_api_stringpuller = API.api_call(
            user_input=user_input,
            temp_level=temp_level,
            max_tokens=cur_tokens_required,
            streaming=True,
            preset=preset,
            char_send=char_send,
            stop=stop
        )

        # Clear streamed emote list
        vtube_studio.clear_streaming_emote_list()

        # Enhanced Contextual Chatpop Check
        streaming_chatpop_prefix = ""  # Store chatpop to include in response text
        if settings.use_chatpops and not settings.live_pipe_no_speak:
            voice.set_speaking(True)
            # Determine platform context from the currently sending message
            platform_context = {"platform": "personal"}  # Default
            if "[Platform: Twitch Chat]" in user_input:
                platform_context["platform"] = "twitch"
            elif "[Platform: Discord]" in user_input:
                platform_context["platform"] = "discord"
            elif "[Platform: Minecraft Game Chat]" in user_input:
                platform_context["platform"] = "minecraft"
            elif "[Platform: Voice Chat" in user_input:
                platform_context["platform"] = "voice"
            elif "[Platform: Web Interface" in user_input:
                platform_context["platform"] = "webui"
            elif "[Platform: Command Line" in user_input:
                platform_context["platform"] = "cmd"
            
            # Get contextual chatpop based on user input and platform
            this_chatpop = ai_handler.get_contextual_chatpop(platform_context, user_input)
            print(f"[API] Generated streaming chatpop: '{this_chatpop}'")
            
            # Store chatpop to include in response text (but don't speak it immediately)
            streaming_chatpop_prefix = this_chatpop
            
            # REMOVED: voice.speak_line(this_chatpop, refuse_pause=True) - Let calling code handle speech


        assistant_message = ''
        supressed_rp = False
        force_skip_streaming = False
        for event in streamed_api_stringpuller:
            # Extract chunk using unified API interface
            chunk = API.extract_streaming_chunk(event)

            # On first chunk, print the speaker header so output isn't blank beforehand
            if not header_printed:
                print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
                      + "----" + settings.char_name + "----"
                      + colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)
                header_printed = True

            assistant_message += chunk
            streamed_response_check = streamed_update_handler(chunk, assistant_message)

            # IF we break out, then make sure we cancel out properly
            if streamed_response_check == "Cut":
                # Clear the currently sending message variable
                currently_sending_message = ""

                # We are ending our API request!
                is_in_api_request = False

                return

            # Cut for the hangout name being said
            if streamed_response_check == "Hangout-Name-Cut" and settings.hangout_mode:
                # Add any existing stuff to our actual chat history (use original input, not converted)
                ooga_history.append([original_user_input, assistant_message, settings.cur_tags,
                                     "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())])
                save_histories()

                # Remove flag
                flag_end_streaming = False

                # Clear the currently sending message variable
                currently_sending_message = ""

                # We are ending our API request!
                is_in_api_request = False

                return

            # Check if we need to force skip the stream (hotkey or manually)
            if hotkeys.pull_next_press_input() or force_skip_streaming:
                force_skip_streaming = True
                break

            # Check if we need to break out due to RP suppression (if it different, then there is a suppression)
            if settings.supress_rp and (supress_rp_as_others(assistant_message) != assistant_message):
                assistant_message = supress_rp_as_others(assistant_message)
                supressed_rp = True
                break

        # Redo it and skip - FIXED: Add recursion depth check
        if force_skip_streaming:
            force_skip_streaming = False
            print("\nSkipping message, redoing!\n")
            zw_logging.update_debug_log("Got an input to regenerate! Re-generating the reply...")
            # SAFETY: Check recursion depth before recursive call
            if recursion_depth < MAX_RECURSION_DEPTH - 1:
                return run_streaming(user_input, 1, recursion_depth + 1)
            else:
                print(f"[API] WARNING: Cannot retry, max recursion depth reached")
                is_in_api_request = False
                return "I'm having trouble generating a response right now."

        # Read the final sentence aloud (if it wasn't suppressed because of anti-RP rules)
        if not supressed_rp:
            s_assistant_message = emoji.replace_emoji(assistant_message, replace='')
            sentence_list = voice_splitter.split_into_sentences(s_assistant_message)

            # Emotes
            if settings.vtube_enabled:
                vtube_studio.set_emote_string(s_assistant_message)
                vtube_studio.check_emote_string_streaming()

            # Speaking
            if not settings.live_pipe_no_speak and len(sentence_list) > 0:
                voice.set_speaking(True)
                voice.speak_line(sentence_list[-1], refuse_pause=True)

        # Print Newline
        print("\n")

        #
        # Set it to the assistant message (streamed response)
        received_message = assistant_message

        # Translate issues with the received message
        received_message = html.unescape(received_message)
        
        # Add streaming chatpop prefix to the response if we generated one
        if streaming_chatpop_prefix:
            received_message = f"{streaming_chatpop_prefix} {received_message}"
            print(f"[API] Added streaming chatpop prefix to response: '{received_message[:100]}...'")

        # If her reply is the same as the last stored one, run another request
        global stored_received_message
        global regenerate_requests_count

        if received_message == stored_received_message and regenerate_requests_count < regenerate_requests_limit:
            print("\nBad message, will retry via fallback!\n")
            zw_logging.update_debug_log("Bad message received; same as last attempted generation. Delegating retry to caller...")
            regenerate_requests_count += 1
            # We are ending our API request!
            is_in_api_request = False
            return ""

        stored_received_message = received_message

        # If her reply is the same as any in the past 20 chats, run another request
        if check_if_in_history(received_message) and regenerate_requests_count < regenerate_requests_limit:
            print("\nBad message matches recent chat, delegating retry to caller!\n")
            zw_logging.update_debug_log("Bad message received; same as a recent chat. Delegating retry to caller...")
            regenerate_requests_count += 1
            is_in_api_request = False
            return ""

        # If her reply is blank, request another run, clearing the previous history add, and escape - FIXED: Add recursion depth check
        if len(received_message) < 3 and regenerate_requests_count < regenerate_requests_limit:
            print("\nBad (blank) message, delegating retry to caller!\n")
            zw_logging.update_debug_log("Bad message received; chat is a runt or blank entirely. Delegating retry to caller...")
            regenerate_requests_count += 1
            # SAFETY: Check recursion depth before recursive call
            if recursion_depth < MAX_RECURSION_DEPTH - 1:
                return run_streaming((user_input + " Hmm."), 1, recursion_depth + 1)
            else:
                print(f"[API] WARNING: Cannot retry blank message, max recursion depth reached")
                is_in_api_request = False
                return "I'm having trouble generating a response right now."

        # Clear our regen requests count, we have hit our limit
        regenerate_requests_count = 0

        # Log it to our history. Ensure it is in double quotes, that is how OOBA stores it natively (use original input, not converted)
        log_user_input = "{0}".format(original_user_input)
        log_received_message = "{0}".format(received_message)

        ooga_history.append([log_user_input, log_received_message, tag_task_controller.apply_tags(), "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())])

        # Run a pruning of the deletables
        prune_deletables()

        # Clear the currently sending message variable
        currently_sending_message = ""

        # Clear any token forcing
        force_token_count = False

        # Save
        save_histories()

    finally:
        # CRITICAL: Always reset the flag, even if exceptions occur
        is_in_api_request = False


def streamed_update_handler(chunk, assistant_message):
    global currently_streaming_message
    global streaming_sentences_ticker

    # Update our two live text output spots
    print(chunk, end='', flush=True)

    currently_streaming_message = assistant_message
    s_assistant_message = emoji.replace_emoji(assistant_message, replace='')

    # Check if the generated update has added a new sentence.
    # If a complete new sentence is found, read it aloud
    sentence_list = voice_splitter.split_into_sentences(s_assistant_message)
    if len(sentence_list) > streaming_sentences_ticker and not settings.live_pipe_no_speak:
        # Emotes for VTube Studio
        if settings.vtube_enabled:
            vtube_studio.set_emote_string(sentence_list[streaming_sentences_ticker - 1])
            vtube_studio.check_emote_string_streaming()

        # Speaking with RVC support
        if settings.use_rvc and not settings.live_pipe_no_speak:
            try:
                # Use RVC for voice conversion
                voice.set_speaking(True)
                voice.speak_line_rvc(sentence_list[streaming_sentences_ticker - 1], refuse_pause=False)
            except Exception as e:
                zw_logging.update_debug_log(f"RVC error: {str(e)}, falling back to default voice")
                # Fallback to default voice if RVC fails
                voice.speak_line(sentence_list[streaming_sentences_ticker - 1], refuse_pause=False)
        else:
            # Use default voice
            voice.set_speaking(True)
            voice.speak_line(sentence_list[streaming_sentences_ticker - 1], refuse_pause=False)

        streaming_sentences_ticker += 1

        # Check for hangout name
        if settings.hangout_mode and hangout.check_for_name_in_message(sentence_list[streaming_sentences_ticker - 1]):
            return "Hangout-Name-Cut"

    # Check for next press
    if hotkeys.pull_next_press_input():
        voice.force_cut_voice()
        return "Cut"

    return "Continue"


def set_force_skip_streaming(tf_input):
    global force_skip_streaming
    force_skip_streaming = tf_input


def send_via_oogabooga(user_input):
    """Send a message to the API"""
    print(f"[API] 'send_via_oogabooga' received user_input: '{user_input}'")
    print(f"[API] About to call API.api_call...")
    
    global received_message
    global force_skip_streaming

    # Check if we should stream or not
    if settings.stream_chats and not force_skip_streaming:
        print(f"[API] Using streaming mode")
        # Attempt streaming first
        local_stream_result = run_streaming(user_input, 0.8)  # Slightly higher temp for more engaging responses

        # `run_streaming` updates the module-level `received_message` variable but does
        # not always return it.  Prefer the global value if the direct return is None.
        received_message = local_stream_result if local_stream_result else received_message
        print(f"[API] Streaming call finished. Received message: '{received_message}'")

        # Fallback: if no message was produced at all, retry with a standard request
        if not received_message or len(str(received_message).strip()) == 0:
            zw_logging.update_debug_log("Streaming response was empty – retrying with standard (non-streaming) request…")
            received_message = run(user_input, 0.8)  # Slightly higher temp for more engaging responses
            print(f"[API] Fallback non-streaming call finished. Received message: '{received_message}'")
    else:
        print(f"[API] Using non-streaming mode")
        try:
            received_message = run(user_input, 0.8)  # Slightly higher temp for more engaging responses
            print(f"[API] Non-streaming call finished. Received message: '{received_message}'")
        except Exception as e:
            print(f"[API] Exception in run() function: {e}")
            received_message = f"Error in API call: {e}"

    # Debug: Check if message was added to history
    print(f"[API] Chat history length after processing: {len(ooga_history)}")
    if len(ooga_history) > 0:
        print(f"[API] Last history entry: {ooga_history[-1][:2]}")  # Show only user message and response

    force_skip_streaming = False
    return received_message

def receive_via_oogabooga():
    """Get the last received message"""
    global received_message
    return received_message or ""

def send_image_via_oobabooga(direct_talk_transcript):

    received_cam_message = ""
    if not settings.stream_chats:
        received_cam_message = view_image(direct_talk_transcript)
    if settings.stream_chats:
        received_cam_message = view_image_streaming(direct_talk_transcript)

    return received_cam_message

def send_image_via_oobabooga_hangout(direct_talk_transcript):

    received_cam_message = view_image_streaming(direct_talk_transcript)

    return received_cam_message


def next_message_oogabooga():
    global ooga_history

    # Record & Clear the old message

    print("Generating Replacement Message!")
    cycle_message = ooga_history[-1][0]
    cycle_tag = ooga_history[-1][2]
    ooga_history.pop()

    # Save
    save_histories()

    # If there was an image tag on the last sent message, use the liveimage and visual.
    # Otherwise, redo as normal

    if cycle_tag.__contains__("ZW-Visual"):

        print("\nRerolling for visual\n")

        # Re-send the new message (visual)
        if not settings.stream_chats:
            view_image(cycle_message)
        if settings.stream_chats:
            view_image_streaming(cycle_message)

        # 'scape from it
        return


    # Re-send the new message
    if not settings.stream_chats:
        run(cycle_message, 0)
    if settings.stream_chats:
        run_streaming(cycle_message, 0)


def undo_message():
    global ooga_history

    ooga_history.pop()

    # Fix the RAG database
    based_rag.remove_latest_database_message()

    # Save
    save_histories()



def check_load_past_chat():
    global ooga_history
    global history_loaded


    if history_loaded == False:

        # Load the history from JSON

        with open("LiveLog.json", 'r') as openfile:
            ooga_history = json.load(openfile)

        history_loaded = True

        # Load in our Based RAG as well
        based_rag.load_rag_history()

        # Make a quick backup of our file, if the new one is larger than the old one
        ooga_history_old = []

        try:
            with open("LiveLogBackup.bak", 'r') as twopenfile:
                ooga_history_old = json.load(twopenfile)
        except Exception as e:
            print(f"Error loading LiveLogBackup.bak: {e}")

        if len(ooga_history) > len(ooga_history_old):
            # Export to JSON
            with open("LiveLogBackup.bak", 'w') as outfile:
                json.dump(ooga_history, outfile, indent=4)



def save_histories():

    # Export to JSON
    with open("LiveLog.json", 'w') as outfile:
        json.dump(ooga_history, outfile, indent=4)

    # Save RAG database too
    based_rag.store_rag_history()



#
#   System Inserts
#

#
#def write_lore(lore_entry):
#
#    # Cleanup our lore string
#    clean_lore = "[System D] Lore Entry, " + lore_entry
#
#    ooga_history.append([clean_lore, "Ah, thank you for the lore!"])
#
#
#    # Save
#    save_histories()
#


def soft_reset():
    global ooga_history

    # Saftey breaker for if the previous message was also a Soft Reset / System D
    if len(ooga_history) > 1 and cane_lib.keyword_check(ooga_history[-2][0], ["[System D]"]):
        print("\nStopping potential additional soft reset!\n")
        return

    print("\n\nRunning a soft reset of the chat system!\n")

    # Clear problematic recent history (keep only last 5 messages to preserve context)
    if len(ooga_history) > 5:
        ooga_history = ooga_history[-5:]
        print("Pruned old conversation history for fresh context")

    # Also clear platform-separated chat histories for a complete reset
    try:
        from utils.chat_history import chat_histories, save_chat_histories
        # Clear all platform histories except keep the last few messages for context
        for user_key in chat_histories:
            if len(chat_histories[user_key]) > 5:
                chat_histories[user_key] = chat_histories[user_key][-5:]
        save_chat_histories()
        print("Pruned platform-separated histories for fresh context")
    except Exception as e:
        print(f"Warning: Could not prune platform histories: {e}")

    # Add in the soft reset messages
    # Cycle through all the configed messages and add them. Allows for (mostly) variable length

    for message_pair in soft_reset_message:

        ooga_history.append([message_pair[0], message_pair[1], message_pair[1], settings.cur_tags, "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())])

    # Save
    save_histories()

    return


def prune_deletables():


    # Search through the 27th - 8th to last entries and clear any with the System D headers
    i = len(ooga_history) - 27

    # Ensure it isn't checking a negative number
    if i < 0:
        i = 0


    while i < len(ooga_history) - 8:
        if cane_lib.keyword_check(ooga_history[i][0], ["[System D]"]):
            del ooga_history[i]
            i = len(ooga_history) - 27
            if i < 0:
                i = 0

        i = i + 1





    return



#
#   Other API Access
#

def summary_memory_run(messages_input, user_sent_message, recursion_depth=0):
    global received_message
    global ooga_history
    global forced_token_level
    global force_token_count
    global currently_sending_message
    global last_message_streamed
    global currently_streaming_message
    global is_in_api_request

    # SAFETY: Prevent infinite recursion
    MAX_RECURSION_DEPTH = 3
    if recursion_depth >= MAX_RECURSION_DEPTH:
        print(f"[API] WARNING: Maximum recursion depth ({MAX_RECURSION_DEPTH}) reached in summary_memory_run, using fallback message")
        zw_logging.log_error(f"Maximum recursion depth reached in summary_memory_run: {recursion_depth}")
        is_in_api_request = False
        return "Summary processing encountered issues, but memories have been processed."

    # We are starting our API request!
    is_in_api_request = True

    try:
        # Set the currently sending message
        currently_sending_message = user_sent_message

        # Clear the old streaming message, also we are not streaming so set it so
        currently_streaming_message = ""
        last_message_streamed = False

        # Load the history from JSON, to clean up the quotation marks
        #
        # with open("LiveLog.json", 'r') as openfile:
        #     ooga_history = json.load(openfile)

        # Determine what preset we want to load in with

        preset = 'Z-Waif-ADEF-Standard'

        if settings.model_preset != "Default":
            preset = settings.model_preset

        zw_logging.kelvin_log = preset
        cur_tokens_required = retrospect.summary_tokens_count

        #
        # NOTE: Does not use the character-task at the moment, be aware.
        #

        # Set the stop right
        stop = settings.stopping_strings

        # Encode
        messages_to_send = messages_input


        # Send the actual API Request
        if API_TYPE == "Oobabooga":
            request = {
                "messages": messages_to_send,
                'max_tokens': cur_tokens_required,
                'mode': 'chat',  # Valid options: 'chat', 'chat-instruct', 'instruct'
                'character': CHARACTER_CARD,
                'truncation_length': max_context,
                'stop': stop,

                'preset': preset
            }

            try:
                received_message = API.api_standard(request)
            except Exception as e:
                zw_logging.log_error(f"Oobabooga API request failed in summary_memory_run: {e}")
                received_message = f"Error: {e}"

        elif API_TYPE == "Ollama":
            try:
                received_message = API.api_standard(history=messages_to_send, temp_level=0, stop=stop, max_tokens=cur_tokens_required)
            except Exception as e:
                zw_logging.log_error(f"Ollama API request failed in summary_memory_run: {e}")
                received_message = f"Error: {e}"
        
        else:
            zw_logging.log_error(f"Unknown API_TYPE in summary_memory_run: {API_TYPE}")
            received_message = f"Error: Unknown API type '{API_TYPE}'. Please check your configuration."


        # Translate issues with the received message
        received_message = html.unescape(received_message)

        # If her reply contains RP-ing as other people, supress it form the message
        if settings.supress_rp:
            received_message = supress_rp_as_others(received_message)

        # If her reply is the same as the last stored one, run another request
        global stored_received_message

        if received_message == stored_received_message:
            if recursion_depth < MAX_RECURSION_DEPTH - 1:
                return summary_memory_run(messages_input, user_sent_message, recursion_depth + 1)
            else:
                print(f"[API] WARNING: Cannot retry summary_memory_run, max recursion depth reached")
                received_message = "Memory summary generated with limitations."

        # If her reply is the same as any in the past 20 chats, run another request
        if check_if_in_history(received_message):
            if recursion_depth < MAX_RECURSION_DEPTH - 1:
                return summary_memory_run(messages_input, user_sent_message, recursion_depth + 1)
            else:
                print(f"[API] WARNING: Cannot retry summary_memory_run, max recursion depth reached")
                received_message = "Memory summary generated with limitations."

        # If her reply is blank, request another run, clearing the previous history add, and escape
        if len(received_message) < 3:
            if recursion_depth < MAX_RECURSION_DEPTH - 1:
                return summary_memory_run(messages_input, user_sent_message, recursion_depth + 1)
            else:
                print(f"[API] WARNING: Cannot retry summary_memory_run, max recursion depth reached")
                received_message = "Memory summary processed."

        stored_received_message = received_message

        # Log it to our history. Ensure it is in double quotes, that is how OOBA stores it natively
        log_user_input = "{0}".format(user_sent_message)
        log_received_message = "{0}".format(received_message)

        ooga_history.append([log_user_input, log_received_message, settings.cur_tags, "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())])

        # Run a pruning of the deletables
        prune_deletables()

        # Clear the currently sending message variable
        currently_sending_message = ""

        # Clear any token forcing
        force_token_count = False

        # Save
        save_histories()

    finally:
        # CRITICAL: Always reset the flag, even if exceptions occur
        is_in_api_request = False



# def swap_language_model(model_ID):
#
#     # Setup and send the JSON request
#
#     print("Swapping model!")
#     model_name = "none_model"
#
#     if model_ID == 0:
#
#         model_name = 'LoneStriker_Loyal-Macaroni-Maid-7B-5.0bpw-h6-exl2'
#
#         request = {
#             'action': 'load',
#             'model_name': model_name,
#
#             'args': {
#                 'loader': 'ExLlamav2_HF',
#
#                 'cache_8bit': True,
#                 'disable_exllama': False,
#                 'disable_exllamav2': False,
#                 'max_seq_len': max_context,
#                 'truncation_length': max_context
#
#                 }
#         }
#
#     elif model_ID == 1:
#
#         model_name = 'TheBloke_vicuna-7B-1.1-GPTQ'
#
#         request = {
#             'action': 'load',
#             'model_name': model_name,
#
#             'args': {
#                 'loader': 'AutoGPTQ',
#
#                 'load_in_4bit': True,
#                 'disable_exllama': True,
#                 'disable_exllamav2': True,
#                 'max_seq_len': max_context,
#                 'truncation_length': max_context
#
#                 }
#
#         }
#
#
#     model_string = URL_MODEL + model_name
#     print(model_string)
#
#     #   Can be used to see the output of the change (and all the config it has)
#     response = requests.post(model_string, json=request)
#     print(response.json())
#     time.sleep(10)


def view_image(direct_talk_transcript):

    global ooga_history
    global currently_streaming_message
    global last_message_streamed
    global is_in_api_request
    global currently_sending_message

    # We are starting our API request!
    is_in_api_request = True

    # Message that is currently being sent
    currently_sending_message = direct_talk_transcript

    # Clear the old streaming message, also we are not streaming so set it so
    currently_streaming_message = ""
    last_message_streamed = False

    # Did the last message we got contain our name?
    check_for_name_in_message(direct_talk_transcript)

    # Write last, non-system message to RAG (Since this is going in addition)
    # NOTE: On re-opening, it will still add the latest message. This is fine! We are just always in debt 1 depth (except from when recalced)
    based_rag.add_message_to_database()

    #
    # Prepare The Context
    #

    global ooga_history
    image_marker_length = 4     # shorting this so we don't take up a ton of context while image processing

    past_messages = []

    message_marker = len(ooga_history) - image_marker_length
    if message_marker < 0:  # if we bottom out, then we would want to start at 0 and go down. we check if i is less than, too
        message_marker = 0

    #
    # Append our system message, if we are using OLLAMA, configs for guidance message and what character card to use
    #
    if API_TYPE_VISUAL == "Ollama":

        system_message = ""

        if OLLAMA_VISUAL_ENCODE_GUIDANCE == "ON":
            system_message += vision_guidance_message + "\n\n"

        if OLLAMA_VISUAL_CARD == "BASE":
            system_message += character_card.character_card

        if OLLAMA_VISUAL_CARD == "VISUAL":
            system_message += character_card.visual_character_card

        # If we have any visual message to append, go for it!
        if system_message != "":
            past_messages.append({"role": "system", "content": system_message})
    #

    past_messages.append({"role": "user", "content": ooga_history[message_marker][0]})
    past_messages.append({"role": "assistant", "content": ooga_history[message_marker][1]})

    i = 1
    while i < image_marker_length and i < len(ooga_history):
        past_messages.append({"role": "user", "content": ooga_history[message_marker + i][0]})
        past_messages.append({"role": "assistant", "content": ooga_history[message_marker + i][1]})

        i = i + 1

    #
    #
    #


    # Prep the prompt

    base_prompt = YOUR_NAME + ", please view and describe this image vivid in detail, for your main system: \n"
    if settings.cam_direct_talk:
        base_prompt = direct_talk_transcript

    # Set the stop right
    stop = settings.stopping_strings
    if settings.newline_cut:
        stop.append("\n")
    if settings.asterisk_ban:
        stop.append("*")


    # Send it in for viewing!

    received_cam_message = ""

    # Send the actual API Request
    if API_TYPE_VISUAL == "Oobabooga":

        # Append the image the good ol' way
        try:
            with open('LiveImage.png', 'rb') as f:
                img_str = base64.b64encode(f.read()).decode('utf-8')
                prompt = f'{base_prompt}<img src="data:image/jpeg;base64,{img_str}">'
                past_messages.append({"role": "user", "content": prompt})

            request = {
                'max_tokens': 300,
                'prompt': "This image",
                'messages': past_messages,
                'mode': 'chat-instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
                'character': OOBA_VISUAL_CHARACTER_NAME,
                'your_name': YOUR_NAME,
                'regenerate': False,
                '_continue': False,
                'truncation_length': 2048,
                'stop': stop,

                'preset': OOBA_VISUAL_PRESET_NAME
            }

            response = requests.post(IMG_URI, json=request)
            received_cam_message = response.json()['choices'][0]['message']['content']
        except Exception as e:
            zw_logging.log_error(f"Oobabooga image API request failed: {e}")
            received_cam_message = f"Error processing image: {e}"

    elif API_TYPE_VISUAL == "Ollama":

        try:
            # Append the image (via file path, so not for real but just link file)
            img_str = str(os.path.abspath('LiveImage.png'))
            past_messages.append({"role": "user", "content": base_prompt, "images": [img_str]})

            received_cam_message = API.api_standard_image(history=past_messages)
        except Exception as e:
            zw_logging.log_error(f"Ollama image API request failed: {e}")
            received_cam_message = f"Error processing image: {e}"
    
    else:
        zw_logging.log_error(f"Unknown API_TYPE for image processing: {API_TYPE}")
        received_cam_message = f"Error: Unknown API type '{API_TYPE}' for image processing. Please check your configuration."


    # Translate issues with the received message
    received_cam_message = html.unescape(received_cam_message)

    # If her reply contains RP-ing as other people, supress it form the message
    if settings.supress_rp:
        received_cam_message = supress_rp_as_others(received_cam_message)

    # Add Header
    # received_cam_message = "[System C] " + received_cam_message
    # No more headers! To stay consistent with streaming & modern good multimodal RP models with Ollama,
    # we don't need two-phasic image use anymore.



    # Write last, non-system message to RAG
    # NOTE: On re-opening, it will still add the latest message. This is fine! We are just always in debt 1 depth (except from when recalced)
    based_rag.add_message_to_database()


    # Add to hist & such
    base_send = "[System C] Sending an image..."
    if settings.cam_direct_talk:
        base_send = direct_talk_transcript

    # Prep with visual tag
    these_tags = settings.cur_tags.copy()
    these_tags.append("ZW-Visual")

    ooga_history.append([base_send, received_cam_message, these_tags, "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())])


    # Save
    save_histories()

    # Clear the currently sending message variable
    currently_sending_message = ""

    # We are ending our API request!
    is_in_api_request = False

    # Set our global, for the reading!
    global received_message
    received_message = received_cam_message

    return received_cam_message


def view_image_streaming(direct_talk_transcript):

    global ooga_history
    global currently_streaming_message
    global currently_sending_message
    global currently_streaming_message
    global last_message_streamed
    global streaming_sentences_ticker
    global is_in_api_request
    global force_skip_streaming

    # We are starting our API request!
    is_in_api_request = True

    # Clear possible streaming endflag
    global flag_end_streaming
    flag_end_streaming = False

    # Message that is currently being sent
    currently_sending_message = direct_talk_transcript

    # Clear the old streaming message, also we are not streaming so set it so
    currently_streaming_message = ""
    assistant_message = ''
    last_message_streamed = True

    # Did the last message we got contain our name?
    check_for_name_in_message(direct_talk_transcript)

    # Write last, non-system message to RAG (Since this is going in addition)
    # NOTE: On re-opening, it will still add the latest message. This is fine! We are just always in debt 1 depth (except from when recalced)
    based_rag.add_message_to_database()

    #
    # Prepare The Context
    #

    global ooga_history
    image_marker_length = 2     # shorting this so we don't take up a ton of context while image processing

    past_messages = []

    message_marker = len(ooga_history) - image_marker_length
    if message_marker < 0:  # if we bottom out, then we would want to start at 0 and go down. we check if i is less than, too
        message_marker = 0


    #
    # Append our system message, if we are using OLLAMA, configs for guidance message and what character card to use
    #
    if API_TYPE_VISUAL == "Ollama":

        system_message = ""

        if OLLAMA_VISUAL_ENCODE_GUIDANCE == "ON":
            system_message += vision_guidance_message + "\n\n"

        if OLLAMA_VISUAL_CARD == "BASE":
            system_message += character_card.character_card

        if OLLAMA_VISUAL_CARD == "VISUAL":
            system_message += character_card.visual_character_card

        # If we have any visual message to append, go for it!
        if system_message != "":
            past_messages.append({"role": "system", "content": system_message})
    #

    past_messages.append({"role": "user", "content": ooga_history[message_marker][0]})
    past_messages.append({"role": "assistant", "content": ooga_history[message_marker][1]})

    i = 1
    while i < image_marker_length and i < len(ooga_history):
        past_messages.append({"role": "user", "content": ooga_history[message_marker + i][0]})
        past_messages.append({"role": "assistant", "content": ooga_history[message_marker + i][1]})

        i = i + 1

    #
    #
    #


    # Prep the prompt

    base_prompt = YOUR_NAME + ", please view and describe this image in detail, for your main system: \n"
    if settings.cam_direct_talk:
        base_prompt = direct_talk_transcript

    # Set the stop right
    stop = settings.stopping_strings
    if settings.newline_cut:
        stop.append("\n")
    if settings.asterisk_ban:
        stop.append("*")

    supressed_rp = False

    # Send it in for viewing!

    received_cam_message = ""

    # We will print the header only when we receive the first chunk,
    # avoiding an empty name banner if the request fails.
    header_printed = False

    # Reset the ticker (starts counting at 1)
    streaming_sentences_ticker = 1

    # Actual streaming bit

    # Reset the ticker (starts counting at 1)
    streaming_sentences_ticker = 1

    # Send the actual API Request
    if API_TYPE_VISUAL == "Oobabooga":
        try:
            with open('LiveImage.png', 'rb') as f:
                img_str = base64.b64encode(f.read()).decode('utf-8')
                prompt = f'{base_prompt}<img src="data:image/jpeg;base64,{img_str}">'
                past_messages.append({"role": "user", "content": prompt})

            request = {
                'max_tokens': 300,
                'prompt': "This image",
                'messages': past_messages,
                'mode': 'chat-instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
                'character': OOBA_VISUAL_CHARACTER_NAME,
                'your_name': YOUR_NAME,
                'regenerate': False,
                '_continue': False,
                'truncation_length': 2048,
                'stop': stop,

                'preset': OOBA_VISUAL_PRESET_NAME,

                'stream': True,
            }

            # Actual streaming bit
            stream_response = requests.post(IMG_URI, headers=headers, json=request, verify=False, stream=True)
            stream_response.raise_for_status()  # Raise an exception for bad status codes
            client = sseclient.SSEClient(stream_response)
            streamed_api_stringpuller = client.events()
        except Exception as e:
            zw_logging.log_error(f"Oobabooga streaming image API request failed: {e}")
            streamed_api_stringpuller = []

    elif API_TYPE_VISUAL == "Ollama":
        try:
            # Append the image (via file path, so not for real but just link file)
            img_str = str(os.path.abspath('LiveImage.png'))
            past_messages.append({"role": "user", "content": base_prompt, "images": [img_str]})

            streamed_api_stringpuller = API.api_stream_image(history=past_messages)
        except Exception as e:
            zw_logging.log_error(f"Ollama streaming image API request failed: {e}")
            streamed_api_stringpuller = []
    
    else:
        zw_logging.log_error(f"Unknown API_TYPE for streaming image processing: {API_TYPE}")
        streamed_api_stringpuller = []


    # Clear streamed emote list
    vtube_studio.clear_streaming_emote_list()

    # Enhanced Contextual Chatpop Check for Image Processing
    if settings.use_chatpops and not settings.live_pipe_no_speak:
        voice.set_speaking(True)
        # Special context for image processing - more thoughtful responses
        platform_context = {"platform": "vision"}
        # For image processing, we want more thoughtful/interested chatpops
        visual_chatpops = [
            "Oh, let me see...", "Hmm, interesting...", "Oh, what do we have here?",
            "Let me take a look", "Oh, that's cool", "Hmm, let me check this out",
            "Oh, nice!", "Interesting image...", "Let me examine this"
        ]
        this_chatpop = random.choice(visual_chatpops)
        voice.speak_line(this_chatpop, refuse_pause=True)

    assistant_message = ''
    force_skip_streaming = False
    supressed_rp = False
    for event in streamed_api_stringpuller:
        # Extract chunk using unified API interface
        chunk = API.extract_streaming_chunk(event)

        # Split based on API type
        if API_TYPE_VISUAL == "Oobabooga":
            payload = json.loads(event.data)
            chunk = payload['choices'][0]['delta']['content']

        elif API_TYPE_VISUAL == "Ollama":
            chunk = event['message']['content']

        # On first chunk, print the speaker header so output isn't blank beforehand
        if not header_printed:
            print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
                  + "----" + settings.char_name + "----"
                  + colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)
            header_printed = True

        assistant_message += chunk
        streamed_response_check = streamed_update_handler(chunk, assistant_message)
        if streamed_response_check == "Cut":

            # Clear the currently sending message variable
            currently_sending_message = ""

            # We are ending our API request!
            is_in_api_request = False

            return

        # Cut for the hangout name being said
        if streamed_response_check == "Hangout-Name-Cut" and settings.hangout_mode:
            # Add any existing stuff to our actual chat history
            ooga_history.append([direct_talk_transcript, assistant_message, settings.cur_tags, "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())])
            save_histories()

            # Remove flag
            flag_end_streaming = False

            # Clear the currently sending message variable
            currently_sending_message = ""

            # We are ending our API request!
            is_in_api_request = False

            return


        # time.sleep(0.0197)    # NOTE: This is purely for style points to "slow" incoming responses
        # IDK, it was a bit annoying to wait, and setting it up in another thread straight up didn't work,
        # The TTS takes up the whole dang program lol.
        # Want to set this to be a rolling ticker at some point, where we get the responses at any rate, read them,
        # and reveal them as needed. Yes! One day... this isn't particularly important at the moment

        # Check if we need to force skip the stream (hotkey or manually)
        if hotkeys.pull_next_press_input() or force_skip_streaming:
            force_skip_streaming = True
            break

        # Check if we need to break out due to RP suppression (if it different, then there is a suppression)
        if settings.supress_rp and (supress_rp_as_others(assistant_message) != assistant_message):
            assistant_message = supress_rp_as_others(assistant_message)
            supressed_rp = True
            break

        # Redo it and skip
        if force_skip_streaming:
            force_skip_streaming = False
            print("\nSkipping message, redoing!\n")
            zw_logging.update_debug_log("Got an input to regenerate! Re-generating the reply...")
            # Just set the message to be small, as this will force a re-run due to our while loop rules
            assistant_message = ""

    # Read the final sentence aloud (if not stopped by RP supr)
    if not supressed_rp:
        s_assistant_message = emoji.replace_emoji(assistant_message, replace='')
        sentence_list = voice_splitter.split_into_sentences(s_assistant_message)

        # Emotes
        if settings.vtube_enabled:
            vtube_studio.set_emote_string(s_assistant_message)
            vtube_studio.check_emote_string_streaming()

        # Speaking
        if not settings.live_pipe_no_speak and len(sentence_list) > 0:
            voice.set_speaking(True)
            voice.speak_line(sentence_list[-1], refuse_pause=True)

    # Print Newline
    print("\n")

    received_cam_message = assistant_message

    # Translate issues with the received message
    received_cam_message = html.unescape(received_cam_message)


    # Add Header
    # NOTE: Not adding this header now... looking to clean all this up later with unipipes
    #
    #received_cam_message = "[System C] " + received_cam_message



    # Write last, non-system message to RAG
    # NOTE: On re-opening, it will still add the latest message. This is fine! We are just always in debt 1 depth (except from when recalced)
    based_rag.add_message_to_database()


    # Add to hist & such
    base_send = "[System C] Sending an image..."
    if settings.cam_direct_talk:
        base_send = direct_talk_transcript

    # Prep with visual tag
    these_tags = settings.cur_tags.copy()
    these_tags.append("ZW-Visual")

    ooga_history.append([base_send, received_cam_message, these_tags, "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())])


    # Save
    save_histories()

    # Clear the currently sending message variable
    currently_sending_message = ""

    # We are ending our API request!
    is_in_api_request = False

    # Set our global, for the reading!
    global received_message
    received_message = received_cam_message


    return received_cam_message



def check_if_in_history(message):

    # Search through the 20th - 1th to last entries to see if we have any matches
    i = len(ooga_history) - 20
    if i < 0:
        i = 0

    while i < len(ooga_history):
        if ooga_history[i][1] == message:
            return True

        i = i + 1

    return False


# def add_rag_to_history(message_a, message_b):
#
#     my_message = "[System M] Past memory:\n" + message_a
#     her_message = "Past memory:\n" + message_b
#
#     # print(my_message)
#     # print(her_message)
#
#     ooga_history['internal'].insert(len(ooga_history['internal']) - 8, [my_message, her_message])
#     ooga_history['visible'].insert(len(ooga_history['visible']) - 8, [my_message, her_message])
#
#     # print(ooga_history['internal'])
#
#     # Export to JSON
#     with open("LiveLog.json", 'w') as outfile:
#         json.dump(ooga_history, outfile, indent=4)
#
#     stored_rag_recall[0] = message_a
#     stored_rag_recall[1] = message_b
#
#     return



# Encodes from the old api's way of storing history (and ooba internal) to the new one
def _encode_new_api_deprecated(user_input):
    """
    DEPRECATED: This function creates a flat string prompt.
    The new standard is to use a structured message list.
    Kept for reference or potential fallback scenarios.
    """
    messages = []
    
    # Add character card
    if CHARACTER_CARD:
        messages.append(character_card.character_card)
    
    # Add history
    history_start = max(0, len(ooga_history) - marker_length)
    for i in range(history_start, len(ooga_history)):
        # Guard against malformed history entries that may be shorter than expected
        try:
            user_msg = ooga_history[i][0]
            assistant_msg = ooga_history[i][1]
        except IndexError:
            # Skip malformed pair to avoid crashes
            continue

        if user_msg:
            messages.append(str(user_msg))
        if assistant_msg:
            messages.append(str(assistant_msg))
    
    # Add current message (fallback to placeholder if blank)
    if user_input and user_input.strip():
        messages.append(user_input)
    else:
        messages.append("*listens attentively*")
    
    # Join all messages with newlines
    prompt = "\n".join(messages)
    
    return prompt


def encode_new_api_ollama(user_input):
    """Enhanced Ollama encoding with platform-specific context"""
    global ooga_history

    messages_to_send = []
    
    # Detect platform from user input
    platform_context = ""
    if "[Platform: Twitch Chat]" in user_input:
        platform_context = "\n\nCONTEXT: You are chatting on Twitch. Keep responses casual, engaging, and chat-friendly. Avoid streaming references but maintain a conversational tone. Be authentic and relatable."
    elif "[Platform: Discord]" in user_input:
        platform_context = "\n\nCONTEXT: You are chatting on Discord. Be casual, fun, and engaging. You can use emojis and informal language. Keep the social energy up."
    elif "[Platform: Web Interface - Personal Chat]" in user_input:
        platform_context = "\n\nCONTEXT: This is a personal one-on-one conversation through a web interface. Be warm, caring, and authentic. Focus on meaningful personal interaction."
    elif "[Platform: Command Line - Personal Chat]" in user_input:
        platform_context = "\n\nCONTEXT: This is a personal conversation through command line. Be direct but friendly. Keep responses clear and engaging."
    elif "[Platform: Voice Chat - Personal Conversation]" in user_input:
        platform_context = "\n\nCONTEXT: This is a voice conversation. Be natural and conversational as if speaking aloud. Use natural speech patterns and be expressive."
    elif "[Platform: Minecraft Game Chat]" in user_input:
        platform_context = "\n\nCONTEXT: You are chatting in Minecraft. Keep responses short, game-appropriate, and fun. Be supportive of gameplay activities."
    elif "[Platform: Alarm/Reminder System]" in user_input:
        platform_context = "\n\nCONTEXT: This is an alarm or reminder. Be helpful, direct, and supportive. Focus on being encouraging and useful."
    elif "[Platform: Hangout Mode - Casual Conversation]" in user_input:
        platform_context = "\n\nCONTEXT: This is casual hangout mode. Be relaxed, fun, and spontaneous. Focus on creating a comfortable, enjoyable atmosphere."
    
    # Simple system prompt - character card with platform context
    if character_card.character_card and isinstance(character_card.character_card, str):
        enhanced_character_card = character_card.character_card.strip() + platform_context
        messages_to_send.append({"role": "system", "content": enhanced_character_card})
        
        # Debug: Show platform detection
        print(f"[API] Ollama Platform detected: {platform_context.split(':')[1].split('.')[0] if platform_context else 'Personal'}")

    # Add recent history (last 10 exchanges like release version)
    recent_history = ooga_history[-10:] if len(ooga_history) > 10 else ooga_history
    
    for entry in recent_history:
        # Handle both old format (2 elements) and new format (4+ elements)
        if len(entry) >= 2:
            user_msg = entry[0]
            assistant_msg = entry[1]
            
            if user_msg:
                messages_to_send.append({"role": "user", "content": str(user_msg)})
            if assistant_msg:
                messages_to_send.append({"role": "assistant", "content": str(assistant_msg)})

    # Add current user input
    if user_input:
        messages_to_send.append({"role": "user", "content": str(user_input)})
    
    # Debug logging when enabled
    try:
        import main
        if main.debug_mode:
            zw_logging.update_debug_log(f"Ollama encoded {len(messages_to_send)} messages with platform context")
            for i, msg in enumerate(messages_to_send):
                content_preview = msg.get('content', '')[:100] + ('...' if len(msg.get('content', '')) > 100 else '')
                zw_logging.update_debug_log(f"Ollama Message {i+1} ({msg.get('role', 'unknown')}): {content_preview}")
    except (ImportError, AttributeError):
        pass

    return messages_to_send


def encode_for_oobabooga_chat(user_input):
    """
    Enhanced encoding with platform-specific context - includes conversation history + platform awareness
    """
    messages = []
    
    # Detect platform from user input
    platform_context = ""
    if "[Platform: Twitch Chat]" in user_input:
        platform_context = "\n\nCONTEXT: You are chatting on Twitch. Keep responses casual, engaging, and chat-friendly. Avoid streaming references but maintain a conversational tone. Be authentic and relatable."
    elif "[Platform: Discord]" in user_input:
        platform_context = "\n\nCONTEXT: You are chatting on Discord. Be casual, fun, and engaging. You can use emojis and informal language. Keep the social energy up."
    elif "[Platform: Web Interface - Personal Chat]" in user_input:
        platform_context = "\n\nCONTEXT: This is a personal one-on-one conversation through a web interface. Be warm, caring, and authentic. Focus on meaningful personal interaction."
    elif "[Platform: Command Line - Personal Chat]" in user_input:
        platform_context = "\n\nCONTEXT: This is a personal conversation through command line. Be direct but friendly. Keep responses clear and engaging."
    elif "[Platform: Voice Chat - Personal Conversation]" in user_input:
        platform_context = "\n\nCONTEXT: This is a voice conversation. Be natural and conversational as if speaking aloud. Use natural speech patterns and be expressive."
    elif "[Platform: Minecraft Game Chat]" in user_input:
        platform_context = "\n\nCONTEXT: You are chatting in Minecraft. Keep responses short, game-appropriate, and fun. Be supportive of gameplay activities."
    elif "[Platform: Alarm/Reminder System]" in user_input:
        platform_context = "\n\nCONTEXT: This is an alarm or reminder. Be helpful, direct, and supportive. Focus on being encouraging and useful."
    elif "[Platform: Hangout Mode - Casual Conversation]" in user_input:
        platform_context = "\n\nCONTEXT: This is casual hangout mode. Be relaxed, fun, and spontaneous. Focus on creating a comfortable, enjoyable atmosphere."
    
    # Add character card as system message with platform context
    if character_card.character_card and isinstance(character_card.character_card, str):
        enhanced_character_card = character_card.character_card.strip() + platform_context
        
        # Add extra emphasis on avoiding formal language
        anti_formal_instruction = """

CRITICAL: NEVER use formal or customer-service language. NEVER say phrases like:
- "How can I assist you"
- "to be of service" 
- "to assist"
- "What can I do for you"
- "How can I help you today"
- "How may I help you"
- Any variation of "assist", "help", "support", "service" in formal context

ALWAYS respond like a real friend having a casual conversation. Use natural, friendly language."""
        
        enhanced_character_card = enhanced_character_card + anti_formal_instruction
        messages.append({"role": "system", "content": enhanced_character_card})
        
        # Debug: Show platform detection
        print(f"[API] Platform detected: {platform_context.split(':')[1].split('.')[0] if platform_context else 'Personal'}")

    # Add recent history (last 10 exchanges like release version)
    recent_history = ooga_history[-10:] if len(ooga_history) > 10 else ooga_history
    
    for entry in recent_history:
        # Handle both old format (2 elements) and new format (4+ elements)
        if len(entry) >= 2:
            user_msg = entry[0]
            assistant_msg = entry[1]
            
            if user_msg:
                messages.append({"role": "user", "content": str(user_msg)})
            if assistant_msg:
                messages.append({"role": "assistant", "content": str(assistant_msg)})

    # Add current user input
    if user_input:
        messages.append({"role": "user", "content": str(user_input)})
    
    # Debug logging when enabled
    try:
        import main
        if main.debug_mode:
            zw_logging.update_debug_log(f"Encoded {len(messages)} messages for API with platform context")
            for i, msg in enumerate(messages):
                content_preview = msg.get('content', '')[:100] + ('...' if len(msg.get('content', '')) > 100 else '')
                zw_logging.update_debug_log(f"Message {i+1} ({msg.get('role', 'unknown')}): {content_preview}")
    except (ImportError, AttributeError):
        pass
        
    return messages


# encodes a given input to the new API, with no additives
def encode_raw_new_api(user_messages_input, user_message_last, raw_marker_length):
    #
    # Append 30 of the most recent history pairs (however long our raw marker length is)
    #

    message_marker = len(user_messages_input) - raw_marker_length
    if message_marker < 0:  # if we bottom out, then we would want to start at 0 and go down. we check if i is less than, too
        message_marker = 0

    messages_to_send = [
        {"role": "user", "content": user_messages_input[message_marker][0]},
        {"role": "assistant", "content": user_messages_input[message_marker][1]},
    ]

    i = 1
    while i < raw_marker_length and i < len(user_messages_input):
        messages_to_send.append({"role": "user", "content": user_messages_input[message_marker + i][0]})
        messages_to_send.append({"role": "assistant", "content": user_messages_input[message_marker + i][1]})

        i = i + 1

    #
    # Append our most recent message
    #

    if user_message_last != "":
        messages_to_send.append({"role": "user", "content": user_message_last})

    return messages_to_send



def supress_rp_as_others(message):

    # do not supress if there is no colon
    if not message.__contains__(":"):
        return message

    # do not supress if there is no newline cuts either
    if not message.__contains__("\n"):
        return message


    # Remove any text past a newline with a person's name
    i = 1
    counter_watchdog = 0
    message_cutoff_marker = 0
    message_cutoff_enabled = False

    while i < len(message):

        if (message[i] == "\n") and (message_cutoff_enabled == False) and (message[i-1] != ":"):
            counter_watchdog = 21
            message_cutoff_marker = i

        if message[i] == ":" and counter_watchdog > 0:
            message_cutoff_enabled = True



        i = i + 1
        counter_watchdog = counter_watchdog - 1

    new_message = message
    if message_cutoff_enabled:
        new_message = message[0:message_cutoff_marker]


    return new_message


def force_tokens_count(tokens):
    global forced_token_level, force_token_count
    forced_token_level = tokens
    force_token_count = True

def pop_if_sent_is_latest(user_input):
    if user_input == ooga_history[-1][0]:
        ooga_history.pop()

def check_for_name_in_message(message):
    global last_message_received_has_own_name

    if message.__contains__(settings.char_name):
        last_message_received_has_own_name = True

    else:
        last_message_received_has_own_name = False
