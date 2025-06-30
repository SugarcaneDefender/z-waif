import asyncio
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
import logging
import time
from API.oobaooga_api import api_standard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Mock TwitchIO classes
@dataclass
class MockAuthor:
    name: str
    id: int

@dataclass
class MockChannel:
    name: str
    _last_message: Optional[str] = None

    async def send(self, message: str):
        print(f"\n[Channel {self.name}] Bot Response: {message}")
        self._last_message = message

@dataclass
class MockMessage:
    content: str
    author: MockAuthor
    channel: MockChannel

# Import actual bot code
from utils.z_waif_twitch import TwitchBot
from utils.zw_logging import log_info, log_error
import API.api_controller as api_controller

async def simulate_message(bot: TwitchBot, username: str, user_id: int, message: str):
    """Simulate receiving a Twitch message"""
    print(f"\n=== Simulating message from {username} ===")
    print(f"Message: {message}")
    
    # Create mock message object
    mock_channel = MockChannel("test_channel")
    mock_author = MockAuthor(username, user_id)
    mock_message = MockMessage(message, mock_author, mock_channel)
    
    # Process the message
    try:
        await bot._process_chat_message(mock_message)
        if mock_channel._last_message:
            print("\nTest Result: SUCCESS - Bot responded")
            print(f"Response: {mock_channel._last_message}")
        else:
            print("\nTest Result: FAILURE - No response received")
    except Exception as e:
        print(f"\nTest Result: ERROR - {str(e)}")
        import traceback
        print(traceback.format_exc())

class MockTwitchUser:
    def __init__(self, username):
        self.name = username
        self.display_name = username

class MockTwitchMessage:
    def __init__(self, content, user):
        self.content = content
        self.author = user

def test_bot_response(message_content, username="test_user1"):
    """Test the bot's response to a message"""
    user = MockTwitchUser(username)
    message = MockTwitchMessage(message_content, user)
    
    # Create API request
    request = {
        "prompt": message_content,
        "user_id": username,
        "platform": "twitch",
        "max_tokens": 300
    }
    
    try:
        # Send request to API
        logger.info(f"Sending message from {username}: {message_content}")
        response = api_standard(request)
        
        if response.startswith("Error:"):
            logger.error(f"API Error: {response}")
            return False
            
        logger.info(f"Bot response: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        return False

def run_tests():
    print("\nStarting test script...")
    print("=== Starting Z-WAIF Twitch Bot Tests ===\n")
    
    test_cases = [
        ("Basic greeting", "hi there!", "test_user1"),
        ("Casual conversation", "how are you doing today?", "test_user2"),
        ("Technical question", "can you help me with a coding problem?", "test_user1"),
        ("Emotional message", "I'm feeling happy today! 😊", "test_user3")
    ]
    
    success_count = 0
    
    for test_name, message, username in test_cases:
        print(f"\n=== Test Case: {test_name} ===\n")
        print(f"=== Simulating message from {username} ===")
        print(f"Message: {message}")
        
        # Add delay between requests
        if success_count > 0:
            time.sleep(2)  # 2 second delay between requests
            
        if test_bot_response(message, username):
            success_count += 1
            print("\nTest Result: SUCCESS")
        else:
            print("\nTest Result: FAILURE")
    
    print(f"\n=== Test Results Summary ===")
    print(f"Successful tests: {success_count}/{len(test_cases)}")
    print("=== Test script completed ===\n")

if __name__ == "__main__":
    run_tests() 