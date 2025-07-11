# Discord Bot Detection Guide

## Overview

The Discord module now includes comprehensive bot detection to prevent infinite loops when multiple AI bots are in the same channel. This system automatically identifies and ignores messages from other bots and AI assistants.

## How It Works

The bot detection system uses multiple methods to identify bot messages:

### 1. Username Detection
- Checks for bot-related keywords in usernames and display names
- Common patterns: `bot`, `ai`, `assistant`, `gpt`, `claude`, `waifu`, etc.

### 2. Content Analysis
- Identifies formal AI language patterns
- Detects training data references
- Recognizes programming/function descriptions

### 3. Message Pattern Recognition
- Assistant prefixes: `Assistant: `, `Bot: `, etc.
- Action text: `*nods*`, `*smiles*`, etc.
- Bracket notation: `[System]`, `[Bot]`, etc.
- Tag notation: `<bot>`, `<ai>`, etc.

### 4. Behavioral Analysis
- Checks for repetitive words
- Identifies unusually short or long messages
- Detects message patterns common in bot loops

## Configuration

The bot detection system is configured through `Configurables/DiscordBotDetection.json`:

```json
{
  "bot_detection_enabled": true,
  "bot_flags": ["bot", "ai", "assistant", "gpt", "claude"],
  "ai_indicators": ["as an ai", "my training", "i am programmed"],
  "bot_names": ["ChatGPT", "Claude", "Bard"],
  "ignored_users": ["FriendBot", "MyOtherBot"],
  "ignored_channels": ["bot-testing", "ai-chat"],
  "detection_settings": {
    "check_username": true,
    "check_message_content": true,
    "check_message_patterns": true,
    "check_message_length": true,
    "check_repetitive_words": true,
    "min_message_length": 3,
    "max_message_length": 2000,
    "max_word_repetition": 3,
    "max_words_for_repetition_check": 20
  }
}
```

## Customization Options

### Adding Custom Bot Names
Add specific bot usernames to the `ignored_users` list:
```json
"ignored_users": ["MyCustomBot", "AnotherAI", "TestBot"]
```

### Adding Custom Channels
Add channels where you want to ignore all messages:
```json
"ignored_channels": ["bot-testing", "ai-experiments", "debug-channel"]
```

### Adjusting Detection Sensitivity
Modify the detection settings to fine-tune the system:
```json
"detection_settings": {
  "min_message_length": 5,        // Minimum message length to consider
  "max_message_length": 1500,     // Maximum message length to consider
  "max_word_repetition": 4,       // How many times a word can repeat
  "max_words_for_repetition_check": 25  // Word count for repetition analysis
}
```

### Disabling Specific Checks
Turn off specific detection methods if needed:
```json
"detection_settings": {
  "check_username": true,         // Check usernames for bot indicators
  "check_message_content": false, // Don't check message content
  "check_message_patterns": true, // Check for bot response patterns
  "check_message_length": true,   // Check message length
  "check_repetitive_words": false // Don't check for repetitive words
}
```

## Testing the System

Run the test suite to verify bot detection is working:

```bash
python test_discord_bot_detection.py
```

This will test various scenarios and show you how the detection system works.

## Troubleshooting

### Bot Detection Too Aggressive
If the system is blocking legitimate messages:
1. Add the user to `ignored_users` list
2. Disable specific detection checks in `detection_settings`
3. Adjust sensitivity parameters

### Bot Detection Not Working
If bots are still getting through:
1. Add their usernames to `bot_flags` or `bot_names`
2. Add specific AI language patterns to `ai_indicators`
3. Enable all detection checks in `detection_settings`

### False Positives
If human messages are being blocked:
1. Check the console logs for detection reasons
2. Add the user to `ignored_users` if needed
3. Adjust detection sensitivity settings

## Logging

The system logs all bot detection events to the console:
```
[DISCORD] Detected bot by username: ChatGPT_Bot (contains 'gpt')
[DISCORD] Detected AI message by content: 'as an ai' in message
[DISCORD] Ignoring bot message from Assistant
```

## Best Practices

1. **Start with Default Settings**: The default configuration works well for most cases
2. **Monitor Logs**: Watch console output to see what's being detected
3. **Add Known Bots**: Add specific bot usernames to `ignored_users`
4. **Test Thoroughly**: Use the test suite to verify your configuration
5. **Adjust Gradually**: Make small changes and test before making more

## Example Configurations

### Strict Detection (Blocks Most Bots)
```json
{
  "bot_detection_enabled": true,
  "detection_settings": {
    "check_username": true,
    "check_message_content": true,
    "check_message_patterns": true,
    "check_message_length": true,
    "check_repetitive_words": true,
    "min_message_length": 5,
    "max_message_length": 1500,
    "max_word_repetition": 2,
    "max_words_for_repetition_check": 15
  }
}
```

### Relaxed Detection (Allows More Messages)
```json
{
  "bot_detection_enabled": true,
  "detection_settings": {
    "check_username": true,
    "check_message_content": false,
    "check_message_patterns": true,
    "check_message_length": false,
    "check_repetitive_words": false,
    "min_message_length": 1,
    "max_message_length": 3000,
    "max_word_repetition": 5,
    "max_words_for_repetition_check": 30
  }
}
```

## Support

If you encounter issues with the bot detection system:
1. Check the console logs for error messages
2. Run the test suite to verify functionality
3. Review your configuration settings
4. Check the Discord module logs for detection events 