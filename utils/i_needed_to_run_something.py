#
# For running an individual script in .env, I'm using Pycharm so I can just hit play to test stuff
#

import os
from ollama import chat

# from pathlib import Path

# You can also pass in base64 encoded image data
# img = base64.b64encode(Path(path).read_bytes()).decode()
# or the raw bytes
# img = Path(path).read_bytes()

# Os Path how TF that works???

# img_str = str(os.path.abspath('..\LiveImage.png'))
# print(img_str)
#
# response = chat(
#   model='llava-phi3',
#   messages=[
#     {
#       "role": "system", "content": "Yor name is Maria!" + "\n\n",
#     },
#     {
#       'role': 'user',
#       'content': 'What is in this image? Be concise.',
#       'images': [img_str],
#     }
#   ],
# )
#
# print(response.message.content)


#
# import json
#
# low_temp = {"temperature": 1.17, "min_p": 0.0597, "top_p": 0.87, "top_k": 64, "repeat_penalty": 1.10, "repeat_last_n": 2048}
# mid_temp = {"temperature": 1.27, "min_p": 0.0497, "top_p": 0.87, "top_k": 79, "repeat_penalty": 1.12, "repeat_last_n": 2048}
# high_temp = {"temperature": 1.47, "min_p": 0.0397, "top_p": 0.97, "top_k": 119, "repeat_penalty": 1.19, "repeat_last_n": 2048}
#
#
# with open("OllamaModelConfigs.json", 'w') as outfile:
#   json.dump([low_temp, mid_temp, high_temp], outfile, indent=4)
#
# print("Dumped!")

# from pydub import AudioSegment
# from pydub.playback import play
#
# sound = AudioSegment.from_wav("BadToTheBone.wav")
# play(sound)
# print("Sound played!")

#
# import win32com.client
#
# speaker = win32com.client.Dispatch("SAPI.SpVoice")
# speaker.Speak("I am Maria! Rawr!")

# input_string = "/Soundboard/Fish/"
#
# input_string = input_string.replace("/Soundboard/", "/soundboard/")
# print(input_string)

# My guiding moonlight
# You were by my side the entire time

# Testing the no repeat voice rule (whisper patch) to make sure it actually works

# import utils.cane_lib
#
#
# stringy = utils.cane_lib.remove_repeats("Jex in minecraft Jex in minecraft Jex in minecraft Jex in minecraft Jex in minecraft Jex in minecraft Jex in minecraft Jex in minecraft ")
# # stringy = utils.cane_lib.super_remove_repeats("Alabama, Alabama, Alabama, Alabama, Alabama, Alabama, Alabama, Alabama, Alabama, Alabama, Alabama, Alabama, Alabama, Alabama, Alabama, Alabama, Alabama")
# # stringy = utils.cane_lib.super_remove_repeats(" blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah blah")
# # stringy = utils.cane_lib.super_remove_repeats("Darling, yeah. Oh yeah, my mom got me a Finch sock. Do you know what a Finch sock is? ")
# print(stringy)

# Silero VAD Time

# current_directory = os.path.dirname(os.path.abspath(__file__))
# FILENAME = "voice.wav"
# SAVE_PATH = os.path.join(current_directory, "resource", "voice_in", FILENAME)
#
# from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
#
# model = load_silero_vad()
# wav = read_audio(SAVE_PATH)
# speech_timestamps = get_speech_timestamps(
#   wav,
#   model,
#   return_seconds=True,  # Return speech timestamps in seconds (default is samples)
# )
# print(speech_timestamps)

# import utils.audio
#
# utils.audio.record_vad_loop()

#
# Testing new keyword speech checking
#

# import speech_recognition as sr
#
# r = sr.Recognizer()
#
# keyWord = 'joker'
#
# with sr.Microphone() as source:
#     print('Please start speaking..\n')
#     while True:
#
#         audio = r.listen(source)
#         #
#         # try:
#         #     text = r.
#         #     if keyWord.lower() in text.lower():
#         #         print('Keyword detected in the speech.')
#         # except Exception as e:
#         #     print('Please speak again.')
#
#         # recognize speech using whisper
#         try:
#             print("Whisper thinks you said " + r.recognize_whisper(audio, language="english"))
#         except sr.UnknownValueError:
#             print("Whisper could not understand audio")
#         except sr.RequestError as e:
#             print(f"Could not request results from Whisper; {e}")
