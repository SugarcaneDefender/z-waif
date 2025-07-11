import os
from dotenv import load_dotenv

load_dotenv()

# Print relevant environment variables
print("\n=== Environment Variables ===")
print(f"MODULE_DISCORD: {os.getenv('MODULE_DISCORD')}")
print(f"DISCORD_TOKEN: {os.getenv('DISCORD_TOKEN')}")
print(f"MODULE_TWITCH: {os.getenv('MODULE_TWITCH')}")
print(f"TWITCH_TOKEN: {os.getenv('TWITCH_TOKEN')}")
print(f"TWITCH_CLIENT_ID: {os.getenv('TWITCH_CLIENT_ID')}")
print(f"TWITCH_CHANNEL: {os.getenv('TWITCH_CHANNEL')}")
print("===========================\n") 