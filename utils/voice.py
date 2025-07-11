import os
# Moved to os-specific files
if os.name == 'nt':
    from .windows.voice import speak_line, check_if_speaking, speak_line_rvc, set_speaking, force_cut_voice
else: # TODO: linux
    from .mac.voice import speak_line, check_if_speaking, set_speaking, force_cut_voice

# Global variables for voice state management
is_speaking = False
cut_voice = False

# Wrapper function to handle RVC vs regular TTS
def speak(text, use_rvc=False, refuse_pause=False):
    """
    Main speak function that handles both RVC and regular TTS
    """
    if os.name == 'nt' and use_rvc:
        try:
            from .windows.voice import speak_line_rvc
            speak_line_rvc(text, refuse_pause)
        except ImportError:
            # Fallback to regular TTS if RVC not available
            speak_line(text, refuse_pause)
    else:
        speak_line(text, refuse_pause)

# Keep the original functions for backward compatibility
def set_speaking(set_val):
    global is_speaking
    is_speaking = set_val

def force_cut_voice():
    global cut_voice
    cut_voice = True

def process_voice_input(text):
    """Process voice input with proper platform context"""
    if not text or not text.strip():
        print("[VOICE] Received empty text input")
        return None
        
    try:
        # Format message with platform context
        platform_message = f"[Platform: Voice Chat] {text}"
        
        # Send through main system with platform context
        import main
        clean_reply = main.send_platform_aware_message(platform_message, platform="voice")
        
        if clean_reply and clean_reply.strip():
            # Log the interaction to chat history
            try:
                from utils.chat_history import add_message_to_history
                add_message_to_history("voice_user", "user", text, "voice")
                add_message_to_history("voice_user", "assistant", clean_reply, "voice")
            except Exception as e:
                print(f"[VOICE] Could not log to chat history: {e}")
            
            return clean_reply
            
    except Exception as e:
        print(f"[VOICE] Error processing voice input: {e}")
        return "Sorry, I'm having trouble processing voice input right now."
        
    return None
