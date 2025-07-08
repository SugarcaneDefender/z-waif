# This example requires the 'message_content' intent.
import asyncio
import json
import os
import time
from dotenv import load_dotenv

import discord
import main
import API.api_controller

# Load environment variables
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Get Discord token from environment variable
discord_enabled_string = os.environ.get("MODULE_DISCORD")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DISCORD_CHANNEL = os.environ.get("DISCORD_CHANNEL", None)  # Optional specific channel

if discord_enabled_string == "ON":
    if not DISCORD_TOKEN:
        print("[DISCORD] Error: DISCORD_TOKEN not found in environment variables!")
        print("[DISCORD] Please set DISCORD_TOKEN in your .env file")
    else:
        print("[DISCORD] Discord token loaded successfully")

@client.event
async def on_ready():
    print(f'[DISCORD] We have logged in as {client.user}')
    print(f'[DISCORD] Bot is ready and listening for messages')
    if DISCORD_CHANNEL:
        print(f'[DISCORD] Will respond in channel: {DISCORD_CHANNEL}')
    else:
        print(f'[DISCORD] Will respond in all channels')

@client.event
async def on_message(message):
    print(f"[DISCORD] Processing message: {message.content} || From: {message.author.name} || Channel: {message.channel.name}")

    # Don't respond to our own messages
    if message.author == client.user:
        return

    # If DISCORD_CHANNEL is set, only respond in that channel
    if DISCORD_CHANNEL and message.channel.name != DISCORD_CHANNEL:
        print(f"[DISCORD] Ignoring message from channel '{message.channel.name}' (only responding in '{DISCORD_CHANNEL}')")
        return

    # DO NOT RUN while we are in an active API request, it could crash!
    while main.is_live_pipe or API.api_controller.is_in_api_request:
        time.sleep(0.1)

    try:
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
            # Format our string with platform context for better responses
            sending_string = f"[Platform: Discord] {message.content}"

            # Typing indicator
            async with message.channel.typing():

                # Call in for the message to be sent
                main.main_discord_chat(sending_string)

                # Retrieve the result now
                message_reply = API.api_controller.receive_via_oogabooga()

            # Clean and send the response
            if message_reply:
                # Apply Discord-specific cleaning
                cleaned_reply = main.clean_discord_response(message_reply)
                await message.channel.send(cleaned_reply)
            else:
                await message.channel.send("Sorry, I'm having trouble responding right now.")

    except Exception as e:
        print(f"[DISCORD] Error processing message: {e}")
        await message.channel.send("Sorry, something went wrong while processing your message.")

def run_z_waif_discord():
    if not DISCORD_TOKEN:
        print("[DISCORD] Cannot start Discord bot: No token provided")
        return
    
    try:
        print("[DISCORD] Starting Discord bot...")
        client.run(DISCORD_TOKEN)
    except discord.LoginFailure:
        print("[DISCORD] Failed to login: Invalid Discord token")
    except Exception as e:
        print(f"[DISCORD] Error starting Discord bot: {e}")
