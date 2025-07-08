# z-waif
Fully local &amp; open source AI Waifu. VTube Studio, Discord, Minecraft, custom made RAG (long term memory), alarm, and plenty more! Has a WebUI and hotkey shortcuts. All software is free (or extremely cheap)!

Reccomended Windows 10/11 and a CUDA (NVidia) GPU with atleast 16GB+ of VRAM.
Can now support Mac and Linux! Any brand (AMD, NVidia, Intel) GPU with 8GB+ VRAM bare mininum requirement!
Uses Oobabooga, RVC, and Whisper to run AI systems locally. Works as a front end to tie many programs together into one cohesive whole.

The goal of the project is less about giving an "all in one package", and moreso to give you the tools and knowledge for you to create your own AI Waifu!


|<img src="https://i.imgur.com/3a5eGQK.png" alt="drawing" width="400"/> | <img src="https://i.imgur.com/BCE1snE.png" alt="drawing" width="400"/> |
|:---:|:---:|
|<img src="https://i.imgur.com/paMSUiy.jpeg" alt="drawing" width="400"/> | <img src="https://i.imgur.com/vXx1vXm.jpeg" alt="drawing" width="400"/> |

## Features

- 🎙️ Quality Conversation &nbsp; &emsp; &emsp; ( /・0・)

	- Speak back and forth, using Whisper text to speech.
 	- Configure your own waifu's voice with thousands of possible models.
  	- Imperial-tons of quality of life tweaks.

- 🍄 Vtuber Integration &nbsp; &nbsp; &emsp; &emsp; ღゝ◡╹ )ノ♡

	- Uses VTube Studio, and any compatible models!
 	- Ability to send emotes to the model, based on their actions.
	- Idle / Speaking animation.
- 💾 Enhanced Memory &nbsp; &nbsp; &nbsp; &emsp; &emsp; (ー_ーゞ
	- Add Lorebook entries, for your waifu to remember a wide array of info as needed.
 	- Enable the custom RAG, giving your them knowledge of older conversations.
    	- Import old logs and conversations, keeping your same AI waifu from another software!
- 🎮 Modularity &emsp; &emsp; &emsp; &emsp; &emsp; &nbsp; &nbsp; ⌌⌈ ╹므╹⌉⌏
	- Enable various built in modules;
 		- Discord, for messaging.
		- Vision, to enable multimodal, and allow them to see!
   	 	- Alarm, so your waifu can wake you up in the morning.
     	 - Minecraft, allowing your waifu to control the game using Baritone, Wurst, and other command based mods.
	- All the options and modularity from any external software used. Oobabogoa, RVC Voice, ect.
	- Open-source, meaning you can edit it as you please.

## YouTube Showcase

[![IMAGE ALT TEXT](http://img.youtube.com/vi/XBZL500hloU/0.jpg)](https://www.youtube.com/watch?v=XBZL500hloU&list=PLH4bHuriW70RCl-2qHbSda8LHpuN8vvZZ&index=1 "Z-Waif Showcase")[![IMAGE ALT TEXT](http://img.youtube.com/vi/IGMregWfhGI/0.jpg)](https://www.youtube.com/watch?v=IGMregWfhGI&list=PLH4bHuriW70RCl-2qHbSda8LHpuN8vvZZ&index=2 "Z-Waif Install")

## Install & Links
Here is [some documentation](https://docs.google.com/document/d/1qzY09kcwfbZTaoJoQZDAWv282z88jeUCadivLnKDXCo/edit?usp=sharing) that you can look at. It will show you how to install, how to use the program, and what options you have. Please also take a look at the [Youtube videos for the install](https://www.youtube.com/playlist?list=PLH4bHuriW70RCl-2qHbSda8LHpuN8vvZZ).

If you need help / assistance, please submit a GitHub issue, or feel free to email me for this project at zwaif77@gmail.com

Z-Waif has [a basic website](https://zwaif.neocities.org/) that you can visit. I have also set up [a small Discord](https://discord.gg/XDWsAyVasH) for community members to chat as well.

### Running on Mac/Linux
Z-Waif supports both Mac and Linux using the ollama backend. You can clone the repo, then run the `./startup.sh` script. For more options, try `./startup.sh --help`. You need `glibc`, `portaudio`, `python3.11`, and `libglvnd` installed and on your PATH.

If you need support on Mac or Linux, ask around in the Discord. However you are expected to be able to solve basic problems (i.e. installing the right version of python) yourself.

For nix users, you can also use the nix flake to grab the os dependencies, then use the `startup.sh` script like usual.

## Diaspora
#### The Original:
[TumblerWarren/Virtual_Avatar_ChatBot](https://github.com/TumblerWarren/Virtual_Avatar_ChatBot), this is the original project that this code is spun-off of. Full credit to that project - it provided the skeleton for the many advancements now in place. It has more of a focus on non-local AI, if that is what you need.
#### Branches & Versions:
<!-- [Drakkadakka/z-waif-experimental-](https://github.com/Drakkadakka/z-waif-experimental-), offers a few upgrades; namely Twitch chat & streaming support, as well as a few other enhancements. -->

[MaolinkLife/z-waif-ru-adaptation](https://github.com/MaolinkLife/z-waif-ru-adaptation/tree/z-waif-ru-adaptation-dev), offers Russian language support, lighter-weight edge-tts, lorebook enhancements, ect.


## Recent Changelog

v1.14-R2

- Fixed the Web UI port back to using port 7864

- Enhanced Volume Listener System
	- Improved volume detection and audio processing for better autochat performance
	- Enhanced sensitivity controls and audio buffer management
	- Better handling of different audio input sources and microphone configurations
	- Reduced false triggers and improved response accuracy

- Improved Hotkey System
	- Enhanced hotkey binding and management for better user control
	- Improved keyboard input handling and response times
	- Better integration with gaming controls and VTuber emotes
	- Fixed hotkey conflicts and improved reliability

- Character Card System Update
	- IMPORTANT: Use the built-in character card system instead of Oobabooga character cards
	- The in-house character card system provides better integration and consistency
	- Oobabooga character cards may cause compatibility issues and reduced functionality
	- Configure character settings through the Configurables/CharacterCard.yaml file
	- Updated character card to be more personal and casual, avoiding formal language
	- Reduced aggressiveness of formal language detection to prevent false positives
	- Fixed issue where legitimate responses were being replaced with generic fallbacks

- Bug Fixes and Improvements
	- Fixed various audio processing issues
	- Improved system stability and performance
	- Enhanced error handling and user feedback

---.---.---.---

v1.14

- Complete Twitch Integration System
	- Full Twitch bot integration with main Z-WAIF application
	- Support for both single and multiple Twitch channels
	- Personal channel setup (simple OAuth token) and advanced bot application setup
	- Platform-aware messaging that adapts responses for Twitch chat context
	- Automatic removal of streaming-specific language for personal conversations
	- Enhanced user context and relationship tracking for Twitch users
	- Built-in safety filtering and spam prevention
	- Smart response control with configurable response chance and cooldowns
	- Comprehensive test suite (test_twitch_bot.py) for setup validation
	- Detailed setup guide (twitch_setup_guide.md) with troubleshooting

- Enhanced AI Handler System
	- New AIHandler class for centralized AI response management
	- Contextual chatpops that adapt based on platform and conversation context
	- Response caching system to improve performance and reduce API calls
	- Platform-specific response cleaning and formatting
	- Personality-based response generation with multiple personality types
	- Enhanced prompt formatting with relationship and context awareness

- Advanced User Relationship Management
	- New user_relationships.py module for tracking user relationships
	- Dynamic relationship progression system (stranger → acquaintance → friend → close_friend → vip)
	- Personality trait tracking and analysis
	- Relationship-based response customization
	- Automatic relationship level calculation based on interaction patterns
	- Support for positive/negative interaction tracking

- Comprehensive User Context System
	- New user_context.py module for storing user preferences and history
	- Interest tracking and topic analysis
	- User engagement level monitoring
	- Platform-specific user data management
	- Automatic user statistics and analytics
	- Cleanup system for inactive users

- Platform-Separated Chat History
	- New chat_history.py module for managing conversation history by platform
	- Separate conversation tracking for Twitch, Discord, Web UI, Voice, etc.
	- Automatic history cleanup and management
	- Conversation summary generation
	- Topic extraction from conversation history
	- Platform-specific statistics and analytics

- Enhanced Conversation Analysis
	- New conversation_analysis.py module for message analysis
	- Tone and sentiment analysis
	- Formality level detection
	- Context and topic extraction
	- Conversation style classification
	- Memory requirement detection

- Improved API Integration
	- Enhanced Oobabooga API with better error handling and retry logic
	- Persistent HTTP sessions with connection pooling
	- Improved request formatting and response processing
	- Better formal language detection and replacement
	- Enhanced platform context awareness in API calls
	- Fixed scope issues with regex imports

- Memory Management Improvements
	- New MemoryManager class for better memory organization
	- Enhanced RAG integration with user-specific memories
	- Better memory retrieval and relevance scoring
	- Improved memory cleanup and maintenance

- System Check and Testing
	- New system_check.py for comprehensive system validation
	- Enhanced feature testing for new AI capabilities
	- Better error detection and reporting
	- Integration testing for new modules

- Development Environment Improvements
	- Added Nix flake support for development environment
	- Enhanced startup scripts with better error handling
	- Automatic .env file creation from .env.example
	- Improved pip installation with retry logic
	- Better dependency management with requirements.txt consolidation
	- Enhanced logging and debugging capabilities

- Configuration Enhancements
	- New configuration files for user relationships and contexts
	- Enhanced chat history management
	- Better platform-specific settings
	- Improved configuration validation
	- Updated environment example with Twitch configuration options

- Bug Fixes and Improvements
	- Fixed regex import scope issues in API modules
	- Improved error handling throughout the system
	- Better logging and debugging capabilities
	- Enhanced performance with connection pooling
	- Fixed various memory leaks and resource management issues
	- Improved startup script reliability and error recovery


## To-Do

### 📶 Enhancements
- [ ] Make the RAG/Long Term Memory be multiprocessed for better performance
- [X] Make the LLM input and TTS output streaming, to lower the "processing time"
- [X] Figure out how to load LLAMA 3.2 Vision, for better multimodal, and no needed loader

### 🤖 Improvements
- [ ] Give internal dialoguing for chain of thought / reasoning
- [ ] Emotional / Tone understanding
- [ ] Automatic gaming & real world interaction
- [ ] Use an integrated voice generation system, with the ability to modify the tone
- [ ] Long term experience-based summarizations of ideas and history (pull form experience)

### 🦄 Imperium
- [X] Create more Youtube tutorials and other related content
- [ ] Look more into optimal LLMs and configs
- [ ] Set up better Git and contribution methods
- [ ] Create a way for users to auto-update the program without having to hack files together
- [ ] Evangelize AI Waifus to the world!

## State of Development

The project could be considered in an "early access state". Some parts may be mildly buggy, janky, or obtuse. The project as a whole, however, is stable and reasonably effective.

The goal of the project is pretty simple; make AI waifus. The extents of this project are intended to stay within the bounds of helping people create a singular, locally hosted AI waifu, who's partnership can benefit both you and them. In short, symbiosis.
