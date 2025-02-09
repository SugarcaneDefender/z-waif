import time
from typing import Any

import utils.cane_lib
import asyncio,os,threading
import pyvts # type: ignore
import json
from dotenv import load_dotenv

VTS = pyvts.vts(
    plugin_info={
        "plugin_name": "Z-Waif",
        "developer": "SugarcaneDefender",
        "authentication_token_path": "./token.txt",
    },
    vts_api_info={
        "version": "1.0",
        "name": "VTubeStudioPublicAPI",
        "port": os.environ.get("VTUBE_STUDIO_API_PORT", 8001)
    }
)


load_dotenv()

# NOTE: Emote ID is now just used for detection! There is now a list that can run multiple emotes at once!
EMOTE_ID = 2
EMOTE_STRING = ""
streaming_emote_list: list[int] = []

emote_request_list: list[int] = []

CUR_LOOK = 0
LOOK_LEVEL_ID = 1
look_start_id = int(os.environ.get("EYES_START_ID", 14))


# Load in the EmoteLib from configurables
with open("Configurables/EmoteLib.json", 'r') as openfile:
    """
    [
        [
            [
                "Pog",
                "Surprise"
            ],
            9
        ],
        ...
    ]
    """
    emote_lib: list[list[list[str]|int]] = json.load(openfile)



# Starter Authentication

def run_vtube_studio_connection():
    asyncio.run(vtube_studio_connection())

async def vtube_studio_connection():
    await VTS.connect()
    await VTS.request_authenticate_token()
    await VTS.request_authenticate()
    await VTS.close()


# Emote System

def set_emote_string(emote_string: str):
    global EMOTE_STRING
    EMOTE_STRING = emote_string # type: ignore

def check_emote_string():

    # Setup our global
    global EMOTE_ID
    EMOTE_ID = -1 # type: ignore

    emote_list: list[int] = []


    # Cleanup the text to only look at the asterisk'ed words

    clean_emote_text = ''
    asterisk_count = 0

    for char in EMOTE_STRING:
        if char == "*":
            asterisk_count += 1
        elif asterisk_count % 2 == 1:
            clean_emote_text = clean_emote_text + char


    # Run through emotes, using OOP to only run one at a time (last = most prominent)

    for emote_page in emote_lib:
        if utils.cane_lib.keyword_check(clean_emote_text, emote_page[0]) and not emote_list.__contains__(emote_page[1]): # type: ignore
            EMOTE_ID = emote_page[1] # type: ignore
            emote_list.append(emote_page[1]) # type: ignore

    # If we got an emote, run it through the system
    if EMOTE_ID != -1:
        for inlist_emote in emote_list:
            emote_request_list.append(inlist_emote)

def check_emote_string_streaming():
    global streaming_emote_list

    # Make our list
    emote_list: list[int] = []

    # Cleanup the text to only look at the asterisk'ed words
    clean_emote_text = ''
    asterisk_count = 0

    for char in EMOTE_STRING:
        if char == "*":
            asterisk_count += 1
        elif asterisk_count % 2 == 1:
            clean_emote_text = clean_emote_text + char

    # Check if there is an emote that we DON'T have in the streaming one!
    for emote_page in emote_lib:
        if utils.cane_lib.keyword_check(clean_emote_text, emote_page[0]) and not streaming_emote_list.__contains__(emote_page[1]): # type: ignore
            emote_list.append(emote_page[1]) # type: ignore
            streaming_emote_list.append(emote_page[1]) # type: ignore

    # Run the emotes, if we have any
    if len(emote_list) > 0:
        for inlist_emote in emote_list:
            emote_request_list.append(inlist_emote)


def clear_streaming_emote_list():
    global streaming_emote_list
    streaming_emote_list = []


#
# This is our basic loop to run emotes. Actually runs it in another thread; just called from main and then looped
def emote_runner_loop():
    while True:
        time.sleep(0.001)

        if len(emote_request_list) > 0:
            this_emote = emote_request_list[-1]
            emote_request_list.pop()

            run_emote(this_emote)




def run_emote(inlist_emote: int):
    time.sleep(0.001)  # Mini Rest (frame pierce happened)

    try:
        asyncio.run(emote(inlist_emote))

    except:
        time.sleep(0.002)

    # ^^^ Runs the emote, if there is an error allow a small rest

async def emote(inlist_emote: int):
    await VTS.connect()
    await VTS.request_authenticate()
    response_data: dict[str,dict[str, Any]] = await VTS.request(VTS.vts_request.requestHotKeyList()) # type: ignore
    hotkey_list: list[str] = []
    for hotkey in response_data["data"]["availableHotkeys"]:
        hotkey_list.append(hotkey["name"])
    send_hotkey_request = VTS.vts_request.requestTriggerHotKey(hotkey_list[inlist_emote]) # type: ignore
    await VTS.request(send_hotkey_request) # type: ignore

    await VTS.close()

def change_look_level(value: float):

    # Inputting value should be from -1 to 1
    # We translate to what the look level should be here

    new_look_ID = -1

    if value < -0.67:
        new_look_ID = 5
    elif value < -0.4:
        new_look_ID = 4
    elif value < -0.2:
        new_look_ID = 3
    elif value > 0.67:
        new_look_ID = 2
    elif value > 0.4:
        new_look_ID = 1
    elif value > 0.2:
        new_look_ID = 0

    global LOOK_LEVEL_ID, CUR_LOOK

    if LOOK_LEVEL_ID != new_look_ID:

        # Start another thread for this look clearing
        vtube_interaction_runner = threading.Thread(target=run_clear_look)
        vtube_interaction_runner.daemon = True
        vtube_interaction_runner.start()

        #mini rest between
        time.sleep(0.017)

        LOOK_LEVEL_ID = new_look_ID

        # only change if we are not at center
        if new_look_ID != -1:
            # Start another thread for this look
            vtube_interaction_runner = threading.Thread(target=run_set_look)
            vtube_interaction_runner.daemon = True
            vtube_interaction_runner.start()
        else:
            CUR_LOOK = 0




def run_clear_look():
    time.sleep(0.001)  # Mini Rest (frame pierce happened)

    try:
        asyncio.run(clear_look())

    except:
        time.sleep(0.002)

    # ^^^ Runs the emote, if there is an error allow a small rest

def run_set_look():
    time.sleep(0.001)  # Mini Rest (frame pierce happened)

    try:
        asyncio.run(set_look())

    except:
        time.sleep(0.002)

    # ^^^ Runs the emote, if there is an error allow a small rest


async def clear_look():
    # Remove the previous look emote

    await VTS.connect()
    await VTS.request_authenticate()

    response_data = await VTS.request(VTS.vts_request.requestHotKeyList())
    hotkey_list = []

    # Do not trigger if the curlook is 0 (or it will trigger the first emote due to framepiercing)
    if CUR_LOOK != 0:
        for hotkey in response_data["data"]["availableHotkeys"]:
            hotkey_list.append(hotkey["name"])
        send_hotkey_request = VTS.vts_request.requestTriggerHotKey(hotkey_list[CUR_LOOK])
        await VTS.request(send_hotkey_request)

    await VTS.close()


async def set_look():
    await VTS.connect()
    await VTS.request_authenticate()


    # Make this configurable. The start of the section of emotes where the looking works
    global look_start_id
    new_look_id = look_start_id + LOOK_LEVEL_ID

    response_data = await VTS.request(VTS.vts_request.requestHotKeyList())
    hotkey_list = []
    for hotkey in response_data["data"]["availableHotkeys"]:
        hotkey_list.append(hotkey["name"])
    send_hotkey_request = VTS.vts_request.requestTriggerHotKey(hotkey_list[new_look_id])
    await VTS.request(send_hotkey_request)

    global CUR_LOOK
    CUR_LOOK = new_look_id

    await VTS.close()
