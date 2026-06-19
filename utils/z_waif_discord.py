# This example requires the 'message_content' intent.
import asyncio
import json
import os
import time

import discord
import main
import API.api_controller
import utils.settings

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

with open("Configurables/Tokens/Discord.json", 'r') as openfile:
    DISCORD_TOKEN = json.load(openfile)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    print("Processing discord message: " + message.content + "|| From " + message.author.name)

    if message.author == client.user:
        return

    # DO NOT RUN while we are in an active API request, it could crash!
    while main.is_live_pipe or API.api_controller.is_in_api_request:
        time.sleep(0.1)


    if (message.content == "/regen") or (message.content == "/reroll") or (message.content == "/redo"):

        # Typing indicator
        async with message.channel.typing():
            # Call in for the message to be sent
            main.main_discord_next()

            # Retrieve the result now
            message_reply = API.api_controller.receive_via_oogabooga()

        # Send it!
        await message.channel.send(message_reply)
        return

    if (message.content == "/allow_newlines"):

        # Toggle it
        utils.settings.newline_cut = False

        # Send it!
        await message.channel.send("New lines are toggled on!")
        return

    if (message.content == "/disallow_newlines") or (message.content == "/cut_newlines"):

        # Toggle it
        utils.settings.newline_cut = True

        # Send it!
        await message.channel.send("New lines are toggled on!")
        return

    # NOTE: Goes last in the order, as a catch-all for any faulty commands
    if (message.content == "/help") or (message.content[0] == "/") or (message.content[0] == "\\"):

        # Send it!
        await message.channel.send("Here is a list of the commands you can use:\n"
                                   "\n/regen = Regenerate the last message."
                                   "\n/reroll = Regenerate the last message."
                                   "\n/redo = Regenerate the last message."
                                   "\n"
                                   "\n/allow_newlines = Allow newline to be generated in the message."
                                   "\n/disallow_newlines = Disallow newline to be generated in the message."
                                   "\n/cut_newlines = Disallow newline to be generated in the message."
                                   "\n"
                                   "\n/help = List out usable commands."
                                   )

        return


    else:
        # Format our string
        sending_string = "[System Q] Discord message from " + message.author.name + "\n\n" + message.content

        # Typing indicator
        async with message.channel.typing():

            # Call in for the message to be sent
            main.main_discord_chat(sending_string)

            # Retrieve the result now
            message_reply = API.api_controller.receive_via_oogabooga()

        # Send it!
        await message.channel.send(message_reply)



def run_z_waif_discord():
    client.run(DISCORD_TOKEN)
