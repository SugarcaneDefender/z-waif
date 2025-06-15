# Standard library imports
import asyncio
import os
import random

# Third-party imports
import twitchio
from twitchio.ext import commands  # type: ignore
from dotenv import load_dotenv

# Local imports - Main module
import main

# Local imports - Utils modules
from utils import uni_pipes

load_dotenv()

#
#   NOTE: This is the experimental version of this script, that has been simplified.
#   It does not contain all the bells and whistles of the main branch,
#   but it should be more stable and easier to maintain.
#

TWITCH_TOKEN = os.getenv("TWITCH_TOKEN", "")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL", "")
TWITCH_CLIENT_ID = os.environ.get('TWITCH_CLIENT_ID', "")

# Global variable to store the bot instance for sending messages
bot_instance = None

class TwitchBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=TWITCH_TOKEN,
            client_id=TWITCH_CLIENT_ID,
            nick=TWITCH_CHANNEL,
            prefix='!',
            initial_channels=[TWITCH_CHANNEL]
        )

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')

    async def event_message(self, message: twitchio.Message):  # type: ignore
        if message.echo:
            return

        print(f"[Twitch] Received: {message.author.name}: {message.content}")

        # Basic command handling
        if message.content.startswith('!hello'):
            await message.channel.send(f'Hello @{message.author.name}!')
            return

        # Enhanced Twitch message handling with better error handling
        try:
            # Always process messages (removed uni_pipes check as it was causing issues)
            formatted_message = f"{message.author.name}: {message.content}"
            print(f"[Twitch] Processing message: {formatted_message}")
            
            # Call Twitch chat handler
            reply = main.main_twitch_chat(formatted_message)
            
            print(f"[Twitch] AI replied with: {reply}")
            
            # Send the reply back to Twitch chat if we got one
            if reply and reply.strip():
                # Limit length for Twitch (500 char limit)
                if len(reply) > 400:
                    reply = reply[:400] + "..."
                
                try:
                    await message.channel.send(reply)
                    print(f"[Twitch] Successfully sent reply: {reply}")
                except Exception as e:
                    print(f"[Twitch] Failed to send reply: {e}")
                    # Try to send a fallback message
                    try:
                        await message.channel.send("Sorry, I'm having trouble responding right now.")
                    except Exception as fallback_error:
                        print(f"[Twitch] Failed to send fallback message: {fallback_error}")
            else:
                print("[Twitch] No reply generated or reply was empty")
                
        except Exception as e:
            print(f"[Twitch] Error processing message: {e}")
            try:
                await message.channel.send("Sorry, I encountered an error processing your message.")
            except Exception as send_error:
                print(f"[Twitch] Failed to send error message to chat: {send_error}")

        await self.handle_commands(message)

def run_twitch_bot():
    """Initializes and runs the Twitch bot."""
    global bot_instance
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    bot_instance = TwitchBot()
    try:
        loop.run_until_complete(bot_instance.start())
    except twitchio.errors.AuthenticationError as e:
        print(f"Failed to start Twitch bot: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in Twitch bot: {e}")
    finally:
        loop.close()

def run_z_waif_twitch():
    """Entry point to run the Twitch bot in a separate thread."""
    print("Twitch bot thread started")
    run_twitch_bot()
