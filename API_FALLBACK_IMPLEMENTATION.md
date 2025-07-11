# API Fallback System Implementation

## Overview
The API fallback system provides a lightweight local LLM backup when the main API (Oobabooga/Ollama) fails. This ensures continuous operation even when external services are unavailable.

## Features Implemented

### ✅ 1. API Fallback Core System
- **Location**: `API/fallback_api.py`
- **Features**:
  - Lightweight local model loading with transformers
  - 4-bit quantization support for low VRAM usage
  - Model-specific prompt templates
  - Thread-safe model switching
  - Streaming support
  - Error handling and graceful degradation

### ✅ 2. Web UI Controls
- **Location**: `utils/web_ui.py` (Settings tab)
- **Controls**:
  - Enable/Disable API fallback checkbox
  - Model selection dropdown with 5 pre-configured models
  - Host configuration textbox
  - Test button for fallback API
  - Model information display

### ✅ 3. API Controller Integration
- **Location**: `API/api_controller.py`
- **Features**:
  - Automatic fallback when primary API fails
  - Character card integration for fallback
  - Maintains all advanced features (chatpops, relationships, etc.)
  - Proper error handling and logging

### ✅ 4. Settings Management
- **Location**: `utils/settings.py`
- **Settings**:
  - `API_FALLBACK_ENABLED`: Toggle fallback on/off
  - `API_FALLBACK_MODEL`: Selected fallback model
  - `API_FALLBACK_HOST`: Fallback API host configuration
  - Environment variable persistence

### ✅ 5. Main Application Integration
- **Location**: `main.py`
- **Features**:
  - Automatic initialization at startup
  - Primary API health checking
  - Fallback system verification

## Available Fallback Models

| Model | Size | VRAM Usage | Quality | Use Case |
|-------|------|------------|---------|----------|
| **TinyLlama-1.1B-Chat** | 1.1B | ~1.1GB | Basic | Ultra lightweight backup |
| **Phi-2** | 2.7B | ~2.7GB | Good | Best quality/size ratio |
| **Mistral-7B-Instruct** | 7B | ~5GB (4-bit) | Excellent | High quality responses |
| **Neural-Chat-7B** | 7B | ~5GB (4-bit) | Excellent | Alternative to Mistral |
| **Custom** | Variable | Variable | Variable | User-specified models |

## Installation Requirements

The following dependencies have been added to `requirements.txt`:

```txt
# Fallback LLM requirements
transformers>=4.36.0
torch>=2.1.0
accelerate>=0.26.0
bitsandbytes>=0.41.0
sentencepiece>=0.1.99
einops>=0.7.0
safetensors>=0.4.0
optimum>=1.12.0
```

## Usage Instructions

### 1. Enable API Fallback
1. Open the web UI
2. Go to the Settings tab
3. Find the "API Fallback Settings" section
4. Check "Enable API Fallback"

### 2. Select Fallback Model
1. Choose from the dropdown menu
2. Consider your VRAM availability:
   - **Low VRAM (<4GB)**: Use TinyLlama-1.1B-Chat
   - **Medium VRAM (4-8GB)**: Use Phi-2
   - **High VRAM (>8GB)**: Use Mistral-7B or Neural-Chat-7B

### 3. Test the System
1. Click "Test Fallback API" to verify it works
2. The system will automatically use fallback when main API fails

### 4. Monitor Usage
- Check logs for fallback usage messages
- Look for "[API] Successfully used fallback API" in logs

## Technical Details

### Model Loading Strategy
- **Quantization**: 4-bit quantization when bitsandbytes is available
- **Fallback**: Standard loading if quantization fails
- **Memory Management**: Automatic CUDA cache clearing on model switch

### Prompt Templates
Each model has optimized prompt templates:
- **TinyLlama**: `<|system|>`, `<|user|>`, `<|assistant|>` format
- **Phi-2**: "System:", "Human:", "Assistant:" format
- **Mistral**: `[INST]` instruction format
- **Neural-Chat**: `### System:`, `### User:`, `### Assistant:` format

### Error Handling
- Graceful degradation when dependencies are missing
- Automatic fallback to simpler loading methods
- Comprehensive error logging and user feedback

## Testing

Run the test script to verify everything works:

```bash
python test_api_fallback.py
```

This will test:
- Settings configuration
- Fallback API import and initialization
- API controller integration
- Model switching
- Web UI integration

## Troubleshooting

### Common Issues

1. **"No package metadata was found for bitsandbytes"**
   - Solution: Install bitsandbytes or the system will use standard loading
   - Command: `pip install bitsandbytes`

2. **"Accelerate version too old"**
   - Solution: Update accelerate to 0.26.0 or higher
   - Command: `pip install "accelerate>=0.26.0"`

3. **"Repo id must use alphanumeric chars"**
   - Solution: Check that API_FALLBACK_MODEL is set correctly
   - Default: "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

4. **High VRAM usage**
   - Solution: Use a smaller model or enable 4-bit quantization
   - Recommended: TinyLlama-1.1B-Chat for low VRAM systems

### Performance Optimization

1. **For Low VRAM Systems**:
   - Use TinyLlama-1.1B-Chat
   - Ensure 4-bit quantization is working
   - Close other GPU applications

2. **For Better Quality**:
   - Use Phi-2 or larger models
   - Ensure sufficient VRAM (4GB+ for Phi-2, 8GB+ for 7B models)

3. **For Faster Loading**:
   - Models are cached after first load
   - Consider using local model files instead of HuggingFace Hub

## Future Enhancements

Potential improvements for future versions:
- Support for GGUF models via llama.cpp
- Automatic model downloading
- Model performance benchmarking
- Dynamic model selection based on VRAM
- Integration with more model formats

## Conclusion

The API fallback system provides a robust backup solution that ensures Z-Waif continues to function even when the primary API is unavailable. The implementation maintains all advanced features while providing multiple model options for different hardware configurations. 