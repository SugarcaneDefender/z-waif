import os
from datetime import datetime

def merge_env_files():
    """Write the exact environment configuration."""
    env_content = """# =============================================================================
# API SETTINGS (REQUIRED)
# =============================================================================
HOST_PORT=127.0.0.1:5000
API_TYPE=Ollama
MODEL_TYPE=chatml
OOGABOOGA_SUPPORT_HOST=127.0.0.1:5000

# API Fallback Settings
API_FALLBACK_ENABLED=ON
API_FALLBACK_MODEL=models\\tinyllama-1.1b-chat-v1.0.Q4_0.gguf
API_FALLBACK_HOST=127.0.0.1:11434

# =============================================================================
# CHARACTER SETTINGS (REQUIRED)
# =============================================================================
CHAR_NAME=Alexcia
YOUR_NAME=User
PARTNER_NAME=YourName
CHARACTER_CONTEXT=You are Alexcia

# =============================================================================
# MODEL CONTEXT SETTINGS
# =============================================================================
TOKEN_LIMIT=4096
MESSAGE_PAIR_LIMIT=40
TIME_IN_ENCODING=OFF

# =============================================================================
# MODEL GENERATION SETTINGS
# =============================================================================
TEMPERATURE=0.7
TOP_P=0.9
TOP_K=40
FREQUENCY_PENALTY=0.0
PRESENCE_PENALTY=0.0
MAX_TOKENS=450
TEMP_LEVEL=0
PRESET_NAME=Default

# =============================================================================
# ANTI-STREAMING SETTINGS
# =============================================================================
NEWLINE_CUT_BOOT=ON
RP_SUP_BOOT=ON
API_STREAM_CHATS=OFF
SILERO_VAD=ON

# =============================================================================
# RELATIONSHIP SETTINGS
# =============================================================================
RELATIONSHIP_SYSTEM_ENABLED=ON
RELATIONSHIP_PARTNER_NAME=
DEFAULT_RELATIONSHIP_LEVEL=friend
RELATIONSHIP_RESPONSES_ENABLED=ON
RELATIONSHIP_MEMORY_ENABLED=ON
RELATIONSHIP_PROGRESSION_SPEED=1.5
RELATIONSHIP_DECAY_RATE=0.05

# =============================================================================
# VOICE AND AUDIO SETTINGS
# =============================================================================
VOICE_SPEED=1.2
VOICE_VOLUME=0.8
AUDIO_DEVICE=default
MIC_DEVICE=default
USE_RVC=true
RVC_HOST=127.0.0.1
RVC_PORT=18888
RVC_MODEL=your_model_name
RVC_SPEAKER=0
RVC_PITCH=0.0
RVC_SPEED=1.0

# =============================================================================
# WHISPER SETTINGS
# =============================================================================
WHISPER_MODEL=base.en
WHISPER_CHOICE=faster-whisper
WHISPER_CHUNKS_MAX=14
FASTER_WHISPER_CPU_TRANSCRIPTION=OFF
FASTER_WHISPER=OFF
WHISPER_CHUNKY=OFF

# =============================================================================
# WEB UI SETTINGS
# =============================================================================
WEB_UI_PORT=8080
WEB_UI_SHARE=ON
WEB_UI_THEME=dark
MAX_RESPONSE_LENGTH=600
CHAT_HISTORY_LIMIT=75
AUTO_SAVE_INTERVAL=15
USE_CHATPOPS=ON

# =============================================================================
# DEBUGGING AND LOGGING
# =============================================================================
DEBUG_MODE=ON
LOG_LEVEL=DEBUG
AUTO_BACKUP=ON
BACKUP_INTERVAL=30
DISABLE_FLASH_ATTN=ON"""

    # Write the content directly to .env
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("Environment file updated successfully!")

if __name__ == "__main__":
    merge_env_files() 