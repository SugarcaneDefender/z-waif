import datetime
import os
import html
import json
import base64
import time
import random

import requests
import sseclient

import main
import utils.cane_lib
import utils.based_rag
import utils.zw_logging
from dotenv import load_dotenv
import utils.settings
import utils.retrospect
import utils.lorebook
import utils.tag_task_controller
import colorama
import utils.voice_splitter
import utils.voice
import emoji
import threading
import utils.hotkeys
import utils.vtube_studio
import utils.hangout

import API.oobaooga_api
import API.ollama_api
import API.character_card

from ollama import chat
from ollama import ChatResponse

from pathlib import Path


load_dotenv()

HOST = os.environ.get("HOST_PORT")
URI = f'http://{HOST}/v1/chat/completions'
URL_MODEL = f'http://{HOST}/v1/engines/'

IMG_PORT = os.environ.get("IMG_PORT")
IMG_URI = f'http://{IMG_PORT}/v1/chat/completions'
IMG_URL_MODEL = f'http://{IMG_PORT}/v1/engines/'

received_message = ""
CHARACTER_CARD = os.environ.get("CHARACTER_CARD")
YOUR_NAME = os.environ.get("YOUR_NAME")

API_TYPE = os.environ.get("API_TYPE")

history_loaded = False

ooga_history = [ ["Hello, I am back!", "Welcome back! *smiles*"] ]

headers = {
    "Content-Type": "application/json"
}

max_context = int(os.environ.get("TOKEN_LIMIT"))
marker_length = int(os.environ.get("MESSAGE_PAIR_LIMIT"))

force_token_count = False
forced_token_level = 120

stored_received_message = "None!"
currently_sending_message = ""
currently_streaming_message = ""
last_message_streamed = False
streaming_sentences_ticker = 0

force_skip_streaming = False
flag_end_streaming = False

is_in_api_request = False

ENCODE_TIME = os.environ.get("TIME_IN_ENCODING")

VISUAL_CHARACTER_NAME = os.environ.get("VISUAL_CHARACTER_NAME")
VISUAL_PRESET_NAME = os.environ.get("VISUAL_PRESET_NAME")

vision_guidance_message = "There is an image attached to this message! Please look at it and describe it for everyone in vivid detail! Describe as many details of the image as you can, and comment on what you think of the features!"

# Load in the configurable SoftReset message
with open("Configurables/SoftReset.json", 'r') as openfile:
    soft_reset_message = json.load(openfile)

# Load in the stopping strings
with open("Configurables/StoppingStrings.json", 'r') as openfile:
    utils.settings.stopping_strings = json.load(openfile)


def run(user_input, temp_level):
    global received_message
    global ooga_history
    global forced_token_level
    global force_token_count
    global currently_sending_message
    global currently_streaming_message
    global last_message_streamed
    global is_in_api_request

    # We are starting our API request!
    is_in_api_request = True

    # Message that is currently being sent
    currently_sending_message = user_input

    # Clear the old streaming message, also we are not streaming so set it so
    currently_streaming_message = ""
    last_message_streamed = False

    # Load the history from JSON, to clean up the quotation marks
    #
    with open("LiveLog.json", 'r') as openfile:
        ooga_history = json.load(openfile)


    # Determine what preset we want to load in with

    preset = 'Z-Waif-ADEF-Standard'

    if random.random() > 0.77:
        preset = 'Z-Waif-ADEF-Tempered'

    if random.random() > 0.994:
        preset = 'Z-Waif-ADEF-Blazing'


    # Higher forced temps for certain scenarios

    if temp_level == 1:
        preset = 'Z-Waif-ADEF-Tempered'

        if random.random() > 0.7:
            preset = 'Z-Waif-ADEF-Blazing'

    if temp_level == 2:
        preset = 'Z-Waif-ADEF-Blazing'

    #
    # NOTE: Random temperatures will be inactive if we set another model preset. Quirky!
    #

    if utils.settings.model_preset != "Default":
        preset = utils.settings.model_preset

    utils.zw_logging.kelvin_log = preset

    # Set what char/task we are sending to, defaulting to the character card if there is none
    char_send = utils.settings.cur_task_char
    if char_send == "None":
        char_send = CHARACTER_CARD


    # Forced tokens check
    cur_tokens_required = utils.settings.max_tokens
    if force_token_count:
        cur_tokens_required = forced_token_level


    # Set the stop right
    stop = utils.settings.stopping_strings
    if utils.settings.newline_cut:
        stop.append("\n")
    if utils.settings.asterisk_ban:
        stop.append("*")


    # Encode
    messages_to_send = encode_new_api(user_input)

    # Send the actual API Request
    if API_TYPE == "Oobabooga":
        request = {
            "messages": messages_to_send,
            'max_tokens': cur_tokens_required,
            'mode': 'chat',  # Valid options: 'chat', 'chat-instruct', 'instruct'
            'character': char_send,
            'truncation_length': max_context,
            'stop': stop,

            'preset': preset
        }

        received_message = API.oobaooga_api.api_standard(request)

    elif API_TYPE == "Ollama":
        received_message = API.ollama_api.api_standard(history=messages_to_send, temp_level=temp_level, stop=stop, max_tokens=cur_tokens_required)



    # Translate issues with the received message
    received_message = html.unescape(received_message)


    # If her reply contains RP-ing as other people, supress it form the message
    if utils.settings.supress_rp:
        received_message = supress_rp_as_others(received_message)


    # If her reply is the same as the last stored one, run another request
    global stored_received_message

    if received_message == stored_received_message:
        utils.zw_logging.update_debug_log("Bad message received; same as last attempted generation. Re-generating the reply...")
        run(user_input, 2)
        return

    stored_received_message = received_message


    # If her reply is the same as any in the past 20 chats, run another request
    if check_if_in_history(received_message):
        utils.zw_logging.update_debug_log("Bad message received; same as a recent chat. Re-generating the reply...")
        run(user_input, 1)
        return

    # If her reply is blank, request another run, clearing the previous history add, and escape
    if len(received_message) < 3:
        utils.zw_logging.update_debug_log("Bad message received; chat is a runt or blank entirely. Re-generating the reply...")
        run(user_input, 1)
        return



    # Log it to our history. Ensure it is in double quotes, that is how OOBA stores it natively
    log_user_input = "{0}".format(user_input)
    log_received_message = "{0}".format(received_message)

    ooga_history.append([log_user_input, log_received_message, utils.tag_task_controller.apply_tags(), "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())])

    # Run a pruning of the deletables
    prune_deletables()

    # Clear the currently sending message variable
    currently_sending_message = ""

    # Clear any token forcing
    force_token_count = False

    # Save
    save_histories()

    # We are ending our API request!
    is_in_api_request = False

#
# For the new streaming chats, runs it continually to grab data as it comes in from Oobabooga. Should run faster
#
def run_streaming(user_input, temp_level):

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

    # We are starting our API request!
    is_in_api_request = True

    # Clear possible streaming endflag
    global flag_end_streaming
    flag_end_streaming = False

    # Message that is currently being sent
    currently_sending_message = user_input

    # Clear the old streaming message
    currently_streaming_message = ""
    last_message_streamed = True

    # Load the history from JSON, to clean up the quotation marks
    #
    with open("LiveLog.json", 'r') as openfile:
        ooga_history = json.load(openfile)


    # Determine what preset we want to load in with

    preset = 'Z-Waif-ADEF-Standard'

    if random.random() > 0.77:
        preset = 'Z-Waif-ADEF-Tempered'

    if random.random() > 0.994:
        preset = 'Z-Waif-ADEF-Blazing'


    # Higher forced temps for certain scenarios

    if temp_level == 1:
        preset = 'Z-Waif-ADEF-Tempered'

        if random.random() > 0.7:
            preset = 'Z-Waif-ADEF-Blazing'

    if temp_level == 2:
        preset = 'Z-Waif-ADEF-Blazing'

    #
    # NOTE: Random temperatures will be inactive if we set another model preset. Quirky!
    #

    if utils.settings.model_preset != "Default":
        preset = utils.settings.model_preset

    utils.zw_logging.kelvin_log = preset

    # Set what char/task we are sending to, defaulting to the character card if there is none
    char_send = utils.settings.cur_task_char
    if char_send == "None":
        char_send = CHARACTER_CARD


    # Forced tokens check
    cur_tokens_required = utils.settings.max_tokens
    if force_token_count:
        cur_tokens_required = forced_token_level


    # Set the stop right
    stop = utils.settings.stopping_strings
    if utils.settings.newline_cut:
        stop.append("\n")
    if utils.settings.asterisk_ban:
        stop.append("*")


    # Encode
    messages_to_send = encode_new_api(user_input)

    #
    # Send the actual API Request
    #

    #
    # STREAMING TOOLING GOES HERE o7
    #

    # Prep console with printing for message output

    print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
          + "----" + utils.settings.char_name + "----"
          + colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)

    # Reset the ticker (starts counting at 1)
    streaming_sentences_ticker = 1

    # Send the actual API Request
    if API_TYPE == "Oobabooga":
        request = {
            "messages": messages_to_send,
            'max_tokens': cur_tokens_required,
            'mode': 'chat',  # Valid options: 'chat', 'chat-instruct', 'instruct'
            'character': char_send,
            'truncation_length': max_context,
            'stop': stop,
            'stream': True,

            'preset': preset
        }

        # Actual streaming bit
        stream_response = requests.post(URI, headers=headers, json=request, verify=False, stream=True)
        client = sseclient.SSEClient(stream_response)

        streamed_api_stringpuller = client.events()


    elif API_TYPE == "Ollama":
        streamed_api_stringpuller = API.ollama_api.api_stream(history=messages_to_send, temp_level=temp_level, stop=stop, max_tokens=cur_tokens_required)



    # Clear streamed emote list
    utils.vtube_studio.clear_streaming_emote_list()

    assistant_message = ''
    supressed_rp = False
    force_skip_streaming = False
    for event in streamed_api_stringpuller:
        chunk = ""

        # Split based on API type
        if API_TYPE == "Oobabooga":
            payload = json.loads(event.data)
            chunk = payload['choices'][0]['delta']['content']

        elif API_TYPE == "Ollama":
            chunk = event['message']['content']


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
        if streamed_response_check == "Hangout-Name-Cut" and utils.settings.hangout_mode:
            # Add any existing stuff to our actual chat history
            ooga_history.append([user_input, assistant_message, utils.settings.cur_tags,
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
        if utils.hotkeys.pull_next_press_input() or force_skip_streaming:
            force_skip_streaming = True
            break

        # Check if we need to break out due to RP suppression (if it different, then there is a suppression)
        if utils.settings.supress_rp and (supress_rp_as_others(assistant_message) != assistant_message):
            assistant_message = supress_rp_as_others(assistant_message)
            supressed_rp = True
            break


    # Redo it and skip
    if force_skip_streaming:
        force_skip_streaming = False
        print("\nSkipping message, redoing!\n")
        utils.zw_logging.update_debug_log("Got an input to regenerate! Re-generating the reply...")
        run_streaming(user_input, 1)
        return

    # Read the final sentence aloud (if it wasn't suppressed because of anti-RP rules)
    if not supressed_rp:
        s_assistant_message = emoji.replace_emoji(assistant_message, replace='')
        sentence_list = utils.voice_splitter.split_into_sentences(s_assistant_message)

        # Emotes
        if utils.settings.vtube_enabled:
            utils.vtube_studio.set_emote_string(s_assistant_message)
            utils.vtube_studio.check_emote_string_streaming()

        # Speaking
        if not main.live_pipe_no_speak:
            utils.voice.set_speaking(True)
            utils.voice.speak_line(sentence_list[-1], refuse_pause=True)

    # Print Newline
    print("\n")

    #
    # Set it to the assistant message (streamed response)
    received_message = assistant_message

    # Translate issues with the received message
    received_message = html.unescape(received_message)


    # If her reply is the same as the last stored one, run another request
    global stored_received_message

    if received_message == stored_received_message:
        print("\nBad message, redoing!\n")
        utils.zw_logging.update_debug_log("Bad message received; same as last attempted generation. Re-generating the reply...")
        run_streaming(user_input, 2)
        return

    stored_received_message = received_message


    # If her reply is the same as any in the past 20 chats, run another request
    if check_if_in_history(received_message):
        print("\nBad message, redoing!\n")
        utils.zw_logging.update_debug_log("Bad message received; same as a recent chat. Re-generating the reply...")
        run_streaming(user_input, 1)
        return

    # If her reply is blank, request another run, clearing the previous history add, and escape
    if len(received_message) < 3:
        print("\nBad message, redoing!\n")
        utils.zw_logging.update_debug_log("Bad message received; chat is a runt or blank entirely. Re-generating the reply...")
        run_streaming(user_input, 1)
        return



    # Log it to our history. Ensure it is in double quotes, that is how OOBA stores it natively
    log_user_input = "{0}".format(user_input)
    log_received_message = "{0}".format(received_message)

    ooga_history.append([log_user_input, log_received_message, utils.tag_task_controller.apply_tags(), "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())])

    # Run a pruning of the deletables
    prune_deletables()

    # Clear the currently sending message variable
    currently_sending_message = ""

    # Clear any token forcing
    force_token_count = False

    # Save
    save_histories()

    # We are ending our API request!
    is_in_api_request = False

#
# Handles all changes in the streamed updates
def streamed_update_handler(chunk, assistant_message):

    global currently_streaming_message
    global streaming_sentences_ticker

    # Update our two live text output spots
    print(chunk, end='', flush=True)

    currently_streaming_message = assistant_message
    s_assistant_message = emoji.replace_emoji(assistant_message, replace='')

    # Check if the generated update has added a new sentence.
    # If a complete new sentence is found, read it aloud
    sentence_list = utils.voice_splitter.split_into_sentences(s_assistant_message)

    if len(sentence_list) > streaming_sentences_ticker:
        streaming_sentences_ticker += 1

        # Emotes
        if utils.settings.vtube_enabled:
            utils.vtube_studio.set_emote_string(s_assistant_message)
            utils.vtube_studio.check_emote_string_streaming()

        if not main.live_pipe_no_speak:
            utils.voice.set_speaking(True)
            utils.voice.speak_line(sentence_list[-2], refuse_pause=True)

    if main.live_pipe_use_streamed_interrupt_watchdog and utils.hotkeys.SPEAK_TOGGLED:
        return "Cut"

    if flag_end_streaming:
        return "Hangout-Name-Cut"

    return "Continue"


def set_force_skip_streaming(tf_input):
    global force_skip_streaming
    force_skip_streaming = tf_input


def send_via_oogabooga(user_input):

    user_input = user_input

    # Write last, non-system message to RAG
    # NOTE: On re-opening, it will still add the latest message. This is fine! We are just always in debt 1 depth (except from when recalced)
    # NOTE: Not safe for undo! Undo will double paste the message! We have a manual check to not add duplicates now, although, if it is supposed to be a dupe then get rekt XD
    utils.based_rag.add_message_to_database()

    # RAG
    if utils.settings.rag_enabled:
        utils.based_rag.run_based_rag(user_input, ooga_history[len(ooga_history) - 1][1])

    # Run
    if not utils.settings.stream_chats:
        run(user_input, 0)
    if utils.settings.stream_chats:
        run_streaming(user_input, 0)

def receive_via_oogabooga():
    return received_message

def send_image_via_oobabooga(direct_talk_transcript):

    received_cam_message = ""
    if not utils.settings.stream_chats:
        received_cam_message = view_image(direct_talk_transcript)
    if utils.settings.stream_chats:
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
        if not utils.settings.stream_chats:
            view_image(cycle_message)
        if utils.settings.stream_chats:
            view_image_streaming(cycle_message)

        # 'scape from it
        return


    # Re-send the new message
    if not utils.settings.stream_chats:
        run(cycle_message, 0)
    if utils.settings.stream_chats:
        run_streaming(cycle_message, 0)


def undo_message():
    global ooga_history

    ooga_history.pop()

    # Fix the RAG database
    utils.based_rag.remove_latest_database_message()

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
        utils.based_rag.load_rag_history()

        # Make a quick backup of our file (if big enough, that way it won't clear if they happen to load again after it errors to 0 somehow)
        if len(ooga_history) > 30:
            # Export to JSON
            with open("LiveLogBackup.bak", 'w') as outfile:
                json.dump(ooga_history, outfile, indent=4)



def save_histories():

    # Export to JSON
    with open("LiveLog.json", 'w') as outfile:
        json.dump(ooga_history, outfile, indent=4)

    # Save RAG database too
    utils.based_rag.store_rag_history()



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

    # Saftey breaker for if the previous message was also a Soft Reset / System D
    if utils.cane_lib.keyword_check(ooga_history[-2][0], ["[System D]"]):
        print("\nStopping potential additional soft reset!\n")
        return

    print("\n\nRunning a soft reset of the chat system!\n")


    # Add in the soft reset messages
    # Cycle through all the configed messages and add them. Allows for (mostly) variable length

    for message_pair in soft_reset_message:

        ooga_history.append([message_pair[0], message_pair[1],  message_pair[1], utils.settings.cur_tags, "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())])



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
        if utils.cane_lib.keyword_check(ooga_history[i][0], ["[System D]"]):
            del ooga_history[i]
            i = len(ooga_history) - 27
            if i < 0:
                i = 0

        i = i + 1





    return



#
#   Other API Access
#

def summary_memory_run(messages_input, user_sent_message):
    global received_message
    global ooga_history
    global forced_token_level
    global force_token_count
    global currently_sending_message
    global last_message_streamed
    global currently_streaming_message
    global is_in_api_request

    # We are starting our API request!
    is_in_api_request = True

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

    if utils.settings.model_preset != "Default":
        preset = utils.settings.model_preset

    utils.zw_logging.kelvin_log = preset
    cur_tokens_required = utils.retrospect.summary_tokens_count

    #
    # NOTE: Does not use the character-task at the moment, be aware.
    #

    # Set the stop right
    stop = utils.settings.stopping_strings

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

        received_message = API.oobaooga_api.api_standard(request)

    elif API_TYPE == "Ollama":
        received_message = API.ollama_api.api_standard(history=messages_to_send, temp_level=0, stop=stop, max_tokens=cur_tokens_required)


    # Translate issues with the received message
    received_message = html.unescape(received_message)

    # If her reply contains RP-ing as other people, supress it form the message
    if utils.settings.supress_rp:
        received_message = supress_rp_as_others(received_message)

    # If her reply is the same as the last stored one, run another request
    global stored_received_message

    if received_message == stored_received_message:
        summary_memory_run(messages_input, user_sent_message)
        return

    # If her reply is the same as any in the past 20 chats, run another request
    if check_if_in_history(received_message):
        summary_memory_run(messages_input, user_sent_message)
        return

    # If her reply is blank, request another run, clearing the previous history add, and escape
    if len(received_message) < 3:
        summary_memory_run(messages_input, user_sent_message)
        return

    stored_received_message = received_message

    # Log it to our history. Ensure it is in double quotes, that is how OOBA stores it natively
    log_user_input = "{0}".format(user_sent_message)
    log_received_message = "{0}".format(received_message)

    ooga_history.append([log_user_input, log_received_message, utils.settings.cur_tags, "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())])

    # Run a pruning of the deletables
    prune_deletables()

    # Clear the currently sending message variable
    currently_sending_message = ""

    # Clear any token forcing
    force_token_count = False

    # Save
    save_histories()

    # We are ending our API request!
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

    # Write last, non-system message to RAG (Since this is going in addition)
    # NOTE: On re-opening, it will still add the latest message. This is fine! We are just always in debt 1 depth (except from when recalced)
    utils.based_rag.add_message_to_database()

    #
    # Prepare The Context
    #

    global ooga_history
    image_marker_length = 5     # shorting this so we don't take up a ton of context while image processing

    past_messages = []

    message_marker = len(ooga_history) - image_marker_length
    if message_marker < 0:  # if we bottom out, then we would want to start at 0 and go down. we check if i is less than, too
        message_marker = 0

    # Append our system message, if we are using OLLAMA
    if API_TYPE == "Ollama":
        past_messages.append({"role": "system", "content": vision_guidance_message + "\n\n" + API.character_card.character_card})

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
    if utils.settings.cam_direct_talk:
        base_prompt = direct_talk_transcript

    # Set the stop right
    stop = utils.settings.stopping_strings
    if utils.settings.newline_cut:
        stop.append("\n")
    if utils.settings.asterisk_ban:
        stop.append("*")


    # Send it in for viewing!

    received_cam_message = ""

    # Send the actual API Request
    if API_TYPE == "Oobabooga":

        # Append the image the good ol' way
        with open('LiveImage.png', 'rb') as f:
            img_str = base64.b64encode(f.read()).decode('utf-8')
            prompt = f'{base_prompt}<img src="data:image/jpeg;base64,{img_str}">'
            past_messages.append({"role": "user", "content": prompt})

        request = {
            'max_tokens': 300,
            'prompt': "This image",
            'messages': past_messages,
            'mode': 'chat-instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
            'character': VISUAL_CHARACTER_NAME,
            'your_name': YOUR_NAME,
            'regenerate': False,
            '_continue': False,
            'truncation_length': 2048,
            'stop': stop,

            'preset': VISUAL_PRESET_NAME
        }

        response = requests.post(IMG_URI, json=request)
        received_cam_message = response.json()['choices'][0]['message']['content']

    elif API_TYPE == "Ollama":

        # Append the image (via file path, so not for real but just link file)
        img_str = str(os.path.abspath('LiveImage.png'))
        past_messages.append({"role": "user", "content": base_prompt, "images": [img_str]})

        received_cam_message = API.ollama_api.api_standard_image(history=past_messages)


    # Translate issues with the received message
    received_cam_message = html.unescape(received_cam_message)

    # If her reply contains RP-ing as other people, supress it form the message
    if utils.settings.supress_rp:
        received_cam_message = supress_rp_as_others(received_cam_message)

    # Add Header
    # received_cam_message = "[System C] " + received_cam_message
    # No more headers! To stay consistent with streaming & modern good multimodal RP models with Ollama,
    # we don't need two-phasic image use anymore.



    # Write last, non-system message to RAG
    # NOTE: On re-opening, it will still add the latest message. This is fine! We are just always in debt 1 depth (except from when recalced)
    utils.based_rag.add_message_to_database()


    # Add to hist & such
    base_send = "[System C] Sending an image..."
    if utils.settings.cam_direct_talk:
        base_send = direct_talk_transcript

    # Prep with visual tag
    these_tags = utils.settings.cur_tags.copy()
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

    # Write last, non-system message to RAG (Since this is going in addition)
    # NOTE: On re-opening, it will still add the latest message. This is fine! We are just always in debt 1 depth (except from when recalced)
    utils.based_rag.add_message_to_database()

    #
    # Prepare The Context
    #

    global ooga_history
    image_marker_length = 5     # shorting this so we don't take up a ton of context while image processing

    past_messages = []

    message_marker = len(ooga_history) - image_marker_length
    if message_marker < 0:  # if we bottom out, then we would want to start at 0 and go down. we check if i is less than, too
        message_marker = 0

    # Append our system message, if we are using OLLAMA
    if API_TYPE == "Ollama":
        past_messages.append({"role": "system", "content": vision_guidance_message})

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
    if utils.settings.cam_direct_talk:
        base_prompt = direct_talk_transcript

    # Set the stop right
    stop = utils.settings.stopping_strings
    if utils.settings.newline_cut:
        stop.append("\n")
    if utils.settings.asterisk_ban:
        stop.append("*")

    supressed_rp = False

    # Send it in for viewing!

    received_cam_message = ""

    # Prep console with printing for message output

    print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--" + colorama.Fore.RESET
          + "----" + utils.settings.char_name + "----"
          + colorama.Fore.MAGENTA + colorama.Style.BRIGHT + "--\n" + colorama.Fore.RESET)

    # Reset the ticker (starts counting at 1)
    streaming_sentences_ticker = 1

    # Actual streaming bit

    # Reset the ticker (starts counting at 1)
    streaming_sentences_ticker = 1

    # Send the actual API Request
    if API_TYPE == "Oobabooga":
        with open('LiveImage.png', 'rb') as f:
            img_str = base64.b64encode(f.read()).decode('utf-8')
            prompt = f'{base_prompt}<img src="data:image/jpeg;base64,{img_str}">'
            past_messages.append({"role": "user", "content": prompt})

        request = {
            'max_tokens': 300,
            'prompt': "This image",
            'messages': past_messages,
            'mode': 'chat-instruct',  # Valid options: 'chat', 'chat-instruct', 'instruct'
            'character': VISUAL_CHARACTER_NAME,
            'your_name': YOUR_NAME,
            'regenerate': False,
            '_continue': False,
            'truncation_length': 2048,
            'stop': stop,

            'preset': VISUAL_PRESET_NAME,

            'stream': True,
        }

        # Actual streaming bit
        stream_response = requests.post(IMG_URI, headers=headers, json=request, verify=False, stream=True)
        client = sseclient.SSEClient(stream_response)

        streamed_api_stringpuller = client.events()


    elif API_TYPE == "Ollama":
        # Append the image (via file path, so not for real but just link file)
        img_str = str(os.path.abspath('LiveImage.png'))
        past_messages.append({"role": "user", "content": base_prompt, "images": [img_str]})

        streamed_api_stringpuller = API.ollama_api.api_stream_image(history=past_messages)


    # Clear streamed emote list
    utils.vtube_studio.clear_streaming_emote_list()

    assistant_message = ''
    force_skip_streaming = False
    supressed_rp = False
    for event in streamed_api_stringpuller:
        chunk = ""

        # Split based on API type
        if API_TYPE == "Oobabooga":
            payload = json.loads(event.data)
            chunk = payload['choices'][0]['delta']['content']

        elif API_TYPE == "Ollama":
            chunk = event['message']['content']


        assistant_message += chunk
        streamed_response_check = streamed_update_handler(chunk, assistant_message)
        if streamed_response_check == "Cut":

            # Clear the currently sending message variable
            currently_sending_message = ""

            # We are ending our API request!
            is_in_api_request = False

            return

        # Cut for the hangout name being said
        if streamed_response_check == "Hangout-Name-Cut" and utils.settings.hangout_mode:
            # Add any existing stuff to our actual chat history
            ooga_history.append([direct_talk_transcript, assistant_message, utils.settings.cur_tags, "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())])
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
        if utils.hotkeys.pull_next_press_input() or force_skip_streaming:
            force_skip_streaming = True
            break

        # Check if we need to break out due to RP suppression (if it different, then there is a suppression)
        if utils.settings.supress_rp and (supress_rp_as_others(assistant_message) != assistant_message):
            assistant_message = supress_rp_as_others(assistant_message)
            supressed_rp = True
            break

        # Redo it and skip
        if force_skip_streaming:
            force_skip_streaming = False
            print("\nSkipping message, redoing!\n")
            utils.zw_logging.update_debug_log("Got an input to regenerate! Re-generating the reply...")
            # Just set the message to be small, as this will force a re-run due to our while loop rules
            assistant_message = ""

    # Read the final sentence aloud (if not stopped by RP supr)
    if not supressed_rp:
        s_assistant_message = emoji.replace_emoji(assistant_message, replace='')
        sentence_list = utils.voice_splitter.split_into_sentences(s_assistant_message)

        # Emotes
        if utils.settings.vtube_enabled:
            utils.vtube_studio.set_emote_string(s_assistant_message)
            utils.vtube_studio.check_emote_string_streaming()

        # Speaking
        if not main.live_pipe_no_speak:
            utils.voice.set_speaking(True)
            utils.voice.speak_line(sentence_list[-1], refuse_pause=True)

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
    utils.based_rag.add_message_to_database()


    # Add to hist & such
    base_send = "[System C] Sending an image..."
    if utils.settings.cam_direct_talk:
        base_send = direct_talk_transcript

    # Prep with visual tag
    these_tags = utils.settings.cur_tags.copy()
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
def encode_new_api(user_input):

    #
    # Append 40 of the most recent history pairs (however long our marker length is)
    #

    global ooga_history

    #
    # Check for Ollama - if so, send it!
    if API_TYPE == "Ollama":
        return encode_new_api_ollama(user_input)

    messages_to_send = []

    message_marker = len(ooga_history) - marker_length
    if message_marker < 0:          # if we bottom out, then we would want to start at 0 and go down. we check if i is less than, too
        message_marker = 0

    messages_to_send.append({"role": "user", "content": ooga_history[message_marker][0]})
    messages_to_send.append({"role": "assistant", "content": ooga_history[message_marker][1]})

    i = 1
    while i < marker_length and i < len(ooga_history):
        messages_to_send.append({"role": "user", "content": ooga_history[message_marker + i][0]})
        messages_to_send.append({"role": "assistant", "content": ooga_history[message_marker + i][1]})

        if len(ooga_history[-1]) > 3 and i == marker_length - 3 and ENCODE_TIME == "ON":

            #
            # Append a relative timestamp, 3 or so back (to make it not super important)
            #

            timestamp_string = "The current time now is "
            current_time = datetime.datetime.now()
            timestamp_string += current_time.strftime("%d %B, %Y at %I:%M %p")
            timestamp_string += "."
            messages_to_send.append({"role": "user", "content": timestamp_string})

        if i == marker_length - 8:

            #
            # Append the lorebook in here, 8 or so back, it will include all lore in the given range
            #

            lore_gathered = utils.lorebook.lorebook_gather(ooga_history[-3:], user_input)

            if lore_gathered != utils.lorebook.total_lore_default:
                messages_to_send.append({"role": "user", "content": lore_gathered})
        
        if i == marker_length - 9:

            #
            # Append the RAG in here, 9 or so back, so it has no need to be saved & has good recall without upsetting spacing (only if RAG enabled)
            #

            if utils.settings.rag_enabled:
                messages_to_send.append({"role": "user", "content": utils.based_rag.call_rag_message()})

        i = i + 1


    #
    # Append our most recent message
    #

    messages_to_send.append({"role": "user", "content": user_input})

    return messages_to_send


def encode_new_api_ollama(user_input):
    #
    # Append 40 of the most recent history pairs (however long our marker length is)
    #

    global ooga_history

    messages_to_send = []

    # Append our system message, if we are using OLLAMA

    #
    # Gather and send our composite metadata!

    # Char card
    ollama_composite_content = API.character_card.character_card + "\n\n"

    # Task
    if utils.settings.cur_task_char != "" and utils.settings.cur_task_char != "None":
        ollama_composite_content += utils.tag_task_controller.get_cur_task_description() + "\n\n"

    # RAG Messegg
    if utils.settings.rag_enabled:
        ollama_composite_content += utils.based_rag.call_rag_message() + "\n\n"

    # Lorebook Gathering
    lore_gathered = utils.lorebook.lorebook_gather(ooga_history[-3:], user_input)

    if lore_gathered != utils.lorebook.total_lore_default:
        ollama_composite_content += lore_gathered + "\n\n"

    # Time
    if ENCODE_TIME:
        timestamp_string = "The current time now is "
        current_time = datetime.datetime.now()
        timestamp_string += current_time.strftime("%d %B, %Y at %I:%M %p")
        timestamp_string += "."
        ollama_composite_content += timestamp_string + "\n\n"

    # Appandage!
    messages_to_send.append({"role": "system", "content": ollama_composite_content})

    message_marker = len(ooga_history) - marker_length
    if message_marker < 0:  # if we bottom out, then we would want to start at 0 and go down. we check if i is less than, too
        message_marker = 0

    messages_to_send.append({"role": "user", "content": ooga_history[message_marker][0]})
    messages_to_send.append({"role": "assistant", "content": ooga_history[message_marker][1]})

    i = 1
    while i < marker_length and i < len(ooga_history):
        messages_to_send.append({"role": "user", "content": ooga_history[message_marker + i][0]})
        messages_to_send.append({"role": "assistant", "content": ooga_history[message_marker + i][1]})


        i = i + 1

    #
    # Append our most recent message
    #

    messages_to_send.append({"role": "user", "content": user_input})

    return messages_to_send


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
