import random
import gradio
import gradio as gr
import API.api_controller
import colorama
import sys

# Ensure UTF-8 encoding for output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Define border character and line
BORDER_CHAR = "═"
BORDER_LINE = BORDER_CHAR * 79

# Ensure project root is in sys.path
import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"[Web-UI] Added project root {project_root} to sys.path")

from utils import zw_logging
from utils import settings
from utils import hotkeys
from utils import tag_task_controller
from utils import voice
# Import chat history with error handling
try:
    from utils import chat_history  # Initialize chat history module early
    CHAT_HISTORY_AVAILABLE = True
except ImportError as e:
    print(f"[Web-UI] Warning: chat_history module not available: {e}")
    CHAT_HISTORY_AVAILABLE = False
import json
# Import fallback API functions with error handling
try:
    from API.fallback_api import (
        discover_models, try_fallbacks, get_model_info, get_system_info, 
        check_model_compatibility, switch_fallback_model,
        get_available_vram_gb, estimate_model_vram_requirement
    )
    FALLBACK_API_AVAILABLE = True
except ImportError as e:
    print(f"[Web-UI] Warning: API.fallback_api not available: {e}")
    FALLBACK_API_AVAILABLE = False
    # Create dummy functions to prevent errors
    def discover_models(): return []
    def try_fallbacks(request): return {"error": "Fallback API not available"}
    def get_model_info(model_name): return {"error": "Fallback API not available"}
    def get_system_info(): return {"error": "Fallback API not available"}
    def check_model_compatibility(model_name): return False, "Fallback API not available", 0.0
    def switch_fallback_model(model_name): return False
    def get_available_vram_gb(): return 0.0
    def estimate_model_vram_requirement(model_name, quantization="fp16"): return 0.0

#from API.api_controller import soft_reset
#from settings import speak_only_spokento

# Import the gradio theme color
with open("Configurables/GradioThemeColor.json", 'r') as openfile:
    theme_data = json.load(openfile)
    # Handle both old string format and new object format
    if isinstance(theme_data, dict):
        gradio_theme_color = theme_data.get("theme", "emerald")
    else:
        gradio_theme_color = theme_data

based_theme = gr.themes.Base(
    primary_hue=gradio_theme_color,
    secondary_hue="indigo",
    neutral_hue="zinc",

)

# Button click handlers with proper error handling and return values
def shadowchats_button_click():
    try:
        settings.speak_shadowchats = not settings.speak_shadowchats
        print(f"[Web-UI] Shadow Chats toggled -> {settings.speak_shadowchats}")
        voice.force_cut_voice()  # Cut any ongoing speech
        return f"✅ Shadow chats {'enabled' if settings.speak_shadowchats else 'disabled'}"
    except Exception as e:
        print(f"[Web-UI] Error toggling shadow chats: {e}")
        return f"❌ Error: {e}"

def speaking_choice_button_click():
    try:
        settings.speak_only_spokento = not settings.speak_only_spokento
        print(f"[Web-UI] Speak-only-when-spoken-to toggled -> {settings.speak_only_spokento}")
        return f"✅ Speak-only-when-spoken-to {'enabled' if settings.speak_only_spokento else 'disabled'}"
    except Exception as e:
        print(f"[Web-UI] Error toggling speak-only-when-spoken-to: {e}")
        return f"❌ Error: {e}"

def supress_rp_button_click():
    try:
        settings.supress_rp = not settings.supress_rp
        print(f"[Web-UI] Suppress RP toggled -> {settings.supress_rp}")
        return f"✅ RP suppression {'enabled' if settings.supress_rp else 'disabled'}"
    except Exception as e:
        print(f"[Web-UI] Error toggling RP suppression: {e}")
        return f"❌ Error: {e}"

def newline_cut_button_click():
    try:
        settings.newline_cut = not settings.newline_cut
        print(f"[Web-UI] Newline cut toggled -> {settings.newline_cut}")
        return f"✅ Newline cut {'enabled' if settings.newline_cut else 'disabled'}"
    except Exception as e:
        print(f"[Web-UI] Error toggling newline cut: {e}")
        return f"❌ Error: {e}"

def asterisk_ban_button_click():
    try:
        settings.asterisk_ban = not settings.asterisk_ban
        print(f"[Web-UI] Asterisk ban toggled -> {settings.asterisk_ban}")
        return f"✅ Asterisk ban {'enabled' if settings.asterisk_ban else 'disabled'}"
    except Exception as e:
        print(f"[Web-UI] Error toggling asterisk ban: {e}")
        return f"❌ Error: {e}"

def hotkey_button_click():
    """Handle hotkey lock toggle from web UI with proper error handling"""
    try:
        settings.hotkeys_locked = not settings.hotkeys_locked
        
        # Update environment to persist the change
        settings.update_env_setting("HOTKEYS_BOOT", "ON" if not settings.hotkeys_locked else "OFF")
        
        print(f"[Web-UI] Hotkeys {'disabled' if settings.hotkeys_locked else 'enabled'}")
        return f"✅ Hotkeys {'disabled' if settings.hotkeys_locked else 'enabled'}"
    except Exception as e:
        print(f"[Web-UI] Error toggling hotkeys: {e}")
        return f"❌ Error: {e}"

def change_max_tokens(tokens_count):
    try:
        settings.max_tokens = int(tokens_count)
        print(f"[Web-UI] Max tokens set -> {settings.max_tokens}")
        return f"✅ Max tokens set to {settings.max_tokens}"
    except Exception as e:
        print(f"[Web-UI] Error changing max tokens: {e}")
        return f"❌ Error: {e}"

def alarm_button_click(input_time):
    try:
        settings.alarm_time = input_time
        print(f"[Web-UI] Alarm time set -> {settings.alarm_time}")
        print(f"\nAlarm time set as {settings.alarm_time}\n")
        return f"✅ Alarm set for {input_time}"
    except Exception as e:
        print(f"[Web-UI] Error setting alarm: {e}")
        return f"❌ Error: {e}"

def model_preset_button_click(input_text):
    try:
        settings.model_preset = input_text
        print(f"[Web-UI] Model preset set -> {settings.model_preset}")
        print(f"\nChanged model preset to {settings.model_preset}\n")
        return f"✅ Model preset set to {input_text}"
    except Exception as e:
        print(f"[Web-UI] Error setting model preset: {e}")
        return f"❌ Error: {e}"

# Add API fallback button handler with proper error handling
def api_fallback_button_click():
    try:
        settings.api_fallback_enabled = not settings.api_fallback_enabled
        print(f"[Web-UI] API Fallback toggled -> {settings.api_fallback_enabled}")
        return f"✅ API fallback {'enabled' if settings.api_fallback_enabled else 'disabled'}"
    except Exception as e:
        print(f"[Web-UI] Error toggling API fallback: {e}")
        return f"❌ Error: {e}"

def api_fallback_checkbox_change(checked):
    try:
        settings.api_fallback_enabled = checked
        settings.update_env_api_fallback(checked)
        print(f"[Web-UI] API Fallback set -> {checked}")
        return f"✅ API fallback {'enabled' if checked else 'disabled'}"
    except Exception as e:
        print(f"[Web-UI] Error setting API fallback: {e}")
        return f"❌ Error: {e}"

def api_fallback_model_change(value):
    try:
        settings.update_env_api_fallback_model(value)
        print(f"[Web-UI] API Fallback model set -> {value}")
        return f"✅ API fallback model set to {value}"
    except Exception as e:
        print(f"[Web-UI] Error setting API fallback model: {e}")
        return f"❌ Error: {e}"

def api_fallback_host_change(value):
    try:
        settings.update_env_api_fallback_host(value)
        print(f"[Web-UI] API Fallback host set -> {value}")
        return f"✅ API fallback host set to {value}"
    except Exception as e:
        print(f"[Web-UI] Error setting API fallback host: {e}")
        return f"❌ Error: {e}"

# TinyLlama GGUF Model Management with enhanced error handling
def load_tinyllama_gguf_preset():
    """Load the TinyLlama GGUF model as the active fallback."""
    if not FALLBACK_API_AVAILABLE:
        return "❌ Fallback API not available"
    
    try:
        from API.fallback_api import ensure_tinyllama_gguf_model, switch_fallback_model
        
        # Ensure model is available
        model_path = ensure_tinyllama_gguf_model()
        
        if model_path:
            # Switch to this model
            success = switch_fallback_model(model_path)
            if success:
                # Update environment
                settings.update_env_api_fallback_model(model_path)
                return f"✅ Successfully loaded TinyLlama GGUF model: {model_path}"
            else:
                return f"❌ Failed to switch to TinyLlama GGUF model"
        else:
            return "❌ TinyLlama GGUF model download failed"
            
    except ImportError as e:
        return f"❌ Import error: {e}. Make sure API.fallback_api is available."
    except Exception as e:
        return f"❌ Error loading TinyLlama GGUF: {e}"

def download_tinyllama_gguf():
    """Download TinyLlama GGUF model if not present."""
    if not FALLBACK_API_AVAILABLE:
        return "❌ Fallback API not available"
    
    try:
        from API.fallback_api import ensure_tinyllama_gguf_model
        from pathlib import Path
        
        model_path = ensure_tinyllama_gguf_model()
        
        if model_path and Path(model_path).exists():
            size_mb = round(Path(model_path).stat().st_size / (1024*1024), 1)
            return f"✅ TinyLlama GGUF available: {model_path} ({size_mb} MB)"
        else:
            return "❌ TinyLlama GGUF download failed. Check internet connection."
            
    except ImportError as e:
        return f"❌ Import error: {e}. Make sure API.fallback_api is available."
    except Exception as e:
        return f"❌ Download error: {e}"

def check_tinyllama_gguf_status():
    """Check the status of the TinyLlama GGUF model."""
    if not FALLBACK_API_AVAILABLE:
        return {"error": "Fallback API not available"}
    
    try:
        from pathlib import Path
        from API.fallback_api import get_model_info
        
        model_path = Path("models/tinyllama-1.1b-chat-v1.0.Q4_0.gguf")
        
        if model_path.exists():
            size_mb = round(model_path.stat().st_size / (1024*1024), 1)
            
            # Get model compatibility info
            model_info = get_model_info(str(model_path))
            
            status = {
                "available": True,
                "path": str(model_path),
                "size_mb": size_mb,
                "compatible": model_info.get("is_compatible", False),
                "vram_required_gb": model_info.get("vram_required_gb", 0.7),
                "compatibility_message": model_info.get("compatibility_message", ""),
                "currently_active": os.getenv("API_FALLBACK_MODEL", "") == str(model_path)
            }
        else:
            status = {
                "available": False,
                "path": str(model_path),
                "size_mb": 0,
                "compatible": False,
                "vram_required_gb": 0.7,
                "compatibility_message": "Model not downloaded",
                "currently_active": False
            }
        
        return status
        
    except ImportError as e:
        return {"error": f"Import error: {e}. Make sure API.fallback_api is available."}
    except Exception as e:
        return {"error": f"Status check failed: {e}"}

def test_tinyllama_gguf():
    """Test the TinyLlama GGUF model with a simple generation."""
    if not FALLBACK_API_AVAILABLE:
        return "❌ Fallback API not available"
    
    try:
        from API.fallback_api import switch_fallback_model, api_call
        from pathlib import Path
        model_path = "models/tinyllama-1.1b-chat-v1.0.Q4_0.gguf"
        if not Path(model_path).exists():
            return "❌ TinyLlama GGUF model not found. Please download first."
        # Switch to the model
        success = switch_fallback_model(model_path)
        if not success:
            return "❌ Failed to load TinyLlama GGUF model"
        # Test generation
        test_request = {
            "messages": [
                {"role": "user", "content": "Hello! Please respond with just 'Hi there!' and nothing else."}
            ],
            "max_tokens": 10,
            "temperature": 0.7
        }
        # Pass language if not auto-detect
        if not settings.AUTO_DETECT_LANGUAGE:
            test_request["language"] = settings.DEFAULT_LANGUAGE
        import time
        start_time = time.time()
        response = api_call(test_request)
        end_time = time.time()
        if isinstance(response, dict) and "choices" in response:
            content = response["choices"][0]["message"]["content"]
            generation_time = round(end_time - start_time, 2)
            return f"✅ Test successful! Response: '{content}' (Generated in {generation_time}s)"
        else:
            return f"❌ Test failed: {response.get('error', 'Unknown error')}"
    except ImportError as e:
        return f"❌ Import error: {e}. Make sure API.fallback_api is available."
    except Exception as e:
        return f"❌ Test error: {e}"

def get_fallback_presets():
    """Get list of available fallback model presets."""
    presets = {
        "TinyLlama GGUF (Local)": {
            "path": "models/tinyllama-1.1b-chat-v1.0.Q4_0.gguf",
            "description": "Ultra-efficient local GGUF model (~700MB, 1-2GB RAM)",
            "type": "local_gguf",
            "priority": 1
        },
        "TinyLlama (HuggingFace)": {
            "path": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "description": "HuggingFace version (requires internet)",
            "type": "huggingface",
            "priority": 2
        },
        "Microsoft Phi-2": {
            "path": "microsoft/phi-2",
            "description": "Small but powerful (~2.7GB VRAM)",
            "type": "huggingface",
            "priority": 3
        },
        "Mistral 7B Instruct": {
            "path": "TheBloke/Mistral-7B-Instruct-v0.1-GGUF",
            "description": "Larger but very capable (~5GB VRAM)",
            "type": "huggingface",
            "priority": 4
        }
    }
    return presets

def load_fallback_preset(preset_name):
    """Load a specific fallback model preset."""
    if not FALLBACK_API_AVAILABLE:
        return "❌ Fallback API not available"
    
    try:
        presets = get_fallback_presets()
        
        if preset_name not in presets:
            return f"❌ Unknown preset: {preset_name}"
        
        preset = presets[preset_name]
        model_path = preset["path"]
        
        # Special handling for TinyLlama GGUF
        if preset["type"] == "local_gguf":
            return load_tinyllama_gguf_preset()
        
        # For other models, just switch
        from API.fallback_api import switch_fallback_model
        success = switch_fallback_model(model_path)
        
        if success:
            settings.update_env_api_fallback_model(model_path)
            return f"✅ Successfully loaded preset: {preset_name}"
        else:
            return f"❌ Failed to load preset: {preset_name}"
            
    except Exception as e:
        return f"❌ Error loading preset: {e}"

def get_current_fallback_status():
    """Get comprehensive status of the current fallback system."""
    if not FALLBACK_API_AVAILABLE:
        return {"error": "Fallback API not available"}
    
    try:
        current_model = os.getenv("API_FALLBACK_MODEL", "")
        fallback_enabled = os.getenv("API_FALLBACK_ENABLED", "ON").upper() == "ON"
        
        # Check TinyLlama GGUF specifically
        tinyllama_status = check_tinyllama_gguf_status()
        
        # Get system info
        from API.fallback_api import get_system_info
        system_info = get_system_info()
        
        status = {
            "fallback_enabled": fallback_enabled,
            "current_model": current_model,
            "tinyllama_gguf": tinyllama_status,
            "system_ram_gb": system_info.get("memory_available_gb", 0),
            "gpu_available": system_info.get("gpu_available", False),
            "gpu_vram_gb": system_info.get("gpu_memory_total_gb", 0) if system_info.get("gpu_available") else 0,
            "recommended_preset": "TinyLlama GGUF (Local)" if tinyllama_status.get("available") else "TinyLlama (HuggingFace)"
        }
        
        return status
        
    except Exception as e:
        return {"error": f"Status check failed: {e}"}

def auto_configure_fallback():
    """Automatically configure the best fallback model based on system resources."""
    if not FALLBACK_API_AVAILABLE:
        return "❌ Fallback API not available"
    
    try:
        status = get_current_fallback_status()
        
        # Enable fallback if not already enabled
        if not status.get("fallback_enabled"):
            settings.update_env_api_fallback(True)
        
        # If TinyLlama GGUF is available and compatible, use it
        tinyllama_status = status.get("tinyllama_gguf", {})
        if tinyllama_status.get("available") and tinyllama_status.get("compatible"):
            result = load_tinyllama_gguf_preset()
            return f"🎯 Auto-configured: {result}"
        
        # Otherwise, try to download TinyLlama GGUF
        download_result = download_tinyllama_gguf()
        if "✅" in download_result:
            load_result = load_tinyllama_gguf_preset()
            return f"🎯 Auto-configured: Downloaded and loaded TinyLlama GGUF"
        
        # Fallback to HuggingFace version
        preset_result = load_fallback_preset("TinyLlama (HuggingFace)")
        return f"🎯 Auto-configured: {preset_result}"
        
    except Exception as e:
        return f"❌ Auto-configuration failed: {e}"

# Advanced fallback functions with enhanced error handling
def get_system_status():
    """Get current system status and resource information."""
    if not FALLBACK_API_AVAILABLE:
        return "❌ Fallback API not available"
    
    try:
        from API.fallback_api import get_system_info, get_available_vram_gb
        
        system_info = get_system_info()
        available_vram = get_available_vram_gb()
        
        status = {
            "platform": system_info.get("platform", "Unknown"),
            "gpu_available": system_info.get("gpu_available", False),
            "gpu_name": system_info.get("gpu_name", "None"),
            "vram_total_gb": system_info.get("gpu_memory_total_gb", 0),
            "vram_available_gb": available_vram,
            "memory_total_gb": system_info.get("memory_total_gb", 0),
            "memory_available_gb": system_info.get("memory_available_gb", 0),
            "cpu_count": system_info.get("cpu_count", 0),
        }
        
        return json.dumps(status, indent=2)
    except ImportError as e:
        return f"❌ Import error: {e}. Make sure API.fallback_api is available."
    except Exception as e:
        return f"❌ Error getting system status: {e}"

def discover_and_analyze_models():
    """Discover models and analyze their compatibility."""
    if not FALLBACK_API_AVAILABLE:
        return [{"error": "Fallback API not available"}]
    
    try:
        from API.fallback_api import discover_models, get_model_info
        
        models = discover_models()
        model_info_list = []
        
        for model in models:
            info = get_model_info(model)
            model_info_list.append(info)
        
        # Sort by compatibility (compatible first, then by VRAM requirement)
        model_info_list.sort(key=lambda x: (not x["is_compatible"], x["vram_required_gb"]))
        
        return model_info_list
    except ImportError as e:
        return [{"error": f"Import error: {e}. Make sure API.fallback_api is available."}]
    except Exception as e:
        return [{"error": f"Failed to discover models: {e}"}]

def test_model_compatibility(model_name):
    """Test if a specific model is compatible with the current system."""
    if not FALLBACK_API_AVAILABLE:
        return "❌ Fallback API not available"
    
    try:
        from API.fallback_api import check_model_compatibility, get_available_vram_gb
        
        is_compatible, message, vram_required = check_model_compatibility(model_name)
        available_vram = get_available_vram_gb()
        
        result = {
            "model": model_name,
            "compatible": is_compatible,
            "message": message,
            "vram_required_gb": vram_required,
            "vram_available_gb": available_vram,
            "margin_gb": available_vram - vram_required if is_compatible else 0
        }
        
        return json.dumps(result, indent=2)
    except ImportError as e:
        return f"❌ Import error: {e}. Make sure API.fallback_api is available."
    except Exception as e:
        return f"❌ Error testing compatibility: {e}"

def test_all_fallbacks_advanced():
    """Test all fallback models and return detailed results."""
    if not FALLBACK_API_AVAILABLE:
        return "❌ Fallback API not available"
    
    try:
        from API.fallback_api import discover_models, check_model_compatibility, switch_fallback_model, api_call
        
        models = discover_models()
        results = []
        
        for model in models:
            try:
                # Test compatibility
                is_compatible, message, vram_required = check_model_compatibility(model)
                
                # Try to switch to model (quick test)
                success = False
                error_msg = ""
                if is_compatible:
                    try:
                        success = switch_fallback_model(model)
                        if success:
                            # Quick generation test
                            test_request = {
                                "messages": [{"role": "user", "content": "Hello"}],
                                "max_tokens": 10,
                                "stream": False
                            }
                            response = api_call(test_request)
                            success = "choices" in response
                            error_msg = "" if success else "Generation failed"
                    except Exception as e:
                        success = False
                        error_msg = str(e)
                else:
                    error_msg = message
                
                results.append({
                    "model": model,
                    "compatible": is_compatible,
                    "test_success": success,
                    "vram_required_gb": vram_required,
                    "error": error_msg
                })
                
            except Exception as e:
                results.append({
                    "model": model,
                    "compatible": False,
                    "test_success": False,
                    "vram_required_gb": 0,
                    "error": str(e)
                })
        
        return json.dumps(results, indent=2)
    except ImportError as e:
        return f"❌ Import error: {e}. Make sure API.fallback_api is available."
    except Exception as e:
        return f"❌ Error testing fallbacks: {e}"

def update_fallback_order_advanced(model_list_json):
    """Update the fallback model order from the advanced interface."""
    try:
        if not model_list_json:
            return "❌ No models provided"
        
        model_list = json.loads(model_list_json)
        if not isinstance(model_list, list):
            return "❌ Invalid model list format"
        
        # Extract model names from the list
        model_names = []
        for item in model_list:
            if isinstance(item, dict) and "name" in item:
                model_names.append(item["name"])
            elif isinstance(item, str):
                model_names.append(item)
        
        if not model_names:
            return "❌ No valid model names found"
        
        # Update environment variable
        fallback_order_str = ",".join(model_names)
        os.environ["FALLBACK_MODEL_ORDER"] = fallback_order_str
        
        # Update .env file
        settings.update_env_setting("FALLBACK_MODEL_ORDER", fallback_order_str)
        
        return f"✅ Updated fallback order: {', '.join(model_names)}"
    except Exception as e:
        return f"❌ Error updating fallback order: {e}"

def add_custom_model_advanced(model_path, model_name=""):
    """Add a custom model to the fallback system."""
    if not FALLBACK_API_AVAILABLE:
        return "❌ Fallback API not available"
    
    try:
        if not model_path:
            return "❌ Please provide a model path"
        
        # Validate path
        if not os.path.exists(model_path):
            return f"❌ Model path does not exist: {model_path}"
        
        # Use provided name or extract from path
        if not model_name:
            model_name = os.path.basename(model_path)
        
        # Test compatibility
        from API.fallback_api import check_model_compatibility
        is_compatible, message, vram_required = check_model_compatibility(model_path)
        
        result = {
            "model_path": model_path,
            "model_name": model_name,
            "compatible": is_compatible,
            "message": message,
            "vram_required_gb": vram_required
        }
        
        return json.dumps(result, indent=2)
    except ImportError as e:
        return f"❌ Import error: {e}. Make sure API.fallback_api is available."
    except Exception as e:
        return f"❌ Error adding custom model: {e}"

def optimize_for_vram_advanced():
    """Automatically optimize model selection for available VRAM."""
    if not FALLBACK_API_AVAILABLE:
        return "❌ Fallback API not available"
    
    try:
        from API.fallback_api import get_available_vram_gb, discover_models, check_model_compatibility
        
        available_vram = get_available_vram_gb()
        models = discover_models()
        
        # Filter compatible models and sort by VRAM requirement
        compatible_models = []
        for model in models:
            is_compatible, _, vram_required = check_model_compatibility(model)
            if is_compatible:
                compatible_models.append((model, vram_required))
        
        if not compatible_models:
            return "❌ No compatible models found for your VRAM"
        
        # Sort by VRAM requirement (smallest first)
        compatible_models.sort(key=lambda x: x[1])
        
        # Create optimized order
        optimized_order = [model for model, _ in compatible_models]
        
        # Update environment
        fallback_order_str = ",".join(optimized_order)
        os.environ["FALLBACK_MODEL_ORDER"] = fallback_order_str
        settings.update_env_setting("FALLBACK_MODEL_ORDER", fallback_order_str)
        
        result = {
            "available_vram_gb": available_vram,
            "optimized_order": optimized_order,
            "model_details": [
                {"model": model, "vram_required_gb": vram}
                for model, vram in compatible_models
            ]
        }
        
        return json.dumps(result, indent=2)
    except ImportError as e:
        return f"❌ Import error: {e}. Make sure API.fallback_api is available."
    except Exception as e:
        return f"❌ Error optimizing for VRAM: {e}"

def update_settings(max_length, history_limit, auto_save):
    """Update chat settings from UI inputs with proper error handling"""
    try:
        import settings
        print(f"[Web-UI] Updating settings: Max Response Length={max_length}, History Limit={history_limit}, Auto Save={auto_save}")
        settings.MAX_RESPONSE_LENGTH = int(max_length)
        settings.HISTORY_LIMIT = int(history_limit)
        settings.AUTO_SAVE_INTERVAL = int(auto_save)
        print(f"[Web-UI] Settings updated successfully")
        return "✅ Settings updated successfully!"
    except ValueError as e:
        return f"❌ Invalid setting value: {e}"
    except Exception as e:
        return f"❌ Error updating settings: {e}"

def process_web_input(text, user_id="webui_user"):
    """Process web UI input with proper platform context"""
    if not text or not text.strip():
        print("[WEBUI] Received empty text input")
        return None
        
    try:
        # Format message with platform context
        platform_message = f"[Platform: Web Interface] {text}"
        
        # Send through main system with platform context
        try:
            import main
            clean_reply = main.send_platform_aware_message(platform_message, platform="webui")
        except ImportError as e:
            print(f"[WEBUI] Error importing main module: {e}")
            clean_reply = "Sorry, I'm having trouble processing your message right now."
        
        if clean_reply and clean_reply.strip():
            # Log the interaction to chat history
            try:
                from utils.chat_history import add_message_to_history
                add_message_to_history(user_id, "user", text, "webui")
                add_message_to_history(user_id, "assistant", clean_reply, "webui")
            except Exception as e:
                print(f"[WEBUI] Could not log to chat history: {e}")
            
            return clean_reply
            
    except Exception as e:
        print(f"[WEBUI] Error processing web input: {e}")
        return "Sorry, I'm having trouble processing your message right now."
        
    return None

def update_chat():
    """Update the chat display with stable, reliable loading"""
    try:
        # Get chat history from both sources
        from utils.chat_history import get_chat_history_for_webui
        chat_pairs = get_chat_history_for_webui("webui_user", "webui")
        
        # If no history from new system, try loading from API controller
        if not chat_pairs:
            try:
                from API.api_controller import ooga_history
                if ooga_history and len(ooga_history) > 0:
                    # Convert API history format to chat pairs
                    chat_pairs = [(msg[0], msg[1]) for msg in ooga_history if len(msg) >= 2]
            except ImportError as e:
                print(f"[Web-UI] Error importing API controller for history: {e}")
                chat_pairs = []
        
        # Return empty list if still no history
        if not chat_pairs:
            return []
        
        # Return the chat pairs
        return chat_pairs
        
    except ImportError as e:
        print(f"[Web-UI] Chat history module not available: {str(e)}")
        return []
    except Exception as e:
        print(f"[Web-UI] Error updating chat: {str(e)}")
        zw_logging.log_error(f"Error updating chat: {str(e)}")
        return []

def clear_history():
    """Clear both chat display and history"""
    try:
        # Clear the chat history file
        from utils.chat_history import clear_all_histories
        clear_all_histories()
        print("[WEBUI] Chat history cleared")
        
        # Clear API history
        try:
            from API.api_controller import soft_reset
            soft_reset()
        except ImportError as e:
            print(f"[WEBUI] Error importing API controller for clear history: {e}")
        
        return []
    except Exception as e:
        print(f"[WEBUI] Error clearing chat history: {e}")
        return []

with gr.Blocks(theme=based_theme, title="Z-Waif UI") as demo:

    #
    # CHAT
    #

    with gr.Tab("Chat"):

        #
        # Main Chatbox
        #

        chatbot = gr.Chatbot(height=540)

        with gr.Row():
            msg = gr.Textbox(scale=3)

            def respond(message, chat_history):
                """Handle chat responses in the web UI"""
                try:
                    # Format user message with platform context
                    platform_message = f"[Platform: Web Interface - Personal Chat] {message}"
                    
                    # Print user message with formatting
                    print(f"\n{BORDER_LINE}")
                    print("                                    Me")
                    print(f"{BORDER_LINE}\n")
                    print(f"{message.strip()}")
                    print("\n")

                    # Get platform-aware response
                    try:
                        from API.api_controller import run
                        response = run(platform_message, settings.temp_level)
                    except ImportError as e:
                        print(f"[WEBUI] Error importing API controller: {e}")
                        response = "Sorry, I'm having trouble connecting to the AI backend right now."
                    
                    if response and response.strip():
                        # Get character name for banner
                        try:
                            from API.character_card import get_character_name
                            banner_name = get_character_name() or 'Assistant'
                        except ImportError:
                            banner_name = 'Assistant'
                        
                        # Clean response for display
                        clean_response = response
                        if settings.char_name and clean_response.startswith(f"{settings.char_name}:"):
                            clean_response = clean_response[len(settings.char_name)+1:].strip()
                        elif clean_response.startswith("Assistant:"):
                            clean_response = clean_response[10:].strip()
                        
                        # Print the response with formatting
                        print(f"\n{BORDER_LINE}")
                        print(f"                                 {banner_name}")
                        print(f"{BORDER_LINE}\n")
                        print(clean_response.strip())
                        print("\n")
                        
                        # Handle TTS speaking if enabled
                        if (settings.speak_shadowchats or not settings.stream_chats) and not settings.live_pipe_no_speak:
                            try:
                                from utils.voice import speak
                                # Strip emojis for clearer TTS
                                try:
                                    import emoji
                                    s_message = emoji.replace_emoji(clean_response, replace="")
                                except ImportError:
                                    # Fallback if emoji module not available
                                    s_message = clean_response
                                
                                if s_message.strip():
                                    speak(s_message)
                            except Exception as e:
                                print(f"[WEBUI] Error speaking response: {e}")
                        
                        # Log to chat history
                        try:
                            from utils.chat_history import add_message_to_history
                            add_message_to_history("webui_user", "user", message, "webui", {
                                "platform": "webui",
                                "username": "webui_user"
                            })
                            add_message_to_history("webui_user", "assistant", clean_response, "webui")
                        except Exception as e:
                            print(f"[WEBUI] Could not log to chat history: {e}")
                        
                        # Update chat display
                        chat_history = list(chat_history)  # Create a new list
                        chat_history.append((message, clean_response))  # Add new message pair
                        
                        return "", chat_history  # Clear input, update chat
                    else:
                        print("[WEBUI] Warning: Received empty response from API")
                        return message, chat_history  # Keep message if no response
                except Exception as e:
                    print(f"[WEBUI] Error in respond: {e}")
                    import traceback
                    traceback.print_exc()
                    return message, chat_history

            msg.submit(respond, [msg, chatbot], [msg, chatbot])

            send_button = gr.Button(variant="primary", value="Send")
            send_button.click(respond, inputs=[msg, chatbot], outputs=[msg, chatbot])

        # Update chat display periodically
        demo.load(update_chat, every=2.0, outputs=[chatbot])

        #
        # Basic Mic Chat
        #

        def recording_button_click():

            hotkeys.speak_input_toggle_from_ui()

            return


        with gradio.Row():

            recording_button = gr.Button(value="Mic (Toggle)")
            recording_button.click(fn=recording_button_click)

            recording_checkbox_view = gr.Checkbox(label="Now Recording!")




        #
        # Buttons
        #

        with gradio.Row():

            def regenerate():
                try:
                    from API.api_controller import next_message_oogabooga, receive_via_oogabooga
                    next_message_oogabooga()
                    return receive_via_oogabooga()
                except ImportError as e:
                    print(f"[WEBUI] Error importing API controller for regenerate: {e}")
                    return "Sorry, I'm having trouble connecting to the AI backend right now."
                
            def send_blank():
                try:
                    from API.api_controller import run
                    from utils import settings
                    return run("", settings.temp_level)
                except ImportError as e:
                    print(f"[WEBUI] Error importing API controller for send_blank: {e}")
                    return "Sorry, I'm having trouble connecting to the AI backend right now."
            
            regenerate_btn = gr.Button("🔄 Regenerate")
            regenerate_btn.click(regenerate)
            
            clear_btn = gr.Button("🗑️ Clear History")
            clear_btn.click(clear_history, outputs=[chatbot])
            
            blank_btn = gr.Button("📝 Send Blank")
            blank_btn.click(send_blank)

            def undo():
                """Undo last message from web UI"""
                try:
                    # Clear from platform-separated history first
                    from utils.chat_history import chat_histories, save_chat_histories
                    user_key = "webui_webui_user"  # Web UI user key
                    
                    if user_key in chat_histories and len(chat_histories[user_key]) >= 2:
                        # Remove the last user and assistant messages
                        chat_histories[user_key] = chat_histories[user_key][:-2]
                        save_chat_histories()
                    
                    # Also handle old system for backward compatibility
                    try:
                        API.api_controller.undo_message()
                    except Exception as e:
                        print(f"[WEBUI] Error calling API controller undo: {e}")
                    
                    # Update the chat display after undo
                    updated_chat = update_chat()
                    status_message = "✅ Last message undone successfully!\n🔄 Conversation reverted to previous state"
                    print(f"[Web-UI] {status_message}")
                    return updated_chat, status_message
                except Exception as e:
                    error_msg = f"❌ Error during undo: {e}"
                    print(f"[Web-UI] {error_msg}")
                    return update_chat(), error_msg

            def clear_history():
                """Clear conversation history from web UI"""
                try:
                    # Clear platform-separated history for web UI user
                    from utils.chat_history import clear_all_histories
                    clear_all_histories()
                    
                    # Also clear old system for backward compatibility
                    try:
                        fresh_history = [["Hello, I am back!", "Welcome back! *smiles*"]]
                        import json
                        with open("LiveLog.json", 'w') as outfile:
                            json.dump(fresh_history, outfile, indent=4)
                        API.api_controller.ooga_history = fresh_history
                    except Exception as e:
                        print(f"[WEBUI] Error clearing old system history: {e}")
                    
                    # Update the chat display after clearing (should be empty now)
                    updated_chat = []  # Empty chat after clearing
                    status_message = "✅ Conversation history cleared successfully!\n🔄 Chat has been reset to fresh start\n🗑️ All conversation data cleared"
                    print(f"[Web-UI] {status_message}")
                    return updated_chat, status_message
                except Exception as e:
                    error_msg = f"❌ Error clearing history: {e}"
                    print(f"[Web-UI] {error_msg}")
                    return update_chat(), error_msg

            def soft_reset():
                """Perform soft reset from web UI"""
                try:
                    # Use the API controller's soft reset which now handles both systems
                    try:
                        API.api_controller.soft_reset()
                    except Exception as e:
                        print(f"[WEBUI] Error calling API controller soft reset: {e}")
                    
                    # Update the chat display after soft reset
                    updated_chat = update_chat()
                    status_message = "✅ Chat soft reset completed successfully!\n🔄 System reset messages added to conversation\n💬 The AI will now respond with refreshed context"
                    print(f"[Web-UI] {status_message}")
                    return updated_chat, status_message
                except Exception as e:
                    error_msg = f"❌ Error during soft reset: {e}"
                    print(f"[Web-UI] {error_msg}")
                    return update_chat(), error_msg

            button_regen = gr.Button(value="Reroll")
            button_blank = gr.Button(value="Send Blank")
            button_undo = gr.Button(value="Undo")
            button_clear_history = gr.Button(value="Clear History")
            button_soft_reset = gr.Button(value="Chat Soft Reset")

            button_regen.click(fn=regenerate)
            button_blank.click(fn=send_blank)
            
        # Add a status display for operations feedback
        with gr.Row():
            status_display = gr.Textbox(label="Status", interactive=False, lines=3, placeholder="Operation status will appear here...")
            
        # Connect buttons with proper outputs to update chat and show status
        button_undo.click(fn=undo, outputs=[chatbot, status_display])
        button_clear_history.click(fn=clear_history, outputs=[chatbot, status_display])
        button_soft_reset.click(fn=soft_reset, outputs=[chatbot, status_display])


        #
        # Autochat Settings
        #

        def autochat_button_click():
            # No toggle in hangout mode
            if settings.hangout_mode:
                return

            hotkeys.input_toggle_autochat_from_ui()
            return


        def change_autochat_sensitivity(autochat_sens):
            
            if not isinstance(autochat_sens, (int, float)):
                autochat_sens = 16 # Default value
            
            hotkeys.input_change_listener_sensitivity_from_ui(int(autochat_sens))
            return


        with gradio.Row():

            autochat_button = gr.Button(value="Toggle Auto-Chat")
            autochat_button.click(fn=autochat_button_click)

            autochat_checkbox_view = gr.Checkbox(label="Auto-Chat Enabled")

            autochat_sensitivity_slider = gr.Slider(minimum=4, maximum=144, value=settings.AUTOCHAT_SENSITIVITY, label="Auto-Chat Sensitivity")
            autochat_sensitivity_slider.change(fn=change_autochat_sensitivity, inputs=autochat_sensitivity_slider)


        #
        # Semi-Auto Chat Settings
        #

        def semi_auto_chat_button_click():

            # No toggle in hangout mode
            if settings.hangout_mode:
                return

            # Toggle
            settings.semi_auto_chat = not settings.semi_auto_chat

            # Log the toggle for UI tracking
            if settings.semi_auto_chat:
                print("Semi-Auto Chat toggled ON (Web UI)")
            else:
                print("Semi-Auto Chat toggled OFF (Web UI)")

            # Disable
            hotkeys.disable_autochat()

            return


        def semi_auto_chat_checkbox_change(checked):
            settings.semi_auto_chat = checked
            settings.update_env_semi_auto_chat(checked)
            return checked

        with gradio.Row():
            semi_auto_chat_checkbox_view = gr.Checkbox(
                label="Semi-Auto Chat Enabled",
                value=settings.semi_auto_chat
            )
            semi_auto_chat_checkbox_view.change(
                fn=semi_auto_chat_checkbox_change,
                inputs=semi_auto_chat_checkbox_view,
                outputs=semi_auto_chat_checkbox_view
            )


        #
        # Hangout Mode
        #

        def hangout_mode_button_click():

            # Toggle (Handled in the hotkey script)
            hotkeys.web_ui_toggle_hangout_mode()

            return

        with gr.Row():
            hangout_mode_button = gr.Button(value="Toggle Hangout Mode")
            hangout_mode_button.click(fn=hangout_mode_button_click)
            hangout_mode_checkbox_view = gr.Checkbox(label="Hangout Mode Enabled")

        #
        # Settings Tab
        #

        with gr.Tab("Settings"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Web UI Settings")
                    
                    web_ui_port_slider = gr.Slider(
                        minimum=1024, maximum=65535, value=settings.WEB_UI_PORT, 
                        step=1, label="Web UI Port"
                    )
                    
                    web_ui_share_checkbox = gr.Checkbox(
                        label="Share Web UI (public)", value=settings.WEB_UI_SHARE
                    )
                    
                    web_ui_theme_dropdown = gr.Dropdown(
                        choices=["default", "dark", "light"], value=settings.WEB_UI_THEME, label="Theme"
                    )
                    
                    # Language selector and auto-detect
                    language_dropdown = gr.Dropdown(
                        choices=list(settings.SUPPORTED_LANGUAGES.keys()),
                        value=settings.DEFAULT_LANGUAGE,
                        label="Language (for AI responses)",
                        interactive=True
                    )
                    
                    auto_detect_checkbox = gr.Checkbox(
                        label="Auto-detect language (experimental)",
                        value=settings.AUTO_DETECT_LANGUAGE
                    )
                    
                    def update_language_settings(lang_code, auto_detect):
                        settings.DEFAULT_LANGUAGE = lang_code
                        settings.AUTO_DETECT_LANGUAGE = auto_detect
                        settings.update_env_default_language(lang_code)
                        settings.update_env_auto_detect_language(auto_detect)
                        print(f"Language settings updated: Language={lang_code}, Auto-detect={auto_detect}")
                        return f"✅ Language settings saved! ({settings.SUPPORTED_LANGUAGES.get(lang_code, lang_code)})"
                    
                    language_save_button = gr.Button("Save Language Settings")
                    language_save_button.click(
                        fn=update_language_settings,
                        inputs=[language_dropdown, auto_detect_checkbox],
                        outputs=gr.Textbox(label="Status", interactive=False)
                    )
                
                with gr.Column():
                    gr.Markdown("### Voice & Audio Settings")
                    
                    voice_speed_slider = gr.Slider(
                        minimum=0.5, maximum=2.0, value=settings.VOICE_SPEED, 
                        step=0.1, label="Voice Speed"
                    )
                    
                    voice_volume_slider = gr.Slider(
                        minimum=0.0, maximum=2.0, value=settings.VOICE_VOLUME, 
                        step=0.1, label="Voice Volume"
                    )
                    
                    def update_voice_settings(speed, volume):
                        settings.VOICE_SPEED = float(speed)
                        settings.VOICE_VOLUME = float(volume)
                        settings.update_env_voice_settings(speed=speed, volume=volume)
                        print(f"Voice settings updated: Speed={speed}, Volume={volume}")
                        return f"✅ Voice settings saved!"
                    
                    voice_save_button = gr.Button("Save Voice Settings")
                    voice_save_button.click(
                        fn=update_voice_settings,
                        inputs=[voice_speed_slider, voice_volume_slider],
                        outputs=gr.Textbox(label="Status", interactive=False)
                    )
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Chat Settings")
                    
                    max_response_slider = gr.Slider(
                        minimum=100, maximum=2000, value=settings.MAX_RESPONSE_LENGTH, 
                        step=50, label="Max Response Length"
                    )
                    
                    history_limit_slider = gr.Slider(
                        minimum=10, maximum=200, value=settings.CHAT_HISTORY_LIMIT, 
                        step=10, label="Chat History Limit"
                    )
                    
                    auto_save_slider = gr.Slider(
                        minimum=1, maximum=60, value=settings.AUTO_SAVE_INTERVAL, 
                        step=1, label="Auto Save Interval (minutes)"
                    )
                    
                    def update_chat_settings(max_length, history_limit, auto_save):
                        settings.MAX_RESPONSE_LENGTH = int(max_length)
                        settings.CHAT_HISTORY_LIMIT = int(history_limit)
                        settings.AUTO_SAVE_INTERVAL = int(auto_save)
                        settings.update_env_chat_settings(max_length, history_limit, auto_save)
                        print(f"Chat settings updated: Max Length={max_length}, History Limit={history_limit}, Auto Save={auto_save}")
                        return f"✅ Chat settings saved!"
                    
                    chat_save_button = gr.Button("Save Chat Settings")
                    chat_save_button.click(
                        fn=update_chat_settings,
                        inputs=[max_response_slider, history_limit_slider, auto_save_slider],
                        outputs=gr.Textbox(label="Status", interactive=False)
                    )
                
                with gr.Column():
                    gr.Markdown("### System Settings")
                    
                    debug_mode_checkbox = gr.Checkbox(
                        label="Debug Mode", value=settings.DEBUG_MODE
                    )
                    
                    log_level_dropdown = gr.Dropdown(
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        value=settings.LOG_LEVEL, label="Log Level"
                    )
                    
                    auto_backup_checkbox = gr.Checkbox(
                        label="Auto Backup", value=settings.AUTO_BACKUP
                    )
                    
                    backup_interval_slider = gr.Slider(
                        minimum=15, maximum=240, value=settings.BACKUP_INTERVAL, 
                        step=15, label="Backup Interval (minutes)"
                    )
                    
                    def update_system_settings(debug, log_level, auto_backup, backup_interval):
                        settings.DEBUG_MODE = debug
                        settings.LOG_LEVEL = log_level
                        settings.AUTO_BACKUP = auto_backup
                        settings.BACKUP_INTERVAL = int(backup_interval)
                        settings.update_env_system_settings(debug, log_level, auto_backup, backup_interval)
                        print(f"System settings updated: Debug={debug}, Log Level={log_level}, Auto Backup={auto_backup}, Backup Interval={backup_interval}")
                        return f"✅ System settings saved!"
                    
                    system_save_button = gr.Button("Save System Settings")
                    system_save_button.click(
                        fn=update_system_settings,
                        inputs=[debug_mode_checkbox, log_level_dropdown, auto_backup_checkbox, backup_interval_slider],
                        outputs=gr.Textbox(label="Status", interactive=False)
                    )
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Flash Attention Control")
                    
                    def toggle_flash_attention():
                        current_state = settings.DISABLE_FLASH_ATTN
                        new_state = not current_state
                        settings.DISABLE_FLASH_ATTN = new_state
                        settings.update_env_flash_attn_disable(new_state)
                        status = "disabled" if new_state else "enabled"
                        print(f"Flash attention {status}")
                        return f"✅ Flash attention {status}!"
                    
                    flash_attn_button = gr.Button("Toggle Flash Attention")
                    flash_attn_status = gr.Textbox(
                        value=f"Flash Attention: {'Disabled' if settings.DISABLE_FLASH_ATTN else 'Enabled'}", 
                        label="Status", interactive=False
                    )
                    flash_attn_button.click(
                        fn=toggle_flash_attention,
                        outputs=flash_attn_status
                    )
                
                with gr.Column():
                    gr.Markdown("### Environment Detection")
                    
                    def run_environment_detection():
                        try:
                            from utils.settings import (
                                auto_detect_model_name, auto_detect_vtube, 
                                auto_detect_img, auto_detect_character_names,
                                auto_detect_flash_attn_compatibility
                            )
                            
                            print("Running environment detection...")
                            auto_detect_flash_attn_compatibility()
                            auto_detect_model_name()
                            auto_detect_vtube()
                            auto_detect_img()
                            auto_detect_character_names()
                            
                            return "✅ Environment detection completed!"
                        except Exception as e:
                            return f"❌ Detection error: {str(e)}"
                    
                    detect_button = gr.Button("Run Environment Detection")
                    detect_status = gr.Textbox(label="Detection Status", interactive=False)
                    detect_button.click(
                        fn=run_environment_detection,
                        outputs=detect_status
                    )
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### VTube Studio Connection")
                    
                    vtube_port_input = gr.Number(
                        value=settings.VTUBE_STUDIO_API_PORT, 
                        label="VTube Studio API Port", 
                        minimum=1000, 
                        maximum=9999
                    )
                    
                    vtube_host_input = gr.Textbox(
                        value=settings.VTUBE_STUDIO_API_HOST, 
                        label="VTube Studio API Host"
                    )
                    
                    def test_vtube_connection(host, port):
                        try:
                            import requests
                            url = f"http://{host}:{port}/api/1.0/"
                            response = requests.get(url, timeout=2)
                            if response.status_code == 200:
                                return f"✅ Connected successfully to VTube Studio API on {host}:{port}"
                            else:
                                return f"❌ Connection failed - Status code: {response.status_code}"
                        except Exception as e:
                            return f"❌ Connection failed - {str(e)}"
                    
                    def save_vtube_settings(host, port):
                        settings.VTUBE_STUDIO_API_HOST = host
                        settings.VTUBE_STUDIO_API_PORT = int(port)
                        settings.update_env_setting("VTUBE_STUDIO_API_HOST", host)
                        settings.update_env_setting("VTUBE_STUDIO_API_PORT", str(port))
                        print(f"VTube Studio settings updated: Host={host}, Port={port}")
                        return f"✅ VTube Studio settings saved!"
                    
                    vtube_test_button = gr.Button("Test Connection")
                    vtube_test_status = gr.Textbox(label="Connection Status", interactive=False)
                    vtube_test_button.click(
                        fn=test_vtube_connection,
                        inputs=[vtube_host_input, vtube_port_input],
                        outputs=vtube_test_status
                    )
                    
                    vtube_save_button = gr.Button("Save VTube Settings")
                    vtube_save_status = gr.Textbox(label="Save Status", interactive=False)
                    vtube_save_button.click(
                        fn=save_vtube_settings,
                        inputs=[vtube_host_input, vtube_port_input],
                        outputs=vtube_save_status
                    )
                
                with gr.Column():
                    gr.Markdown("### Relationship Settings")
                    
                    relationship_system_checkbox = gr.Checkbox(
                        label="Enable Relationship System", value=settings.RELATIONSHIP_SYSTEM_ENABLED
                    )
                    
                    relationship_partner_input = gr.Textbox(
                        label="Relationship Partner Name", 
                        value=settings.RELATIONSHIP_PARTNER_NAME,
                        placeholder="Enter the name of your relationship partner..."
                    )
                    
                    default_relationship_dropdown = gr.Dropdown(
                        choices=["stranger", "acquaintance", "friend", "close_friend", "vip"], 
                        value=settings.DEFAULT_RELATIONSHIP_LEVEL, label="Default Relationship Level"
                    )
                    
                    relationship_responses_checkbox = gr.Checkbox(
                        label="Enable Relationship-Based Responses", value=settings.RELATIONSHIP_RESPONSES_ENABLED
                    )
                    
                    relationship_memory_checkbox = gr.Checkbox(
                        label="Enable Relationship Memory", value=settings.RELATIONSHIP_MEMORY_ENABLED
                    )
                    
                    progression_speed_slider = gr.Slider(
                        minimum=0.1, maximum=3.0, value=settings.RELATIONSHIP_PROGRESSION_SPEED, 
                        step=0.1, label="Relationship Progression Speed"
                    )
                    
                    decay_rate_slider = gr.Slider(
                        minimum=0.0, maximum=1.0, value=settings.RELATIONSHIP_DECAY_RATE, 
                        step=0.05, label="Relationship Decay Rate"
                    )
                    
                    def update_relationship_settings(
                        system_enabled, partner_name, default_level, responses_enabled, 
                        memory_enabled, progression_speed, decay_rate
                    ):
                        settings.RELATIONSHIP_SYSTEM_ENABLED = system_enabled
                        settings.RELATIONSHIP_PARTNER_NAME = partner_name
                        settings.DEFAULT_RELATIONSHIP_LEVEL = default_level
                        settings.RELATIONSHIP_RESPONSES_ENABLED = responses_enabled
                        settings.RELATIONSHIP_MEMORY_ENABLED = memory_enabled
                        settings.RELATIONSHIP_PROGRESSION_SPEED = float(progression_speed)
                        settings.RELATIONSHIP_DECAY_RATE = float(decay_rate)
                        settings.update_env_relationship_settings(
                            system_enabled, default_level, responses_enabled, 
                            memory_enabled, progression_speed, decay_rate, partner_name
                        )
                        print(f"Relationship settings updated: System={system_enabled}, Partner={partner_name}, Level={default_level}, Responses={responses_enabled}, Memory={memory_enabled}, Speed={progression_speed}, Decay={decay_rate}")
                        return f"✅ Relationship settings saved!"
                    
                    relationship_save_button = gr.Button("Save Relationship Settings")
                    relationship_save_button.click(
                        fn=update_relationship_settings,
                        inputs=[
                            relationship_system_checkbox, relationship_partner_input, default_relationship_dropdown, 
                            relationship_responses_checkbox, relationship_memory_checkbox,
                            progression_speed_slider, decay_rate_slider
                        ],
                        outputs=gr.Textbox(label="Status", interactive=False)
                    )
                
                with gr.Column():
                    gr.Markdown("### Formal Filter Settings")
                    
                    formal_filter_enabled_checkbox = gr.Checkbox(
                        label="Enable Formal Filter", value=settings.FORMAL_FILTER_ENABLED
                    )
                    
                    formal_filter_strength_dropdown = gr.Dropdown(
                        choices=["low", "medium", "high"], 
                        value=settings.FORMAL_FILTER_STRENGTH, label="Filter Strength"
                    )
                    
                    formal_filter_replacement_dropdown = gr.Dropdown(
                        choices=["natural", "casual", "friendly", "custom"], 
                        value=settings.FORMAL_FILTER_REPLACEMENT_MODE, label="Replacement Style"
                    )
                    
                    formal_filter_custom_phrases_textbox = gr.Textbox(
                        value=",".join(settings.FORMAL_FILTER_CUSTOM_PHRASES), 
                        label="Custom Phrases (comma-separated)",
                        placeholder="how can i help, to be of service, what can i do for you"
                    )
                    
                    formal_filter_custom_patterns_textbox = gr.Textbox(
                        value=",".join(settings.FORMAL_FILTER_CUSTOM_PATTERNS), 
                        label="Custom Patterns (comma-separated regex)",
                        placeholder="\\bto\\s+be\\s+of\\s+service\\b,\\bhow\\s+can\\s+i\\s+assist\\b"
                    )
                    
                    def update_formal_filter_settings(enabled, strength, replacement_mode, custom_phrases, custom_patterns):
                        settings.FORMAL_FILTER_ENABLED = enabled
                        settings.FORMAL_FILTER_STRENGTH = strength
                        settings.FORMAL_FILTER_REPLACEMENT_MODE = replacement_mode
                        
                        # Parse custom phrases and patterns
                        phrases = [p.strip() for p in custom_phrases.split(",") if p.strip()]
                        patterns = [p.strip() for p in custom_patterns.split(",") if p.strip()]
                        
                        settings.FORMAL_FILTER_CUSTOM_PHRASES = phrases
                        settings.FORMAL_FILTER_CUSTOM_PATTERNS = patterns
                        
                        # Update environment variables
                        settings.update_env_formal_filter(enabled)
                        settings.update_env_formal_filter_strength(strength)
                        settings.update_env_formal_filter_replacement_mode(replacement_mode)
                        settings.update_env_formal_filter_custom_phrases(phrases)
                        settings.update_env_formal_filter_custom_patterns(patterns)
                        
                        print(f"Formal filter settings updated: Enabled={enabled}, Strength={strength}, Replacement={replacement_mode}")
                        return f"✅ Formal filter settings saved!"
                    
                    formal_filter_save_button = gr.Button("Save Formal Filter Settings")
                    formal_filter_save_button.click(
                        fn=update_formal_filter_settings,
                        inputs=[
                            formal_filter_enabled_checkbox, 
                            formal_filter_strength_dropdown, 
                            formal_filter_replacement_dropdown,
                            formal_filter_custom_phrases_textbox,
                            formal_filter_custom_patterns_textbox
                        ],
                        outputs=gr.Textbox(label="Status", interactive=False)
                    )
                    
                    def test_formal_filter():
                        """Test the formal filter with sample text."""
                        try:
                            from utils.formal_filter import test_formal_filter
                            config = settings.get_formal_filter_config()
                            
                            test_texts = [
                                "How can I assist you today?",
                                "I'm here to be of service!",
                                "What can I do for you?",
                                "Hey! How's it going?",
                                "Hi there! What's up?"
                            ]
                            
                            results = []
                            for text in test_texts:
                                result = test_formal_filter(text, config)
                                status = "🚫 FORMAL" if result["is_formal"] else "✅ NATURAL"
                                results.append(f"{status}: {text}")
                                if result["is_formal"] and result["replacement"]:
                                    results.append(f"   → Replacement: {result['replacement']}")
                            
                            return "\n".join(results)
                        except Exception as e:
                            return f"❌ Test error: {str(e)}"
                    
                    formal_filter_test_button = gr.Button("Test Formal Filter")
                    formal_filter_test_output = gr.Textbox(label="Test Results", interactive=False, lines=10)
                    formal_filter_test_button.click(
                        fn=test_formal_filter,
                        outputs=formal_filter_test_output
                    )

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### API Fallback Settings")

                    # Discover models (GGUF and HuggingFace)
                    discovered_models = discover_models()
                    model_choices = discovered_models + ["custom"]

                    api_fallback_enabled_checkbox = gr.Checkbox(
                        label="Enable API Fallback",
                        value=settings.api_fallback_enabled,
                        info="Use lightweight local model when main API fails"
                    )
                    api_fallback_enabled_checkbox.change(
                        api_fallback_checkbox_change,
                        inputs=[api_fallback_enabled_checkbox]
                    )

                    api_fallback_model = gr.Dropdown(
                        label="Fallback Model (Primary)",
                        choices=model_choices,
                        value=os.getenv("API_FALLBACK_MODEL", discovered_models[0] if discovered_models else "TinyLlama/TinyLlama-1.1B-Chat-v1.0"),
                        info="Select fallback model (smaller = less VRAM)"
                    )
                    api_fallback_model.change(
                        api_fallback_model_change,
                        inputs=[api_fallback_model]
                    )

                    custom_model_path = gr.Textbox(
                        label="Custom Model Path (GGUF or HuggingFace)",
                        value=os.getenv("API_FALLBACK_MODEL", ""),
                        info="Enter a custom model path or repo name."
                    )
                    def custom_model_path_change(value):
                        settings.update_env_api_fallback_model(value)
                        print(f"[Web-UI] Custom fallback model path set -> {value}")
                        return
                    custom_model_path.change(custom_model_path_change, inputs=[custom_model_path])

                    # Fallback order (multi-select)
                    fallback_order = gr.Dropdown(
                        label="Fallback Model Order (try in order)",
                        choices=model_choices,
                        value=model_choices[:3],
                        multiselect=True,
                        info="Order in which fallback models are tried."
                    )
                    def fallback_order_change(values):
                        # Save to env or config as needed
                        os.environ["FALLBACK_MODEL_ORDER"] = ",".join(values)
                        print(f"[Web-UI] Fallback model order set -> {values}")
                        return
                    fallback_order.change(fallback_order_change, inputs=[fallback_order])

                    # Test all fallbacks
                    def test_all_fallbacks():
                        test_messages = [
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": "Hello! This is a test."}
                        ]
                        request = {
                            "messages": test_messages,
                            "max_tokens": 50,
                            "temperature": 0.7
                        }
                        response = try_fallbacks(request)
                        if isinstance(response, dict) and "choices" in response:
                            return "✅ At least one fallback model worked!"
                        else:
                            return f"❌ All fallback models failed: {response.get('error', response)}"
                    fallback_test_all_button = gr.Button("Test All Fallbacks")
                    fallback_test_all_status = gr.Textbox(label="Test Status", interactive=False)
                    fallback_test_all_button.click(
                        fn=test_all_fallbacks,
                        outputs=fallback_test_all_status
                    )

                    # TinyLlama GGUF Preset Management
                    gr.Markdown("### 🎯 TinyLlama GGUF Preset (Recommended)")
                    
                    with gr.Row():
                        tinyllama_status_btn = gr.Button("📊 Check Status", variant="secondary", size="sm")
                        tinyllama_download_btn = gr.Button("📥 Download", variant="secondary", size="sm")
                        tinyllama_load_btn = gr.Button("🚀 Load Model", variant="primary", size="sm")
                        tinyllama_test_btn = gr.Button("🧪 Test", variant="secondary", size="sm")
                    
                    tinyllama_status_output = gr.JSON(label="TinyLlama GGUF Status")
                    tinyllama_action_output = gr.Textbox(label="Action Result", interactive=False)
                    
                    # Wire up TinyLlama controls
                    tinyllama_status_btn.click(
                        fn=check_tinyllama_gguf_status,
                        outputs=tinyllama_status_output
                    )
                    
                    tinyllama_download_btn.click(
                        fn=download_tinyllama_gguf,
                        outputs=tinyllama_action_output
                    )
                    
                    tinyllama_load_btn.click(
                        fn=load_tinyllama_gguf_preset,
                        outputs=tinyllama_action_output
                    )
                    
                    tinyllama_test_btn.click(
                        fn=test_tinyllama_gguf,
                        outputs=tinyllama_action_output
                    )

                    # Fallback Model Presets
                    gr.Markdown("### 🔧 Fallback Model Presets")
                    
                    preset_choices = list(get_fallback_presets().keys())
                    fallback_preset_dropdown = gr.Dropdown(
                        label="Select Preset",
                        choices=preset_choices,
                        value=preset_choices[0] if preset_choices else None,
                        info="Choose a pre-configured fallback model"
                    )
                    
                    with gr.Row():
                        load_preset_btn = gr.Button("🔄 Load Preset", variant="primary", size="sm")
                        preset_info_btn = gr.Button("ℹ️ Info", variant="secondary", size="sm")
                    
                    preset_output = gr.Textbox(label="Preset Status", interactive=False)
                    preset_info_output = gr.JSON(label="Preset Information")
                    
                    def show_preset_info(preset_name):
                        presets = get_fallback_presets()
                        if preset_name in presets:
                            return presets[preset_name]
                        return {"error": "Preset not found"}
                    
                    load_preset_btn.click(
                        fn=load_fallback_preset,
                        inputs=fallback_preset_dropdown,
                        outputs=preset_output
                    )
                    
                    preset_info_btn.click(
                        fn=show_preset_info,
                        inputs=fallback_preset_dropdown,
                        outputs=preset_info_output
                    )
                    
                    # Note: refresh functionality will be connected after all components are defined

                    # Add model info section
                    gr.Markdown("""
                    #### Available Fallback Models:
                    - **TinyLlama GGUF (Local)**: Ultra-efficient local model (~700MB, 1-2GB RAM) ⭐ **RECOMMENDED**
                    - **TinyLlama (HuggingFace)**: Online version (requires internet)
                    - **Phi-2**: Small but powerful (~2.7GB VRAM), great quality/size ratio
                    - **Mistral-7B-Instruct**: Larger but very capable (~5GB VRAM with 4-bit)
                    - **Neural-Chat-7B**: Alternative to Mistral, similar size
                    - **GGUF**: Any .gguf file in the models/ directory
                    - **custom**: Use your own model path
                    """)

                # Advanced Fallback Interface
                with gr.Column():
                    gr.Markdown("### 🚀 Advanced Fallback Management")
                    
                    # Quick Actions
                    with gr.Row():
                        auto_config_btn = gr.Button("⚡ Auto-Configure", variant="primary", size="sm")
                        fallback_status_btn = gr.Button("📊 System Status", variant="secondary", size="sm")
                        refresh_models_btn = gr.Button("🔄 Refresh", variant="secondary", size="sm")
                    
                    auto_config_output = gr.Textbox(label="Auto-Configuration Result", interactive=False)
                    fallback_status_output = gr.JSON(label="Fallback System Status")
                    
                    auto_config_btn.click(
                        fn=auto_configure_fallback,
                        outputs=auto_config_output
                    )
                    
                    fallback_status_btn.click(
                        fn=get_current_fallback_status,
                        outputs=fallback_status_output
                    )
                    
                    # Note: refresh functionality will be connected after all components are defined
                    
                    # System Status
                    with gr.Row():
                        refresh_status_btn = gr.Button("🔄 System Status", variant="secondary", size="sm")
                        system_status_output = gr.JSON(label="System Info")
                    
                    refresh_status_btn.click(
                        fn=get_system_status,
                        outputs=system_status_output
                    )
                    
                    # VRAM Optimization
                    with gr.Row():
                        optimize_vram_btn = gr.Button("⚡ Optimize for VRAM", variant="secondary", size="sm")
                        vram_optimization_output = gr.JSON(label="VRAM Optimization")
                    
                    optimize_vram_btn.click(
                        fn=optimize_for_vram_advanced,
                        outputs=vram_optimization_output
                    )
                    
                    # Model Discovery and Analysis
                    with gr.Row():
                        discover_btn = gr.Button("🔍 Analyze Models", variant="secondary", size="sm")
                        model_analysis_output = gr.JSON(label="Model Analysis")
                    
                    discover_btn.click(
                        fn=discover_and_analyze_models,
                        outputs=model_analysis_output
                    )
                    
                    # Custom Model Addition
                    with gr.Row():
                        custom_model_path_advanced = gr.Textbox(
                            label="Custom Model Path",
                            placeholder="/path/to/model.gguf or huggingface/model/name",
                            scale=2
                        )
                        custom_model_name_advanced = gr.Textbox(
                            label="Model Name (optional)",
                            placeholder="Custom name",
                            scale=1
                        )
                    
                    with gr.Row():
                        add_custom_btn = gr.Button("➕ Add Custom Model", variant="secondary", size="sm")
                        custom_model_output = gr.JSON(label="Custom Model Analysis")
                    
                    add_custom_btn.click(
                        fn=add_custom_model_advanced,
                        inputs=[custom_model_path_advanced, custom_model_name_advanced],
                        outputs=custom_model_output
                    )
                    
                    # Model Compatibility Testing
                    with gr.Row():
                        test_model_input = gr.Textbox(
                            label="Test Model Compatibility",
                            placeholder="Enter model name or path",
                            scale=2
                        )
                        test_compatibility_btn = gr.Button("🧪 Test", variant="secondary", size="sm")
                    
                    test_compatibility_output = gr.JSON(label="Compatibility Results")
                    
                    test_compatibility_btn.click(
                        fn=test_model_compatibility,
                        inputs=test_model_input,
                        outputs=test_compatibility_output
                    )
                    
                    # Advanced Fallback Testing
                    with gr.Row():
                        test_all_advanced_btn = gr.Button("🧪 Test All Fallbacks (Advanced)", variant="primary", size="sm")
                        test_all_advanced_output = gr.JSON(label="Advanced Test Results")
                    
                    test_all_advanced_btn.click(
                        fn=test_all_fallbacks_advanced,
                        outputs=test_all_advanced_output
                    )
                    
                    # Model Order Management (Drag-and-Drop simulation)
                    gr.Markdown("### 📋 Model Order Management")
                    gr.Markdown("Models will be tried in the order shown below. Use the dropdown to reorder.")
                    
                    model_order_input = gr.JSON(
                        label="Current Model Order",
                        value=discover_and_analyze_models()
                    )
                    
                    with gr.Row():
                        update_order_btn = gr.Button("💾 Save Model Order", variant="primary", size="sm")
                        order_update_output = gr.Textbox(label="Order Update Status")
                    
                    update_order_btn.click(
                        fn=update_fallback_order_advanced,
                        inputs=model_order_input,
                        outputs=order_update_output
                    )
                    
                    # Connect refresh functionality now that all components are defined
                    def refresh_fallback_interface():
                        presets = get_fallback_presets()
                        models = discover_and_analyze_models()
                        status = get_current_fallback_status()
                        return list(presets.keys()), models, status
                    
                    refresh_models_btn.click(
                        fn=refresh_fallback_interface,
                        outputs=[fallback_preset_dropdown, model_analysis_output, fallback_status_output]
                    )


        # Define dummy/invisible components to avoid NameError
        shadowchats_checkbox_view = gr.Checkbox(visible=False)
        speaking_choice_checkbox_view = gr.Checkbox(visible=False)
        supress_rp_checkbox_view = gr.Checkbox(visible=False)
        newline_cut_checkbox_view = gr.Checkbox(visible=False)
        asterisk_ban_checkbox_view = gr.Checkbox(visible=False)
        hotkey_locked_checkbox_view = gr.Checkbox(visible=False)
        max_tokens_slider = gr.Slider(visible=False)
        alarm_time_box = gr.Textbox(visible=False)
        model_preset_box = gr.Textbox(visible=False)


        def update_settings_view():
            """Update all settings views with current values."""
            return (
                settings.is_recording,
                hotkeys.get_autochat_toggle(),  # Fix: Use correct autochat variable
                settings.semi_auto_chat,
                settings.hangout_mode,
                settings.speak_shadowchats,
                settings.speak_only_spokento,
                settings.supress_rp,
                settings.newline_cut,
                settings.asterisk_ban,
                settings.hotkeys_locked,
                settings.max_tokens,
                settings.alarm_time,
                settings.model_preset
            )


        # Note: Checkbox updates moved to consolidated update_all_views function below
        # This prevents duplicate updates that cause visual glitching






    #
    # VISUAL
    #

    if settings.vision_enabled:
        with gr.Tab("Visual"):

            #
            # Take / Retake Image
            #

            with gr.Row():
                def take_image_button_click():
                    hotkeys.view_image_from_ui()

                    return

                take_image_button = gr.Button(value="Take / Send Image")
                take_image_button.click(fn=take_image_button_click)


            #
            # Image Feed
            #

            with gr.Row():
                def cam_use_image_feed_button_click():
                    settings.cam_use_image_feed = not settings.cam_use_image_feed

                    return


                with gr.Row():
                    cam_use_image_feed_button = gr.Button(value="Check/Uncheck")
                    cam_use_image_feed_button.click(fn=cam_use_image_feed_button_click)

                    cam_use_image_feed_checkbox_view = gr.Checkbox(label="Use Image Feed (File Select)")


            #
            # Direct Talk
            #

            with gr.Row():
                def cam_direct_talk_button_click():
                    settings.cam_direct_talk = not settings.cam_direct_talk

                    return


                with gr.Row():
                    cam_direct_talk_button = gr.Button(value="Check/Uncheck")
                    cam_direct_talk_button.click(fn=cam_direct_talk_button_click)

                    cam_direct_talk_checkbox_view = gr.Checkbox(label="Direct Talk & Send")


            #
            # Image Preview
            #

            with gr.Row():
                def cam_image_preview_button_click():
                    settings.cam_image_preview = not settings.cam_image_preview

                    return


                with gr.Row():
                    cam_image_preview_button = gr.Button(value="Check/Uncheck")
                    cam_image_preview_button.click(fn=cam_image_preview_button_click)

                    cam_image_preview_checkbox_view = gr.Checkbox(label="Preview before Sending")

            #
            # Capture screenshot
            #

            with gr.Row():
                def cam_capture_screenshot_button_click():
                    settings.cam_use_screenshot = not settings.cam_use_screenshot

                    return


                with gr.Row():
                    cam_capture_screenshot_button = gr.Button(value="Check/Uncheck")
                    cam_capture_screenshot_button.click(fn=cam_capture_screenshot_button_click)

                    cam_capture_screenshot_checkbox_view = gr.Checkbox(label="Capture Screenshot")

            def update_visual_view():
                return settings.cam_use_image_feed, settings.cam_direct_talk, settings.cam_image_preview, settings.cam_use_screenshot


            demo.load(update_visual_view, every=0.1,
                      outputs=[cam_use_image_feed_checkbox_view, cam_direct_talk_checkbox_view, cam_image_preview_checkbox_view, cam_capture_screenshot_checkbox_view])



    #
    # SETTINGS
    #


    with gr.Tab("Settings"):
        # Shadow Chat Settings
        with gr.Row():
            gr.Markdown("### Shadow Chat Settings")
        
        with gr.Row():
            # This checkbox controls whether the AI will speak responses (shadow chat/voice).
            # When disabled, the AI will not speak any responses, including startup and Web UI chats.
            def speak_shadowchats_checkbox_change(checked):
                try:
                    settings.speak_shadowchats = checked
                    settings.update_env_speak_shadowchats(checked)
                    print(f"[Web-UI] Shadow chats {'enabled' if checked else 'disabled'}")
                    return checked
                except Exception as e:
                    print(f"[Web-UI] Error updating shadow chats setting: {e}")
                    return not checked  # Revert the change
            speak_shadowchats_checkbox = gr.Checkbox(
                label="Enable Shadow Chats",
                value=settings.speak_shadowchats,
                info="When enabled, the AI will respond to all messages. When disabled, only responds to messages starting with its name."
            )
            speak_shadowchats_checkbox.change(
                fn=speak_shadowchats_checkbox_change,
                inputs=speak_shadowchats_checkbox,
                outputs=speak_shadowchats_checkbox
            )

        with gr.Row():
            def speak_only_spokento_checkbox_change(checked):
                try:
                    settings.speak_only_spokento = checked
                    settings.update_env_speak_only_spokento(checked)
                    print(f"[Web-UI] Speak-only-when-spoken-to {'enabled' if checked else 'disabled'}")
                    return checked
                except Exception as e:
                    print(f"[Web-UI] Error updating speak-only setting: {e}")
                    return not checked  # Revert the change
            speak_only_spokento_checkbox = gr.Checkbox(
                label="Only Respond When Spoken To",
                value=settings.speak_only_spokento,
                info="When enabled, the AI will only respond to messages that start with its name."
            )
            speak_only_spokento_checkbox.change(
                fn=speak_only_spokento_checkbox_change,
                inputs=speak_only_spokento_checkbox,
                outputs=speak_only_spokento_checkbox
            )

        gr.Markdown("---")  # Add a separator

        # Other Settings (existing)
        with gr.Row():
            def supress_rp_checkbox_change(checked):
                try:
                    settings.supress_rp = checked
                    settings.update_env_supress_rp(checked)
                    print(f"[Web-UI] RP suppression {'enabled' if checked else 'disabled'}")
                    return checked
                except Exception as e:
                    print(f"[Web-UI] Error updating RP suppression setting: {e}")
                    return not checked  # Revert the change
            supress_rp_checkbox = gr.Checkbox(
                label="Suppress RP",
                value=settings.supress_rp
            )
            supress_rp_checkbox.change(
                fn=supress_rp_checkbox_change,
                inputs=supress_rp_checkbox,
                outputs=supress_rp_checkbox
            )

        # Newline Cut
        with gr.Row():
            def newline_cut_checkbox_change(checked):
                try:
                    settings.newline_cut = checked
                    settings.update_env_newline_cut(checked)
                    print(f"[Web-UI] Newline cut {'enabled' if checked else 'disabled'}")
                    return checked
                except Exception as e:
                    print(f"[Web-UI] Error updating newline cut setting: {e}")
                    return not checked  # Revert the change
            newline_cut_checkbox = gr.Checkbox(
                label="Newline Cut",
                value=settings.newline_cut
            )
            newline_cut_checkbox.change(
                fn=newline_cut_checkbox_change,
                inputs=newline_cut_checkbox,
                outputs=newline_cut_checkbox
            )
        
        # Asterisk Ban
        with gr.Row():
            def asterisk_ban_checkbox_change(checked):
                try:
                    settings.asterisk_ban = checked
                    settings.update_env_asterisk_ban(checked)
                    print(f"[Web-UI] Asterisk ban {'enabled' if checked else 'disabled'}")
                    return checked
                except Exception as e:
                    print(f"[Web-UI] Error updating asterisk ban setting: {e}")
                    return not checked  # Revert the change
            asterisk_ban_checkbox = gr.Checkbox(
                label="Asterisk Ban",
                value=settings.asterisk_ban
            )
            asterisk_ban_checkbox.change(
                fn=asterisk_ban_checkbox_change,
                inputs=asterisk_ban_checkbox,
                outputs=asterisk_ban_checkbox
            )

        # Hotkeys Locked
        with gr.Row():
            def hotkeys_locked_checkbox_change(checked):
                try:
                    settings.hotkeys_locked = checked
                    settings.update_env_hotkeys_locked(checked)
                    print(f"[Web-UI] Hotkeys {'locked' if checked else 'unlocked'}")
                    return checked
                except Exception as e:
                    print(f"[Web-UI] Error updating hotkeys setting: {e}")
                    return not checked  # Revert the change
            hotkeys_locked_checkbox = gr.Checkbox(
                label="Hotkeys Locked",
                value=settings.hotkeys_locked
            )
            hotkeys_locked_checkbox.change(
                fn=hotkeys_locked_checkbox_change,
                inputs=hotkeys_locked_checkbox,
                outputs=hotkeys_locked_checkbox
            )

        # Max Tokens
        with gr.Row():
            def max_tokens_slider_change(value):
                try:
                    settings.max_tokens = int(value)
                    settings.update_env_max_tokens(value)
                    print(f"[Web-UI] Max tokens set to {value}")
                    return value
                except Exception as e:
                    print(f"[Web-UI] Error updating max tokens setting: {e}")
                    return settings.max_tokens  # Return current value
            max_tokens_slider = gr.Slider(
                minimum=50, maximum=4096, value=settings.max_tokens, step=1, label="Max Tokens"
            )
            max_tokens_slider.change(
                fn=max_tokens_slider_change,
                inputs=max_tokens_slider,
                outputs=max_tokens_slider
            )

        # Alarm Time
        with gr.Row():
            def alarm_time_textbox_change(value):
                try:
                    settings.alarm_time = value
                    settings.update_env_alarm_time(value)
                    print(f"[Web-UI] Alarm time set to {value}")
                    return value
                except Exception as e:
                    print(f"[Web-UI] Error updating alarm time setting: {e}")
                    return settings.alarm_time  # Return current value
            alarm_time_textbox = gr.Textbox(
                label="Alarm Time",
                value=settings.alarm_time
            )
            alarm_time_textbox.change(
                fn=alarm_time_textbox_change,
                inputs=alarm_time_textbox,
                outputs=alarm_time_textbox
            )

        # Model Preset
        with gr.Row():
            def model_preset_textbox_change(value):
                try:
                    settings.model_preset = value
                    settings.update_env_model_preset(value)
                    print(f"[Web-UI] Model preset set to {value}")
                    return value
                except Exception as e:
                    print(f"[Web-UI] Error updating model preset setting: {e}")
                    return settings.model_preset  # Return current value
            model_preset_textbox = gr.Textbox(
                label="Model Preset",
                value=settings.model_preset
            )
            model_preset_textbox.change(
                fn=model_preset_textbox_change,
                inputs=model_preset_textbox,
                outputs=model_preset_textbox
            )

        # API Fallback Settings
        with gr.Row():
            with gr.Column():
                gr.Markdown("### API Settings")
                api_fallback_checkbox = gr.Checkbox(
                    label="Enable API Fallback",
                    value=settings.api_fallback_enabled
                )
                api_fallback_model = gr.Textbox(
                    label="API Fallback Model",
                    value=settings.API_FALLBACK_MODEL,
                    placeholder="Enter fallback model name"
                )
                api_fallback_host = gr.Textbox(
                    label="API Fallback Host",
                    value=settings.API_FALLBACK_HOST,
                    placeholder="Enter fallback host (e.g. 127.0.0.1:5000)"
                )

                # Connect event handlers
                api_fallback_checkbox.change(
                    fn=api_fallback_checkbox_change,
                    inputs=api_fallback_checkbox
                )
                api_fallback_model.change(
                    fn=api_fallback_model_change,
                    inputs=api_fallback_model
                )
                api_fallback_host.change(
                    fn=api_fallback_host_change,
                    inputs=api_fallback_host
                )

    #
    # TAGS & TASKS
    #
    with gr.Tab("Tags & Tasks"):
        def get_current_tags():
            return ", ".join(settings.cur_tags) if settings.cur_tags else "None"

        def get_current_task():
            return settings.cur_task_char

        with gr.Row():
            current_tags_view = gr.Textbox(label="Current Tags", interactive=False)
            current_task_view = gr.Textbox(label="Current Task", interactive=False)
        
        demo.load(get_current_tags, outputs=current_tags_view, every=0.5)
        demo.load(get_current_task, outputs=current_task_view, every=0.5)

        with gr.Row():
            tag_input = gr.Textbox(label="Add/Remove Tag")
            add_tag_button = gr.Button("Add Tag")
            remove_tag_button = gr.Button("Remove Tag")

            add_tag_button.click(lambda x: tag_task_controller.add_tag(x), inputs=tag_input)
            remove_tag_button.click(lambda x: tag_task_controller.remove_tag(x), inputs=tag_input)

        with gr.Row():
            task_dropdown = gr.Dropdown(choices=settings.all_task_char_list, label="Select Task", interactive=True)
            set_task_button = gr.Button("Set Task")
            clear_task_button = gr.Button("Clear Task")

            set_task_button.click(lambda x: tag_task_controller.set_task(x), inputs=task_dropdown)
            clear_task_button.click(lambda: tag_task_controller.set_task("None"))



    #
    # DEBUG
    #

    with gr.Tab("Debug"):
        debug_log = gr.Textbox(zw_logging.debug_log, lines=10, label="General Debug", autoscroll=True)
        rag_log = gr.Textbox(zw_logging.rag_log, lines=10, label="RAG Debug", autoscroll=True)
        kelvin_log = gr.Textbox(zw_logging.kelvin_log, lines=1, label="Random Temperature Readout")

        def update_logs():
            return zw_logging.debug_log, zw_logging.rag_log, zw_logging.kelvin_log

        demo.load(update_logs, every=0.1, outputs=[debug_log, rag_log, kelvin_log])



    #
    # LINKS
    #

    with gr.Tab("Links"):

        links_text = (
                      "Github Project:\n" +
                      "https://github.com/SugarcaneDefender/z-waif \n" +
                      "\n" +
                      "Documentation:\n" +
                      "https://docs.google.com/document/d/1qzY09kcwfbZTaoJoQZDAWv282z88jeUCadivLnKDXCo/edit?usp=sharing \n" +
                      "\n" +
                      "YouTube:\n" +
                      "https://www.youtube.com/@SugarcaneDefender \n" +
                      "\n" +
                      "Support more development on Ko-Fi:\n" +
                      "https://ko-fi.com/zwaif \n" +
                      "\n" +
                      "Email me for premium AI-waifu development, install, and assistance:\n" +
                      "zwaif77@gmail.com")

        rag_log = gr.Textbox(links_text, lines=14, label="Links")

    # Universal update function for all dynamic UI elements (consolidated to prevent conflicts)
    def update_all_views():
        return (
            hotkeys.get_speak_input(),           # recording_checkbox_view
            hotkeys.get_autochat_toggle(),       # autochat_checkbox_view - FIXED: use correct variable
            settings.semi_auto_chat,             # semi_auto_chat_checkbox_view
            settings.hangout_mode,               # hangout_mode_checkbox_view
            settings.speak_shadowchats,          # shadowchats_checkbox_view
            settings.hotkeys_locked,             # hotkey_locked_checkbox_view
            settings.supress_rp,                 # supress_rp_checkbox_view
            settings.newline_cut,                # newline_cut_checkbox_view
            settings.asterisk_ban                # asterisk_ban_checkbox_view
        )

    # A single demo.load call to update all checkboxes simultaneously
    # Update frequency reduced to prevent visual glitching
    demo.load(
        fn=update_all_views,
        every=0.25,  # Reduced frequency to prevent glitching
        outputs=[
            recording_checkbox_view,
            autochat_checkbox_view,
            semi_auto_chat_checkbox_view,
            hangout_mode_checkbox_view,
            shadowchats_checkbox_view,
            hotkey_locked_checkbox_view,
            supress_rp_checkbox_view,
            newline_cut_checkbox_view,
            asterisk_ban_checkbox_view
        ]
    )

    with gr.Tab("LLM Extended Settings"):
        gr.Markdown("# LLM Extended Settings")
        gr.Markdown("Configure advanced settings for the Language Model, including temperature, generation parameters, presets, and character card.")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### Temperature & Generation Settings")
                temperature_slider = gr.Slider(minimum=0.0, maximum=1.0, value=settings.TEMPERATURE, step=0.05, label="Temperature")
                top_p_slider = gr.Slider(minimum=0.0, maximum=1.0, value=settings.TOP_P, step=0.05, label="Top P")
                top_k_slider = gr.Slider(minimum=0, maximum=100, value=settings.TOP_K, step=1, label="Top K")
                frequency_penalty_slider = gr.Slider(minimum=-2.0, maximum=2.0, value=settings.FREQUENCY_PENALTY, step=0.1, label="Frequency Penalty")
                presence_penalty_slider = gr.Slider(minimum=-2.0, maximum=2.0, value=settings.PRESENCE_PENALTY, step=0.1, label="Presence Penalty")
                max_tokens_slider = gr.Slider(minimum=50, maximum=2000, value=settings.MAX_TOKENS, step=50, label="Max Tokens")

                def update_llm_settings(temp, top_p, top_k, freq_penalty, pres_penalty, max_tokens):
                    # Update continuous parameters
                    settings.TEMPERATURE = float(temp)
                    settings.TOP_P = float(top_p)
                    settings.TOP_K = int(top_k)
                    settings.FREQUENCY_PENALTY = float(freq_penalty)
                    settings.PRESENCE_PENALTY = float(pres_penalty)
                    settings.MAX_TOKENS = int(max_tokens)

                    # Map continuous temperature to discrete temp_level used by core APIs
                    try:
                        if settings.TEMPERATURE >= 0.66:
                            temp_level_int = 2
                        elif settings.TEMPERATURE >= 0.33:
                            temp_level_int = 1
                        else:
                            temp_level_int = 0
                    except Exception:
                        temp_level_int = 0

                    settings.temp_level = temp_level_int

                    # Persist to .env for next launch
                    settings.update_env_llm_settings(temp, top_p, top_k, freq_penalty, pres_penalty, max_tokens)
                    settings.update_env_setting("TEMP_LEVEL", str(temp_level_int))

                    print(
                        f"[Web-UI] LLM settings updated: Temperature={temp} (level {temp_level_int}), "
                        f"Top P={top_p}, Top K={top_k}, Frequency Penalty={freq_penalty}, "
                        f"Presence Penalty={pres_penalty}, Max Tokens={max_tokens}"
                    )
                    return "✅ LLM settings saved!"

                save_llm_button = gr.Button("Save LLM Settings")
                llm_save_status = gr.Textbox(label="Status", interactive=False)
                save_llm_button.click(
                    fn=update_llm_settings,
                    inputs=[temperature_slider, top_p_slider, top_k_slider, frequency_penalty_slider, presence_penalty_slider, max_tokens_slider],
                    outputs=llm_save_status
                )

            with gr.Column():
                gr.Markdown("### Preset Management")
                # Initialize with empty choices to avoid circular import, will be populated later
                preset_dropdown = gr.Dropdown(choices=[], label="Select Preset", value=settings.PRESET_NAME)
                load_preset_button = gr.Button("Load Preset")
                preset_status = gr.Textbox(label="Preset Status", interactive=False)

                def load_preset(preset_name):
                    settings.PRESET_NAME = preset_name
                    settings.update_env_preset_name(preset_name)
                    print(f"[Web-UI] Preset loaded: {preset_name}")
                    return f"✅ Preset {preset_name} loaded!"

                def refresh_preset_dropdown():
                    """Refresh the preset dropdown with current choices"""
                    try:
                        choices = settings.get_preset_list()
                        return gr.Dropdown(choices=choices, value=settings.PRESET_NAME)
                    except Exception as e:
                        print(f"[Web-UI] Error refreshing preset dropdown: {e}")
                        return gr.Dropdown(choices=["Default"], value="Default")

                load_preset_button.click(
                    fn=load_preset,
                    inputs=preset_dropdown,
                    outputs=preset_status
                )
                
                # Add a refresh button for presets
                refresh_preset_button = gr.Button("🔄 Refresh Presets")
                refresh_preset_button.click(
                    fn=refresh_preset_dropdown,
                    outputs=preset_dropdown
                )

                gr.Markdown("#### Upload New Preset")
                preset_upload = gr.File(label="Upload Preset File (YAML/JSON)")
                preset_name_input = gr.Textbox(label="Preset Name", placeholder="Enter a name for the uploaded preset")
                upload_preset_button = gr.Button("Upload Preset")
                upload_preset_status = gr.Textbox(label="Upload Status", interactive=False)

                def upload_preset(file, preset_name):
                    if file is None:
                        return "❌ No file uploaded."
                    try:
                        import os
                        preset_path = os.path.join('OOBA_Presets', f"{preset_name}.yaml")
                        with open(file.name, 'r') as f:
                            content = f.read()
                        with open(preset_path, 'w') as f:
                            f.write(content)
                        settings.update_env_preset_name(preset_name)
                        print(f"[Web-UI] Preset uploaded: {preset_name}")
                        return f"✅ Preset {preset_name} uploaded successfully!"
                    except Exception as e:
                        return f"❌ Error uploading preset: {str(e)}"

                upload_preset_button.click(
                    fn=upload_preset,
                    inputs=[preset_upload, preset_name_input],
                    outputs=upload_preset_status
                )

        with gr.Row():
            with gr.Column():
                gr.Markdown("### Character Card Management")
                character_card_upload = gr.File(label="Upload Character Card (YAML/JSON)")
                upload_card_button = gr.Button("Upload Character Card")
                card_status = gr.Textbox(label="Card Upload Status", interactive=False)

                def upload_character_card(file):
                    if file is None:
                        return "❌ No file uploaded."
                    try:
                        import os
                        card_path = os.path.join('Configurables', 'CharacterCard.yaml')
                        with open(file.name, 'r') as f:
                            content = f.read()
                        with open(card_path, 'w') as f:
                            f.write(content)
                        print(f"[Web-UI] Character card uploaded: {card_path}")
                        return "✅ Character card uploaded successfully!"
                    except Exception as e:
                        return f"❌ Error uploading character card: {str(e)}"

                upload_card_button.click(
                    fn=upload_character_card,
                    inputs=character_card_upload,
                    outputs=card_status
                )

                gr.Markdown("#### Current Character Card")
                current_card_button = gr.Button("View Current Character Card")
                current_card_content = gr.Textbox(label="Current Character Card", interactive=False, lines=10)

                def view_current_card():
                    try:
                        import os
                        card_path = os.path.join('Configurables', 'CharacterCard.yaml')
                        if os.path.exists(card_path):
                            with open(card_path, 'r') as f:
                                content = f.read()
                            return content
                        else:
                            return "❌ Character card not found."
                    except Exception as e:
                        return f"❌ Error reading character card: {str(e)}"

                current_card_button.click(
                    fn=view_current_card,
                    outputs=current_card_content
                )

    # === Advanced Fallback Diagnostics and Model Management Endpoints ===
    def get_system_info_ui():
        """Expose system info for diagnostics via Web UI."""
        if not FALLBACK_API_AVAILABLE:
            return "❌ Fallback API not available"
        return get_system_status()

    def get_available_vram_gb_ui():
        """Expose available VRAM in GB for diagnostics via Web UI."""
        if not FALLBACK_API_AVAILABLE:
            return 0.0
        return get_available_vram_gb()

    def estimate_model_vram_requirement_ui(model_name, quantization="fp16"):
        """Expose VRAM requirement estimation for a given model via Web UI."""
        if not FALLBACK_API_AVAILABLE:
            return 0.0
        return estimate_model_vram_requirement(model_name, quantization)

    def check_model_compatibility_ui(model_name):
        """Expose model compatibility check for diagnostics via Web UI."""
        if not FALLBACK_API_AVAILABLE:
            return False, "Fallback API not available", 0.0
        return check_model_compatibility(model_name)

    def discover_models_ui():
        """Expose model discovery for advanced fallback management via Web UI."""
        if not FALLBACK_API_AVAILABLE:
            return []
        return discover_models()

    def get_model_info_ui(model_name):
        """Expose detailed model info for diagnostics via Web UI."""
        if not FALLBACK_API_AVAILABLE:
            return {"error": "Fallback API not available"}
        return get_model_info(model_name)

    # Add after other settings panels, in the settings/diagnostics tab
    with gr.Tab("Advanced Fallback Diagnostics"):
        gr.Markdown("## Advanced Fallback Diagnostics & Model Management")
        gr.Markdown("View system status, available VRAM, fallback model info, and test model compatibility.")

        system_status_box = gr.Textbox(label="System Status", interactive=False, lines=10)
        vram_box = gr.Textbox(label="Available VRAM (GB)", interactive=False)
        models_box = gr.Textbox(label="Discovered Fallback Models", interactive=False, lines=6)
        model_name_input = gr.Textbox(label="Model Name for Compatibility Test")
        model_compat_box = gr.Textbox(label="Model Compatibility Result", interactive=False, lines=4)
        refresh_button = gr.Button("Refresh Diagnostics")
        test_compat_button = gr.Button("Test Model Compatibility")

        def refresh_fallback_diagnostics():
            return (
                get_system_status(),
                str(get_available_vram_gb()),
                json.dumps(discover_and_analyze_models(), indent=2)
            )

        refresh_button.click(
            fn=refresh_fallback_diagnostics,
            outputs=[system_status_box, vram_box, models_box]
        )

        def test_model_compat(model_name):
            return test_model_compatibility(model_name)

        test_compat_button.click(
            fn=test_model_compat,
            inputs=model_name_input,
            outputs=model_compat_box
        )

    # Advanced Fallback Management Tab
    with gr.Tab("Advanced Fallback Management"):
        gr.Markdown("## Advanced Fallback Model Management & Optimization")
        gr.Markdown("Manage fallback models, optimize VRAM usage, and configure advanced fallback settings.")

        # Model Management Section
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Model Management")
                current_model_display = gr.Textbox(label="Current Active Model", interactive=False)
                model_list_display = gr.Textbox(label="Available Models", interactive=False, lines=8)
                refresh_models_button = gr.Button("🔄 Refresh Model List")
                
                with gr.Row():
                    switch_model_input = gr.Textbox(label="Model Name to Switch To")
                    switch_model_button = gr.Button("🔄 Switch Model")
                
                switch_result = gr.Textbox(label="Switch Result", interactive=False, lines=2)

        # VRAM Optimization Section
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### VRAM Optimization")
                vram_usage_display = gr.Textbox(label="Current VRAM Usage", interactive=False)
                vram_optimization_status = gr.Textbox(label="Optimization Status", interactive=False)
                
                with gr.Row():
                    optimize_vram_button = gr.Button("⚡ Optimize VRAM")
                    auto_optimize_checkbox = gr.Checkbox(label="Auto-optimize VRAM", value=False)
                
                optimization_result = gr.Textbox(label="Optimization Result", interactive=False, lines=3)

        # Advanced Settings Section
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Advanced Settings")
                
                with gr.Row():
                    fallback_timeout_input = gr.Number(label="Fallback Timeout (seconds)", value=30, minimum=5, maximum=120)
                    max_retries_input = gr.Number(label="Max Retries", value=3, minimum=1, maximum=10)
                
                with gr.Row():
                    enable_auto_switch = gr.Checkbox(label="Auto-switch on failure", value=True)
                    enable_vram_monitoring = gr.Checkbox(label="Monitor VRAM usage", value=True)
                
                with gr.Row():
                    save_advanced_settings_button = gr.Button("💾 Save Advanced Settings")
                    reset_advanced_settings_button = gr.Button("🔄 Reset to Defaults")
                
                advanced_settings_result = gr.Textbox(label="Settings Result", interactive=False, lines=2)

        # Model Performance Testing
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Model Performance Testing")
                test_model_input = gr.Textbox(label="Model to Test")
                test_prompt_input = gr.Textbox(label="Test Prompt", value="Hello, how are you today?", lines=2)
                
                with gr.Row():
                    run_performance_test_button = gr.Button("🧪 Run Performance Test")
                    benchmark_all_models_button = gr.Button("📊 Benchmark All Models")
                
                performance_result = gr.Textbox(label="Performance Test Result", interactive=False, lines=6)

        # Event handlers for Advanced Fallback Management
        def refresh_model_list():
            try:
                if not FALLBACK_API_AVAILABLE:
                    return "Fallback API not available", "Fallback API not available"
                
                models = discover_models()
                current_model = get_current_fallback_model()
                
                model_info = []
                for model in models:
                    compat, reason, vram_req = check_model_compatibility(model)
                    status = "✅ Compatible" if compat else "❌ Incompatible"
                    model_info.append(f"{model}: {status} ({vram_req:.1f}GB VRAM)")
                
                return current_model, "\n".join(model_info)
            except Exception as e:
                return f"Error: {e}", f"Error refreshing models: {e}"

        def switch_fallback_model(model_name):
            try:
                if not FALLBACK_API_AVAILABLE:
                    return "Fallback API not available"
                
                success = switch_fallback_model_advanced(model_name)
                if success:
                    return f"✅ Successfully switched to {model_name}"
                else:
                    return f"❌ Failed to switch to {model_name}"
            except Exception as e:
                return f"❌ Error switching model: {e}"

        def optimize_vram_usage():
            try:
                if not FALLBACK_API_AVAILABLE:
                    return "Fallback API not available", "Fallback API not available"
                
                result = optimize_vram_advanced()
                return result, "VRAM optimization completed"
            except Exception as e:
                return f"❌ Error optimizing VRAM: {e}", f"Error: {e}"

        def save_advanced_fallback_settings(timeout, retries, auto_switch, vram_monitoring):
            try:
                # Save to environment or config file
                from utils.settings import update_env_setting
                update_env_setting("FALLBACK_TIMEOUT", str(timeout))
                update_env_setting("FALLBACK_MAX_RETRIES", str(retries))
                update_env_setting("FALLBACK_AUTO_SWITCH", "ON" if auto_switch else "OFF")
                update_env_setting("FALLBACK_VRAM_MONITORING", "ON" if vram_monitoring else "OFF")
                
                return "✅ Advanced fallback settings saved successfully"
            except Exception as e:
                return f"❌ Error saving settings: {e}"

        def reset_advanced_fallback_settings():
            try:
                from utils.settings import update_env_setting
                update_env_setting("FALLBACK_TIMEOUT", "30")
                update_env_setting("FALLBACK_MAX_RETRIES", "3")
                update_env_setting("FALLBACK_AUTO_SWITCH", "ON")
                update_env_setting("FALLBACK_VRAM_MONITORING", "ON")
                
                return "✅ Advanced fallback settings reset to defaults"
            except Exception as e:
                return f"❌ Error resetting settings: {e}"

        def run_model_performance_test(model_name, test_prompt):
            try:
                if not FALLBACK_API_AVAILABLE:
                    return "Fallback API not available"
                
                result = benchmark_model_performance(model_name, test_prompt)
                return result
            except Exception as e:
                return f"❌ Error running performance test: {e}"

        def benchmark_all_available_models():
            try:
                if not FALLBACK_API_AVAILABLE:
                    return "Fallback API not available"
                
                result = benchmark_all_models_advanced()
                return result
            except Exception as e:
                return f"❌ Error benchmarking models: {e}"

        # Connect event handlers
        refresh_models_button.click(
            fn=refresh_model_list,
            outputs=[current_model_display, model_list_display]
        )

        switch_model_button.click(
            fn=switch_fallback_model,
            inputs=switch_model_input,
            outputs=switch_result
        )

        optimize_vram_button.click(
            fn=optimize_vram_usage,
            outputs=[vram_usage_display, optimization_result]
        )

        save_advanced_settings_button.click(
            fn=save_advanced_fallback_settings,
            inputs=[fallback_timeout_input, max_retries_input, enable_auto_switch, enable_vram_monitoring],
            outputs=advanced_settings_result
        )

        reset_advanced_settings_button.click(
            fn=reset_advanced_fallback_settings,
            outputs=advanced_settings_result
        )

        run_performance_test_button.click(
            fn=run_model_performance_test,
            inputs=[test_model_input, test_prompt_input],
            outputs=performance_result
        )

        benchmark_all_models_button.click(
            fn=benchmark_all_available_models,
            outputs=performance_result
        )

        # Initialize the interface
        refresh_models_button.click()  # Auto-refresh on load

    # System Health Monitoring Tab
    with gr.Tab("System Health Monitor"):
        gr.Markdown("## Fallback System Health & Performance Monitoring")
        gr.Markdown("Monitor system health, performance metrics, and get optimization recommendations.")

        # Health Overview Section
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### System Health Overview")
                health_score_display = gr.Textbox(label="Health Score", interactive=False)
                health_status_display = gr.Textbox(label="Health Status", interactive=False)
                current_model_display_health = gr.Textbox(label="Current Model", interactive=False)
                optimal_model_display = gr.Textbox(label="Optimal Model", interactive=False)
                
                refresh_health_button = gr.Button("🔄 Refresh Health Status")
                optimize_system_button = gr.Button("⚡ Auto-Optimize System")

        # Performance Metrics Section
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Performance Metrics")
                vram_usage_display_health = gr.Textbox(label="VRAM Usage", interactive=False)
                system_memory_display = gr.Textbox(label="System Memory", interactive=False)
                cpu_info_display = gr.Textbox(label="CPU Information", interactive=False)
                gpu_status_display = gr.Textbox(label="GPU Status", interactive=False)

        # Recommendations Section
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Optimization Recommendations")
                recommendations_display = gr.Textbox(label="Recommendations", interactive=False, lines=6)
                
                with gr.Row():
                    run_health_check_button = gr.Button("🔍 Run Health Check")
                    get_performance_stats_button = gr.Button("📊 Get Performance Stats")

        # Performance Monitoring Section
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Performance Monitoring")
                monitoring_duration_input = gr.Number(label="Monitoring Duration (seconds)", value=60, minimum=10, maximum=300)
                
                with gr.Row():
                    start_monitoring_button = gr.Button("📈 Start Monitoring")
                    stop_monitoring_button = gr.Button("⏹️ Stop Monitoring")
                
                monitoring_results_display = gr.Textbox(label="Monitoring Results", interactive=False, lines=8)

        # Event handlers for System Health Monitoring
        def refresh_system_health():
            try:
                if not FALLBACK_API_AVAILABLE:
                    return "Fallback API not available", "Fallback API not available", "Fallback API not available", "Fallback API not available"
                
                from API.fallback_api import get_fallback_system_health
                health_data = get_fallback_system_health()
                
                if "error" in health_data:
                    return f"Error: {health_data['error']}", "Error", "Error", "Error"
                
                health_score = f"{health_data['health_score']}/100"
                health_status = health_data['health_status']
                current_model = health_data['current_model']
                optimal_model = health_data['optimal_model']
                
                return health_score, health_status, current_model, optimal_model
            except Exception as e:
                return f"Error: {e}", "Error", "Error", "Error"

        def auto_optimize_system():
            try:
                if not FALLBACK_API_AVAILABLE:
                    return "Fallback API not available"
                
                from API.fallback_api import optimize_fallback_model_selection
                result = optimize_fallback_model_selection()
                
                if result["status"] == "success":
                    return f"✅ System optimized! Selected: {result['selected_model']}\nReason: {result['reason']}"
                elif result["status"] == "warning":
                    return f"⚠️ {result['reason']}"
                else:
                    return f"❌ Optimization failed: {result.get('error', 'Unknown error')}"
            except Exception as e:
                return f"❌ Error optimizing system: {e}"

        def get_system_metrics():
            try:
                if not FALLBACK_API_AVAILABLE:
                    return "Fallback API not available", "Fallback API not available", "Fallback API not available", "Fallback API not available"
                
                from API.fallback_api import get_system_info, get_available_vram_gb
                
                system_info = get_system_info()
                available_vram = get_available_vram_gb()
                
                vram_usage = f"{available_vram:.1f}GB available"
                system_memory = f"{system_info.get('memory_total_gb', 0):.1f}GB total, {system_info.get('memory_available_gb', 0):.1f}GB available"
                cpu_info = f"{system_info.get('cpu_cores', 0)} cores, {system_info.get('cpu_model', 'Unknown')}"
                gpu_status = "Available" if system_info.get('gpu_available', False) else "Not available"
                
                return vram_usage, system_memory, cpu_info, gpu_status
            except Exception as e:
                return f"Error: {e}", f"Error: {e}", f"Error: {e}", f"Error: {e}"

        def get_optimization_recommendations():
            try:
                if not FALLBACK_API_AVAILABLE:
                    return "Fallback API not available"
                
                from API.fallback_api import get_fallback_system_health
                health_data = get_fallback_system_health()
                
                if "error" in health_data:
                    return f"Error getting recommendations: {health_data['error']}"
                
                recommendations = health_data.get('recommendations', [])
                if recommendations:
                    return "\n".join([f"• {rec}" for rec in recommendations])
                else:
                    return "No recommendations at this time."
            except Exception as e:
                return f"Error getting recommendations: {e}"

        def start_performance_monitoring(duration):
            try:
                if not FALLBACK_API_AVAILABLE:
                    return "Fallback API not available"
                
                from API.fallback_api import monitor_fallback_performance
                monitoring_data = monitor_fallback_performance(duration)
                
                if "error" in monitoring_data:
                    return f"Error starting monitoring: {monitoring_data['error']}"
                
                result = f"Monitoring started at {monitoring_data['start_time']}\n"
                result += f"Duration: {monitoring_data['duration_seconds']} seconds\n"
                result += f"Status: {monitoring_data.get('status', 'Unknown')}\n"
                
                return result
            except Exception as e:
                return f"Error starting monitoring: {e}"

        # Connect event handlers
        refresh_health_button.click(
            fn=refresh_system_health,
            outputs=[health_score_display, health_status_display, current_model_display_health, optimal_model_display]
        )

        optimize_system_button.click(
            fn=auto_optimize_system,
            outputs=recommendations_display
        )

        run_health_check_button.click(
            fn=get_system_metrics,
            outputs=[vram_usage_display_health, system_memory_display, cpu_info_display, gpu_status_display]
        )

        get_performance_stats_button.click(
            fn=get_optimization_recommendations,
            outputs=recommendations_display
        )

        start_monitoring_button.click(
            fn=start_performance_monitoring,
            inputs=monitoring_duration_input,
            outputs=monitoring_results_display
        )

        # Initialize the health interface
        refresh_health_button.click()  # Auto-refresh on load

# Advanced Fallback Management Support Functions
def get_current_fallback_model():
    """Get the currently active fallback model"""
    if not FALLBACK_API_AVAILABLE:
        return "Fallback API not available"
    
    try:
        from API.fallback_api import get_fallback_llm
        llm = get_fallback_llm()
        return llm.model_name if llm else "No model loaded"
    except Exception as e:
        return f"Error getting current model: {e}"

def switch_fallback_model_advanced(model_name):
    """Advanced model switching with validation"""
    if not FALLBACK_API_AVAILABLE:
        return False
    
    try:
        from API.fallback_api import switch_fallback_model
        success = switch_fallback_model(model_name)
        return success
    except Exception as e:
        print(f"Error switching fallback model: {e}")
        return False

def optimize_vram_advanced():
    """Advanced VRAM optimization with detailed reporting"""
    if not FALLBACK_API_AVAILABLE:
        return "Fallback API not available"
    
    try:
        import psutil
        import GPUtil
        
        # Get current VRAM usage
        try:
            import torch
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    current_vram = gpus[0].memoryUsed
                    total_vram = gpus[0].memoryTotal
                    vram_percent = (current_vram / total_vram) * 100
                    current_status = f"Current VRAM: {current_vram:.1f}GB / {total_vram:.1f}GB ({vram_percent:.1f}%)"
                else:
                    current_status = "GPU not detected"
            except ImportError:
                # Fallback to torch if GPUtil not available
                if torch.cuda.is_available():
                    total_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    allocated_vram = torch.cuda.memory_allocated(0) / (1024**3)
                    current_status = f"Current VRAM: {allocated_vram:.1f}GB / {total_vram:.1f}GB"
                else:
                    current_status = "GPU not detected"
        except Exception:
            current_status = "VRAM monitoring not available"
        
        # Get available models and their VRAM requirements
        models = discover_models()
        available_vram = get_available_vram_gb()
        
        optimization_suggestions = []
        
        for model in models:
            compat, reason, vram_req = check_model_compatibility(model)
            if compat and vram_req <= available_vram:
                optimization_suggestions.append(f"✅ {model}: {vram_req:.1f}GB (compatible)")
            elif compat:
                optimization_suggestions.append(f"⚠️ {model}: {vram_req:.1f}GB (needs {vram_req - available_vram:.1f}GB more)")
            else:
                optimization_suggestions.append(f"❌ {model}: {reason}")
        
        # Find optimal model
        optimal_model = None
        for model in models:
            compat, reason, vram_req = check_model_compatibility(model)
            if compat and vram_req <= available_vram:
                if optimal_model is None or vram_req < check_model_compatibility(optimal_model)[2]:
                    optimal_model = model
        
        result = f"{current_status}\n\nAvailable VRAM: {available_vram:.1f}GB\n\n"
        result += "Model Compatibility:\n" + "\n".join(optimization_suggestions) + "\n\n"
        
        if optimal_model:
            result += f"Recommended model: {optimal_model}"
            # Auto-switch to optimal model if different from current
            current_model = get_current_fallback_model()
            if current_model != optimal_model:
                switch_fallback_model_advanced(optimal_model)
                result += f"\n✅ Auto-switched to {optimal_model}"
        else:
            result += "No compatible models found with current VRAM"
        
        return result
        
    except Exception as e:
        return f"Error optimizing VRAM: {e}"

def benchmark_model_performance(model_name, test_prompt):
    """Benchmark a specific model's performance"""
    if not FALLBACK_API_AVAILABLE:
        return "Fallback API not available"
    
    try:
        import time
        # Check model compatibility first
        compat, reason, vram_req = check_model_compatibility(model_name)
        if not compat:
            return f"Model {model_name} is not compatible: {reason}"
        
        # Test generation performance
        start_time = time.time()
        response = test_fallback_generation(model_name, test_prompt)
        end_time = time.time()
        
        response_time = end_time - start_time
        response_length = len(response) if response else 0
        
        # Calculate tokens per second (rough estimate)
        tokens_per_second = response_length / response_time if response_time > 0 else 0
        
        result = f"Performance Test Results for {model_name}:\n"
        result += f"Response Time: {response_time:.2f} seconds\n"
        result += f"Response Length: {response_length} characters\n"
        result += f"Speed: {tokens_per_second:.1f} chars/second\n"
        result += f"VRAM Requirement: {vram_req:.1f}GB\n"
        result += f"Compatibility: ✅ Compatible\n\n"
        result += f"Test Response: {response[:200]}{'...' if len(response) > 200 else ''}"
        
        return result
        
    except Exception as e:
        return f"Error benchmarking {model_name}: {e}"

def test_fallback_generation(model_name, prompt):
    """Test fallback generation with a specific model"""
    if not FALLBACK_API_AVAILABLE:
        return "Fallback API not available"
    
    try:
        from API.fallback_api import get_fallback_llm
        
        # Switch to the specified model
        llm = get_fallback_llm()
        if llm:
            llm.switch_model(model_name)
            
            # Test generation
            messages = [{"role": "user", "content": prompt}]
            response = llm.generate(messages, max_tokens=100, temperature=0.7)
            
            if isinstance(response, dict) and "content" in response:
                return response["content"]
            elif isinstance(response, str):
                return response
            else:
                return "No response generated"
        else:
            return "Fallback LLM not available"
            
    except Exception as e:
        return f"Error testing generation: {e}"

def launch_demo():
    """Launch Gradio with enhanced error handling, port conflict detection, and automatic fallback"""
    import socket
    import time
    from dotenv import load_dotenv
    
    # Ensure environment variables are loaded
    load_dotenv()
    
    # Ensure settings are initialized
    try:
        from utils import settings
        if not hasattr(settings, 'WEB_UI_PORT'):
            print("⚠️ Settings not initialized. Loading defaults...")
            settings.WEB_UI_PORT = int(os.getenv('WEB_UI_PORT', 7860))
            settings.WEB_UI_SHARE = os.getenv('WEB_UI_SHARE', 'OFF').upper() == 'ON'
            settings.MAX_RESPONSE_LENGTH = int(os.getenv('MAX_RESPONSE_LENGTH', 500))
            settings.CHAT_HISTORY_LIMIT = int(os.getenv('CHAT_HISTORY_LIMIT', 50))
            settings.AUTO_SAVE_INTERVAL = int(os.getenv('AUTO_SAVE_INTERVAL', 5))
    except Exception as e:
        print(f"❌ Error initializing settings: {e}")
        print("💡 Using default values")
        settings.WEB_UI_PORT = 7860
        settings.WEB_UI_SHARE = False
        settings.MAX_RESPONSE_LENGTH = 500
        settings.CHAT_HISTORY_LIMIT = 50
        settings.AUTO_SAVE_INTERVAL = 5
    
    def is_port_in_use(port):
        """Check if a port is already in use"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return False
            except OSError:
                return True
    
    def find_available_port(start_port, max_attempts=10):
        """Find an available port starting from start_port"""
        for i in range(max_attempts):
            port = start_port + i
            if not is_port_in_use(port):
                return port
        return None
    
    # Get the configured port
    configured_port = settings.WEB_UI_PORT
    
    # Check if the configured port is available
    if is_port_in_use(configured_port):
        print(f"⚠️ Port {configured_port} is already in use. Searching for available port...")
        
        # Try to find an available port
        available_port = find_available_port(configured_port)
        
        if available_port:
            print(f"✅ Found available port: {available_port}")
            # Update the settings to use the available port
            settings.WEB_UI_PORT = available_port
            # Update environment variable
            try:
                from utils.settings import update_env_setting
                update_env_setting("WEB_UI_PORT", str(available_port))
                print(f"🔧 Updated WEB_UI_PORT to {available_port}")
            except Exception as e:
                print(f"⚠️ Could not update environment variable: {e}")
        else:
            print(f"❌ Could not find available port starting from {configured_port}")
            print("💡 Please close other applications using these ports or manually set WEB_UI_PORT in your .env file")
            return
    
    # Wait a moment for any port conflicts to resolve
    time.sleep(1)
    
    # Launch Gradio with comprehensive error handling
    try:
        print(f"🚀 Launching Web UI on port {settings.WEB_UI_PORT}...")
        
        # Populate preset dropdown after module is fully loaded to avoid circular import
        try:
            preset_choices = settings.get_preset_list()
            print(f"[Web-UI] Loaded {len(preset_choices)} preset choices")
        except Exception as e:
            print(f"[Web-UI] Warning: Could not load preset list: {e}")
            preset_choices = ["Default"]
        
        # Launch with specific port and enhanced error handling
        demo.launch(
            server_name="127.0.0.1",  # Bind to localhost only
            server_port=settings.WEB_UI_PORT,
            inbrowser=True, 
            share=settings.WEB_UI_SHARE,
            quiet=False,  # Show launch messages for debugging
            show_error=True  # Show detailed error messages
        )
        
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {settings.WEB_UI_PORT} is still in use despite our check.")
            print("💡 This might be a race condition. Please:")
            print("   1. Close any other applications using this port")
            print("   2. Wait a moment and restart Z-WAIF")
            print("   3. Or manually set WEB_UI_PORT to a different port in your .env file")
        else:
            print(f"❌ OS Error launching Web UI: {e}")
            print("💡 This might be a permission issue or system resource problem")
            
    except Exception as e:
        error_msg = str(e).lower()
        
        if "conflict" in error_msg:
            print("❌ Gradio server conflict detected.")
            print("💡 Another Gradio instance might be running. Please:")
            print("   1. Close any other Gradio applications")
            print("   2. Check for other Z-WAIF instances")
            print("   3. Restart your system if the issue persists")
        elif "permission" in error_msg:
            print("❌ Permission error launching Web UI.")
            print("💡 Try running Z-WAIF as administrator or check firewall settings")
        elif "memory" in error_msg or "resource" in error_msg:
            print("❌ Resource error launching Web UI.")
            print("💡 Your system might be low on memory or resources")
        else:
            print(f"❌ Unexpected error launching Web UI: {e}")
            print("💡 This might be a Gradio version compatibility issue")
            print("   Try updating Gradio: pip install --upgrade gradio")
        
        # Log the error for debugging
        try:
            from utils import zw_logging
            zw_logging.log_error(f"Web UI launch failed: {e}")
        except:
            pass  # Don't fail if logging is not available

