# This example requires the 'message_content' intent.
import asyncio
import os

import discord
import main
import API.Oogabooga_Api_Support

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    print("Processing discord message: " + message.content + "|| From " + message.author.name)

    if message.author == client.user:
        return


    if (message.content == "/regen") or (message.content == "/reroll") or (message.content == "/redo"):

        # Typing indicator
        async with message.channel.typing():
            # Call in for the message to be sent
            main.main_discord_next()

            # Retrieve the result now
            message_reply = API.Oogabooga_Api_Support.receive_via_oogabooga()

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
            message_reply = API.Oogabooga_Api_Support.receive_via_oogabooga()

        # Send it!
        await message.channel.send(message_reply)



def run_z_waif_discord():
    client.run(DISCORD_TOKEN)
