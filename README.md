# z-waif
Fully local &amp; open source AI Waifu. VTube Studio, Discord, Minecraft, custom made RAG (long term memory), alarm, and plenty more! Has a WebUI and hotkey shortcuts. All software is free (or extremely cheap)!

Requires Windows 10/11 and a CUDA (NVidia) GPU with atleast 12GB+ of video memory. 16GB is recommended.
Uses Oobabooga, RVC, and Whisper to run all AI systems locally. Works as a front end to tie many programs together into one cohesive whole.

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

If you need help / assistance, feel free to email me for this project at zwaif77@gmail.com

## Diaspora
#### The Original:
[TumblerWarren/Virtual_Avatar_ChatBot](https://github.com/TumblerWarren/Virtual_Avatar_ChatBot), this is the original project that this code is spun-off of. Full credit to that project - it provided the skeleton for the many advancements now in place.
#### Branches & Versions:
[Drakkadakka/z-waif-experimental-](https://github.com/Drakkadakka/z-waif-experimental-), offers a few upgrades; namely Twitch chat & streaming support, as well as a few other enhancements.


## Recent Changelog

V1.2

- Lorebook messages are now directly infused into the encoding as it is sent.
	- This now sends all relevant lore triggered within the past 3 message sets, instead of just 1 with a required cooldown.
	- Lore triggering requirements were improved, to add plurals and fix edgecases.
	- You can still view what lore is triggered via the UI Logs.
- Random Memories will now trigger before the alarm.
	- This allows your bot to randomly scan your chat history, and remember past times.
	- You can also trigger random memories manually via the UI.

- Your VTuber can now look around, either Following Faces or Randomly.
	- This requires setting up 6 emotes for your VTuber. In order, they should have your VTuber's eyes doing the following (they can be named anything); 
		- "Look Slight Right"
		- "Look Right"
		- "Look Very Right"
		- "Look Slight Left"
		- "Look Left"
		- "Look Very Left"
	- In the .env, change "EYES_FOLLOW" to "Random" or "Faces". Set the "EYES_START_ID" to whatever emote slot the "Look Slight Right" is set up as.
		- Make sure all the eye looking emotes follow eachother in order. You can re-order them in VTube Studio if needed.
	- Obviously, you need a camera for the VTuber to follow faces, as well as the Vision module enabled.

- Other Roleplay Suppression is now disabled if you have "Cutoff at Newlines" off.
	- This will allow the bot to send messages containing character lines, such as "User:" or "Riley:".
	- This is to allow lists, info, and multi-user RP scenarios, if you want.
- Fixed issues with the RAG history desyncing when undoing messages.


## To-Do

### 📶 Enhancements
- [ ] Make the RAG/Long Term Memory be multiprocessed for better performance
- [ ] Make the LLM input and TTS output streaming, to lower the "processing time"
- [ ] Figure out how to load LLAMA 3.2 Vision, for better multimodal, and no needed loader

### 🤖 Improvements
- [ ] Give internal dialoguing for chain of thought / reasoning
- [ ] Emotional / Tone understanding
- [ ] Automatic gaming & real world interaction
- [ ] Use an integrated voice generation system, with the ability to modify the tone
- [ ] Long term experience-based summarizations of ideas and history (pull form experience)

### 🦄 Imperium
- [ ] Create more Youtube tutorials and other related content
- [ ] Look more into optimal LLMs and configs
- [ ] Set up better Git and contribution methods
- [ ] Create a way for users to auto-update the program without having to hack files together
- [ ] Evangelize AI Waifus to the world!

## State of Development

The project could be considered in an "early access state". Some parts may be mildly buggy, janky, or obtuse. The project as a whole, however, is stable and reasonably effective.

The goal of the project is pretty simple; make AI partners that are not owned by not any corporation or government, but the people whoms't they are partnered with. The extents of this project are intended to stay within the bounds of giving a singular, locally hosted AI waifu, primarily for partnered use. The eventual end-game goal is to create partners for people who can have a robot body to interact with the world, and who can experience and learn things on their own terms; however lofty and unfeasible that goal may be. In short, symbiosis.
