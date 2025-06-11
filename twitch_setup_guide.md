# Twitch Bot Setup Guide

## 1. Getting Twitch Credentials

### Step 1: Create a Twitch Application
1. Go to [Twitch Developer Console](https://dev.twitch.tv/console/apps)
2. Click "Create App" (or "Register Your Application")
3. Fill in the form:
   - **Name**: "Z-WAIF Bot" (or your preferred name)
   - **OAuth Redirect URLs**: `http://localhost:17563`
   - **Category**: "Chat Bot"
   - **Client Type**: "Confidential"
4. Click "Create"

### Step 2: Get Your Credentials
1. After creating the app, you'll see your **Client ID** - copy this
2. Click "New Secret" to generate a **Client Secret** - copy this
3. The **Client Secret** becomes your `TWITCH_TOKEN`

### Step 3: Get OAuth Token (Alternative Method)
If you need an OAuth token instead of Client Secret:
1. Go to [Twitch Token Generator](https://twitchtokengenerator.com/)
2. Select "Bot Chat Token"
3. Connect with your Twitch account
4. Copy the generated token

## 2. Configure Your .env File

Add these lines to your `.env` file:

```env
# Change this line to enable Twitch
MODULE_TWITCH = ON

# Twitch Bot Configuration
TWITCH_TOKEN = your_client_secret_or_oauth_token_here
TWITCH_CLIENT_ID = your_client_id_here
TWITCH_CHANNEL = your_twitch_username_here

# Twitch Bot Behavior Settings
TWITCH_PERSONALITY = friendly
TWITCH_AUTO_RESPOND = ON
TWITCH_RESPONSE_CHANCE = 0.8
TWITCH_COOLDOWN_SECONDS = 3
TWITCH_MAX_MESSAGE_LENGTH = 450
```

## 3. Configuration Options

### Personalities Available:
- `friendly` - Warm and welcoming responses
- `enthusiastic` - High energy and excited responses  
- `sarcastic` - Witty and slightly sarcastic responses
- `supportive` - Encouraging and helpful responses
- `casual` - Relaxed and informal responses
- `playful` - Fun and playful responses

### Settings Explanation:
- **MODULE_TWITCH**: `ON`/`OFF` - Enable/disable the entire Twitch module
- **TWITCH_AUTO_RESPOND**: `ON`/`OFF` - Whether to automatically respond to chat messages
- **TWITCH_RESPONSE_CHANCE**: `0.0`-`1.0` - Probability of responding to each message (0.8 = 80%)
- **TWITCH_COOLDOWN_SECONDS**: Number of seconds between AI responses
- **TWITCH_MAX_MESSAGE_LENGTH**: Maximum length for AI responses (Twitch limit is 500)

## 4. Bot Commands

Once running, your bot will respond to these commands:

- `!stats` - Show user's relationship level and interaction count
- `!personality` - Show current bot personality
- `!help` - Show available commands
- `!joke` - Tell a random joke
- `!quote` - Share an inspirational quote
- `!flip` - Flip a coin
- `!dice` - Roll a dice
- `!8ball [question]` - Magic 8-ball responses
- `!time` - Show current time
- `!uptime` - Show bot uptime

## 5. Features

### Relationship Tracking
The bot tracks relationships with users:
- **Stranger** (0-4 interactions)
- **Acquaintance** (5-19 interactions) 
- **Friend** (20-49 interactions)
- **Close Friend** (50-99 interactions)
- **VIP** (100+ interactions)

### Memory System
- Contextual memory using AI embeddings
- Remembers past conversations
- Provides relevant responses based on conversation history

### Safety Features
- Twitch TOS compliance filtering
- Message length limits
- Cooldown systems
- Self-response loop prevention

## 6. Troubleshooting

### Common Issues:

**Bot not connecting:**
- Check your TWITCH_TOKEN and TWITCH_CLIENT_ID are correct
- Ensure TWITCH_CHANNEL is your exact Twitch username (lowercase)
- Verify MODULE_TWITCH is set to "ON"

**Bot not responding:**
- Check TWITCH_AUTO_RESPOND is "ON"
- Verify TWITCH_RESPONSE_CHANCE is above 0.0
- Check if cooldown period has passed

**Token errors:**
- Regenerate your Client Secret in Twitch Developer Console
- Make sure you're using the Client Secret, not Client ID as the token
- For OAuth tokens, ensure they have proper chat permissions

### Debug Steps:
1. Check the console output for error messages
2. Verify all environment variables are set correctly
3. Test with a simple message in your Twitch chat
4. Check the log files for detailed error information

## 7. Advanced Configuration

You can modify the behavior in `utils/settings.py`:

```python
# Twitch-specific settings
twitch_personality = "friendly"
twitch_auto_respond = True
twitch_response_chance = 0.8
twitch_cooldown_seconds = 3
twitch_max_message_length = 450
```

## 8. Running the Bot

1. Set up your `.env` file with the correct credentials
2. Run your Z-WAIF application as normal
3. The Twitch bot will automatically start if `MODULE_TWITCH = ON`
4. Check the console for "Twitch bot connected" message
5. Test by sending a message in your Twitch chat

Your AI waifu is now ready to interact with your Twitch community! 