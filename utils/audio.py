import time

import pyaudio
import wave

from pydub import AudioSegment
import utils.hotkeys
import os, audioop

import sounddevice as sd

import utils.volume_listener
import utils.transcriber_translate

CHUNK = 1024
CHUNKY_TRANSCRIPTION_RATE = os.environ.get("WHISPER_CHUNKY_RATE")
MAX_CHUNKS = int(os.environ.get("WHISPER_CHUNKS_MAX"))

FORMAT = pyaudio.paInt16

CHANNELS = 1

RATE = 44100

current_directory = os.path.dirname(os.path.abspath(__file__))
FILENAME = "voice.wav"
SAVE_PATH = os.path.join(current_directory, "resource", "voice_in", FILENAME)
SAVE_PATH_ORDUS = os.path.join(current_directory, "resource", "voice_in", "interrupt_voice.wav")

chat_buffer_frames = []

latest_chat_frame_count = 0



def play_mp3(path, audio_level_callback=None):
    audio_file = AudioSegment.from_file(path, format="mp3")
    play_mp3_memory(audio_file, audio_level_callback)


# Plays an MP3 file from memory
def play_mp3_memory(audio_file, audio_level_callback=None):
    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open a stream to play the audio
    stream = p.open(format=pyaudio.paInt16,
                    channels=audio_file.channels,
                    rate=audio_file.frame_rate,
                    output=True)

    # Read the audio data in chunks and play it
    chunk_size = 1024
    data = audio_file.raw_data
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


def play_wav_memory(audio_file, audio_level_callback=None):
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
def play_wav(path, audio_level_callback=None):
    audio_file = wave.open(path)
    play_wav_memory(audio_file, audio_level_callback)


def record():
    # Breaker for if we are doing chunky transcription, go do that instead!
    if utils.transcriber_translate.CHUNKY_TRANSCRIPTION == "ON":
        return record_chunky()

    #
    # Otherwise, record as ususal
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

def record_ordus():
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


    wf = wave.open(SAVE_PATH_ORDUS, 'wb')

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


# For chunky audio recording/processing
def record_chunky():
    frames = []
    all_frames = []
    utils.transcriber_translate.clear_transcription_chunks()    # Clear old chunks

    # Check for if we want to add our audio buffer
    global chat_buffer_frames
    if len(chat_buffer_frames) > 1:
        frames = chat_buffer_frames.copy()

    # Loop through until done recording, and limit it to X frames
    while utils.hotkeys.get_speak_input() and (1 + len(utils.transcriber_translate.transcription_chunks)) < MAX_CHUNKS:
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

        while len(frames) < int(CHUNKY_TRANSCRIPTION_RATE) and utils.hotkeys.get_speak_input():
            data = stream.read(CHUNK)
            frames.append(data)
            all_frames.append(data)

        # Wait for another opening to transcribe, we are still transcribing the last chunk!
        # NOTE: If this happens to you, that is bad! It can't even keep up to realtime!
        while utils.transcriber_translate.chunky_request != None:
            time.sleep(0.01)

        stream.stop_stream()
        stream.close()

        p.terminate()

        wf = wave.open(SAVE_PATH, 'wb')

        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        # Transcribe this chunk in another thread!
        utils.transcriber_translate.give_chunky_request(SAVE_PATH)

        # Clear frames for next loop (keep latest one for quality)
        frames = [frames[-1]]



    # Write out our frame count
    global latest_chat_frame_count
    latest_chat_frame_count = len(all_frames)

    return "CHUNKY" # faker so we have something for the return


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


