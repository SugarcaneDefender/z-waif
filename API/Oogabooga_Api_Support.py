import os
import html
import json
import base64
import time
import random

import requests
import utils.cane_lib
import utils.based_rag
import utils.logging
from dotenv import load_dotenv
import utils.settings
import utils.retrospect
import utils.lorebook


load_dotenv()

HOST = '127.0.0.1:5000'
URI = f'http://{HOST}/v1/chat/completions'
URL_MODEL = f'http://{HOST}/v1/engines/'

IMG_PORT = os.environ.get("IMG_PORT")
IMG_URI = f'http://{IMG_PORT}/v1/chat/completions'
IMG_URL_MODEL = f'http://{IMG_PORT}/v1/engines/'

received_message = ""
CHARACTER_CARD = os.environ.get("CHARACTER_CARD")
YOUR_NAME = os.environ.get("YOUR_NAME")

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

VISUAL_CHARACTER_NAME = os.environ.get("VISUAL_CHARACTER_NAME")
VISUAL_PRESET_NAME = os.environ.get("VISUAL_PRESET_NAME")

# Load in the configurable SoftReset message
with open("Configurables/SoftReset.json", 'r') as openfile:
    soft_reset_message = json.load(openfile)


def run(user_input, temp_level):
    global received_message
    global ooga_history
    global forced_token_level
    global force_token_count
    global currently_sending_message


    # Message that is currently being sent
    currently_sending_message = user_input

    # Load the history from JSON, to clean up the quotation marks

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

    utils.logging.kelvin_log = preset


    # Forced tokens check
    cur_tokens_required = utils.settings.max_tokens
    if force_token_count:
        cur_tokens_required = forced_token_level


    # Set the stop right
    stop = ["[System", "\nUser:", "---", "<|"]
    if utils.settings.newline_cut:
        stop = ["[System", "\nUser:", "---", "<|", "\n"]


    # Encode
    messages_to_send = encode_new_api(user_input)

    # Send the actual API Request

    request = {
        "messages": messages_to_send,
        'max_tokens': cur_tokens_required,
        'mode': 'chat',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'character': CHARACTER_CARD,
        'truncation_length': max_context,
        'stop': stop,

        'preset': preset
    }

    response = requests.post(URI, headers=headers, json=request, verify=False)


    if response.status_code == 200:
        received_message = response.json()['choices'][0]['message']['content']

        # Translate issues with the received message
        received_message = html.unescape(received_message)


        # If her reply contains RP-ing as other people, supress it form the message
        received_message = supress_rp_as_others(received_message)


        # If her reply is the same as the last stored one, run another request
        global stored_received_message

        if received_message == stored_received_message:
            run(user_input, 2)
            return

        stored_received_message = received_message


        # If her reply is the same as any in the past 20 chats, run another request
        if check_if_in_history(received_message):
            run(user_input, 1)
            return

        # If her reply is blank, request another run, clearing the previous history add, and escape
        if len(received_message) < 3:
            run(user_input, 1)
            return



        # Log it to our history. Ensure it is in double quotes, that is how OOBA stores it natively
        log_user_input = "{0}".format(user_input)
        log_received_message = "{0}".format(received_message)

        ooga_history.append([log_user_input, log_received_message])

        # Run a pruning of the deletables
        prune_deletables()

        # Clear the currently sending message variable
        currently_sending_message = ""

        # Clear any token forcing
        force_token_count = False

        # Save
        save_histories()





def send_via_oogabooga(user_input):

    user_input = user_input

    # Write last, non-system message to RAG
    # NOTE: On re-opening, it will still add the latest message. This is fine! We are just always in debt 1 depth (except from when recalced)
    # NOTE: Not safe for undo! Undo will double paste the message! We have a manual check to not add duplicates now, although, if it is supposed to be a dupe then get rekt XD
    utils.based_rag.add_message_to_database()

    # RAG
    utils.based_rag.run_based_rag(user_input, ooga_history[len(ooga_history) - 1][1])

    # Run
    run(user_input, 0)

def receive_via_oogabooga():
    return received_message


def next_message_oogabooga():
    global ooga_history

    # Record & Clear the old message

    print("Generating Replacement Message!")
    cycle_message = ooga_history[-1][0]
    ooga_history.pop()

    # Save
    save_histories()


    # Re-send the new message
    run(cycle_message, 1)


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

        ooga_history.append([message_pair[0], message_pair[1]])



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

    # Set the currently sending message
    currently_sending_message = user_sent_message

    # Load the history from JSON, to clean up the quotation marks

    with open("LiveLog.json", 'r') as openfile:
        ooga_history = json.load(openfile)

    # Determine what preset we want to load in with

    preset = 'Z-Waif-ADEF-Standard'

    if utils.settings.model_preset != "Default":
        preset = utils.settings.model_preset

    utils.logging.kelvin_log = preset
    cur_tokens_required = utils.retrospect.summary_tokens_count

    # Set the stop right
    stop = ["[System", "\nUser:", "---", "<|"]

    # Encode
    messages_to_send = messages_input

    # Send the actual API Request

    request = {
        "messages": messages_to_send,
        'max_tokens': cur_tokens_required,
        'mode': 'chat',  # Valid options: 'chat', 'chat-instruct', 'instruct'
        'character': CHARACTER_CARD,
        'truncation_length': max_context,
        'stop': stop,

        'preset': preset
    }

    response = requests.post(URI, headers=headers, json=request, verify=False)

    if response.status_code == 200:
        received_message = response.json()['choices'][0]['message']['content']

        # Translate issues with the received message
        received_message = html.unescape(received_message)

        # If her reply contains RP-ing as other people, supress it form the message
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

        ooga_history.append([log_user_input, log_received_message])

        # Run a pruning of the deletables
        prune_deletables()

        # Clear the currently sending message variable
        currently_sending_message = ""

        # Clear any token forcing
        force_token_count = False

        # Save
        save_histories()



def swap_language_model(model_ID):

    # Setup and send the JSON request

    print("Swapping model!")
    model_name = "none_model"

    if model_ID == 0:

        model_name = 'LoneStriker_Loyal-Macaroni-Maid-7B-5.0bpw-h6-exl2'

        request = {
            'action': 'load',
            'model_name': model_name,

            'args': {
                'loader': 'ExLlamav2_HF',

                'cache_8bit': True,
                'disable_exllama': False,
                'disable_exllamav2': False,
                'max_seq_len': max_context,
                'truncation_length': max_context

                }
        }

    elif model_ID == 1:

        model_name = 'TheBloke_vicuna-7B-1.1-GPTQ'

        request = {
            'action': 'load',
            'model_name': model_name,

            'args': {
                'loader': 'AutoGPTQ',

                'load_in_4bit': True,
                'disable_exllama': True,
                'disable_exllamav2': True,
                'max_seq_len': max_context,
                'truncation_length': max_context

                }

        }


    model_string = URL_MODEL + model_name
    print(model_string)

    #   Can be used to see the output of the change (and all the config it has)
    response = requests.post(model_string, json=request)
    print(response.json())
    time.sleep(10)


def view_image(direct_talk_transcript):

    global ooga_history

    # Write last, non-system message to RAG (Since this is going in addition)
    # NOTE: On re-opening, it will still add the latest message. This is fine! We are just always in debt 1 depth (except from when recalced)
    utils.based_rag.add_message_to_database()

    #
    # Prepare The Context
    #

    global ooga_history
    image_marker_length = 3     # shorting this so we don't take up a ton of context

    message_marker = len(ooga_history) - image_marker_length
    if message_marker < 0:  # if we bottom out, then we would want to start at 0 and go down. we check if i is less than, too
        message_marker = 0

    past_messages = [
        {"role": "user", "content": ooga_history[message_marker][0]},
        {"role": "assistant", "content": ooga_history[message_marker][1]},
    ]

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


    with open('LiveImage.png', 'rb') as f:
        img_str = base64.b64encode(f.read()).decode('utf-8')
        prompt = f'{base_prompt}<img src="data:image/jpeg;base64,{img_str}">'
        past_messages.append({"role": "user", "content": prompt})


    # Stopping Strings (real important, early vicuna is godlike but also starts to get derailed.

    # Set the stop right
    stop = ["[System", "Human:", "---", "Assistant:", "###"]



    # Send it in for viewing!

    received_cam_message = ""
    while len(received_cam_message) < 9:    # must not be a blank reply

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

        # Translate issues with the received message
        received_cam_message = html.unescape(received_cam_message)


    # Add Header
    received_cam_message = "[System C] " + received_cam_message



    # Write last, non-system message to RAG
    # NOTE: On re-opening, it will still add the latest message. This is fine! We are just always in debt 1 depth (except from when recalced)
    utils.based_rag.add_message_to_database()


    # Add to hist & such
    base_send = "[System C] Sending an image..."
    if utils.settings.cam_direct_talk:
        base_send = direct_talk_transcript

    ooga_history.append([base_send, received_cam_message])


    # Save
    save_histories()


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

    message_marker = len(ooga_history) - marker_length
    if message_marker < 0:          # if we bottom out, then we would want to start at 0 and go down. we check if i is less than, too
        message_marker = 0

    messages_to_send = [
        {"role": "user", "content": ooga_history[message_marker][0]},
        {"role": "assistant", "content": ooga_history[message_marker][1]},
    ]

    i = 1
    while i < marker_length and i < len(ooga_history):
        messages_to_send.append({"role": "user", "content": ooga_history[message_marker + i][0]})
        messages_to_send.append({"role": "assistant", "content": ooga_history[message_marker + i][1]})

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

    # do not supress if we have newlines enabled
    if not utils.settings.newline_cut:
        return message

    # do nut supress if there is no colon
    if not message.__contains__(":"):
        return message


    # Remove any text past a newline with a person's name
    i = 1
    counter_watchdog = 0
    message_cutoff_marker = 0
    message_cutoff_enabled = False

    while i < len(message):

        if (message[i] == "\n") and (message_cutoff_enabled == False) and (message[i-1] != ":"):
            counter_watchdog = 27
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

