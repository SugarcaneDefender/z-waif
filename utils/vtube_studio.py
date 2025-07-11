# Standard library imports
import asyncio
import json
import os
import threading
import time

# Third-party imports
import pyvts
from dotenv import load_dotenv

# Local imports - Utils modules
from utils import cane_lib

load_dotenv()

# Check if VTube Studio module is enabled before initializing
MODULE_VTUBE = os.environ.get("MODULE_VTUBE", "OFF").lower()
vtube_enabled = MODULE_VTUBE == "on"

# Only initialize VTS if the module is enabled
if vtube_enabled:
    VTS = pyvts.vts(
        plugin_info={
            "plugin_info": "Z-Waif",
            "developer": "SugarcaneDefender",
            "authentication_token_path": "./token.txt",
        },
        vts_api_info={
            "version": "1.0",
            "name": "VTubeStudioPublicAPI",
            "port": os.environ.get("VTUBE_STUDIO_API_PORT", 8001)
        }
    )
else:
    VTS = None

# NOTE: Emote ID is now just used for detection! There is now a list that can run multiple emotes at once!
EMOTE_ID = 2
EMOTE_STRING = ""
streaming_emote_list = []

emote_request_list = []

CUR_LOOK = 0
LOOK_LEVEL_ID = 1
look_start_id = int(os.environ.get("EYES_START_ID", "0"))

# Load in the EmoteLib from configurables
try:
    with open("Configurables/EmoteLib.json", 'r') as openfile:
        emote_lib = json.load(openfile)
except Exception as e:
    print(f"Warning: Could not load EmoteLib.json: {e}")
    emote_lib = []

# Starter Authentication

def run_vtube_studio_connection():
    """Run VTube Studio connection with proper error handling"""
    if not vtube_enabled:
        print("VTube Studio module is disabled. Skipping connection.")
        return
    
    if VTS is None:
        print("VTube Studio not initialized. Skipping connection.")
        return
    
    try:
        asyncio.run(vtube_studio_connection())
    except Exception as e:
        print(f"VTube Studio connection failed: {e}")
        # Don't retry if connection fails - this prevents the repeated error messages

async def vtube_studio_connection():
    """VTube Studio connection with timeout and error handling"""
    if not vtube_enabled or VTS is None:
        return
    
    try:
        # Add timeout to prevent hanging
        await asyncio.wait_for(VTS.connect(), timeout=5.0)
        await asyncio.wait_for(VTS.request_authenticate_token(), timeout=5.0)
        await asyncio.wait_for(VTS.request_authenticate(), timeout=5.0)
        await asyncio.wait_for(VTS.close(), timeout=5.0)
        print("VTube Studio connection successful")
    except asyncio.TimeoutError:
        print("VTube Studio connection timed out - VTube Studio may not be running")
    except Exception as e:
        print(f"VTube Studio connection error: {e}")
        # Don't retry - this prevents the repeated error messages

# Emote System

def set_emote_string(emote_string):
    global EMOTE_STRING
    EMOTE_STRING = emote_string

def check_emote_string():
    """Check emote string with proper error handling"""
    if not vtube_enabled:
        return

    # Setup our global
    global EMOTE_ID
    EMOTE_ID = -1

    emote_list = []

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
        if cane_lib.keyword_check(clean_emote_text, emote_page[0]) and not emote_list.__contains__(emote_page[1]):
            EMOTE_ID = emote_page[1]
            emote_list.append(emote_page[1])

    # If we got an emote, run it through the system
    if EMOTE_ID != -1:
        for inlist_emote in emote_list:
            emote_request_list.append(inlist_emote)

def check_emote_string_streaming():
    """Check emote string for streaming with proper error handling"""
    if not vtube_enabled:
        return
        
    global streaming_emote_list

    # Make our list
    emote_list = []

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
        if cane_lib.keyword_check(clean_emote_text, emote_page[0]) and not streaming_emote_list.__contains__(emote_page[1]):
            emote_list.append(emote_page[1])
            streaming_emote_list.append(emote_page[1])

    # Run the emotes, if we have any
    if len(emote_list) > 0:
        for inlist_emote in emote_list:
            emote_request_list.append(inlist_emote)

def clear_streaming_emote_list():
    global streaming_emote_list
    streaming_emote_list = []

# This is our basic loop to run emotes. Actually runs it in another thread; just called from main and then looped
def emote_runner_loop():
    """Emote runner loop with proper error handling"""
    if not vtube_enabled:
        print("VTube Studio module is disabled. Skipping emote runner loop.")
        return
        
    while True:
        time.sleep(0.001)

        if len(emote_request_list) > 0:
            this_emote = emote_request_list[-1]
            emote_request_list.pop()

            run_emote(this_emote)

def run_emote(inlist_emote):
    """Run emote with proper error handling"""
    if not vtube_enabled:
        return
        
    time.sleep(0.001)  # Mini Rest (frame pierce happened)

    try:
        asyncio.run(emote(inlist_emote))
    except Exception as e:
        print(f"Error running VTube Studio emote {inlist_emote}: {e}")
        time.sleep(0.002)

async def emote(inlist_emote):
    """Execute emote with proper error handling"""
    if not vtube_enabled or VTS is None:
        return
        
    try:
        await asyncio.wait_for(VTS.connect(), timeout=5.0)
        await asyncio.wait_for(VTS.request_authenticate(), timeout=5.0)
        response_data = await asyncio.wait_for(VTS.request(VTS.vts_request.requestHotKeyList()), timeout=5.0)
        hotkey_list = []
        for hotkey in response_data["data"]["availableHotkeys"]:
            hotkey_list.append(hotkey["name"])
        send_hotkey_request = VTS.vts_request.requestTriggerHotKey(hotkey_list[inlist_emote])
        await asyncio.wait_for(VTS.request(send_hotkey_request), timeout=5.0)
        await asyncio.wait_for(VTS.close(), timeout=5.0)
    except asyncio.TimeoutError:
        print(f"VTube Studio emote {inlist_emote} timed out")
    except Exception as e:
        print(f"VTube Studio emote {inlist_emote} error: {e}")

def change_look_level(value):
    """Change look level with proper error handling"""
    if not vtube_enabled:
        return

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

        # mini rest between
        time.sleep(0.001)

        # Start another thread for this look setting
        vtube_interaction_runner = threading.Thread(target=run_set_look)
        vtube_interaction_runner.daemon = True
        vtube_interaction_runner.start()

        LOOK_LEVEL_ID = new_look_ID

def run_clear_look():
    """Run clear look with proper error handling"""
    if not vtube_enabled:
        return
        
    try:
        asyncio.run(clear_look())
    except Exception as e:
        print(f"Error clearing VTube Studio look: {e}")

def run_set_look():
    """Run set look with proper error handling"""
    if not vtube_enabled:
        return
        
    try:
        asyncio.run(set_look())
    except Exception as e:
        print(f"Error setting VTube Studio look: {e}")

async def clear_look():
    """Remove the previous look emote with proper error handling"""
    if not vtube_enabled or VTS is None:
        return
        
    try:
        await asyncio.wait_for(VTS.connect(), timeout=5.0)
        await asyncio.wait_for(VTS.request_authenticate(), timeout=5.0)
        response_data = await asyncio.wait_for(VTS.request(VTS.vts_request.requestHotKeyList()), timeout=5.0)
        hotkey_list = []
        for hotkey in response_data["data"]["availableHotkeys"]:
            hotkey_list.append(hotkey["name"])
        send_hotkey_request = VTS.vts_request.requestTriggerHotKey(hotkey_list[CUR_LOOK])
        await asyncio.wait_for(VTS.request(send_hotkey_request), timeout=5.0)
        await asyncio.wait_for(VTS.close(), timeout=5.0)
    except asyncio.TimeoutError:
        print("VTube Studio clear look timed out")
    except Exception as e:
        print(f"VTube Studio clear look error: {e}")

async def set_look():
    """Set the new look emote with proper error handling"""
    if not vtube_enabled or VTS is None:
        return
        
    try:
        await asyncio.wait_for(VTS.connect(), timeout=5.0)
        await asyncio.wait_for(VTS.request_authenticate(), timeout=5.0)
        response_data = await asyncio.wait_for(VTS.request(VTS.vts_request.requestHotKeyList()), timeout=5.0)
        hotkey_list = []
        for hotkey in response_data["data"]["availableHotkeys"]:
            hotkey_list.append(hotkey["name"])
        send_hotkey_request = VTS.vts_request.requestTriggerHotKey(hotkey_list[LOOK_LEVEL_ID])
        await asyncio.wait_for(VTS.request(send_hotkey_request), timeout=5.0)
        await asyncio.wait_for(VTS.close(), timeout=5.0)
        
        global CUR_LOOK
        CUR_LOOK = LOOK_LEVEL_ID
    except asyncio.TimeoutError:
        print("VTube Studio set look timed out")
    except Exception as e:
        print(f"VTube Studio set look error: {e}")
