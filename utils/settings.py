import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API settings
API_TYPE = os.getenv("API_TYPE", "Oobabooga")  # Default to Oobabooga if not set
HOST_PORT = os.getenv("HOST_PORT", "127.0.0.1:50534")  # Default to the running server port

# Character settings
char_name = os.getenv("CHAR_NAME", "")

# General settings
hotkeys_locked = False
speak_shadowchats = False
speak_only_spokento = False

max_tokens = 300
stream_chats = True
newline_cut = False
asterisk_ban = False
supress_rp = False
stopping_strings = ["[System", "\nUser:", "---", "<|", "###"]

semi_auto_chat = False
hangout_mode = False

autochat_mininum_chat_frames = 149
use_silero_vad = True

alarm_time = "09:09"
model_preset = "Default"

# Camera settings
cam_use_image_feed = False
cam_direct_talk = True
cam_image_preview = True
cam_use_screenshot = False
# cam_reply_after = False

# Valid values; "Faces", "Random", "None"
eyes_follow = "None"

# Tags and tasks
all_tag_list = []
cur_tags = []
all_task_char_list = []
cur_task_char = "None"

# Gaming
is_gaming_loop = False

# Module settings
minecraft_enabled = False
gaming_enabled = True
alarm_enabled = True
vtube_enabled = True
discord_enabled = True
twitch_enabled = os.getenv("MODULE_TWITCH", "OFF").upper() == "ON"
rag_enabled = True
vision_enabled = True

# Twitch-specific settings
TWITCH_ENABLED = twitch_enabled
twitch_personality = os.getenv("TWITCH_PERSONALITY", "friendly")
twitch_auto_respond = os.getenv("TWITCH_AUTO_RESPOND", "ON").upper() == "ON"
twitch_response_chance = float(os.getenv("TWITCH_RESPONSE_CHANCE", "0.8"))
twitch_cooldown_seconds = int(os.getenv("TWITCH_COOLDOWN_SECONDS", "3"))
twitch_max_message_length = int(os.getenv("TWITCH_MAX_MESSAGE_LENGTH", "450"))

# Add RVC settings
use_rvc = os.environ.get("USE_RVC", "false").lower() == "true"
rvc_model = os.environ.get("RVC_MODEL", "default")
rvc_speaker = os.environ.get("RVC_SPEAKER", "0")
rvc_pitch = float(os.environ.get("RVC_PITCH", "0.0"))
rvc_speed = float(os.environ.get("RVC_SPEED", "1.0"))
