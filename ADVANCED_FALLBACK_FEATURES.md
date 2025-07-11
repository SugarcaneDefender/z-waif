# Advanced Fallback Features Documentation

## Overview

The Z-WAIF system now includes comprehensive advanced fallback management features that provide:

- **Model Management**: Switch between different fallback models dynamically
- **VRAM Optimization**: Automatic optimization based on available system resources
- **System Health Monitoring**: Real-time health scoring and recommendations
- **Performance Benchmarking**: Test and compare model performance
- **Advanced Settings**: Configure timeout, retries, and monitoring options

## Web UI Tabs

### 1. Advanced Fallback Diagnostics

**Location**: Settings → Advanced Fallback Diagnostics

**Features**:
- System status overview
- Available VRAM display
- Discovered fallback models list
- Model compatibility testing
- Real-time diagnostics refresh

**Usage**:
1. Click "Refresh Diagnostics" to update system information
2. Enter a model name in "Model Name for Compatibility Test"
3. Click "Test Model Compatibility" to check if a model can run on your system

### 2. Advanced Fallback Management

**Location**: Settings → Advanced Fallback Management

**Features**:
- **Model Management**: View current model, available models, and switch between them
- **VRAM Optimization**: Monitor VRAM usage and optimize model selection
- **Advanced Settings**: Configure timeout, retries, auto-switching, and VRAM monitoring
- **Performance Testing**: Benchmark individual models and test generation speed

**Usage**:

#### Model Management
1. Click "🔄 Refresh Model List" to discover available models
2. Enter a model name in "Model Name to Switch To"
3. Click "🔄 Switch Model" to change the active fallback model

#### VRAM Optimization
1. Click "⚡ Optimize VRAM" to automatically select the best model for your system
2. View current VRAM usage and optimization status
3. Enable "Auto-optimize VRAM" for automatic optimization

#### Advanced Settings
1. Set "Fallback Timeout" (5-120 seconds) - how long to wait before falling back
2. Set "Max Retries" (1-10) - how many times to retry failed requests
3. Enable "Auto-switch on failure" to automatically try different models
4. Enable "Monitor VRAM usage" for real-time VRAM tracking
5. Click "💾 Save Advanced Settings" to apply changes
6. Click "🔄 Reset to Defaults" to restore default settings

#### Performance Testing
1. Enter a model name in "Model to Test"
2. Modify the test prompt if desired
3. Click "🧪 Run Performance Test" to benchmark a specific model
4. Click "📊 Benchmark All Models" to test all available models

### 3. System Health Monitor

**Location**: Settings → System Health Monitor

**Features**:
- **Health Overview**: Real-time health score (0-100) and status
- **Performance Metrics**: VRAM usage, system memory, CPU info, GPU status
- **Optimization Recommendations**: Automatic suggestions for improving performance
- **Performance Monitoring**: Start/stop monitoring sessions

**Usage**:

#### Health Overview
1. Click "🔄 Refresh Health Status" to update health information
2. View health score and status (Excellent/Good/Fair/Poor)
3. Compare current model vs optimal model
4. Click "⚡ Auto-Optimize System" for automatic optimization

#### Performance Metrics
1. Click "🔍 Run Health Check" to get detailed system metrics
2. View VRAM usage, system memory, CPU information, and GPU status

#### Recommendations
1. Click "📊 Get Performance Stats" to see optimization recommendations
2. Follow the suggested actions to improve system performance

#### Performance Monitoring
1. Set monitoring duration (10-300 seconds)
2. Click "📈 Start Monitoring" to begin performance tracking
3. Click "⏹️ Stop Monitoring" to end the session
4. View monitoring results in the results display

## Advanced Features

### Model Performance Statistics

The system tracks detailed performance metrics for each model:

- **Response Time**: How long it takes to generate a response
- **Speed**: Characters generated per second
- **VRAM Requirement**: Memory needed to run the model
- **Compatibility**: Whether the model can run on your system
- **Model Type**: GGUF or Transformers format

### Automatic Model Optimization

The system automatically:

1. **Discovers** available models in the models directory
2. **Checks compatibility** based on available VRAM
3. **Benchmarks performance** of compatible models
4. **Scores models** based on VRAM usage and speed
5. **Selects the optimal model** for your system
6. **Auto-switches** if the current model fails

### System Health Scoring

Health scores are calculated based on:

- **VRAM Availability**: More VRAM = higher score
- **Model Optimization**: Using optimal model = higher score
- **System Resources**: More CPU cores and memory = higher score
- **GPU Availability**: Having a GPU = higher score

**Score Ranges**:
- **80-100**: Excellent - System is well-optimized
- **60-79**: Good - Minor optimizations possible
- **40-59**: Fair - Consider hardware upgrades
- **0-39**: Poor - System may struggle with fallback models

### VRAM Optimization

The system provides:

- **Real-time VRAM monitoring** using GPUtil or PyTorch fallback
- **Model compatibility checking** based on VRAM requirements
- **Automatic model selection** that fits available VRAM
- **Optimization recommendations** for better performance

### Advanced Settings

Configurable parameters:

- **FALLBACK_TIMEOUT**: How long to wait before falling back (default: 30s)
- **FALLBACK_MAX_RETRIES**: Maximum retry attempts (default: 3)
- **FALLBACK_AUTO_SWITCH**: Enable automatic model switching (default: ON)
- **FALLBACK_VRAM_MONITORING**: Enable VRAM monitoring (default: ON)

## Technical Details

### Model Discovery

The system automatically discovers models by:

1. **Scanning the models directory** for .gguf files
2. **Checking environment variables** for HuggingFace models
3. **Validating model compatibility** with system resources
4. **Prioritizing local GGUF models** over remote HuggingFace models

### Performance Benchmarking

Benchmarking includes:

1. **Compatibility testing** - Can the model run on this system?
2. **Speed testing** - How fast does it generate responses?
3. **Memory testing** - How much VRAM does it use?
4. **Quality testing** - How good are the generated responses?

### Health Monitoring

The health monitoring system:

1. **Collects system metrics** (CPU, memory, GPU, VRAM)
2. **Analyzes model performance** (speed, memory usage, compatibility)
3. **Calculates health scores** based on multiple factors
4. **Generates recommendations** for improvement
5. **Tracks performance over time** for trend analysis

## Troubleshooting

### Common Issues

**"Fallback API not available"**
- Ensure the fallback API module is properly installed
- Check that required dependencies are available

**"No compatible models found"**
- Check available VRAM (need at least 2GB for most models)
- Ensure models are properly downloaded to the models directory
- Try downloading smaller models like TinyLlama

**"VRAM optimization failed"**
- Install GPUtil: `pip install GPUtil`
- Or the system will fall back to PyTorch-based monitoring

**"Performance monitoring not implemented"**
- This is a placeholder for future implementation
- Basic monitoring data is still available

### Performance Tips

1. **Use GGUF models** - They're more memory efficient than HuggingFace models
2. **Enable auto-optimization** - Let the system choose the best model automatically
3. **Monitor VRAM usage** - Keep other applications closed to free VRAM
4. **Use smaller models** - TinyLlama (1.1B) is very efficient for most use cases
5. **Enable auto-switching** - Automatically try different models if one fails

### Getting Help

If you encounter issues:

1. **Check the logs** in the Logs directory
2. **Run the test script** - `python test_advanced_fallback_features.py`
3. **Check system requirements** - Ensure you have sufficient VRAM and memory
4. **Update dependencies** - Ensure all required packages are up to date

## Future Enhancements

Planned features include:

- **Real-time performance monitoring** with graphs and charts
- **Model quality assessment** based on response quality
- **Automatic model downloading** for missing models
- **Advanced scheduling** for model switching based on usage patterns
- **Integration with external monitoring tools**
- **Custom model training** and optimization

---

**Note**: These advanced features are designed to work alongside the existing fallback system without removing any current functionality. All advanced features are optional and can be enabled/disabled as needed. 