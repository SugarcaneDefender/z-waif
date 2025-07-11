# Support for playing Minecraft!

# Standard library imports
import json
import time

# Third-party imports
import pygetwindow
from pythmc import ChatLink

# Local imports - API modules
import API.api_controller

# Local imports - Main module
# import main

# Local imports - Utils modules
from utils import cane_lib
from utils import settings
from utils.minecraft import process_minecraft_message

if settings.minecraft_enabled:
    chat = ChatLink()  # Initialises an instance of ChatLink, to take control of the Minecraft Chat.

last_chat = "None!"
remembered_messages = ["", "Minecraft Chat Loaded!"]

# Load the configurable MC names
with open("Configurables/MinecraftNames.json", 'r') as openfile:
    mc_names = json.load(openfile)

with open("Configurables/MinecraftUsername.json", 'r') as openfile:
    username_data = json.load(openfile)
    # Handle both old string format and new object format
    if isinstance(username_data, dict):
        mc_username = username_data.get("username", "BotUsernameHere")
    else:
        mc_username = username_data

with open("Configurables/MinecraftUsernameFollow.json", 'r') as openfile:
    follow_data = json.load(openfile)
    # Handle both old string format and new object format
    if isinstance(follow_data, dict):
        mc_username_follow = follow_data.get("username", "YourUsernameHere")
    else:
        mc_username_follow = follow_data

def check_for_command(message):

    if str(message).__contains__("#") or str(message).__contains__("/"):

        # Search for the command
        i = 0
        word_collector = ""
        word_collector_on = False

        # Look for stopping, either spaces or end of message
        while i < len(message):

            # Collect once we have got our hashtag for our command
            if (message[i] == "#" or message[i] == "/") or word_collector_on == True:

                if message[i] == "\"":
                    word_collector_on = False

                else:
                    word_collector_on = True
                    word_collector += message[i]

            # Continue
            i = i + 1

        if word_collector.__contains__("#follow"):
            word_collector = "#follow player " + mc_username_follow

        if word_collector.__contains__("#drop"):
            word_collector = ".drop"


        try:
            chat.send(word_collector)
        except Exception as e:
            print(f"No MC Client or error sending command: {e}")




def chat_check_loop():

    while True:
        # Loop every 0.1 seconds
        time.sleep(0.1)

        # Check
        if settings.minecraft_enabled:
            check_mc_chat()


def check_mc_chat():

    global last_chat
    global remembered_messages

    # Returns a list of messages from the in-game chat.
    message_list = chat.get_history(limit=10)

    if message_list is None:
        message_list = ["None!"]


    # Check Output 1 to see how it looks!
    combined_message = ""
    last_sent = ""
    temp_remembered_messages = ["", "Minecraft Chat Loaded!"]

    i = 0
    for message in message_list:

        add_message = True

        # do not add our own messages, as those are already tracked
        if cane_lib.keyword_check(message.content, ["<" + mc_username + ">", mc_username + "\u00a7r\u00a7r:"]):
            add_message = False

        # do not add in remembered messages, as those are already tracked
        for remembered_message in remembered_messages:
            if message.content == remembered_message:
                add_message = False


        if add_message:
            combined_message += message.content + "\n"
            temp_remembered_messages.append(message.content)         # rember this for later, so we can filter it out from new context


        i = i + 1
        if i == 10:
            last_sent = message.content


    temp_remembered_messages = temp_remembered_messages[2:]    # Cut off the starting bits of it


    if last_sent == last_chat:
        return
    else:
        last_chat = last_sent

        # Check if we should process this message based on shadow chat settings
        if cane_lib.keyword_check(last_sent, mc_names) and not cane_lib.keyword_check(last_sent, ["<" + mc_username + ">", mc_username + "\u00a7r\u00a7r:"]):
            
            # Check shadow chat settings
            if not settings.speak_shadowchats and not cane_lib.keyword_check(last_sent, [settings.char_name]):
                print(f"[MINECRAFT] Skipping message due to shadow chat settings")
                return

            # Check speak only when spoken to
            if settings.speak_only_spokento and not cane_lib.keyword_check(last_sent, [settings.char_name]):
                print(f"[MINECRAFT] Skipping message - not spoken to directly")
                return

            # Send a MC specific message
            process_minecraft_message(combined_message)

            # make the remembered messages be added to the memory, and set it to be only the past ten messages

            for message in temp_remembered_messages:
                remembered_messages.append(message)

            remembered_messages = remembered_messages[-10:]

def minecraft_chat():

    message = API.api_controller.receive_via_oogabooga()
    chat.send(message)

