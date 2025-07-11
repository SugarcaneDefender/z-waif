#!/usr/bin/env python3
"""
Setup script for TinyLlama GGUF model in Z-Waif fallback system.
This script ensures the optimal GGUF model is available for local inference.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed."""
    missing_deps = []
    
    try:
        import torch
        logger.info(f"✅ PyTorch {torch.__version__} available")
    except ImportError:
        missing_deps.append("torch")
    
    try:
        import huggingface_hub
        logger.info(f"✅ Hugging Face Hub available")
    except ImportError:
        missing_deps.append("huggingface_hub")
    
    try:
        import requests
        logger.info("✅ Requests available")
    except ImportError:
        missing_deps.append("requests")
    
    if missing_deps:
        logger.error(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        logger.error("Please install them with: pip install " + " ".join(missing_deps))
        return False
    
    return True

def get_system_info():
    """Get basic system information for model compatibility."""
    try:
        import psutil
        
        memory_gb = round(psutil.virtual_memory().total / (1024**3), 2)
        available_gb = round(psutil.virtual_memory().available / (1024**3), 2)
        
        info = {
            "total_memory_gb": memory_gb,
            "available_memory_gb": available_gb,
            "platform": sys.platform
        }
        
        # Check GPU
        try:
            import torch
            if torch.cuda.is_available():
                info["gpu_available"] = True
                info["gpu_memory_gb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
            else:
                info["gpu_available"] = False
        except:
            info["gpu_available"] = False
        
        return info
    except ImportError:
        logger.warning("psutil not available, cannot get detailed system info")
        return {"total_memory_gb": 4.0, "available_memory_gb": 2.0, "platform": sys.platform}

def download_tinyllama_gguf():
    """Download the TinyLlama GGUF model."""
    model_path = Path("models/tinyllama-1.1b-chat-v1.0.Q4_0.gguf")
    model_dir = model_path.parent
    
    # Create models directory
    model_dir.mkdir(exist_ok=True)
    logger.info(f"Created models directory: {model_dir}")
    
    # Check if already exists
    if model_path.exists():
        size_mb = round(model_path.stat().st_size / (1024*1024), 1)
        logger.info(f"✅ TinyLlama GGUF already exists: {model_path} ({size_mb} MB)")
        return str(model_path)
    
    logger.info("📥 Downloading TinyLlama GGUF model...")
    
    # HuggingFace download method
    try:
        from huggingface_hub import hf_hub_download
        
        repo_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        filename = "tinyllama-1.1b-chat-v1.0.Q4_0.gguf"
        
        logger.info(f"Downloading {filename} from {repo_id}...")
        logger.info("This may take a few minutes (model is ~700MB)...")
        
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=str(model_dir),
            local_dir_use_symlinks=False
        )
        
        final_path = model_dir / filename
        if Path(downloaded_path) != final_path:
            import shutil
            shutil.move(downloaded_path, final_path)
        
        size_mb = round(final_path.stat().st_size / (1024*1024), 1)
        logger.info(f"✅ Successfully downloaded: {final_path} ({size_mb} MB)")
        return str(final_path)
        
    except Exception as e:
        logger.error(f"❌ Hugging Face download failed: {e}")
        
        # Fallback to direct download
        try:
            import requests
            
            url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
            logger.info(f"Trying direct download from: {url}")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(model_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\rProgress: {percent:.1f}%", end="", flush=True)
            
            print()  # New line after progress
            size_mb = round(model_path.stat().st_size / (1024*1024), 1)
            logger.info(f"✅ Successfully downloaded: {model_path} ({size_mb} MB)")
            return str(model_path)
            
        except Exception as download_error:
            logger.error(f"❌ Direct download also failed: {download_error}")
            logger.error("Please check your internet connection and try again")
            return None

def update_env_settings(model_path):
    """Update .env file with the fallback model path."""
    env_file = Path(".env")
    
    try:
        # Read existing .env
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Update or add API_FALLBACK_MODEL
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('API_FALLBACK_MODEL='):
                lines[i] = f'API_FALLBACK_MODEL={model_path}\n'
                updated = True
                break
        
        if not updated:
            lines.append(f'API_FALLBACK_MODEL={model_path}\n')
        
        # Write back
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        logger.info(f"✅ Updated .env with fallback model: {model_path}")
        
    except Exception as e:
        logger.error(f"❌ Failed to update .env file: {e}")

def test_model_loading():
    """Test if the model can be loaded successfully."""
    try:
        from API.fallback_api import get_fallback_llm, get_system_info
        
        logger.info("🧪 Testing model loading...")
        
        # Get system info
        system_info = get_system_info()
        logger.info(f"System: {system_info.get('memory_available_gb', 0):.1f}GB RAM available")
        
        # Try to initialize the fallback LLM
        llm = get_fallback_llm()
        
        # Test a simple generation
        test_messages = [
            {"role": "user", "content": "Hello! Say hi back in one word."}
        ]
        
        response = llm.generate(test_messages, max_new_tokens=10)
        logger.info(f"✅ Model test successful! Response: {response[:50]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Model test failed: {e}")
        logger.info("The model was downloaded but may need different dependencies")
        return False

def main():
    """Main setup function."""
    logger.info("🚀 Z-Waif TinyLlama GGUF Model Setup")
    logger.info("=" * 50)
    
    # Check system
    system_info = get_system_info()
    logger.info(f"System: {system_info['platform']}")
    logger.info(f"RAM: {system_info['available_memory_gb']:.1f}GB available / {system_info['total_memory_gb']:.1f}GB total")
    
    if system_info.get('gpu_available'):
        logger.info(f"GPU: Available ({system_info.get('gpu_memory_gb', 0):.1f}GB VRAM)")
    else:
        logger.info("GPU: Not available (will use CPU)")
    
    # Check if we have enough memory (TinyLlama needs ~1GB)
    if system_info['available_memory_gb'] < 1.5:
        logger.warning("⚠️ Low memory detected. Model may run slowly or fail to load.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            logger.info("Setup cancelled.")
            return
    
    # Check dependencies
    if not check_dependencies():
        logger.error("❌ Missing dependencies. Please install requirements.txt first.")
        return
    
    # Download model
    model_path = download_tinyllama_gguf()
    if not model_path:
        logger.error("❌ Failed to download model")
        return
    
    # Update settings
    update_env_settings(model_path)
    
    # Test model (optional)
    test_choice = input("\n🧪 Test model loading? (Y/n): ").strip().lower()
    if test_choice != 'n':
        test_model_loading()
    
    logger.info("\n✅ Setup complete!")
    logger.info(f"Model location: {model_path}")
    logger.info("The fallback API is now ready with TinyLlama GGUF model.")
    logger.info("\nTo use it, start Z-Waif normally. The fallback API will activate")
    logger.info("automatically when other AI services are unavailable.")

if __name__ == "__main__":
    main() 