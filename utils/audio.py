import time
import threading

import pyaudio
import wave

from pydub import AudioSegment
from utils import hotkeys
import os, audioop

import sounddevice as sd

from utils import volume_listener
from utils import transcriber_translate
from utils import settings
from utils import voice

from silero_vad import load_silero_vad, read_audio, get_speech_timestamps

CHUNK = 1024
CHUNKY_TRANSCRIPTION_RATE = os.environ.get("WHISPER_CHUNKY_RATE", "1000")
MAX_CHUNKS = int(os.environ.get("WHISPER_CHUNKS_MAX", "10"))

FORMAT = pyaudio.paInt16

CHANNELS = 1

RATE = 44100

current_directory = os.path.dirname(os.path.abspath(__file__))
FILENAME = "voice.wav"
SAVE_PATH = os.path.join(current_directory, "resource", "voice_in", FILENAME)
SAVE_PATH_ORDUS = os.path.join(current_directory, "resource", "voice_in", "interrupt_voice.wav")
SAVE_PATH_VAD = os.path.join(current_directory, "resource", "voice_in", "vad_voice.wav")

# Thread-safe global variables with locks
chat_buffer_frames = []
_chat_buffer_lock = threading.Lock()

latest_chat_frame_count = 0
_frame_count_lock = threading.Lock()

vad_voice_detected = False
_vad_lock = threading.Lock()

# Thread-safe accessor functions
def get_chat_buffer_frames():
    """Thread-safe getter for chat buffer frames"""
    with _chat_buffer_lock:
        return chat_buffer_frames.copy()

def set_chat_buffer_frames(frames):
    """Thread-safe setter for chat buffer frames"""
    with _chat_buffer_lock:
        global chat_buffer_frames
        chat_buffer_frames = frames

def append_chat_buffer_frame(frame):
    """Thread-safe append to chat buffer frames"""
    with _chat_buffer_lock:
        global chat_buffer_frames
        chat_buffer_frames.append(frame)
        # Clearing anything over the buffer
        if len(chat_buffer_frames) > 91:
            chat_buffer_frames.pop(0)

def clear_chat_buffer_frames():
    """Thread-safe clear of chat buffer frames"""
    with _chat_buffer_lock:
        global chat_buffer_frames
        chat_buffer_frames = []

def get_latest_chat_frame_count():
    """Thread-safe getter for latest chat frame count"""
    with _frame_count_lock:
        return latest_chat_frame_count

def set_latest_chat_frame_count(count):
    """Thread-safe setter for latest chat frame count"""
    with _frame_count_lock:
        global latest_chat_frame_count
        latest_chat_frame_count = count

def get_vad_voice_detected():
    """Thread-safe getter for VAD voice detection"""
    with _vad_lock:
        return vad_voice_detected

def set_vad_voice_detected(detected):
    """Thread-safe setter for VAD voice detection"""
    with _vad_lock:
        global vad_voice_detected
        vad_voice_detected = detected

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
    if transcriber_translate.CHUNKY_TRANSCRIPTION == "ON":
        return record_chunky()

    #
    # Otherwise, record as ususal
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []

    # Check for if we want to add our audio buffer
    buffer_frames = get_chat_buffer_frames()
    if len(buffer_frames) > 1:
        frames = buffer_frames

    while hotkeys.get_speak_input():
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
    set_latest_chat_frame_count(len(frames))

    return SAVE_PATH

def record_ordus():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []

    # Check for if we want to add our audio buffer
    buffer_frames = get_chat_buffer_frames()
    if len(buffer_frames) > 1:
        frames = buffer_frames

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
    set_latest_chat_frame_count(len(frames))

    return SAVE_PATH_ORDUS


# For chunky audio recording/processing
def record_chunky():
    frames = []
    all_frames = []
    transcriber_translate.clear_transcription_chunks()    # Clear old chunks

    # Check for if we want to add our audio buffer
    buffer_frames = get_chat_buffer_frames()
    if len(buffer_frames) > 1:
        frames = buffer_frames

    # Initialize PyAudio once outside the loop for better resource management
    p = None
    stream = None
    
    try:
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        
        # Loop through until done recording, and limit it to X frames
        while hotkeys.get_speak_input() and (1 + len(transcriber_translate.transcription_chunks)) < MAX_CHUNKS:
            
            # Record audio chunk
            while len(frames) < int(CHUNKY_TRANSCRIPTION_RATE) and hotkeys.get_speak_input():
                try:
                    data = stream.read(CHUNK)
                    frames.append(data)
                    all_frames.append(data)
                except Exception as e:
                    print(f"Audio recording error in chunky mode: {e}")
                    break

            # Wait for another opening to transcribe, we are still transcribing the last chunk!
            # NOTE: If this happens to you, that is bad! It can't even keep up to realtime!
            while transcriber_translate.chunky_request != None:
                time.sleep(0.01)

            # Write the audio chunk to file
            wf = None
            try:
                wf = wave.open(SAVE_PATH, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            except Exception as e:
                print(f"Error writing audio chunk: {e}")
            finally:
                if wf is not None:
                    try:
                        wf.close()
                    except:
                        pass

            # Transcribe this chunk in another thread!
            transcriber_translate.give_chunky_request(SAVE_PATH)

            # Clear frames for next loop (keep latest one for quality)
            frames = [frames[-1]] if frames else []

    except Exception as e:
        print(f"Error in chunky recording: {e}")
    finally:
        # Always clean up audio resources
        if stream is not None:
            try:
                stream.stop_stream()
                stream.close()
            except:
                pass
        if p is not None:
            try:
                p.terminate()
            except:
                pass

    # Write out our frame count
    set_latest_chat_frame_count(len(all_frames))

    return "CHUNKY" # faker so we have something for the return


def autochat_audio_buffer_record():

    # Make sure we have an actual audio device, return otherwise
    if volume_listener.no_mic:
        return

    # Main recording buffer with proper resource management
    p = None
    stream = None
    
    try:
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

        while True:

            # If there is no autochat, or we are actively in the middle of a chat, clear it
            if hotkeys.get_autochat_toggle() == False:
                time.sleep(0.002)     # Rest here a bit, no need to hotloop it
                clear_chat_buffer_frames()


            # If there is autochat, and no active chat, record it
            elif hotkeys.get_autochat_toggle() == True:

                try:
                    # Record
                    data = stream.read(CHUNK)
                    append_chat_buffer_frame(data)
                except Exception as e:
                    print(f"Audio buffer recording error: {e}")
                    time.sleep(0.1)  # Brief pause on error
                    
    except Exception as e:
        print(f"Failed to initialize audio buffer recording: {e}")
    finally:
        # Clean up audio resources
        if stream is not None:
            try:
                stream.stop_stream()
                stream.close()
            except:
                pass
        if p is not None:
            try:
                p.terminate()
            except:
                pass

def record_vad_loop():
    time.sleep(7)   # 7 second rest to ensure there is time to boot up

    # Close out if we are to not use Silero VAD
    if settings.use_silero_vad == False:
        return

    #
    # Loop us
    while True:

        # Breaker here to sleep if our VAD/Autochat/Whatever is not running
        while hotkeys.get_autochat_toggle() == False or hotkeys.SPEAKING_TIMER_COOLDOWN > 0:
            set_vad_voice_detected(False)
            time.sleep(0.01)

        p = None
        stream = None
        wf = None
        
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            frames = []
            vad_loop_frames_limit = 32
            vad_loop_cur_frames = 0

            while vad_loop_cur_frames <= vad_loop_frames_limit:
                data = stream.read(CHUNK)
                frames.append(data)
                vad_loop_cur_frames += 1

            wf = wave.open(SAVE_PATH_VAD, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))

            time.sleep(0.01)    # Rest to write the file and do system I/O (also slight delay)

            # Now that we have written, look for voice activity!
            try:
                model = load_silero_vad()
                wav = read_audio(SAVE_PATH_VAD)
                speech_timestamps = get_speech_timestamps(
                    wav,
                    model,
                    return_seconds=True,  # Return speech timestamps in seconds (default is samples)
                )

                # If we have voice activity, flag it as valid
                if len(speech_timestamps) > 0:
                    set_vad_voice_detected(True)
                else:
                    set_vad_voice_detected(False)
            except Exception as e:
                print(f"VAD processing error: {e}")
                set_vad_voice_detected(False)

        except Exception as e:
            print(f"Audio recording error in VAD loop: {e}")
            set_vad_voice_detected(False)
        finally:
            # Always clean up resources
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass
            if p is not None:
                try:
                    p.terminate()
                except:
                    pass
            if wf is not None:
                try:
                    wf.close()
                except:
                    pass

