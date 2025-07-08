# Z-WAIF Twitch Integration Setup Guide

## Quick Setup for Personal Channel (Recommended)

This is the simplest way to get your AI companion working on Twitch. Perfect for personal channels or small streamers.

### Step 1: Get Your Twitch OAuth Token

1. Go to [Twitch Token Generator](https://twitchtokengenerator.com/)
2. Click "Connect with Twitch"
3. Select the scopes you need:
   - `chat:read` (to read chat messages)
   - `chat:edit` (to send chat messages)
4. Copy the OAuth token (starts with `oauth:`)

### Step 2: Configure Environment Variables

Open your `.env` file and add:

```env
# Enable Twitch Module
MODULE_TWITCH=ON

# Basic Twitch Configuration
TWITCH_TOKEN=oauth:your_token_here
TWITCH_CHANNEL=your_channel_name
TWITCH_BOT_NAME=z_waif_bot

# Optional: Customize Bot Behavior
TWITCH_PERSONALITY=friendly
TWITCH_AUTO_RESPOND=ON
TWITCH_RESPONSE_CHANCE=0.8
TWITCH_COOLDOWN_SECONDS=3
TWITCH_MAX_MESSAGE_LENGTH=450
```

### Step 3: Test Your Setup

Run the test script to verify everything is working:

```bash
python test_twitch_bot.py
```

This will check:
- ✅ Environment configuration
- ✅ Module imports
- ✅ Bot initialization
- ✅ Main application integration
- ✅ AI modules
- ✅ Async functionality
- ✅ Thread integration

### Step 4: Start Z-WAIF

```bash
python main.py
```

You should see:
```
🎮 Starting Z-WAIF Twitch integration for channel: your_channel
🧠 Verifying AI modules...
   ✅ AI Handler: True
   ✅ Memory Manager: True
   ...
🎮 Twitch bot ready! Connected to: your_channel
```

---

## Advanced Setup: Multiple Channels

For managing multiple Twitch channels simultaneously:

```env
# Use TWITCH_CHANNELS instead of TWITCH_CHANNEL
TWITCH_CHANNELS=channel1,channel2,channel3
```

The bot will connect to all specified channels and respond in each one independently, maintaining separate conversation histories and user relationships per channel.

---

## Advanced Setup: Dedicated Bot Application

For larger streamers or organizations wanting a dedicated bot application:

### Step 1: Create Twitch Application

1. Go to [Twitch Developer Console](https://dev.twitch.tv/console)
2. Click "Register Your Application"
3. Fill in the details:
   - **Name**: Your bot name
   - **OAuth Redirect URLs**: `http://localhost:3000`
   - **Category**: Chat Bot
4. Save and copy the **Client ID** and **Client Secret**

### Step 2: Configure Advanced Settings

```env
# Bot Application Setup
TWITCH_CLIENT_ID=your_client_id_here
TWITCH_CLIENT_SECRET=your_client_secret_here
TWITCH_TOKEN=oauth:your_bot_token_here
TWITCH_CHANNEL=target_channel_name
TWITCH_BOT_NAME=your_bot_name
```

---

## Bot Commands

Users can interact with your AI using these commands:

- `!personality [type]` - Change AI personality (friendly, playful, sarcastic, supportive, energetic)
- `!memory [query]` - Search the AI's memories about conversations
- `!status` - Show bot status and relationship level

---

## Customization Options

### Personality Settings
```env
TWITCH_PERSONALITY=friendly          # Default personality
TWITCH_AUTO_RESPOND=ON              # Auto-respond to messages
TWITCH_RESPONSE_CHANCE=0.8          # 80% chance to respond
TWITCH_COOLDOWN_SECONDS=3           # Minimum time between responses
TWITCH_MAX_MESSAGE_LENGTH=450       # Maximum message length
```

### Character Configuration
The bot uses your main character configuration from `Configurables/CharacterCard.yaml`. It automatically adapts responses for Twitch chat context while maintaining your character's personality.

---

## Integration Features

### ✅ **Flawless Main Application Integration**
- Uses the same AI system as your main Z-WAIF instance
- Shares character personality and memory across all platforms
- Platform-specific response cleaning for Twitch chat
- Seamless integration with voice, vision, and other modules

### ✅ **Enhanced AI Capabilities**
- **Contextual Responses**: AI understands it's on Twitch and adapts accordingly
- **User Memory**: Remembers individual users across chat sessions
- **Relationship Tracking**: Builds relationships with individual chatters
- **Smart Response Control**: Prevents spam and maintains conversation flow
- **Safety Filtering**: Built-in content filtering for appropriate responses

### ✅ **Platform-Aware Messaging**
- Automatically removes streaming-specific language for personal conversations
- Adapts response length and style for Twitch chat
- Maintains consistent personality across all platforms
- Handles both chat messages and commands intelligently

### ✅ **Multi-Platform Memory**
- Chat history is saved separately per platform
- Cross-platform user recognition and relationship building
- RAG (Retrieval-Augmented Generation) for long-term memory
- Conversation analysis and sentiment tracking

---

## Troubleshooting

### Common Issues

**Bot doesn't connect:**
- Check your OAuth token is valid and starts with `oauth:`
- Verify the channel name is correct (no spaces or special characters)
- Make sure `MODULE_TWITCH=ON` in your .env file

**Bot connects but doesn't respond:**
- Check `TWITCH_AUTO_RESPOND=ON`
- Verify `TWITCH_RESPONSE_CHANCE` is above 0.0
- Check the console for any error messages
- Run `python test_twitch_bot.py` to diagnose issues

**Responses are cut off:**
- Increase `TWITCH_MAX_MESSAGE_LENGTH` (Twitch limit is 500 characters)
- Check if the AI is generating very long responses

**Bot responds to its own messages:**
- This is automatically prevented by the AI message tracking system
- If it happens, check for configuration conflicts

### Testing Your Setup

Run the comprehensive test suite:
```bash
python test_twitch_bot.py
```

This will verify all aspects of the integration and provide detailed feedback on any issues.

---

## Integration Architecture

The Twitch integration works seamlessly with the main Z-WAIF application:

```
Twitch Chat → TwitchBot → main.main_twitch_chat() → AI System → Response → Twitch Chat
                   ↓
            User Context & Memory Systems
                   ↓
        Cross-Platform Relationship Tracking
```

### Key Components:

1. **utils/z_waif_twitch.py** - Main Twitch bot implementation
2. **main.main_twitch_chat()** - Integration bridge to main AI system
3. **Platform-aware messaging** - Adapts responses for Twitch context
4. **Enhanced AI modules** - Memory, relationships, and conversation analysis
5. **Thread-safe operation** - Runs independently without blocking main application

This ensures your AI companion maintains the same personality and memory across all platforms while adapting appropriately for each context.

---

## Support

If you encounter any issues:

1. Run `python test_twitch_bot.py` for detailed diagnostics
2. Check the console output for error messages
3. Verify your `.env` configuration matches this guide
4. Ensure all dependencies are installed: `pip install -r requirements.txt`

Your Twitch integration is now ready to provide seamless, intelligent conversation with your viewers while maintaining the full personality and capabilities of your Z-WAIF companion! 