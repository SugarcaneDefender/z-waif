# z-waif
Fully local &amp; open source AI Waifu. VTube Studio, Discord, Minecraft, custom made RAG (long term memory), alarm, and plenty more! Has a WebUI and hotkey shortcuts. All software is free (or extremely cheap)!

Reccomended Windows 10/11 and a CUDA (NVidia) GPU with atleast 16GB+ of VRAM.
Can now support Mac and Linux! Thanks [@cootshk](https://github.com/cootshk)! Any brand (AMD, NVidia, Intel) GPU with 8GB+ VRAM bare mininum requirement.
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

## Diaspora
#### The Original:
[TumblerWarren/Virtual_Avatar_ChatBot](https://github.com/TumblerWarren/Virtual_Avatar_ChatBot), this is the original project that this code is spun-off of. Full credit to that project - it provided the skeleton for the many advancements now in place. It has more of a focus on non-local AI, if that is what you need.
#### Branches & Versions:
[Drakkadakka/z-waif-experimental-](https://github.com/Drakkadakka/z-waif-experimental-), offers a few upgrades; namely Twitch chat & streaming support, as well as a few other enhancements.

[MaolinkLife/z-waif-ru-adaptation](https://github.com/MaolinkLife/z-waif-ru-adaptation/tree/z-waif-ru-adaptation-dev), offers Russian language support, lighter-weight edge-tts, lorebook enhancements, ect.


## Recent Changelog

v1.9-R4

- Emergency patch for broken requirments.txt
	- Broke any new installs (the UI in particular) this past week
	- Still working on diagnosis - for now older requirements with "pip freeze" are being used
 	- Maybe for the best so that they stop changing automatically, sub-packages don't really need frequent updates.
  	- People who have already installed and are having issues should;
  		- Delete your old "venv" folder
  	 	- Paste in the new "requirements.txt" file
  	  	- Run "startup-install.bat"
 
---.---.---.---

v1.9-R3

- While using Ollama, all system messages are appeneded as if they are the "Character Card", meaning they are more condensed in memory. Includes:
	- Current Time
	- Lorebook Additions
	- Current Task
	- RAG Memory

- Can now define a different model for visual use while using Ollama.

- RP Suppression starts off by default now.
- Max Tokens default is now 300.

- RAG prefers slightly more focused / shorter messages when picking from different options.

- Re-added standard configs and random temps to Ollama.
- "TOKEN_LIMIT" (aka context length) also works in Ollama now, and is no longer stuck to 2048.
	- This makes it only somewhat faster while loading memory than Oobabooga, keep in mind.
- Non-streamed image API now replies as if they are the waifu and not a "visual assistant".
- Fixed errors being made due to the Oobabooga streaming image API going to the wrong port after the recent update.

---.---.---.---

v1.9-R2

- Fixed the .env file not being updated, crashing the whole program. GitHub likes to ignore that file and I forgot to check. Whoops!

---.---.---.---

v1.9

- Ollama Support!
	- Thanks to @cootshk and myself!
	- Properly functioning visual models!
	- No need to load models manually after booting - it happens automatically.
	- Memory is cached, meaning instant replies and ability to jack up the max memory w/o much penalty.
	- Less control at the moment - beware! Max Tokens, Stopping Strings, and other model control features are non-functional.
		- This is a priority to tinker with and fix.
		- Also due to models having their settings (temperature, rep_penalty, ect.) baked into themselves.
	- Tutorials will be out after I properly update it in a week or two.

- Images can be sent at different sizes using "IMG_SCALE" in the .env.
- API port for Oobabooga / other Open-AI typed endpoints can now be configured in the .env.
- Tasks can now be set in configurables, although there is no way for the AI to access them right now.

- Removed classic transcription being hardcoded to English only.
- Renamed "utils.logging" to "utils.zw_logging" so that it's not overlapping a base library.
- Renamed "API.Oogabooga_API_Support" to "API.api_controller", as it is the generic now.

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
