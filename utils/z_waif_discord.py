# This example requires the 'message_content' intent.
import asyncio
import json
import os
import time

import discord
import main
import API.api_controller

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
