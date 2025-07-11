# Standard library imports
import os
import json
import re
import requests
import socket
from pathlib import Path
import colorama

# Load environment variables
from dotenv import load_dotenv
try:
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    print("Using default environment variables")

# Environment variables
HOST_PORT = os.getenv("HOST_PORT", "127.0.0.1:5000")  # Default to the running server port
API_TYPE = os.getenv("API_TYPE", "Oobabooga")
MODEL_TYPE = os.getenv("MODEL_TYPE", "chatml")
OOGABOOGA_SUPPORT_HOST = os.getenv("OOGABOOGA_SUPPORT_HOST", "127.0.0.1:5000")

# Character settings
CHAR_NAME = os.getenv("CHAR_NAME", "Z-Waif")
CHARACTER_CARD = os.getenv("CHARACTER_CARD", "Z-Waif")
YOUR_NAME = os.getenv("YOUR_NAME", "User")
PARTNER_NAME = os.getenv("PARTNER_NAME", "User")
CHARACTER_CONTEXT = os.getenv("CHARACTER_CONTEXT", "You are a friendly and caring AI companion who speaks naturally and conversationally.")

# Model settings
MODEL_NAME = os.getenv("MODEL_NAME", "ADEF")

# Model context settings
TOKEN_LIMIT = int(os.getenv("TOKEN_LIMIT", "4096"))
MESSAGE_PAIR_LIMIT = int(os.getenv("MESSAGE_PAIR_LIMIT", "40"))
TIME_IN_ENCODING = os.getenv("TIME_IN_ENCODING", "OFF")

# LLM Temperature and Generation Settings
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
TOP_P = float(os.getenv("TOP_P", "0.9"))
TOP_K = int(os.getenv("TOP_K", "40"))
FREQUENCY_PENALTY = float(os.getenv("FREQUENCY_PENALTY", "0.0"))
PRESENCE_PENALTY = float(os.getenv("PRESENCE_PENALTY", "0.0"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "450"))

# Add discrete temperature level (legacy support)
TEMP_LEVEL = int(os.getenv("TEMP_LEVEL", "0"))  # 0: conservative, 1: balanced, 2: creative
# Alias for backward-compatibility with older modules
temp_level = TEMP_LEVEL

# Preset Management
PRESET_NAME = os.getenv("PRESET_NAME", "Default")

# Anti-streaming settings
NEWLINE_CUT_BOOT = os.getenv("NEWLINE_CUT_BOOT", "ON")
RP_SUP_BOOT = os.getenv("RP_SUP_BOOT", "ON")
API_STREAM_CHATS = os.getenv("API_STREAM_CHATS", "OFF")
SILERO_VAD = os.getenv("SILERO_VAD", "ON")

# Whisper settings
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base.en")
WHISPER_CHOICE = os.getenv("WHISPER_CHOICE", "faster-whisper")
WHISPER_CHUNKS_MAX = int(os.getenv("WHISPER_CHUNKS_MAX", "14"))
AUTOCHAT_MIN_LENGTH = int(os.getenv("AUTOCHAT_MIN_LENGTH", "10"))

# Autochat sensitivity (shared setting)
AUTOCHAT_SENSITIVITY = int(os.getenv("AUTOCHAT_SENSITIVITY", "16"))

# Flash attention control (for CUDA compatibility)
DISABLE_FLASH_ATTN = os.getenv("DISABLE_FLASH_ATTN", "OFF").lower() == "on"

# Web UI settings
WEB_UI_PORT = int(os.getenv("WEB_UI_PORT", "7864"))
WEB_UI_SHARE = os.getenv("WEB_UI_SHARE", "OFF").lower() == "on"
WEB_UI_THEME = os.getenv("WEB_UI_THEME", "default")

# Voice and audio settings
VOICE_SPEED = float(os.getenv("VOICE_SPEED", "1.0"))
VOICE_VOLUME = float(os.getenv("VOICE_VOLUME", "1.0"))
AUDIO_DEVICE = os.getenv("AUDIO_DEVICE", "default")
MIC_DEVICE = os.getenv("MIC_DEVICE", "default")

# Chat and response settings
MAX_RESPONSE_LENGTH = int(os.getenv("MAX_RESPONSE_LENGTH", "500"))
CHAT_HISTORY_LIMIT = int(os.getenv("CHAT_HISTORY_LIMIT", "50"))
AUTO_SAVE_INTERVAL = int(os.getenv("AUTO_SAVE_INTERVAL", "10"))

# System behavior settings
DEBUG_MODE = os.getenv("DEBUG_MODE", "OFF").lower() == "on"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
AUTO_BACKUP = os.getenv("AUTO_BACKUP", "ON").lower() == "on"
BACKUP_INTERVAL = int(os.getenv("BACKUP_INTERVAL", "60"))  # minutes

# Relationship settings
RELATIONSHIP_SYSTEM_ENABLED = os.getenv("RELATIONSHIP_SYSTEM_ENABLED", "ON").lower() == "on"
DEFAULT_RELATIONSHIP_LEVEL = os.getenv("DEFAULT_RELATIONSHIP_LEVEL", "stranger")
RELATIONSHIP_RESPONSES_ENABLED = os.getenv("RELATIONSHIP_RESPONSES_ENABLED", "ON").lower() == "on"
RELATIONSHIP_MEMORY_ENABLED = os.getenv("RELATIONSHIP_MEMORY_ENABLED", "ON").lower() == "on"
RELATIONSHIP_PROGRESSION_SPEED = float(os.getenv("RELATIONSHIP_PROGRESSION_SPEED", "1.0"))
RELATIONSHIP_DECAY_RATE = float(os.getenv("RELATIONSHIP_DECAY_RATE", "0.1"))
RELATIONSHIP_PARTNER_NAME = os.getenv("RELATIONSHIP_PARTNER_NAME", "")

# Chatpops settings
USE_CHATPOPS = os.getenv("USE_CHATPOPS", "ON").lower() == "on"
# Load chatpop phrases from JSON file
try:
    with open("Configurables/Chatpops.json", 'r') as chatpops_file:
        chatpop_phrases = json.load(chatpops_file)
    print(f"[Settings] Loaded {len(chatpop_phrases)} chatpop phrases")
except Exception as e:
    chatpop_phrases = []
    print(f"[Settings] Error loading chatpop phrases: {e}")

# Module toggles
MODULE_MINECRAFT = os.getenv("MODULE_MINECRAFT", "OFF")

# Gaming mode settings
is_gaming_loop = MODULE_MINECRAFT.lower() == "on"  # Whether gaming features are enabled

def update_env_autochat_sensitivity(new_value):
    """Update AUTOCHAT_SENSITIVITY in the .env file."""
    import re
    env_path = ".env"
    try:
        with open(env_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith("AUTOCHAT_SENSITIVITY="):
            lines[i] = f"AUTOCHAT_SENSITIVITY={new_value}\n"
            found = True
            break
    if not found:
        lines.append(f"AUTOCHAT_SENSITIVITY={new_value}\n")

    with open(env_path, "w") as f:
        f.writelines(lines)

def update_env_flash_attn_disable(disable=True):
    """Update DISABLE_FLASH_ATTN in the .env file."""
    import re
    env_path = ".env"
    try:
        with open(env_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith("DISABLE_FLASH_ATTN="):
            lines[i] = f"DISABLE_FLASH_ATTN={'ON' if disable else 'OFF'}\n"
            found = True
            break
    if not found:
        lines.append(f"DISABLE_FLASH_ATTN={'ON' if disable else 'OFF'}\n")

    with open(env_path, "w") as f:
        f.writelines(lines)

def update_env_setting(setting_name, value):
    """Generic function to update any setting in the .env file."""
    import re
    env_path = ".env"
    try:
        with open(env_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{setting_name}="):
            lines[i] = f"{setting_name}={value}\n"
            found = True
            break
    if not found:
        lines.append(f"{setting_name}={value}\n")

    with open(env_path, "w") as f:
        f.writelines(lines)

def update_env_web_ui_settings(port=None, share=None, theme=None):
    """Update web UI settings in the .env file."""
    if port is not None:
        update_env_setting("WEB_UI_PORT", str(port))
    if share is not None:
        update_env_setting("WEB_UI_SHARE", "ON" if share else "OFF")
    if theme is not None:
        update_env_setting("WEB_UI_THEME", theme)

def update_env_voice_settings(speed=None, volume=None, audio_device=None, mic_device=None):
    """Update voice settings in the .env file."""
    if speed is not None:
        update_env_setting("VOICE_SPEED", str(speed))
    if volume is not None:
        update_env_setting("VOICE_VOLUME", str(volume))
    if audio_device is not None:
        update_env_setting("AUDIO_DEVICE", audio_device)
    if mic_device is not None:
        update_env_setting("MIC_DEVICE", mic_device)

def update_env_chat_settings(max_length=None, history_limit=None, auto_save=None):
    """Update chat settings in the .env file."""
    if max_length is not None:
        update_env_setting("MAX_RESPONSE_LENGTH", str(max_length))
    if history_limit is not None:
        update_env_setting("CHAT_HISTORY_LIMIT", str(history_limit))
    if auto_save is not None:
        update_env_setting("AUTO_SAVE_INTERVAL", str(auto_save))

def update_env_system_settings(debug_mode=None, log_level=None, auto_backup=None, backup_interval=None):
    """Update system settings in the .env file."""
    if debug_mode is not None:
        update_env_setting("DEBUG_MODE", "ON" if debug_mode else "OFF")
    if log_level is not None:
        update_env_setting("LOG_LEVEL", log_level)
    if auto_backup is not None:
        update_env_setting("AUTO_BACKUP", "ON" if auto_backup else "OFF")
    if backup_interval is not None:
        update_env_setting("BACKUP_INTERVAL", str(backup_interval))

def update_env_relationship_settings(
    system_enabled=None, default_level=None, responses_enabled=None, 
    memory_enabled=None, progression_speed=None, decay_rate=None, partner_name=None
):
    """Update relationship settings in the .env file."""
    if system_enabled is not None:
        update_env_setting("RELATIONSHIP_SYSTEM_ENABLED", "ON" if system_enabled else "OFF")
    if default_level is not None:
        update_env_setting("DEFAULT_RELATIONSHIP_LEVEL", default_level)
    if responses_enabled is not None:
        update_env_setting("RELATIONSHIP_RESPONSES_ENABLED", "ON" if responses_enabled else "OFF")
    if memory_enabled is not None:
        update_env_setting("RELATIONSHIP_MEMORY_ENABLED", "ON" if memory_enabled else "OFF")
    if progression_speed is not None:
        update_env_setting("RELATIONSHIP_PROGRESSION_SPEED", str(progression_speed))
    if decay_rate is not None:
        update_env_setting("RELATIONSHIP_DECAY_RATE", str(decay_rate))
    if partner_name is not None:
        update_env_setting("RELATIONSHIP_PARTNER_NAME", partner_name)

def auto_detect_flash_attn_compatibility():
    """Auto-detect and handle flash attention compatibility issues."""
    print("[SETTINGS] Checking flash attention compatibility...")
    
    # If already disabled via env, skip check
    if DISABLE_FLASH_ATTN:
        print("[SETTINGS] Flash attention disabled via environment")
        return
    
    try:
        import torch
        if not torch.cuda.is_available():
            print("[SETTINGS] CUDA not available, disabling flash attention")
            update_env_flash_attn_disable(True)
            return
    except ImportError:
        print("[SETTINGS] PyTorch not available, disabling flash attention")
        update_env_flash_attn_disable(True)
        return
    
    try:
        import flash_attn  # type: ignore
        _ = flash_attn  # Prevent unused import warning
        print("[SETTINGS] Flash attention available and working")
    except ImportError as e:
        if "DLL load failed" in str(e) or "flash_attn" in str(e):
            print("[SETTINGS] Flash attention DLL error detected, disabling")
            update_env_flash_attn_disable(True)
        else:
            print(f"[SETTINGS] Flash attention import error: {e}")
            update_env_flash_attn_disable(True)

# Voice settings (RVC)
USE_RVC = os.getenv("USE_RVC", "false").lower() == "true"
RVC_HOST = os.getenv("RVC_HOST", "127.0.0.1")
RVC_PORT = int(os.getenv("RVC_PORT", "7897"))
RVC_MODEL = os.getenv("RVC_MODEL", "your_model_name")
RVC_SPEAKER = int(os.getenv("RVC_SPEAKER", "0"))
RVC_PITCH = float(os.getenv("RVC_PITCH", "0.0"))
RVC_SPEED = float(os.getenv("RVC_SPEED", "1.0"))

# Image/Vision settings
IMG_PORT = os.getenv("IMG_PORT", "127.0.0.1:5007")
VISUAL_CHARACTER_NAME = os.getenv("VISUAL_CHARACTER_NAME", "Z-WAIF-VisualAssist")
VISUAL_PRESET_NAME = os.getenv("VISUAL_PRESET_NAME", "Z-WAIF-VisualPreset")

# Ollama Visual Settings
ZW_OLLAMA_MODEL = os.getenv("ZW_OLLAMA_MODEL", "")
ZW_OLLAMA_MODEL_VISUAL = os.getenv("ZW_OLLAMA_MODEL_VISUAL", "")
OLLAMA_VISUAL_ENCODE_GUIDANCE = os.getenv("OLLAMA_VISUAL_ENCODE_GUIDANCE", "")
OLLAMA_VISUAL_CARD = os.getenv("OLLAMA_VISUAL_CARD", "")

# VTube Studio settings
EYES_FOLLOW = os.getenv("EYES_FOLLOW", "None")
EYES_START_ID = int(os.getenv("EYES_START_ID", "14"))
VTUBE_STUDIO_API_HOST = os.getenv("VTUBE_STUDIO_API_HOST", "127.0.0.1")
VTUBE_STUDIO_API_PORT = int(os.getenv("VTUBE_STUDIO_API_PORT", "8001"))
VTUBE_MODEL_NAME = os.getenv("VTUBE_MODEL_NAME", "Z-Waif")
VTUBE_FACE_TRACKING = os.getenv("VTUBE_FACE_TRACKING", "ON")
VTUBE_VIRTUAL_CAMERA = os.getenv("VTUBE_VIRTUAL_CAMERA", "OBS Virtual Camera")
VTUBE_AVATAR_MODE = os.getenv("VTUBE_AVATAR_MODE", "UNITY")

# Unity Avatar settings
MODULE_UNITY_AVATAR = os.getenv("MODULE_UNITY_AVATAR", "OFF")
MODULE_REALTIME_AVATAR = os.getenv("MODULE_REALTIME_AVATAR", "OFF")
UNITY_AVATAR_QUALITY = os.getenv("UNITY_AVATAR_QUALITY", "HIGH")
UNITY_AVATAR_FPS = int(os.getenv("UNITY_AVATAR_FPS", "30"))
UNITY_AVATAR_FALLBACK = os.getenv("UNITY_AVATAR_FALLBACK", "AUTO")

# Emotion processing
EMOTION_ANALYSIS_ENABLED = os.getenv("EMOTION_ANALYSIS_ENABLED", "ON")
EMOTION_INTENSITY_SCALING = float(os.getenv("EMOTION_INTENSITY_SCALING", "1.0"))
REALTIME_EMOTION_SYNC = os.getenv("REALTIME_EMOTION_SYNC", "ON")
AVATAR_EMOTION_MAPPING = os.getenv("AVATAR_EMOTION_MAPPING", "ADVANCED")

# Avatar performance
AVATAR_RENDER_QUALITY = os.getenv("AVATAR_RENDER_QUALITY", "HIGH")
AVATAR_CONTINUOUS_MODE = os.getenv("AVATAR_CONTINUOUS_MODE", "ON")
VIRTUAL_CAMERA_BACKEND = os.getenv("VIRTUAL_CAMERA_BACKEND", "unitycapture")
AVATAR_AUTO_RESTART = os.getenv("AVATAR_AUTO_RESTART", "ON")

# Module toggles
MODULE_MINECRAFT = os.getenv("MODULE_MINECRAFT", "OFF")
MODULE_ALARM = os.getenv("MODULE_ALARM", "ON")
MODULE_VTUBE = os.getenv("MODULE_VTUBE", "OFF")
MODULE_DISCORD = os.getenv("MODULE_DISCORD", "OFF")
MODULE_RAG = os.getenv("MODULE_RAG", "ON")
MODULE_VISUAL = os.getenv("MODULE_VISUAL", "OFF")
MODULE_TWITCH = os.getenv("MODULE_TWITCH", "OFF")
HOTKEYS_BOOT = os.getenv("HOTKEYS_BOOT", "OFF")

# Minecraft settings
minecraft_enabled = MODULE_MINECRAFT.lower() == "on"

# Memory settings
MEMORY_CLEANUP_FREQUENCY = int(os.getenv("MEMORY_CLEANUP_FREQUENCY", "60"))
MEMORY_PERSISTENCE = os.getenv("MEMORY_PERSISTENCE", "ON")

# Discord settings
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
DISCORD_CHANNEL = os.getenv("DISCORD_CHANNEL", "")

# Twitch settings
TWITCH_TOKEN = os.getenv("TWITCH_TOKEN", "")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL", "")
TWITCH_BOT_NAME = os.getenv("TWITCH_BOT_NAME", "z_waif_bot")

# Twitch bot behavior
TWITCH_PERSONALITY = os.getenv("TWITCH_PERSONALITY", "friendly")
TWITCH_AUTO_RESPOND = os.getenv("TWITCH_AUTO_RESPOND", "ON")
TWITCH_RESPONSE_CHANCE = float(os.getenv("TWITCH_RESPONSE_CHANCE", "0.8"))
TWITCH_COOLDOWN_SECONDS = int(os.getenv("TWITCH_COOLDOWN_SECONDS", "3"))
TWITCH_MAX_MESSAGE_LENGTH = int(os.getenv("TWITCH_MAX_MESSAGE_LENGTH", "450"))

# Runtime settings (not in .env)
char_name = CHAR_NAME
model_preset = "Default"
cur_task_char = "None"
cur_tags = []
max_tokens = 450
stream_chats = API_STREAM_CHATS.lower() == "on"
use_chatpops = True
live_pipe_no_speak = False
supress_rp = RP_SUP_BOOT.lower() == "on"
newline_cut = NEWLINE_CUT_BOOT.lower() == "on"
asterisk_ban = False
stopping_strings = []
vtube_enabled = MODULE_VTUBE.lower() == "on"
use_rvc = USE_RVC
cam_direct_talk = False
hangout_mode = False

# Shadow chat settings
SPEAK_SHADOWCHATS = os.getenv("SPEAK_SHADOWCHATS", "OFF").upper() == "ON"
SPEAK_ONLY_SPOKENTO = os.getenv("SPEAK_ONLY_SPOKENTO", "OFF").upper() == "ON"

# Shadow chat runtime settings
speak_shadowchats = SPEAK_SHADOWCHATS
speak_only_spokento = SPEAK_ONLY_SPOKENTO

# Semi-auto chat toggle (default: False)
semi_auto_chat = False

# Task and character lists (initialized by tag_task_controller)
all_task_char_list = []

VERBOSE_DETECTION = os.getenv("VERBOSE_DETECTION", "false").lower() == "true"

def detect_and_update_oobabooga_port():
    """
    Automatically detect Oobabooga server port and update .env file if needed.
    Returns the detected port or None if not found.
    """
    print("[SETTINGS] Searching for Oobabooga server...")
    
    # Common ports to check (UI or API)
    common_ports = [5000, 7860, 62191, 7861, 7862, 7863, 7864, 7865, 7866, 7867, 7868, 7869, 7870]
    
    detected_port = None
    
    # Helper: does a port expose at least one working API endpoint?
    def _port_has_api(port:int) -> bool:
        """Return True if any known Oobabooga API endpoint on this port returns a non-404/405 status."""
        api_paths = [
            "/api/v1/chat",
            "/api/v1/generate",
            "/v1/chat/completions",      # OpenAI extension
            "/v1/completions",
        ]
        for path in api_paths:
            try:
                r = requests.post(f"http://127.0.0.1:{port}{path}", json={"prompt": "ping", "max_new_tokens": 1}, timeout=2)
                if r.status_code not in (404, 405):
                    return True
            except requests.exceptions.RequestException:
                continue
        return False
    
    # First, try to detect from common ports
    for port in common_ports:
        try:
            url = f"http://127.0.0.1:{port}/startup-events"
            response = requests.get(url, timeout=2)
            # We only accept the port if /startup-events is 200 **and** at least one API endpoint works
            if response.status_code == 200 and _port_has_api(port):
                print(f"[SETTINGS] Found Oobabooga UI+API on port {port}")
                detected_port = port
                break
        except requests.exceptions.RequestException:
            continue
    
    # If UI+API on same port not found, specifically look for API-only ports (skip /startup-events)
    if detected_port is None:
        print("[SETTINGS] Looking for standalone API server ports...")
        for port in common_ports:
            if _port_has_api(port):
                print(f"[SETTINGS] Found Oobabooga API server on port {port}")
                detected_port = port
                break
    
    if detected_port is None:
        print("[SETTINGS] Not found on common ports, scanning broader range...")
        for port in range(5000, 8000):
            if _port_has_api(port):
                print(f"[SETTINGS] Found Oobabooga API server on port {port}")
                detected_port = port
                break
    
    # If we found a port, update the .env file
    if detected_port is not None:
        update_env_file(detected_port)
        return detected_port
    else:
        print("[SETTINGS] No Oobabooga server detected")
        return None

def update_env_file(port):
    """
    Update the .env file with the detected Oobabooga server port.
    """
    env_file = Path(".env")
    
    if not env_file.exists():
        print("[SETTINGS] .env file not found, creating from template...")
        create_env_from_template(port)
        return
    
    try:
        # Read current .env file
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update HOST_PORT and OOGABOOGA_SUPPORT_HOST
        new_host_port = f"127.0.0.1:{port}"
        
        # Replace existing values or add new ones
        lines = content.split('\n')
        updated_lines = []
        host_port_updated = False
        oogabooga_host_updated = False
        
        for line in lines:
            if line.startswith('HOST_PORT='):
                updated_lines.append(f'HOST_PORT={new_host_port}')
                host_port_updated = True
            elif line.startswith('OOGABOOGA_SUPPORT_HOST='):
                updated_lines.append(f'OOGABOOGA_SUPPORT_HOST={new_host_port}')
                oogabooga_host_updated = True
            else:
                updated_lines.append(line)
        
        # Add if not found
        if not host_port_updated:
            updated_lines.append(f'HOST_PORT={new_host_port}')
        if not oogabooga_host_updated:
            updated_lines.append(f'OOGABOOGA_SUPPORT_HOST={new_host_port}')
        
        # Write back to file
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))
        
        print(f"[SETTINGS] Updated .env file with Oobabooga server port: {port}")
        
        # Reload environment variables
        load_dotenv(override=True)
        
        # Refresh API URIs if modules are already imported
        try:
            import API.api_controller
            if hasattr(API.api_controller, 'refresh_uris'):
                API.api_controller.refresh_uris()
        except ImportError:
            pass  # API modules not imported yet
        
        try:
            import API.oobaooga_api
            if hasattr(API.oobaooga_api, 'refresh_base_uri'):
                API.oobaooga_api.refresh_base_uri()
        except ImportError:
            pass  # API modules not imported yet
        
    except Exception as e:
        print(f"[SETTINGS] Error updating .env file: {e}")

def create_env_from_template(port):
    """
    Create a new .env file from the template with the detected port.
    """
    template_file = Path("env_example.txt")
    env_file = Path(".env")
    
    if not template_file.exists():
        print("[SETTINGS] env_example.txt not found, cannot create .env file")
        return
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace default port with detected port
        new_host_port = f"127.0.0.1:{port}"
        content = content.replace('HOST_PORT=127.0.0.1:5000', f'HOST_PORT={new_host_port}')
        content = content.replace('OOGABOOGA_SUPPORT_HOST=127.0.0.1:5000', f'OOGABOOGA_SUPPORT_HOST={new_host_port}')
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[SETTINGS] Created .env file with Oobabooga server port: {port}")
        
        # Reload environment variables
        load_dotenv(override=True)
        
        # Refresh API URIs if modules are already imported
        try:
            import API.api_controller
            if hasattr(API.api_controller, 'refresh_uris'):
                API.api_controller.refresh_uris()
        except ImportError:
            pass  # API modules not imported yet
        
        try:
            import API.oobaooga_api
            if hasattr(API.oobaooga_api, 'refresh_base_uri'):
                API.oobaooga_api.refresh_base_uri()
        except ImportError:
            pass  # API modules not imported yet
        
    except Exception as e:
        print(f"[SETTINGS] Error creating .env file: {e}")

def auto_detect_oobabooga():
    """
    Main function to automatically detect and configure Oobabooga server.
    Call this at startup to ensure proper configuration.
    """
    print("[SETTINGS] Starting automatic Oobabooga server detection...")
    
    # Check if we already have a working configuration
    try:
        current_host = os.getenv("HOST_PORT", "127.0.0.1:5000")
        if ":" in current_host:
            current_port = int(current_host.split(":")[1])
            url = f"http://127.0.0.1:{current_port}/startup-events"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"[SETTINGS] Current configuration is working (port {current_port})")
                # Ensure current process environment is updated
                os.environ["HOST_PORT"] = current_host
                os.environ["OOGABOOGA_SUPPORT_HOST"] = current_host
                return current_port
    except:
        pass
    
    # If current config doesn't work, detect and update
    detected_port = detect_and_update_oobabooga_port()
    
    if detected_port:
        # Ensure current process environment is updated immediately
        detected_host = f"127.0.0.1:{detected_port}"
        os.environ["HOST_PORT"] = detected_host
        os.environ["OOGABOOGA_SUPPORT_HOST"] = detected_host
        print(f"[SETTINGS] Successfully configured Oobabooga server on port {detected_port}")
        
        # Refresh API URIs if modules are already imported
        try:
            import API.api_controller
            if hasattr(API.api_controller, 'refresh_uris'):
                API.api_controller.refresh_uris()
        except ImportError:
            pass  # API modules not imported yet
        
        try:
            import API.oobaooga_api
            if hasattr(API.oobaooga_api, 'refresh_base_uri'):
                API.oobaooga_api.refresh_base_uri()
        except ImportError:
            pass  # API modules not imported yet
        
        return detected_port
    else:
        print("[SETTINGS] Warning: Could not detect Oobabooga server. Please ensure it's running.")
        return None

def is_rvc_response(response):
    """
    Check if the response is actually from an RVC server.
    Only accept responses that are clearly from RVC, not other web servers.
    """
    try:
        # Only accept 200 status codes for successful RVC responses
        if response.status_code != 200:
            return False
        
        # Check if response contains audio data (base64 or binary)
        if response.headers.get('content-type', '').startswith('audio/'):
            return True
        
        # Check if response is JSON with RVC-specific fields
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                json_data = response.json()
                # Look for RVC-specific response patterns
                if any(key in json_data for key in ['audio', 'audio_data', 'result', 'status', 'version', 'modelSlotIndex', 'inputSampleRate', 'outputSampleRate']):
                    return True
            except:
                pass
        
        # Check for RVC-specific error messages (only for 200 responses)
        response_text = response.text.lower()
        rvc_indicators = [
            'rvc', 'voice conversion', 'speaker', 'pitch', 'speed',
            'model not found', 'speaker not found', 'invalid model',
            'voice changer', 'sample rate', 'model slot'
        ]
        
        for indicator in rvc_indicators:
            if indicator in response_text:
                return True
        
        # Check for binary responses that might be audio data
        if response.headers.get('content-type', '') == 'application/octet-stream':
            # This could be audio data from RVC
                return True
        
        # If we get here, it's not a clear RVC response
        return False
    except:
        return False

def detect_and_update_rvc_port():
    """
    Automatically detect RVC server port and update .env file if needed.
    Returns the detected port or None if not found.
    """
    print("[SETTINGS] Searching for RVC server...")
    
    # Common RVC ports to check (prioritize known working ports)
    common_ports = [18888, 18889, 18890, 18891, 18892, 7897, 7860, 8000, 8080, 5000, 7864, 7861, 7862, 7863]
    
    detected_port = None
    
    # Common RVC endpoints to test
    endpoints = [
        "/api/tts",
        "/tts", 
        "/voice",
        "/api/voice",
        "/synthesize",
        "/api/synthesize",
        "/test",
        "/info",
        "/api/hello"
    ]
    
    # Simple test payload
    test_payload = {
        "text": "test",
        "model": "default",
        "speaker_id": 0,
        "pitch_adjust": 0.0,
        "speed": 1.0
    }
    
    # First, try to detect from common ports
    for port in common_ports:
        for endpoint in endpoints:
            try:
                url = f"http://127.0.0.1:{port}{endpoint}"
                response = requests.post(url, json=test_payload, timeout=2)
                if response.status_code == 200 and is_rvc_response(response):
                    print(f"[SETTINGS] Found RVC server on port {port} (endpoint: {endpoint})")
                    detected_port = port
                    break
                elif response.status_code in [404, 422]:
                    if VERBOSE_DETECTION:
                        print(f"[SETTINGS] Found web server on port {port} but not RVC (status: {response.status_code})")
            except requests.exceptions.RequestException:
                continue
        if detected_port:
            break
    
    # If not found on common ports, try a broader range
    if detected_port is None:
        if VERBOSE_DETECTION:
            print("[SETTINGS] Not found on common ports, scanning broader range...")
        for port in range(5000, 19000):
            for endpoint in endpoints:
                try:
                    url = f"http://127.0.0.1:{port}{endpoint}"
                    response = requests.post(url, json=test_payload, timeout=1)
                    if response.status_code == 200 and is_rvc_response(response):
                        print(f"[SETTINGS] Found RVC server on port {port} (endpoint: {endpoint})")
                        detected_port = port
                        break
                    elif response.status_code in [404, 422]:
                        if VERBOSE_DETECTION:
                            print(f"[SETTINGS] Found web server on port {port} but not RVC (status: {response.status_code})")
                except requests.exceptions.RequestException:
                    continue
            if detected_port:
                break
    
    # If we found a port, update the .env file
    if detected_port is not None:
        update_rvc_env_file(detected_port)
        print(f"✅ RVC server detected on port {detected_port}")
        return detected_port
    else:
        print("❌ No RVC server detected")
        return None

def update_rvc_env_file(port):
    """
    Update the .env file with the detected RVC server port.
    """
    env_file = Path(".env")
    
    if not env_file.exists():
        print("[SETTINGS] .env file not found, creating from template...")
        create_rvc_env_from_template(port)
        return
    
    try:
        # Read current .env file
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update RVC_PORT
        lines = content.split('\n')
        updated_lines = []
        rvc_port_updated = False
        
        for line in lines:
            if line.startswith('RVC_PORT='):
                updated_lines.append(f'RVC_PORT={port}')
                rvc_port_updated = True
            else:
                updated_lines.append(line)
        
        # Add if not found
        if not rvc_port_updated:
            # Find a good place to insert (after other RVC settings)
            insert_index = len(updated_lines)
            for i, line in enumerate(updated_lines):
                if line.startswith('RVC_HOST='):
                    insert_index = i + 1
                    break
            
            updated_lines.insert(insert_index, f'RVC_PORT={port}')
        
        # Write back to file
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))
        
        print(f"[SETTINGS] Updated .env file with RVC server port: {port}")
        
        # Reload environment variables
        load_dotenv(override=True)
        
    except Exception as e:
        print(f"[SETTINGS] Error updating .env file: {e}")

def create_rvc_env_from_template(port):
    """
    Create a new .env file from the template with the detected RVC port.
    """
    template_file = Path("env_example.txt")
    env_file = Path(".env")
    
    if not template_file.exists():
        print("[SETTINGS] env_example.txt not found, cannot create .env file")
        return
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace default RVC port with detected port
        content = content.replace('RVC_PORT=7897', f'RVC_PORT={port}')
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[SETTINGS] Created .env file with RVC server port: {port}")
        
        # Reload environment variables
        load_dotenv(override=True)
        
    except Exception as e:
        print(f"[SETTINGS] Error creating .env file: {e}")

def auto_detect_rvc():
    """
    Main function to automatically detect and configure RVC server.
    Call this at startup to ensure proper configuration.
    """
    print("[SETTINGS] Starting automatic RVC server detection...")
    
    # Check if we already have a working configuration
    try:
        current_port = int(os.getenv("RVC_PORT", "7897"))
        test_payload = {
            "text": "test",
            "model": "default",
            "speaker_id": 0,
            "pitch_adjust": 0.0,
            "speed": 1.0
        }
        
        # Test common endpoints
        endpoints = ["/api/tts", "/tts", "/voice", "/api/voice", "/test", "/info", "/api/hello"]
        for endpoint in endpoints:
            try:
                url = f"http://127.0.0.1:{current_port}{endpoint}"
                response = requests.post(url, json=test_payload, timeout=2)
                if response.status_code == 200 and is_rvc_response(response):
                    print(f"[SETTINGS] Current RVC configuration is working (port {current_port}, endpoint: {endpoint})")
                    print(f"✅ RVC server detected on port {current_port}")
                    return current_port
                elif response.status_code in [404, 422]:
                    if VERBOSE_DETECTION:
                        print(f"[SETTINGS] Found web server on port {current_port} but not RVC (status: {response.status_code})")
            except:
                continue
    except:
        pass
    
    # If current config doesn't work, detect and update
    detected_port = detect_and_update_rvc_port()
    
    if detected_port:
        return detected_port
    else:
        print("❌ No RVC server detected. Please ensure it's running.")
        return None

def detect_and_update_model_name():
    """
    Automatically detect the available model name from OOBA_Presets/ and update .env file if needed.
    Returns the detected model name or None if not found.
    """
    print("[SETTINGS] Scanning for available model names in OOBA_Presets/ ...")
    presets_dir = Path("OOBA_Presets")
    if not presets_dir.exists():
        print("[SETTINGS] OOBA_Presets directory not found.")
        return None
    
    # Scan for Z-Waif-*.yaml files
    model_names = []
    for file in presets_dir.glob("Z-Waif-*.yaml"):
        # Extract model name from filename: Z-Waif-<MODEL>.yaml
        parts = file.stem.split("-")
        if len(parts) >= 3:
            model_name = parts[2]  # e.g., ADEF, Mythalion, Noromaid
            if model_name not in model_names:
                model_names.append(model_name)
    
    if not model_names:
        print("[SETTINGS] No model presets found in OOBA_Presets/.")
        return None
    
    # Prefer the first found model, or you could add logic to select preferred/default
    detected_model_name = model_names[0]
    print(f"[SETTINGS] Detected model name: {detected_model_name}")
    update_model_name_env_file(detected_model_name)
    return detected_model_name

def update_model_name_env_file(model_name):
    """
    Update the .env file with the detected MODEL_NAME.
    """
    env_file = Path(".env")
    if not env_file.exists():
        print("[SETTINGS] .env file not found, creating from template...")
        create_model_name_env_from_template(model_name)
        return
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        lines = content.split('\n')
        updated_lines = []
        model_name_updated = False
        for line in lines:
            if line.startswith('MODEL_NAME='):
                updated_lines.append(f'MODEL_NAME={model_name}')
                model_name_updated = True
            else:
                updated_lines.append(line)
        if not model_name_updated:
            # Insert after model context settings if possible
            insert_index = len(updated_lines)
            for i, line in enumerate(updated_lines):
                if line.startswith('TOKEN_LIMIT='):
                    insert_index = i
                    break
            updated_lines.insert(insert_index, f'MODEL_NAME={model_name}')
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))
        print(f"[SETTINGS] Updated .env file with MODEL_NAME: {model_name}")
        load_dotenv(override=True)
    except Exception as e:
        print(f"[SETTINGS] Error updating .env file for MODEL_NAME: {e}")

def create_model_name_env_from_template(model_name):
    """
    Create a new .env file from the template with the detected MODEL_NAME.
    """
    template_file = Path("env_example.txt")
    env_file = Path(".env")
    if not template_file.exists():
        print("[SETTINGS] env_example.txt not found, cannot create .env file")
        return
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        # Replace or add MODEL_NAME
        if 'MODEL_NAME=' in content:
            content = re.sub(r'MODEL_NAME=.*', f'MODEL_NAME={model_name}', content)
        else:
            # Insert after TOKEN_LIMIT if possible
            if 'TOKEN_LIMIT=' in content:
                content = content.replace('TOKEN_LIMIT=4096', f'TOKEN_LIMIT=4096\nMODEL_NAME={model_name}')
            else:
                content += f'\nMODEL_NAME={model_name}'
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[SETTINGS] Created .env file with MODEL_NAME: {model_name}")
        load_dotenv(override=True)
    except Exception as e:
        print(f"[SETTINGS] Error creating .env file for MODEL_NAME: {e}")

def auto_detect_model_name():
    """
    Main function to automatically detect and configure MODEL_NAME.
    Call this at startup to ensure proper configuration.
    """
    print("[SETTINGS] Starting automatic MODEL_NAME detection...")
    # Check if we already have a working configuration
    try:
        current_model_name = os.getenv("MODEL_NAME", "")
        if current_model_name:
            print(f"[SETTINGS] Current MODEL_NAME is set: {current_model_name}")
            return current_model_name
    except:
        pass
    # If not set, detect and update
    detected_model_name = detect_and_update_model_name()
    if detected_model_name:
        print(f"[SETTINGS] Successfully configured MODEL_NAME: {detected_model_name}")
        return detected_model_name
    else:
        print("[SETTINGS] Warning: Could not detect MODEL_NAME. Please ensure presets exist.")
        return None

def detect_and_update_vtube_port():
    """
    Automatically detect VTube Studio API port and update .env file if needed.
    Returns the detected port or None if not found.
    """
    print("[SETTINGS] Searching for VTube Studio API...")
    
    # Common VTube Studio ports to check (reduced list for speed)
    common_ports = [8001, 8000, 8002, 8003]
    
    detected_port = None
    
    # VTube Studio API endpoints to test (reduced list for speed)
    endpoints = [
        "/api/1.0/",
        "/api/1.0/statistics"
    ]
    
    # First, try to detect from common ports with shorter timeout
    for port in common_ports:
        for endpoint in endpoints:
            try:
                url = f"http://127.0.0.1:{port}{endpoint}"
                response = requests.get(url, timeout=1)  # Reduced timeout
                if response.status_code == 200:
                    # Check if response contains VTube Studio indicators
                    response_text = response.text.lower()
                    if any(indicator in response_text for indicator in ["vtubestudio", "vts", "api", "statistics", "models"]):
                        print(f"[SETTINGS] Found VTube Studio API on port {port} (endpoint: {endpoint})")
                        detected_port = port
                        break
            except requests.exceptions.RequestException:
                continue
        if detected_port:
            break
    
    # If not found on common ports, try a very limited broader range
    if detected_port is None:
        print("[SETTINGS] Not found on common ports, scanning limited range...")
        for port in range(8004, 8010):  # Reduced range
            for endpoint in endpoints:
                try:
                    url = f"http://127.0.0.1:{port}{endpoint}"
                    response = requests.get(url, timeout=2)  # Increased from 0.5 to 2
                    if response.status_code == 200:
                        response_text = response.text.lower()
                        if any(indicator in response_text for indicator in ["vtubestudio", "vts", "api", "statistics", "models"]):
                            print(f"[SETTINGS] Found VTube Studio API on port {port} (endpoint: {endpoint})")
                            detected_port = port
                            break
                except requests.exceptions.RequestException:
                    continue
            if detected_port:
                break
    
    # If we found a port, update the .env file
    if detected_port is not None:
        update_vtube_env_file(detected_port)
        return detected_port
    else:
        print("[SETTINGS] No VTube Studio API detected")
        return None

def update_vtube_env_file(port):
    """
    Update the .env file with the detected VTube Studio API port.
    """
    env_file = Path(".env")
    
    if not env_file.exists():
        print("[SETTINGS] .env file not found, creating from template...")
        create_vtube_env_from_template(port)
        return
    
    try:
        # Read current .env file
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update VTUBE_STUDIO_API_PORT
        lines = content.split('\n')
        updated_lines = []
        vtube_port_updated = False
        
        for line in lines:
            if line.startswith('VTUBE_STUDIO_API_PORT='):
                updated_lines.append(f'VTUBE_STUDIO_API_PORT={port}')
                vtube_port_updated = True
            else:
                updated_lines.append(line)
        
        # Add if not found
        if not vtube_port_updated:
            # Find a good place to insert (after other VTube settings)
            insert_index = len(updated_lines)
            for i, line in enumerate(updated_lines):
                if line.startswith('VTUBE_STUDIO_API_HOST='):
                    insert_index = i + 1
                    break
            
            updated_lines.insert(insert_index, f'VTUBE_STUDIO_API_PORT={port}')
        
        # Write back to file
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))
        
        print(f"[SETTINGS] Updated .env file with VTube Studio API port: {port}")
        
        # Reload environment variables
        load_dotenv(override=True)
        
    except Exception as e:
        print(f"[SETTINGS] Error updating .env file: {e}")

def create_vtube_env_from_template(port):
    """
    Create a new .env file from the template with the detected VTube Studio port.
    """
    template_file = Path("env_example.txt")
    env_file = Path(".env")
    
    if not template_file.exists():
        print("[SETTINGS] env_example.txt not found, cannot create .env file")
        return
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace default VTube Studio port with detected port
        content = content.replace('VTUBE_STUDIO_API_PORT=8001', f'VTUBE_STUDIO_API_PORT={port}')
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[SETTINGS] Created .env file with VTube Studio API port: {port}")
        
        # Reload environment variables
        load_dotenv(override=True)
        
    except Exception as e:
        print(f"[SETTINGS] Error creating .env file: {e}")

def auto_detect_vtube():
    """
    Main function to automatically detect and configure VTube Studio API.
    Call this at startup to ensure proper configuration.
    """
    print("[SETTINGS] Starting automatic VTube Studio API detection...")
    
    # Quick check if we already have a working configuration
    try:
        current_port = int(os.getenv("VTUBE_STUDIO_API_PORT", "8001"))
        url = f"http://127.0.0.1:{current_port}/api/1.0/"
        response = requests.get(url, timeout=1)  # Quick timeout
        if response.status_code == 200:
            print(f"[SETTINGS] Current VTube Studio configuration is working (port {current_port})")
            return current_port
    except:
        pass
    
    # If current config doesn't work, do a very quick detection
    print("[SETTINGS] Quick VTube Studio detection (will skip if not found)...")
    
    # Only check the most common port with very short timeout
    try:
        url = "http://127.0.0.1:8001/api/1.0/"
        response = requests.get(url, timeout=2)  # Increased from 0.5 to 2
        if response.status_code == 200:
            print("[SETTINGS] Found VTube Studio API on port 8001")
            update_vtube_env_file(8001)
            return 8001
    except:
        pass
    
    # If not found quickly, skip and let user configure manually
    print("[SETTINGS] VTube Studio API not detected quickly - skipping for manual configuration")
    print("[SETTINGS] You can configure VTube Studio connection in the web UI settings")
    return None

def detect_and_update_img_port():
    """
    Automatically detect image/visual API port and update .env file if needed.
    Returns the detected port or None if not found.
    """
    print("[SETTINGS] Searching for image/visual API...")
    
    # Common image API ports to check (usually same as main API or dedicated visual port)
    common_ports = [5007, 5000, 7860, 7861, 7862, 7863, 7864, 7865, 7866, 7867, 7868, 7869, 7870]
    
    detected_port = None
    
    # Image API endpoints to test
    endpoints = [
        "/v1/chat/completions",
        "/api/chat/completions",
        "/chat/completions",
        "/v1/completions",
        "/api/completions",
        "/completions"
    ]
    
    # First, try to detect from common ports
    for port in common_ports:
        for endpoint in endpoints:
            try:
                url = f"http://127.0.0.1:{port}{endpoint}"
                response = requests.post(url, json={"test": "test"}, timeout=2)
                # Accept various status codes as indicators of API presence
                if response.status_code in [200, 400, 422, 500]:
                    print(f"[SETTINGS] Found image/visual API on port {port} (endpoint: {endpoint})")
                    detected_port = port
                    break
            except requests.exceptions.RequestException:
                continue
        if detected_port:
            break
    
    # If not found on common ports, try a broader range
    if detected_port is None:
        print("[SETTINGS] Not found on common ports, scanning broader range...")
        for port in range(5000, 8000):
            for endpoint in endpoints:
                try:
                    url = f"http://127.0.0.1:{port}{endpoint}"
                    response = requests.post(url, json={"test": "test"}, timeout=1)
                    if response.status_code in [200, 400, 422, 500]:
                        print(f"[SETTINGS] Found image/visual API on port {port} (endpoint: {endpoint})")
                        detected_port = port
                        break
                except requests.exceptions.RequestException:
                    continue
            if detected_port:
                break
    
    # If we found a port, update the .env file
    if detected_port is not None:
        update_img_env_file(detected_port)
        return detected_port
    else:
        print("[SETTINGS] No image/visual API detected")
        return None

def update_img_env_file(port):
    """
    Update the .env file with the detected image/visual API port.
    """
    env_file = Path(".env")
    
    if not env_file.exists():
        print("[SETTINGS] .env file not found, creating from template...")
        create_img_env_from_template(port)
        return
    
    try:
        # Read current .env file
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update IMG_PORT
        lines = content.split('\n')
        updated_lines = []
        img_port_updated = False
        
        for line in lines:
            if line.startswith('IMG_PORT='):
                updated_lines.append(f'IMG_PORT=127.0.0.1:{port}')
                img_port_updated = True
            else:
                updated_lines.append(line)
        
        # Add if not found
        if not img_port_updated:
            # Find a good place to insert (after other image settings)
            insert_index = len(updated_lines)
            for i, line in enumerate(updated_lines):
                if line.startswith('VISUAL_CHARACTER_NAME='):
                    insert_index = i - 1  # Insert before visual settings
                    break
            
            updated_lines.insert(insert_index, f'IMG_PORT=127.0.0.1:{port}')
        
        # Write back to file
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))
        
        print(f"[SETTINGS] Updated .env file with image/visual API port: {port}")
        
        # Reload environment variables
        load_dotenv(override=True)
        
    except Exception as e:
        print(f"[SETTINGS] Error updating .env file: {e}")

def create_img_env_from_template(port):
    """
    Create a new .env file from the template with the detected image/visual port.
    """
    template_file = Path("env_example.txt")
    env_file = Path(".env")
    
    if not template_file.exists():
        print("[SETTINGS] env_example.txt not found, cannot create .env file")
        return
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace default image port with detected port
        content = content.replace('IMG_PORT=127.0.0.1:5007', f'IMG_PORT=127.0.0.1:{port}')
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[SETTINGS] Created .env file with image/visual API port: {port}")
        
        # Reload environment variables
        load_dotenv(override=True)
        
    except Exception as e:
        print(f"[SETTINGS] Error creating .env file: {e}")

def auto_detect_img():
    """
    Main function to automatically detect and configure image/visual API.
    Call this at startup to ensure proper configuration.
    """
    print("[SETTINGS] Starting automatic image/visual API detection...")
    
    # Check if we already have a working configuration
    try:
        current_img_port = os.getenv("IMG_PORT", "127.0.0.1:5007")
        if ":" in current_img_port:
            current_port = int(current_img_port.split(":")[1])
            url = f"http://127.0.0.1:{current_port}/v1/chat/completions"
            response = requests.post(url, json={"test": "test"}, timeout=2)
            if response.status_code in [200, 400, 422, 500]:
                print(f"[SETTINGS] Current image/visual configuration is working (port {current_port})")
                return current_port
    except:
        pass
    
    # If current config doesn't work, detect and update
    detected_port = detect_and_update_img_port()
    
    if detected_port:
        print(f"[SETTINGS] Successfully configured image/visual API on port {detected_port}")
        return detected_port
    else:
        print("[SETTINGS] Warning: Could not detect image/visual API. Please ensure it's running.")
        return None

def detect_and_update_character_names():
    """
    Automatically detect character name and user name from character card files.
    Returns tuple of (char_name, your_name) or (None, None) if not found.
    """
    print("[SETTINGS] Scanning for character names in character cards...")
    
    # Check for character card files
    char_card_files = [
        "Configurables/CharacterCard.yaml",
        "Configurables/CharacterCardExample.yaml",
        "Configurables/CharacterCardVisual.yaml"
    ]
    
    char_name = None
    your_name = None
    
    for card_file in char_card_files:
        card_path = Path(card_file)
        if card_path.exists():
            try:
                with open(card_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for character name patterns
                import re
                
                # Look for "You are [NAME]" pattern
                char_match = re.search(r'You are ([A-Za-z0-9_-]+)', content, re.IGNORECASE)
                if char_match and not char_name:
                    char_name = char_match.group(1)
                    print(f"[SETTINGS] Detected character name: {char_name}")
                
                # Look for user name patterns
                user_patterns = [
                    r'partner.*?([A-Za-z0-9_-]+)',
                    r'beloved.*?([A-Za-z0-9_-]+)',
                    r'with ([A-Za-z0-9_-]+)',
                    r'([A-Za-z0-9_-]+).*?partner'
                ]
                
                for pattern in user_patterns:
                    user_match = re.search(pattern, content, re.IGNORECASE)
                    if user_match and not your_name:
                        potential_name = user_match.group(1)
                        # Filter out common words that aren't names
                        if potential_name.lower() not in ['your', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']:
                            your_name = potential_name
                            print(f"[SETTINGS] Detected user name: {your_name}")
                            break
                
                if char_name and your_name:
                    break
                    
            except Exception as e:
                print(f"[SETTINGS] Error reading character card {card_file}: {e}")
                continue
    
    if char_name or your_name:
        update_character_names_env_file(char_name, your_name)
        return char_name, your_name
    else:
        print("[SETTINGS] No character names detected in character cards.")
        return None, None

def update_character_names_env_file(char_name, your_name):
    """
    Update the .env file with the detected character names.
    """
    env_file = Path(".env")
    
    if not env_file.exists():
        print("[SETTINGS] .env file not found, creating from template...")
        create_character_names_env_from_template(char_name, your_name)
        return
    
    try:
        # Read current .env file
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update CHAR_NAME and YOUR_NAME
        lines = content.split('\n')
        updated_lines = []
        char_name_updated = False
        your_name_updated = False
        
        for line in lines:
            if line.startswith('CHAR_NAME='):
                if char_name:
                    updated_lines.append(f'CHAR_NAME={char_name}')
                    char_name_updated = True
                else:
                    updated_lines.append(line)
            elif line.startswith('YOUR_NAME='):
                if your_name:
                    updated_lines.append(f'YOUR_NAME={your_name}')
                    your_name_updated = True
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Add if not found
        if char_name and not char_name_updated:
            # Find a good place to insert (after other character settings)
            insert_index = len(updated_lines)
            for i, line in enumerate(updated_lines):
                if line.startswith('CHARACTER_CARD='):
                    insert_index = i + 1
                    break
            
            updated_lines.insert(insert_index, f'CHAR_NAME={char_name}')
        
        if your_name and not your_name_updated:
            # Find a good place to insert (after CHAR_NAME)
            insert_index = len(updated_lines)
            for i, line in enumerate(updated_lines):
                if line.startswith('CHAR_NAME='):
                    insert_index = i + 1
                    break
            
            updated_lines.insert(insert_index, f'YOUR_NAME={your_name}')
        
        # Write back to file
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))
        
        if char_name:
            print(f"[SETTINGS] Updated .env file with character name: {char_name}")
        if your_name:
            print(f"[SETTINGS] Updated .env file with user name: {your_name}")
        
        # Reload environment variables
        load_dotenv(override=True)
        
    except Exception as e:
        print(f"[SETTINGS] Error updating .env file: {e}")

def create_character_names_env_from_template(char_name, your_name):
    """
    Create a new .env file from the template with the detected character names.
    """
    template_file = Path("env_example.txt")
    env_file = Path(".env")
    
    if not template_file.exists():
        print("[SETTINGS] env_example.txt not found, cannot create .env file")
        return
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace default names with detected names
        if char_name:
            content = content.replace('CHAR_NAME=NAME OF AI', f'CHAR_NAME={char_name}')
        if your_name:
            content = content.replace('YOUR_NAME= YOUR NAME', f'YOUR_NAME={your_name}')
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        if char_name:
            print(f"[SETTINGS] Created .env file with character name: {char_name}")
        if your_name:
            print(f"[SETTINGS] Created .env file with user name: {your_name}")
        
        # Reload environment variables
        load_dotenv(override=True)
        
    except Exception as e:
        print(f"[SETTINGS] Error creating .env file: {e}")

def auto_detect_character_names():
    """
    Main function to automatically detect and configure character names.
    Call this at startup to ensure proper configuration.
    """
    print("[SETTINGS] Starting automatic character name detection...")
    
    # Check if we already have working configurations
    current_char_name = os.getenv("CHAR_NAME", "")
    current_your_name = os.getenv("YOUR_NAME", "")
    
    if current_char_name and current_your_name:
        print(f"[SETTINGS] Current character names are set: {current_char_name}, {current_your_name}")
        return current_char_name, current_your_name
    
    # If not set, detect and update
    detected_char_name, detected_your_name = detect_and_update_character_names()
    
    if detected_char_name or detected_your_name:
        print(f"[SETTINGS] Successfully configured character names: {detected_char_name}, {detected_your_name}")
        return detected_char_name, detected_your_name
    else:
        print("[SETTINGS] Warning: Could not detect character names. Please check character card files.")
        return None, None

import socket

def update_env_semi_auto_chat(enabled):
    """Update SEMI_AUTO_CHAT in the .env file."""
    update_env_setting("SEMI_AUTO_CHAT", "ON" if enabled else "OFF")

def load_semi_auto_chat_from_env():
    """Load SEMI_AUTO_CHAT from the .env file or environment."""
    import os
    value = os.getenv("SEMI_AUTO_CHAT", "OFF").strip().upper()
    return value == "ON"

# Persistent toggles and values (always defined at top level)
semi_auto_chat = load_semi_auto_chat_from_env()

def update_env_speak_shadowchats(enabled):
    """Update SPEAK_SHADOWCHATS in the .env file."""
    update_env_setting("SPEAK_SHADOWCHATS", "ON" if enabled else "OFF")

def load_speak_shadowchats_from_env():
    """Load SPEAK_SHADOWCHATS from the .env file or environment."""
    import os
    value = os.getenv("SPEAK_SHADOWCHATS", "OFF").strip().upper()
    return value == "ON"

# Speak Shadowchats toggle (persistent)
speak_shadowchats = load_speak_shadowchats_from_env()

import socket

def update_env_speak_only_spokento(enabled):
    update_env_setting("SPEAK_ONLY_SPOKENTO", "ON" if enabled else "OFF")
def load_speak_only_spokento_from_env():
    value = os.getenv("SPEAK_ONLY_SPOKENTO", "OFF").strip().upper()
    return value == "ON"
speak_only_spokento = load_speak_only_spokento_from_env()

def update_env_supress_rp(enabled):
    update_env_setting("SUPRESS_RP", "ON" if enabled else "OFF")
def load_supress_rp_from_env():
    value = os.getenv("SUPRESS_RP", "OFF").strip().upper()
    return value == "ON"
supress_rp = load_supress_rp_from_env()

def update_env_newline_cut(enabled):
    update_env_setting("NEWLINE_CUT", "ON" if enabled else "OFF")
def load_newline_cut_from_env():
    value = os.getenv("NEWLINE_CUT", "OFF").strip().upper()
    return value == "ON"
newline_cut = load_newline_cut_from_env()

def update_env_asterisk_ban(enabled):
    update_env_setting("ASTERISK_BAN", "ON" if enabled else "OFF")
def load_asterisk_ban_from_env():
    value = os.getenv("ASTERISK_BAN", "OFF").strip().upper()
    return value == "ON"
asterisk_ban = load_asterisk_ban_from_env()

def update_env_hotkeys_locked(enabled):
    update_env_setting("HOTKEYS_LOCKED", "ON" if enabled else "OFF")
def load_hotkeys_locked_from_env():
    value = os.getenv("HOTKEYS_LOCKED", "OFF").strip().upper()
    return value == "ON"
hotkeys_locked = load_hotkeys_locked_from_env()

def update_env_max_tokens(value):
    update_env_setting("MAX_TOKENS", str(value))
def load_max_tokens_from_env():
    try:
        return int(os.getenv("MAX_TOKENS", "450"))
    except Exception:
        return 450
max_tokens = load_max_tokens_from_env()

def update_env_alarm_time(value):
    update_env_setting("ALARM_TIME", str(value))
def load_alarm_time_from_env():
    return os.getenv("ALARM_TIME", "")
alarm_time = load_alarm_time_from_env()

def update_env_model_preset(value):
    update_env_setting("MODEL_PRESET", str(value))
def load_model_preset_from_env():
    return os.getenv("MODEL_PRESET", "Default")
model_preset = load_model_preset_from_env()

import socket

def auto_detect_ollama_models():
    """
    Automatically detect available Ollama models and update .env file.
    Returns the detected models list or None if not found.
    """
    print("[SETTINGS] Searching for available Ollama models...")
    
    # Ensure we know which host:port Ollama is on
    detected_host = ensure_ollama_host()
    
    try:
        import requests
        response = requests.get(f"http://{detected_host}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            if models:
                print(f"[SETTINGS] Found {len(models)} Ollama models: {', '.join(models)}")
                return models
            else:
                print("[SETTINGS] No Ollama models found.")
                return None
        else:
            print(f"[SETTINGS] Ollama API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"[SETTINGS] Could not connect to Ollama: {e}")
        return None

def auto_detect_and_set_ollama_model():
    """
    Smartly detect and set the best available Ollama model for the environment.
    1. Prefer user-set model if available.
    2. Prefer models from a preferred list.
    3. Prefer the smallest model (for speed).
    4. If all else fails, pick the most recently modified model.
    5. Log all decisions and results.
    """
    print("[SETTINGS] Starting smart Ollama model detection...")
    models = auto_detect_ollama_models()
    if not models:
        print("[SETTINGS] No Ollama models detected. Please ensure Ollama is running.")
        return None

    # 1. Check for user-set model and validate it
    current_model = os.getenv("ZW_OLLAMA_MODEL", "").strip()
    if current_model:
        for model in models:
            if current_model.lower() in model.lower() or model.lower() in current_model.lower():
                print(f"[SETTINGS] User-set model '{current_model}' is available and will be used.")
                update_env_setting("ZW_OLLAMA_MODEL", model)
                return model
        print(f"[SETTINGS] User-set model '{current_model}' is NOT available. Will auto-select.")

    # 2. Preferred list (ordered by desirability)
    preferred_models = [
        'llama3.2', 'llama3', 'deepseek', 'quasar', 'mistral', 'llama2', 'macaroni', 'maid', 'uncensored'
    ]
    for preferred in preferred_models:
        for model in models:
            if preferred in model.lower():
                print(f"[SETTINGS] Preferred model found: {model}")
                update_env_setting("ZW_OLLAMA_MODEL", model)
                return model

    # 3. Smallest model (by name heuristic, since Ollama API doesn't give size)
    # Try to find the model with the shortest name (often the smallest model)
    smallest_model = min(models, key=lambda m: len(m))
    print(f"[SETTINGS] No preferred model found. Using smallest-named model: {smallest_model}")
    update_env_setting("ZW_OLLAMA_MODEL", smallest_model)
    return smallest_model

    # 4. (Optional) Most recently modified model (not available via API, so skip)
    # If Ollama API adds this, you could sort by modification date.

    # 5. If nothing is available, print error
    print("[SETTINGS] No suitable Ollama model found. Please install a model in Ollama.")
    return None

def choose_ollama_model():
    """
    Interactive function to let user choose which Ollama model to use.
    Returns the selected model name or None if cancelled.
    """
    print("[SETTINGS] Interactive Ollama model selection...")
    
    models = auto_detect_ollama_models()
    if not models:
        print("[SETTINGS] No Ollama models found. Please ensure Ollama is running.")
        return None
    
    print("\nAvailable Ollama models:")
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")
    
    try:
        choice = input(f"\nSelect model (1-{len(models)}) or press Enter to skip: ").strip()
        if not choice:
            print("[SETTINGS] Model selection skipped.")
            return None
        
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(models):
            selected_model = models[choice_idx]
            print(f"[SETTINGS] Selected model: {selected_model}")
            update_env_setting("ZW_OLLAMA_MODEL", selected_model)
            return selected_model
        else:
            print("[SETTINGS] Invalid selection.")
            return None
    except (ValueError, KeyboardInterrupt):
        print("[SETTINGS] Model selection cancelled.")
        return None

def auto_detect_web_ui_port(start_port=7864, max_attempts=10):
    """Auto-detect an available port for the Web UI, update settings and .env."""
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return False
            except OSError:
                return True
    
    # Use the port from env if set and available
    env_port = int(os.getenv("WEB_UI_PORT", str(start_port)))
    if not is_port_in_use(env_port):
        WEB_UI_PORT = env_port
        update_env_setting("WEB_UI_PORT", str(WEB_UI_PORT))
        globals()["WEB_UI_PORT"] = WEB_UI_PORT
        return WEB_UI_PORT
    # Otherwise, find a free port
    for i in range(max_attempts):
        port = start_port + i
        if not is_port_in_use(port):
            WEB_UI_PORT = port
            update_env_setting("WEB_UI_PORT", str(WEB_UI_PORT))
            globals()["WEB_UI_PORT"] = WEB_UI_PORT
            return WEB_UI_PORT
    # If none found, fallback to start_port
    WEB_UI_PORT = start_port
    update_env_setting("WEB_UI_PORT", str(WEB_UI_PORT))
    globals()["WEB_UI_PORT"] = WEB_UI_PORT
    return WEB_UI_PORT

# API Fallback settings
API_FALLBACK_ENABLED = os.getenv("API_FALLBACK_ENABLED", "ON").upper() == "ON"
API_FALLBACK_MODEL = os.getenv("API_FALLBACK_MODEL", "")
API_FALLBACK_HOST = os.getenv("API_FALLBACK_HOST", "127.0.0.1:5000")

# Language settings
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en").lower()
AUTO_DETECT_LANGUAGE = os.getenv("AUTO_DETECT_LANGUAGE", "OFF").upper() == "ON"
LANGUAGE_DETECTION_CONFIDENCE = float(os.getenv("LANGUAGE_DETECTION_CONFIDENCE", "0.7"))
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish", 
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ar": "Arabic",
    "hi": "Hindi",
    "auto": "Auto-detect"
}

def update_env_api_fallback(enabled):
    """Update API_FALLBACK_ENABLED in the .env file."""
    update_env_setting("API_FALLBACK_ENABLED", "ON" if enabled else "OFF")

def load_api_fallback_from_env():
    """Load API_FALLBACK_ENABLED from the .env file or environment."""
    value = os.getenv("API_FALLBACK_ENABLED", "ON").strip().upper()
    return value == "ON"

# API Fallback toggle (persistent)
api_fallback_enabled = load_api_fallback_from_env()

def update_env_api_fallback_model(model):
    """Update API_FALLBACK_MODEL in the .env file."""
    update_env_setting("API_FALLBACK_MODEL", model)

def update_env_api_fallback_host(host):
    """Update API_FALLBACK_HOST in the .env file."""
    update_env_setting("API_FALLBACK_HOST", host)

# Formal Filter settings
FORMAL_FILTER_ENABLED = os.getenv("FORMAL_FILTER_ENABLED", "ON").upper() == "ON"
FORMAL_FILTER_STRENGTH = os.getenv("FORMAL_FILTER_STRENGTH", "medium").lower()  # low, medium, high
FORMAL_FILTER_CUSTOM_PHRASES = os.getenv("FORMAL_FILTER_CUSTOM_PHRASES", "").split(",") if os.getenv("FORMAL_FILTER_CUSTOM_PHRASES") else []
FORMAL_FILTER_CUSTOM_PATTERNS = os.getenv("FORMAL_FILTER_CUSTOM_PATTERNS", "").split(",") if os.getenv("FORMAL_FILTER_CUSTOM_PATTERNS") else []
FORMAL_FILTER_REPLACEMENT_MODE = os.getenv("FORMAL_FILTER_REPLACEMENT_MODE", "natural").lower()  # natural, casual, friendly, custom

def update_env_formal_filter(enabled):
    """Update FORMAL_FILTER_ENABLED in the .env file."""
    update_env_setting("FORMAL_FILTER_ENABLED", "ON" if enabled else "OFF")

def load_formal_filter_from_env():
    """Load FORMAL_FILTER_ENABLED from the .env file or environment."""
    value = os.getenv("FORMAL_FILTER_ENABLED", "ON").strip().upper()
    return value == "ON"

def update_env_formal_filter_strength(strength):
    """Update FORMAL_FILTER_STRENGTH in the .env file."""
    update_env_setting("FORMAL_FILTER_STRENGTH", strength.lower())

def update_env_formal_filter_custom_phrases(phrases):
    """Update FORMAL_FILTER_CUSTOM_PHRASES in the .env file."""
    phrase_string = ",".join(phrases) if phrases else ""
    update_env_setting("FORMAL_FILTER_CUSTOM_PHRASES", phrase_string)

def update_env_formal_filter_custom_patterns(patterns):
    """Update FORMAL_FILTER_CUSTOM_PATTERNS in the .env file."""
    pattern_string = ",".join(patterns) if patterns else ""
    update_env_setting("FORMAL_FILTER_CUSTOM_PATTERNS", pattern_string)

def update_env_formal_filter_replacement_mode(mode):
    """Update FORMAL_FILTER_REPLACEMENT_MODE in the .env file."""
    update_env_setting("FORMAL_FILTER_REPLACEMENT_MODE", mode.lower())

# Formal Filter toggle (persistent)
formal_filter_enabled = load_formal_filter_from_env()

# Default formal filter configurations
DEFAULT_FORMAL_PHRASES = {
    "low": [
        "how can i assist you",
        "to be of service",
        "how may i help you"
    ],
    "medium": [
        "how can i assist you",
        "how may i help you", 
        "how can i help you today",
        "how may i assist you today",
        "what can i do for you",
        "how can i be of assistance",
        "is there anything i can help you with",
        "how can i support you",
        "what would you like me to help you with",
        "how can i be of service",
        "to see you again! how can i assist you today",
        "to be of service",
        "how can i be of assistance today",
        "what would you like assistance with",
        "how can i be helpful",
        "what can i help you with today"
    ],
    "high": [
        "how can i assist you",
        "how may i help you", 
        "how can i help you today",
        "how may i assist you today",
        "what can i do for you",
        "how can i be of assistance",
        "is there anything i can help you with",
        "how can i support you",
        "what would you like me to help you with",
        "how can i be of service",
        "to see you again! how can i assist you today",
        "to be of service",
        "how can i be of assistance today",
        "what would you like assistance with",
        "how can i be helpful",
        "what can i help you with today",
        "to assist",
        "to help",
        "to support",
        "to be of assistance",
        "how can i be of help",
        "what can i assist you with",
        "how may i be of service",
        "what would you like me to do for you",
        "how can i be of use",
        "what can i do to help",
        "how may i be of assistance",
        "what would you like assistance with",
        "how can i be of service to you",
        "what can i help you with",
        "how may i help you today",
        "what would you like me to help you with today"
    ]
}

DEFAULT_FORMAL_PATTERNS = {
    "low": [
        r'\bto\s+be\s+of\s+service\b',
        r'\bhow\s+can\s+i\s+assist\s+you\b'
    ],
    "medium": [
        r'\bto\s+be\s+of\s+service\b',
        r'\bhow\s+can\s+i\s+assist\s+you\b',
        r'\bhow\s+may\s+i\s+assist\s+you\b',
        r'\bwhat\s+can\s+i\s+do\s+for\s+you\b',
        r'\bis\s+there\s+anything\s+i\s+can\s+help\s+you\s+with\b',
        r'\bhow\s+can\s+i\s+be\s+of\s+assistance\b'
    ],
    "high": [
        r'\bto\s+be\s+of\s+service\b',
        r'\bhow\s+can\s+i\s+assist\s+you\b',
        r'\bhow\s+may\s+i\s+assist\s+you\b',
        r'\bwhat\s+can\s+i\s+do\s+for\s+you\b',
        r'\bis\s+there\s+anything\s+i\s+can\s+help\s+you\s+with\b',
        r'\bhow\s+can\s+i\s+be\s+of\s+assistance\b',
        r'\bto\s+(?:be\s+of\s+)?(?:service|assist|help)\b',
        r'\bhow\s+can\s+i\s+(?:assist|help|support)\b',
        r'\bwhat\s+can\s+i\s+(?:do|assist|help)\b',
        r'\bhow\s+may\s+i\s+(?:assist|help|support)\b',
        r'\bwhat\s+would\s+you\s+like\s+me\s+to\s+(?:do|assist|help)\b',
        r'\bhow\s+can\s+i\s+be\s+of\s+(?:service|assistance|help)\b',
        r'\bwhat\s+can\s+i\s+(?:assist|help)\s+you\s+with\b',
        r'\bhow\s+may\s+i\s+be\s+of\s+(?:service|assistance|help)\b'
    ]
}

DEFAULT_REPLACEMENT_RESPONSES = {
    "natural": [
        "Hey! How's it going?",
        "Hi there! What's up?",
        "Hey! How are you doing?",
        "What's on your mind?"
    ],
    "casual": [
        "Hey! How's it going? What's up?",
        "Hi there! What's on your mind?",
        "Hey! How are you doing?",
        "What's up? How's your day going?"
    ],
    "friendly": [
        "Hey there! What's on your mind? 😊",
        "Hi! How are you doing today?",
        "Hey! What's up?",
        "How's it going? 😊"
    ],
    "custom": [
        "Hey! How are you doing? What's on your mind?",
        "Hi there! How's your day going?",
        "Hey! What's up?",
        "How are you feeling today?"
    ]
}

def get_formal_filter_config():
    """Get the current formal filter configuration"""
    strength = FORMAL_FILTER_STRENGTH
    custom_phrases = FORMAL_FILTER_CUSTOM_PHRASES
    custom_patterns = FORMAL_FILTER_CUSTOM_PATTERNS
    replacement_mode = FORMAL_FILTER_REPLACEMENT_MODE
    
    # Combine default phrases with custom ones
    phrases = DEFAULT_FORMAL_PHRASES.get(strength, DEFAULT_FORMAL_PHRASES["medium"]).copy()
    if custom_phrases:
        phrases.extend([p.strip().lower() for p in custom_phrases if p.strip()])
    
    # Combine default patterns with custom ones
    patterns = DEFAULT_FORMAL_PATTERNS.get(strength, DEFAULT_FORMAL_PATTERNS["medium"]).copy()
    if custom_patterns:
        patterns.extend([p.strip() for p in custom_patterns if p.strip()])
    
    # Get replacement responses
    replacements = DEFAULT_REPLACEMENT_RESPONSES.get(replacement_mode, DEFAULT_REPLACEMENT_RESPONSES["natural"])
    
    return {
        "enabled": FORMAL_FILTER_ENABLED,
        "strength": strength,
        "phrases": phrases,
        "patterns": patterns,
        "replacements": replacements,
        "custom_phrases": custom_phrases,
        "custom_patterns": custom_patterns,
        "replacement_mode": replacement_mode
    }

# ---------------------------------------------------------------------------
# Ollama Server Auto-Detection
# ---------------------------------------------------------------------------


# Default host candidates (localhost plus common docker / WSL port forwards)
_OLLAMA_CANDIDATE_PORTS = [11434, 51134, 11435, 11436]

# Cache detected host in module global
_DETECTED_OLLAMA_HOST = None


def _port_has_ollama(port: int) -> bool:
    """Check if an Ollama server responds on the given port."""
    import requests, json
    try:
        r = requests.get(f"http://127.0.0.1:{port}/api/tags", timeout=2)
        if r.status_code == 200 and "models" in r.text:
            return True
    except requests.exceptions.RequestException:
        pass
    return False


def ensure_ollama_host() -> str:
    """Return host:port for Ollama, auto-detect if needed and print the choice."""
    global _DETECTED_OLLAMA_HOST

    # If we already detected during this run, reuse it
    if _DETECTED_OLLAMA_HOST:
        return _DETECTED_OLLAMA_HOST

    # 1. Check env var
    env_host = os.getenv("OLLAMA_HOST", "").strip()
    if env_host:
        _DETECTED_OLLAMA_HOST = env_host
        # Ensure the current process also uses the detected host immediately
        os.environ["OLLAMA_HOST"] = _DETECTED_OLLAMA_HOST
        print(f"[SETTINGS] Using OLLAMA_HOST from environment: {_DETECTED_OLLAMA_HOST}")
        return _DETECTED_OLLAMA_HOST

    # 2. Probe common ports
    print("[SETTINGS] Searching for local Ollama server…")
    for p in _OLLAMA_CANDIDATE_PORTS:
        if _port_has_ollama(p):
            _DETECTED_OLLAMA_HOST = f"127.0.0.1:{p}"
            # Persist in current env so downstream imports (e.g. ollama) pick it up
            os.environ["OLLAMA_HOST"] = _DETECTED_OLLAMA_HOST
            print(f"[SETTINGS] Found Ollama on {_DETECTED_OLLAMA_HOST}")
            # Update env file for next launch
            update_env_setting("OLLAMA_HOST", _DETECTED_OLLAMA_HOST)
            return _DETECTED_OLLAMA_HOST

    # 3. Fallback to default 127.0.0.1:11434 (even if not responding) so code still builds URL
    _DETECTED_OLLAMA_HOST = "127.0.0.1:11434"
    # Fallback host – also set for the running session so the ollama client resolves
    os.environ["OLLAMA_HOST"] = _DETECTED_OLLAMA_HOST
    print("[SETTINGS] Could not find running Ollama – defaulting to 127.0.0.1:11434")
    return _DETECTED_OLLAMA_HOST

def check_api_health():
    """
    Check the health of all detected API endpoints.
    Returns dict with status of each API type.
    """
    print("[SETTINGS] Checking API health...")
    health_status = {
        "oobabooga": {"available": False, "host": None, "error": None},
        "ollama": {"available": False, "host": None, "error": None},
        "fallback": {"available": False, "models": [], "error": None}
    }
    
    # Check Oobabooga
    try:
        ooga_host = os.getenv("HOST_PORT", "127.0.0.1:5000")
        # Try multiple endpoints to detect Oobabooga
        ooga_detected = False
        
        # Try startup-events first (Gradio endpoint)
        try:
            response = requests.get(f"http://{ooga_host}/startup-events", timeout=3)
            if response.status_code == 200:
                ooga_detected = True
        except:
            pass
        
        # If startup-events didn't work, try the API endpoints
        if not ooga_detected:
            try:
                response = requests.get(f"http://{ooga_host}/v1/chat/completions", timeout=3)
                if response.status_code in [200, 405]:  # 405 is "Method Not Allowed" which means endpoint exists
                    ooga_detected = True
            except:
                pass
        
        if not ooga_detected:
            try:
                response = requests.get(f"http://{ooga_host}/api/v1/model", timeout=3)
                if response.status_code == 200:
                    ooga_detected = True
            except:
                pass
        
        if not ooga_detected:
            try:
                response = requests.get(f"http://{ooga_host}/api/v1/generate", timeout=3)
                if response.status_code in [200, 405]:
                    ooga_detected = True
            except:
                pass
        
        if ooga_detected:
            health_status["oobabooga"]["available"] = True
            health_status["oobabooga"]["host"] = ooga_host
            print(f"[SETTINGS] ✅ Oobabooga healthy at {ooga_host}")
        else:
            health_status["oobabooga"]["error"] = "No API endpoints responding"
            print(f"[SETTINGS] ❌ Oobabooga not available: no API endpoints responding")
    except Exception as e:
        health_status["oobabooga"]["error"] = str(e)
        print(f"[SETTINGS] ❌ Oobabooga not available: {e}")
    
    # Check Ollama
    try:
        ollama_host = ensure_ollama_host()
        response = requests.get(f"http://{ollama_host}/api/tags", timeout=3)  # Reduced to 3 seconds for consistency
        if response.status_code == 200:
            models_data = response.json()
            available_models = models_data.get("models", [])
            model_count = len(available_models)
            
            # Check if any models are actually loaded (have VRAM usage)
            loaded_models = []
            for model in available_models:
                try:
                    # Check if model is loaded by trying to get its info
                    model_name = model.get("name", "")
                    if model_name:
                        # Try to get model info to see if it's loaded
                        info_response = requests.get(f"http://{ollama_host}/api/show", json={"name": model_name}, timeout=3)
                        if info_response.status_code == 200:
                            model_info = info_response.json()
                            # Check if model has parameters (indicates it's loaded)
                            if model_info.get("parameters"):
                                loaded_models.append(model_name)
                except Exception:
                    # If we can't check individual model, assume it's not loaded
                    pass
            
            if loaded_models:
                health_status["ollama"]["available"] = True
                health_status["ollama"]["host"] = ollama_host
                print(f"[SETTINGS] ✅ Ollama healthy at {ollama_host} ({len(loaded_models)}/{model_count} models loaded)")
            else:
                health_status["ollama"]["available"] = False
                health_status["ollama"]["error"] = f"Daemon running but no models loaded ({model_count} available)"
                print(f"[SETTINGS] ⚠️ Ollama daemon running but no models loaded ({model_count} available)")
        else:
            health_status["ollama"]["error"] = f"HTTP {response.status_code}"
    except Exception as e:
        health_status["ollama"]["error"] = str(e)
        print(f"[SETTINGS] ❌ Ollama not available: {e}")
    
    # Check Fallback API
    try:
        from API.fallback_api import discover_models, get_system_info
        available_models = discover_models()
        system_info = get_system_info()
        health_status["fallback"]["available"] = True
        health_status["fallback"]["models"] = available_models
        print(f"[SETTINGS] ✅ Fallback API available ({len(available_models)} models, {system_info.get('memory_available_gb', 0):.1f}GB RAM)")
    except Exception as e:
        health_status["fallback"]["error"] = str(e)
        print(f"[SETTINGS] ❌ Fallback API not available: {e}")
    
    return health_status

def load_model_via_api(model_name, api_type="auto"):
    """
    Load a model through the specified API type.
    
    Args:
        model_name: Name of the model to load
        api_type: "oobabooga", "ollama", "fallback", or "auto"
    
    Returns:
        dict with success status and details
    """
    print(f"[SETTINGS] Loading model '{model_name}' via {api_type} API...")
    
    if api_type == "auto":
        # Try in order of preference: Oobabooga -> Ollama -> Fallback
        health = check_api_health()
        if health["oobabooga"]["available"]:
            api_type = "oobabooga"
        elif health["ollama"]["available"]:
            api_type = "ollama"
        elif health["fallback"]["available"]:
            api_type = "fallback"
        else:
            return {"success": False, "error": "No APIs available"}
    
    try:
        if api_type == "oobabooga":
            return load_model_oobabooga(model_name)
        elif api_type == "ollama":
            return load_model_ollama(model_name)
        elif api_type == "fallback":
            return load_model_fallback(model_name)
        else:
            return {"success": False, "error": f"Unknown API type: {api_type}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def load_model_oobabooga(model_name):
    """Load a model in Oobabooga via API."""
    try:
        ooga_host = os.getenv("HOST_PORT", "127.0.0.1:5000")
        load_url = f"http://{ooga_host}/api/v1/model"
        
        # First, check current model
        response = requests.get(load_url, timeout=10)
        if response.status_code == 200:
            current_model = response.json().get("result", "")
            if current_model == model_name:
                print(f"[SETTINGS] Model '{model_name}' already loaded in Oobabooga")
                return {"success": True, "message": f"Model '{model_name}' already loaded"}
        
        # Load the new model
        load_data = {"model_name": model_name}
        response = requests.post(load_url, json=load_data, timeout=60)  # Model loading can take time
        
        if response.status_code == 200:
            result = response.json()
            if result.get("result") == model_name:
                print(f"[SETTINGS] ✅ Successfully loaded '{model_name}' in Oobabooga")
                return {"success": True, "message": f"Loaded '{model_name}' in Oobabooga"}
            else:
                return {"success": False, "error": f"Model load result mismatch: {result}"}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"success": False, "error": f"Exception loading Oobabooga model: {e}"}

def load_model_ollama(model_name):
    """Load/pull a model in Ollama via API."""
    try:
        ollama_host = ensure_ollama_host()
        
        # Check if model exists locally
        list_url = f"http://{ollama_host}/api/tags"
        response = requests.get(list_url, timeout=10)
        if response.status_code == 200:
            models_data = response.json()
            local_models = [m["name"] for m in models_data.get("models", [])]
            if model_name in local_models:
                print(f"[SETTINGS] Model '{model_name}' already available in Ollama")
                # Update environment variable
                update_env_setting("ZW_OLLAMA_MODEL", model_name)
                return {"success": True, "message": f"Model '{model_name}' ready in Ollama"}
        
        # Pull the model
        pull_url = f"http://{ollama_host}/api/pull"
        pull_data = {"name": model_name}
        
        print(f"[SETTINGS] Pulling model '{model_name}' in Ollama (this may take a while)...")
        response = requests.post(pull_url, json=pull_data, timeout=300)  # 5 minutes timeout
        
        if response.status_code == 200:
            print(f"[SETTINGS] ✅ Successfully pulled '{model_name}' in Ollama")
            # Update environment variable
            update_env_setting("ZW_OLLAMA_MODEL", model_name)
            return {"success": True, "message": f"Pulled '{model_name}' in Ollama"}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"success": False, "error": f"Exception loading Ollama model: {e}"}

def load_model_fallback(model_name):
    """Load a model in the fallback API system."""
    try:
        from API.fallback_api import switch_fallback_model, get_fallback_llm
        
        # Try to switch to the model
        success = switch_fallback_model(model_name)
        if success:
            print(f"[SETTINGS] ✅ Successfully loaded '{model_name}' in fallback API")
            # Update environment variable
            update_env_setting("API_FALLBACK_MODEL", model_name)
            return {"success": True, "message": f"Loaded '{model_name}' in fallback API"}
        else:
            return {"success": False, "error": f"Failed to switch to model '{model_name}'"}
            
    except Exception as e:
        return {"success": False, "error": f"Exception loading fallback model: {e}"}

def get_available_models(api_type="all"):
    """
    Get list of available models from the specified API(s).
    
    Args:
        api_type: "oobabooga", "ollama", "fallback", or "all"
    
    Returns:
        dict with models from each API
    """
    models = {"oobabooga": [], "ollama": [], "fallback": []}
    
    if api_type in ["oobabooga", "all"]:
        try:
            ooga_host = os.getenv("HOST_PORT", "127.0.0.1:5000")
            # Oobabooga doesn't have a direct list endpoint, but we can try to get available models
            # This would need to be implemented based on the specific Oobabooga installation
            # For now, we'll leave this empty or check for common model directories
            models["oobabooga"] = []  # Could scan models/ directory if accessible
        except Exception as e:
            print(f"[SETTINGS] Error getting Oobabooga models: {e}")
    
    if api_type in ["ollama", "all"]:
        try:
            ollama_host = ensure_ollama_host()
            response = requests.get(f"http://{ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                models["ollama"] = [m["name"] for m in models_data.get("models", [])]
        except Exception as e:
            print(f"[SETTINGS] Error getting Ollama models: {e}")
    
    if api_type in ["fallback", "all"]:
        try:
            from API.fallback_api import discover_models
            models["fallback"] = discover_models()
        except Exception as e:
            print(f"[SETTINGS] Error getting fallback models: {e}")
    
    return models

def check_daemon_status():
    """
    Check if required AI daemons (Ollama, Oobabooga) are running.
    Returns status and provides guidance on starting them.
    """
    print("[SETTINGS] Checking daemon status...")
    daemon_status = {
        "ollama": {"running": False, "command": None, "error": None},
        "oobabooga": {"running": False, "command": None, "error": None}
    }
    
    # Check Ollama daemon
    try:
        ollama_host = ensure_ollama_host()
        response = requests.get(f"http://{ollama_host}/api/tags", timeout=3)  # Reduced to 3 seconds for consistency
        if response.status_code == 200:
            models_data = response.json()
            available_models = models_data.get("models", [])
            model_count = len(available_models)
            
            # Check if any models are actually loaded (have VRAM usage)
            loaded_models = []
            for model in available_models:
                try:
                    # Check if model is loaded by trying to get its info
                    model_name = model.get("name", "")
                    if model_name:
                        # Try to get model info to see if it's loaded
                        info_response = requests.get(f"http://{ollama_host}/api/show", json={"name": model_name}, timeout=3)
                        if info_response.status_code == 200:
                            model_info = info_response.json()
                            # Check if model has parameters (indicates it's loaded)
                            if model_info.get("parameters"):
                                loaded_models.append(model_name)
                except Exception:
                    # If we can't check individual model, assume it's not loaded
                    pass
            
            if loaded_models:
                daemon_status["ollama"]["running"] = True
                print(f"[SETTINGS] ✅ Ollama daemon running at {ollama_host} ({len(loaded_models)}/{model_count} models loaded)")
            else:
                daemon_status["ollama"]["running"] = False
                daemon_status["ollama"]["error"] = f"No models loaded ({model_count} available)"
                print(f"[SETTINGS] ⚠️ Ollama daemon running but no models loaded ({model_count} available)")
        else:
            daemon_status["ollama"]["error"] = f"HTTP {response.status_code}"
    except Exception as e:
        daemon_status["ollama"]["error"] = str(e)
        daemon_status["ollama"]["command"] = get_ollama_start_command()
        print(f"[SETTINGS] ❌ Ollama daemon not running: {e}")
        print(f"[SETTINGS] 💡 To start Ollama: {daemon_status['ollama']['command']}")
    
    # Check Oobabooga daemon  
    try:
        ooga_host = os.getenv("HOST_PORT", "127.0.0.1:5000")
        # Try multiple endpoints to detect Oobabooga
        ooga_detected = False
        
        # Try startup-events first (Gradio endpoint)
        try:
            response = requests.get(f"http://{ooga_host}/startup-events", timeout=3)
            if response.status_code == 200:
                ooga_detected = True
        except:
            pass
        
        # If startup-events didn't work, try the API endpoints
        if not ooga_detected:
            try:
                response = requests.get(f"http://{ooga_host}/v1/chat/completions", timeout=3)
                if response.status_code in [200, 405]:  # 405 is "Method Not Allowed" which means endpoint exists
                    ooga_detected = True
            except:
                pass
        
        if not ooga_detected:
            try:
                response = requests.get(f"http://{ooga_host}/api/v1/model", timeout=3)
                if response.status_code == 200:
                    ooga_detected = True
            except:
                pass
        
        if not ooga_detected:
            try:
                response = requests.get(f"http://{ooga_host}/api/v1/generate", timeout=3)
                if response.status_code in [200, 405]:
                    ooga_detected = True
            except:
                pass
        
        if ooga_detected:
            daemon_status["oobabooga"]["running"] = True
            print(f"[SETTINGS] ✅ Oobabooga daemon running at {ooga_host}")
        else:
            daemon_status["oobabooga"]["error"] = "No API endpoints responding"
            daemon_status["oobabooga"]["command"] = get_oobabooga_start_command()
            print(f"[SETTINGS] ❌ Oobabooga daemon not running: no API endpoints responding")
            print(f"[SETTINGS] 💡 To start Oobabooga: {daemon_status['oobabooga']['command']}")
    except Exception as e:
        daemon_status["oobabooga"]["error"] = str(e)
        daemon_status["oobabooga"]["command"] = get_oobabooga_start_command()
        print(f"[SETTINGS] ❌ Oobabooga daemon not running: {e}")
        print(f"[SETTINGS] 💡 To start Oobabooga: {daemon_status['oobabooga']['command']}")
    
    return daemon_status

def get_ollama_start_command():
    """Get the appropriate command to start Ollama based on the OS."""
    import platform
    system = platform.system().lower()
    
    if system == "windows":
        return "ollama serve (or start Ollama Desktop app)"
    elif system == "darwin":  # macOS
        return "ollama serve (or start Ollama.app)"
    else:  # Linux and others
        return "ollama serve"

def get_oobabooga_start_command():
    """Get guidance for starting Oobabooga."""
    return "Start text-generation-webui with API enabled (--api flag)"

def ensure_daemons_running():
    """
    Check daemon status and provide helpful guidance if they're not running.
    This function doesn't auto-start daemons but helps users start them manually.
    """
    print("[SETTINGS] Ensuring AI daemons are available...")
    status = check_daemon_status()
    
    running_count = sum(1 for daemon in status.values() if daemon["running"])
    total_count = len(status)
    
    # Always ensure fallback model is set up
    try:
        from API.fallback_api import auto_setup_fallback_model
        fallback_model = auto_setup_fallback_model()
        if fallback_model:
            print(f"[SETTINGS] ✅ Fallback model ready: {fallback_model}")
    except Exception as e:
        print(f"[SETTINGS] ⚠️ Fallback model setup failed: {e}")
    
    if running_count == total_count:
        print(f"[SETTINGS] ✅ All {total_count} daemons are running!")
        return True
    elif running_count > 0:
        print(f"[SETTINGS] ⚠️ {running_count}/{total_count} daemons running - partial functionality available")
        print("[SETTINGS] Fallback API will be used when primary APIs are unavailable")
        return True  # Partial success is still success
    else:
        print(f"[SETTINGS] ❌ No AI daemons running - only fallback API available")
        print("[SETTINGS] For full functionality, please start at least one AI daemon:")
        for name, info in status.items():
            if info["command"]:
                print(f"[SETTINGS]   {name.title()}: {info['command']}")
        return False

def auto_configure_api_priority():
    """
    Automatically configure API priority based on what's available and working.
    Updates API_TYPE environment variable accordingly.
    """
    print("[SETTINGS] Auto-configuring API priority...")
    
    health = check_api_health()
    current_api_type = os.getenv("API_TYPE", "Oobabooga")
    
    # Priority order: Oobabooga > Ollama > Fallback
    if health["oobabooga"]["available"]:
        recommended_api = "Oobabooga"
        print(f"[SETTINGS] ✅ Oobabooga available - recommending as primary API")
    elif health["ollama"]["available"]:
        recommended_api = "Ollama"  
        print(f"[SETTINGS] ✅ Ollama available - recommending as primary API")
    else:
        recommended_api = "Oobabooga"  # Keep default, fallback will handle it
        print(f"[SETTINGS] ⚠️ No external APIs available - fallback API will be used")
    
    if current_api_type != recommended_api:
        print(f"[SETTINGS] Updating API_TYPE from '{current_api_type}' to '{recommended_api}'")
        update_env_setting("API_TYPE", recommended_api)
        # Update the environment variable immediately for current session
        os.environ["API_TYPE"] = recommended_api
    else:
        print(f"[SETTINGS] API_TYPE already set to optimal value: '{current_api_type}'")
    
    return recommended_api

# Language update functions
def update_env_default_language(lang_code):
    update_env_setting("DEFAULT_LANGUAGE", lang_code)

def load_default_language_from_env():
    return os.getenv("DEFAULT_LANGUAGE", "en").lower()

def update_env_auto_detect_language(enabled):
    update_env_setting("AUTO_DETECT_LANGUAGE", "ON" if enabled else "OFF")

def load_auto_detect_language_from_env():
    return os.getenv("AUTO_DETECT_LANGUAGE", "OFF").strip().upper() == "ON"

# Character name global (do not call load_character_name_from_card at module level)
char_name = os.environ.get('CHAR_NAME', 'Assistant')

def load_character_name_from_card():
    """Load character name from character card, with fallback to environment variable."""
    try:
        from API.character_card import get_character_name, load_char_card
        load_char_card()  # Load character card first
        name = get_character_name()
        if not name:
            name = os.environ.get('CHAR_NAME', 'Assistant')
        return name
    except Exception as e:
        print(f"Error loading character name from card: {e}")
        return os.environ.get('CHAR_NAME', 'Assistant')

def update_env_llm_settings(temperature=None, top_p=None, top_k=None, frequency_penalty=None, presence_penalty=None, max_tokens=None):
    """Update LLM generation settings in the .env file."""
    if temperature is not None:
        update_env_setting("TEMPERATURE", str(temperature))
    if top_p is not None:
        update_env_setting("TOP_P", str(top_p))
    if top_k is not None:
        update_env_setting("TOP_K", str(top_k))
    if frequency_penalty is not None:
        update_env_setting("FREQUENCY_PENALTY", str(frequency_penalty))
    if presence_penalty is not None:
        update_env_setting("PRESENCE_PENALTY", str(presence_penalty))
    if max_tokens is not None:
        update_env_setting("MAX_TOKENS", str(max_tokens))

def load_llm_settings_from_env():
    """Load LLM settings from environment variables."""
    global TEMPERATURE, TOP_P, TOP_K, FREQUENCY_PENALTY, PRESENCE_PENALTY, MAX_TOKENS
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    TOP_P = float(os.getenv("TOP_P", "0.9"))
    TOP_K = int(os.getenv("TOP_K", "40"))
    FREQUENCY_PENALTY = float(os.getenv("FREQUENCY_PENALTY", "0.0"))
    PRESENCE_PENALTY = float(os.getenv("PRESENCE_PENALTY", "0.0"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "450"))

def update_env_preset_name(preset_name):
    """Update PRESET_NAME in the .env file."""
    update_env_setting("PRESET_NAME", preset_name)

def load_preset_name_from_env():
    """Load PRESET_NAME from environment variables."""
    global PRESET_NAME
    PRESET_NAME = os.getenv("PRESET_NAME", "Default")

# Utility: list available preset names (YAML/JSON) in OOBA_Presets/

def get_preset_list():
    """Return a list of preset file names (without extension) found in OOBA_Presets/."""
    presets_dir = Path("OOBA_Presets")
    if not presets_dir.exists():
        return [PRESET_NAME] if PRESET_NAME else []
    preset_files = list(presets_dir.glob("*.yaml")) + list(presets_dir.glob("*.yml")) + list(presets_dir.glob("*.json"))
    names: list[str] = []
    for file in preset_files:
        # Strip extension
        names.append(file.stem)
    # Always include current preset name at least once
    if PRESET_NAME and PRESET_NAME not in names:
        names.insert(0, PRESET_NAME)
    # Sort alphabetically (case-insensitive)
    names.sort(key=str.lower)
    return names
def check_all_daemons_and_print_status():
    """Check Oobabooga, Ollama, and Fallback daemons and print their status. Set primary API accordingly."""
    import requests
    import os
    import colorama
    from API.fallback_api import ensure_tinyllama_gguf_model

    status = {"oobabooga": False, "ollama": False, "fallback": False}
    details = {"oobabooga": "", "ollama": "", "fallback": ""}
    primary_api = None

    print(colorama.Fore.CYAN + "[SETTINGS] Checking all daemon status..." + colorama.Fore.RESET)

    # --- Oobabooga ---
    ooga_host = os.getenv("HOST_PORT", "127.0.0.1:5000")
    try:
        resp = requests.get(f"http://{ooga_host}/v1/chat/completions", timeout=3)
        if resp.status_code in [200, 405]:
            status["oobabooga"] = True
            details["oobabooga"] = f"running at {ooga_host} (endpoint /v1/chat/completions: {resp.status_code})"
        else:
            details["oobabooga"] = f"endpoint /v1/chat/completions: {resp.status_code}"
    except Exception as e:
        details["oobabooga"] = f"not available: {e}"

    # --- Ollama ---
    ollama_host = os.getenv("OLLAMA_HOST", "127.0.0.1:11434")
    try:
        resp = requests.get(f"http://{ollama_host}/api/tags", timeout=3)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            loaded = False
            for model in models:
                model_name = model.get("name")
                if model_name:
                    try:
                        info = requests.get(f"http://{ollama_host}/api/show", json={"name": model_name}, timeout=3)
                        if info.status_code == 200 and info.json().get("parameters"):
                            loaded = True
                            break
                    except Exception:
                        continue
            if loaded:
                status["ollama"] = True
                details["ollama"] = f"running at {ollama_host} (model loaded)"
            else:
                details["ollama"] = f"daemon running at {ollama_host} (no models loaded)"
        else:
            details["ollama"] = f"endpoint /api/tags: {resp.status_code}"
    except Exception as e:
        details["ollama"] = f"not available: {e}"

    # --- Fallback ---
    try:
        fallback_model = ensure_tinyllama_gguf_model()
        if fallback_model:
            status["fallback"] = True
            details["fallback"] = f"model available: {fallback_model}"
        else:
            details["fallback"] = "model not available"
    except Exception as e:
        details["fallback"] = f"error: {e}"

    # --- Print status table ---
    print("\n" + colorama.Fore.CYAN + "[SETTINGS] Daemon Status:" + colorama.Fore.RESET)
    for k in ["oobabooga", "ollama", "fallback"]:
        icon = colorama.Fore.GREEN + "✅" if status[k] else colorama.Fore.YELLOW + "⚠️"
        print(f"  - {k.capitalize():10}: {icon} {details[k]}" + colorama.Fore.RESET)

    # --- Set primary API ---
    if status["oobabooga"]:
        primary_api = "Oobabooga"
    elif status["ollama"]:
        primary_api = "Ollama"
    elif status["fallback"]:
        primary_api = "Fallback"
    else:
        primary_api = None

    if primary_api:
        print(colorama.Fore.GREEN + f"[SETTINGS] Primary API: {primary_api}" + colorama.Fore.RESET)
        os.environ["API_TYPE"] = primary_api
    else:
        print(colorama.Fore.RED + "[SETTINGS] No available API daemons!" + colorama.Fore.RESET)

    print(colorama.Fore.CYAN + "[SETTINGS] Daemon status check complete." + colorama.Fore.RESET)
    return status, primary_api

# --- Settings Initialization Function ---
def initialize_settings():
    """
    Initialize or reload all global settings from environment variables and config files.
    This is idempotent and can be called multiple times.
    """
    global HOST_PORT, API_TYPE, MODEL_TYPE, OOGABOOGA_SUPPORT_HOST
    global CHAR_NAME, CHARACTER_CARD, YOUR_NAME, PARTNER_NAME, CHARACTER_CONTEXT
    global MODEL_NAME, TOKEN_LIMIT, MESSAGE_PAIR_LIMIT, TIME_IN_ENCODING
    global TEMPERATURE, TOP_P, TOP_K, FREQUENCY_PENALTY, PRESENCE_PENALTY, MAX_TOKENS
    global TEMP_LEVEL, temp_level, PRESET_NAME
    global NEWLINE_CUT_BOOT, RP_SUP_BOOT, API_STREAM_CHATS, SILERO_VAD
    global WHISPER_MODEL, WHISPER_CHOICE, WHISPER_CHUNKS_MAX, AUTOCHAT_MIN_LENGTH
    global AUTOCHAT_SENSITIVITY, DISABLE_FLASH_ATTN
    global WEB_UI_PORT, WEB_UI_SHARE, WEB_UI_THEME
    global VOICE_SPEED, VOICE_VOLUME, AUDIO_DEVICE, MIC_DEVICE
    global MAX_RESPONSE_LENGTH, CHAT_HISTORY_LIMIT, AUTO_SAVE_INTERVAL
    global DEBUG_MODE, LOG_LEVEL, AUTO_BACKUP, BACKUP_INTERVAL
    global RELATIONSHIP_SYSTEM_ENABLED, DEFAULT_RELATIONSHIP_LEVEL, RELATIONSHIP_RESPONSES_ENABLED
    global RELATIONSHIP_MEMORY_ENABLED, RELATIONSHIP_PROGRESSION_SPEED, RELATIONSHIP_DECAY_RATE, RELATIONSHIP_PARTNER_NAME
    global USE_CHATPOPS, chatpop_phrases
    global MODULE_MINECRAFT, is_gaming_loop
    global MODEL_TYPE, MODEL_NAME, MODEL_TEMPLATE
    global hotkeys_locked, speak_shadowchats, speak_only_spokento, max_tokens, stream_chats, newline_cut, asterisk_ban, supress_rp, stopping_strings
    global is_recording, auto_chat, hangout_mode, semi_auto_chat, use_chatpops
    global model_preset, alarm_time, cam_use_image_feed, cam_direct_talk, cam_image_preview, cam_use_screenshot, eyes_follow
    global all_tag_list, cur_tags, all_task_char_list, cur_task_char
    global is_gaming_loop, minecraft_enabled, gaming_enabled, alarm_enabled, vtube_enabled, discord_enabled, twitch_enabled, rag_enabled, vision_enabled
    global TWITCH_ENABLED, twitch_personality, twitch_auto_respond, twitch_response_chance, twitch_cooldown_seconds, twitch_max_message_length
    global use_rvc, rvc_model, rvc_speaker, rvc_pitch, rvc_speed
    global live_pipe_no_speak

    from dotenv import load_dotenv
    load_dotenv(override=True)

    # Environment variables
    HOST_PORT = os.getenv("HOST_PORT", "127.0.0.1:5000")
    API_TYPE = os.getenv("API_TYPE", "Oobabooga")
    MODEL_TYPE = os.getenv("MODEL_TYPE", "chatml")
    OOGABOOGA_SUPPORT_HOST = os.getenv("OOGABOOGA_SUPPORT_HOST", "127.0.0.1:5000")

    # Character settings
    CHAR_NAME = os.getenv("CHAR_NAME", "Z-Waif")
    CHARACTER_CARD = os.getenv("CHARACTER_CARD", "Z-Waif")
    YOUR_NAME = os.getenv("YOUR_NAME", "User")
    PARTNER_NAME = os.getenv("PARTNER_NAME", "User")
    CHARACTER_CONTEXT = os.getenv("CHARACTER_CONTEXT", "You are a friendly and caring AI companion who speaks naturally and conversationally.")

    # Model settings
    MODEL_NAME = os.getenv("MODEL_NAME", "ADEF")
    MODEL_TEMPLATE = os.environ.get("MODEL_TEMPLATE", "chatml")

    # Model context settings
    TOKEN_LIMIT = int(os.getenv("TOKEN_LIMIT", "4096"))
    MESSAGE_PAIR_LIMIT = int(os.getenv("MESSAGE_PAIR_LIMIT", "40"))
    TIME_IN_ENCODING = os.getenv("TIME_IN_ENCODING", "OFF")

    # LLM Temperature and Generation Settings
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    TOP_P = float(os.getenv("TOP_P", "0.9"))
    TOP_K = int(os.getenv("TOP_K", "40"))
    FREQUENCY_PENALTY = float(os.getenv("FREQUENCY_PENALTY", "0.0"))
    PRESENCE_PENALTY = float(os.getenv("PRESENCE_PENALTY", "0.0"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "450"))

    # Add discrete temperature level (legacy support)
    TEMP_LEVEL = int(os.getenv("TEMP_LEVEL", "0"))
    temp_level = TEMP_LEVEL

    # Preset Management
    PRESET_NAME = os.getenv("PRESET_NAME", "Default")

    # Anti-streaming settings
    NEWLINE_CUT_BOOT = os.getenv("NEWLINE_CUT_BOOT", "ON")
    RP_SUP_BOOT = os.getenv("RP_SUP_BOOT", "ON")
    API_STREAM_CHATS = os.getenv("API_STREAM_CHATS", "OFF")
    SILERO_VAD = os.getenv("SILERO_VAD", "ON")

    # Whisper settings
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base.en")
    WHISPER_CHOICE = os.getenv("WHISPER_CHOICE", "faster-whisper")
    WHISPER_CHUNKS_MAX = int(os.getenv("WHISPER_CHUNKS_MAX", "14"))
    AUTOCHAT_MIN_LENGTH = int(os.getenv("AUTOCHAT_MIN_LENGTH", "10"))

    # Autochat sensitivity (shared setting)
    AUTOCHAT_SENSITIVITY = int(os.getenv("AUTOCHAT_SENSITIVITY", "16"))

    # Flash attention control (for CUDA compatibility)
    DISABLE_FLASH_ATTN = os.getenv("DISABLE_FLASH_ATTN", "OFF").lower() == "on"

    # Web UI settings
    WEB_UI_PORT = int(os.getenv("WEB_UI_PORT", "7864"))
    WEB_UI_SHARE = os.getenv("WEB_UI_SHARE", "OFF").lower() == "on"
    WEB_UI_THEME = os.getenv("WEB_UI_THEME", "default")

    # Voice and audio settings
    VOICE_SPEED = float(os.getenv("VOICE_SPEED", "1.0"))
    VOICE_VOLUME = float(os.getenv("VOICE_VOLUME", "1.0"))
    AUDIO_DEVICE = os.getenv("AUDIO_DEVICE", "default")
    MIC_DEVICE = os.getenv("MIC_DEVICE", "default")

    # Chat and response settings
    MAX_RESPONSE_LENGTH = int(os.getenv("MAX_RESPONSE_LENGTH", "500"))
    CHAT_HISTORY_LIMIT = int(os.getenv("CHAT_HISTORY_LIMIT", "50"))
    AUTO_SAVE_INTERVAL = int(os.getenv("AUTO_SAVE_INTERVAL", "10"))

    # System behavior settings
    DEBUG_MODE = os.getenv("DEBUG_MODE", "OFF").lower() == "on"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    AUTO_BACKUP = os.getenv("AUTO_BACKUP", "ON").lower() == "on"
    BACKUP_INTERVAL = int(os.getenv("BACKUP_INTERVAL", "60"))

    # Relationship settings
    RELATIONSHIP_SYSTEM_ENABLED = os.getenv("RELATIONSHIP_SYSTEM_ENABLED", "ON").lower() == "on"
    DEFAULT_RELATIONSHIP_LEVEL = os.getenv("DEFAULT_RELATIONSHIP_LEVEL", "stranger")
    RELATIONSHIP_RESPONSES_ENABLED = os.getenv("RELATIONSHIP_RESPONSES_ENABLED", "ON").lower() == "on"
    RELATIONSHIP_MEMORY_ENABLED = os.getenv("RELATIONSHIP_MEMORY_ENABLED", "ON").lower() == "on"
    RELATIONSHIP_PROGRESSION_SPEED = float(os.getenv("RELATIONSHIP_PROGRESSION_SPEED", "1.0"))
    RELATIONSHIP_DECAY_RATE = float(os.getenv("RELATIONSHIP_DECAY_RATE", "0.1"))
    RELATIONSHIP_PARTNER_NAME = os.getenv("RELATIONSHIP_PARTNER_NAME", "")

    # Chatpops settings
    USE_CHATPOPS = os.getenv("USE_CHATPOPS", "ON").lower() == "on"
    # Load chatpop phrases from JSON file
    try:
        with open("Configurables/Chatpops.json", 'r') as chatpops_file:
            globals()['chatpop_phrases'] = json.load(chatpops_file)
        print(f"[Settings] Loaded {len(chatpop_phrases)} chatpop phrases (reloaded)")
    except Exception as e:
        globals()['chatpop_phrases'] = []
        print(f"[Settings] Error loading chatpop phrases: {e}")

    # Module toggles
    MODULE_MINECRAFT = os.getenv("MODULE_MINECRAFT", "OFF")
    is_gaming_loop = MODULE_MINECRAFT.lower() == "on"

    # --- Release-style settings ---
    hotkeys_locked = False
    speak_shadowchats = True
    speak_only_spokento = False
    max_tokens = MAX_TOKENS
    stream_chats = API_STREAM_CHATS == "ON"
    newline_cut = NEWLINE_CUT_BOOT == "ON"
    asterisk_ban = False
    supress_rp = RP_SUP_BOOT == "ON"
    stopping_strings = ["[System", "\nUser:", "---", "<|", "###"]
    is_recording = False
    auto_chat = False
    hangout_mode = False
    semi_auto_chat = False
    use_chatpops = USE_CHATPOPS
    model_preset = PRESET_NAME
    alarm_time = "00:00"
    cam_use_image_feed = False
    cam_direct_talk = True
    cam_image_preview = True
    cam_use_screenshot = False
    eyes_follow = "None"
    all_tag_list = []
    cur_tags = []
    all_task_char_list = []
    cur_task_char = "None"
    is_gaming_loop = MODULE_MINECRAFT.lower() == "on"
    minecraft_enabled = MODULE_MINECRAFT.lower() == "on"
    gaming_enabled = True
    alarm_enabled = True
    vtube_enabled = False
    discord_enabled = False
    twitch_enabled = os.getenv("MODULE_TWITCH", "OFF").upper() == "ON"
    rag_enabled = True
    vision_enabled = True
    TWITCH_ENABLED = twitch_enabled
    twitch_personality = os.getenv("TWITCH_PERSONALITY", "friendly")
    twitch_auto_respond = os.getenv("TWITCH_AUTO_RESPOND", "ON").upper() == "ON"
    twitch_response_chance = float(os.getenv("TWITCH_RESPONSE_CHANCE", "0.8"))
    twitch_cooldown_seconds = int(os.getenv("TWITCH_COOLDOWN_SECONDS", "3"))
    twitch_max_message_length = int(os.getenv("TWITCH_MAX_MESSAGE_LENGTH", "450"))
    use_rvc = os.environ.get("USE_RVC", "false").lower() == "true"
    rvc_model = os.environ.get("RVC_MODEL", "default")
    rvc_speaker = os.environ.get("RVC_SPEAKER", "0")
    rvc_pitch = float(os.environ.get("RVC_PITCH", "0.0"))
    rvc_speed = float(os.environ.get("RVC_SPEED", "1.0"))
    live_pipe_no_speak = False

    # Voice and audio settings - enable shadow chat by default like release version
    speak_shadowchats = True
    speak_only_spokento = os.environ.get('SPEAK_ONLY_SPOKENTO', 'OFF').upper() == 'ON'
    use_chatpops = os.environ.get('USE_CHATPOPS', 'ON').upper() == 'ON'
