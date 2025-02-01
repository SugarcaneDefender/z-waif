import time
from typing import Any, Callable

import pyaudio
import wave

from pydub import AudioSegment # type: ignore
import utils.hotkeys
import os, audioop

import sounddevice as sd # type: ignore

import utils.volume_listener

CHUNK = 1024

FORMAT = pyaudio.paInt16

CHANNELS = 1

RATE = 44100

current_directory = os.path.dirname(os.path.abspath(__file__))
FILENAME = "voice.wav"
SAVE_PATH = os.path.join(current_directory, "resource", "voice_in", FILENAME)
SAVE_PATH_ORDUS = os.path.join(current_directory, "resource", "voice_in", "interrupt_voice.wav")

chat_buffer_frames: list[bytes] = []

latest_chat_frame_count: int = 0



def play_mp3(path: str, audio_level_callback: Callable[..., Any]|None=None):
    audio_file: AudioSegment = AudioSegment.from_file(path, format="mp3") # type: ignore
    play_mp3_memory(audio_file, audio_level_callback) # type: ignore


# Plays an MP3 file from memory
def play_mp3_memory(audio_file: AudioSegment, audio_level_callback: Callable[...,Any]|None=None):
    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open a stream to play the audio
    stream = p.open(format=pyaudio.paInt16,
                    channels=audio_file.channels, # type: ignore
                    rate=audio_file.frame_rate, # type: ignore
                    output=True)

    # Read the audio data in chunks and play it
    chunk_size = 1024
    data: bytes = audio_file.raw_data # type: ignore
    while data:
        chunk = data[:chunk_size]
        stream.write(chunk)
        data = data[chunk_size:]
        if audio_level_callback is not None:
            volume = audioop.rms(chunk, 2)
            normalized_volume = (volume / 32767) * 100
            audio_level_callback(normalized_volume / 14)

    stream.stop_stream()
    stream.close()
    p.terminate()


def play_wav_memory(audio_file: wave.Wave_read, audio_level_callback: Callable[...,Any]|None=None):
    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open a stream to play the audio
    stream = p.open(format=p.get_format_from_width(audio_file.getsampwidth()),
                    channels=audio_file.getnchannels(),
                    rate=audio_file.getframerate(),
                    output=True)

    # Read the audio data in chunks and play it
    chunk_size = 1024
    data = audio_file.readframes(chunk_size)
    while data:
        stream.write(data)
        data = audio_file.readframes(chunk_size)
        if audio_level_callback is not None:
            volume = audioop.rms(data, 2)
            audio_level_callback(volume / 10000)

    stream.stop_stream()
    stream.close()
    p.terminate()


# Plays wav file
def play_wav(path: str, audio_level_callback: Callable[...,Any] | None=None):
    audio_file = wave.open(path)
    play_wav_memory(audio_file, audio_level_callback)


def record():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []

    # Check for if we want to add our audio buffer
    global chat_buffer_frames
    if len(chat_buffer_frames) > 1:
        frames = chat_buffer_frames.copy()

    while utils.hotkeys.get_speak_input():
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()

    p.terminate()


    wf = wave.open(SAVE_PATH, 'wb')

    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    # Test out playing the recorded audio (wav file)
    # play_wav(SAVE_PATH)

    # Write out our frame count
    global latest_chat_frame_count
    latest_chat_frame_count = len(frames)

    return SAVE_PATH

def record_for_streaming_snipper():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []

    # Check for if we want to add our audio buffer
    global chat_buffer_frames
    if len(chat_buffer_frames) > 1:
        frames = chat_buffer_frames.copy()

    while len(frames) < 150:
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()

    p.terminate()


    wf = wave.open(SAVE_PATH, 'wb')

    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    # Test out playing the recorded audio (wav file)
    # play_wav(SAVE_PATH)

    # Write out our frame count
    global latest_chat_frame_count
    latest_chat_frame_count = len(frames)

    return SAVE_PATH_ORDUS

def autochat_audio_buffer_record():

    # Make sure we have an actual audio device, return otherwise
    if utils.volume_listener.no_mic:
        return

    global chat_buffer_frames

    # Main recording buffer
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    while True:

        # If there is no autochat, or we are actively in the middle of a chat, clear it
        if utils.hotkeys.get_autochat_toggle() == False:
            time.sleep(0.002)     # Rest here a bit, no need to hotloop it
            chat_buffer_frames = []


        # If there is autochat, and no active chat, record it
        elif utils.hotkeys.get_autochat_toggle() == True:

            # Record
            data = stream.read(CHUNK)
            chat_buffer_frames.append(data)

            # Clearing anything over the buffer
            if len(chat_buffer_frames) > 74:
                chat_buffer_frames.pop(0)


