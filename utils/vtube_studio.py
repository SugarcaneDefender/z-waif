import utils.cane_lib
import asyncio,os,threading
import pyvts
import json
from dotenv import load_dotenv

VTS = pyvts.vts(
    plugin_info={
        "plugin_name": "Z-Waif",
        "developer": "sugarcanefarmer",
        "authentication_token_path": "./token.txt",
    },
    vts_api_info={
        "version": "1.0",
        "name": "VTubeStudioPublicAPI",
        "port": os.environ.get("VTUBE_STUDIO_API_PORT", 8001)
    }
)


load_dotenv()

global EMOTE_ID
EMOTE_ID = 2

global EMOTE_STRING
EMOTE_STRING = ""


# Load in the EmoteLib from configurables
with open("Configurables/EmoteLib.json", 'r') as openfile:
    emote_lib = json.load(openfile)



# Starter Authentication

def run_vtube_studio_connection():
    asyncio.run(vtube_studio_connection())

async def vtube_studio_connection():
    await VTS.connect()
    await VTS.request_authenticate_token()
    await VTS.request_authenticate()
    await VTS.close()


# Emote System

def set_emote_string(emote_string):
    global EMOTE_STRING
    EMOTE_STRING = emote_string

def check_emote_string():

    # Setup our global
    global EMOTE_ID
    EMOTE_ID = -1


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
        if utils.cane_lib.keyword_check(clean_emote_text, emote_page[0]):
            EMOTE_ID = emote_page[1]




    # If we got an emote, run it through the system
    if EMOTE_ID != -1:
        run_emote()


def run_emote():
    asyncio.run(emote())

async def emote():
    await VTS.connect()
    await VTS.request_authenticate()
    response_data = await VTS.request(VTS.vts_request.requestHotKeyList())
    hotkey_list = []
    for hotkey in response_data["data"]["availableHotkeys"]:
        hotkey_list.append(hotkey["name"])
    send_hotkey_request = VTS.vts_request.requestTriggerHotKey(hotkey_list[EMOTE_ID])
    await VTS.request(send_hotkey_request)

    await VTS.close()


