# Support for playing Minecraft!

from pythmc import ChatLink
import pygetwindow
import utils.cane_lib
import time
import main
import API.Oogabooga_Api_Support
import utils.settings
import json

from utils.settings import minecraft_enabled

if minecraft_enabled:
    chat = ChatLink()  # Initialises an instance of ChatLink, to take control of the Minecraft Chat.

last_chat = "None!"
remembered_messages = ["", "Minecraft Chat Loaded!"]

# Load the configurable MC names
with open("Configurables/MinecraftNames.json", 'r') as openfile:
    mc_names = json.load(openfile)

with open("Configurables/MinecraftUsername.json", 'r') as openfile:
    mc_username = json.load(openfile)

with open("Configurables/MinecraftUsernameFollow.json", 'r') as openfile:
    mc_username_follow = json.load(openfile)

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
        except:
            print("No MC Client!")




def chat_check_loop():

    while True:
        # Loop every 0.1 seconds
        time.sleep(0.1)

        # Check
        if utils.settings.minecraft_enabled:
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
        if utils.cane_lib.keyword_check(message.content, ["<" + mc_username + ">", mc_username + "\u00a7r\u00a7r:"]):
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

        if utils.cane_lib.keyword_check(last_sent, mc_names) and not utils.cane_lib.keyword_check(last_sent, ["<" + mc_username + ">", mc_username + "\u00a7r\u00a7r:"]):

            # Send a MC specific message
            main.main_minecraft_chat(combined_message)

            # make the remembered messages be added to the memory, and set it to be only the past ten messages

            for message in temp_remembered_messages:
                remembered_messages.append(message)

            remembered_messages = remembered_messages[-10:]

def minecraft_chat():

    message = API.Oogabooga_Api_Support.receive_via_oogabooga()
    chat.send(message)

