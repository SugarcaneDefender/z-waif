# This example requires the 'message_content' intent.
import json

import discord
import main

from API import backend

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

with open("Configurables/Tokens/Discord.json", 'r') as openfile:
    DISCORD_TOKEN = json.load(openfile)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message: discord.Message):
    print("Processing discord message: " + message.content + "|| From " + message.author.name)

    if message.author == client.user:
        return


    if (message.content == "/regen") or (message.content == "/reroll") or (message.content == "/redo"):

        # Typing indicator
        async with message.channel.typing():
            # Call in for the message to be sent
            main.main_discord_next()

            # Retrieve the result now
            message_reply = backend.receive()

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
            message_reply = backend.receive()

        # Send it!
        await message.channel.send(message_reply)



def run_z_waif_discord():
    client.run(DISCORD_TOKEN)
