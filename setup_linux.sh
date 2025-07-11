#!/bin/bash

# Z-Waif Linux Setup Script
# This script installs system dependencies and sets up the environment

echo "🚀 Z-Waif Linux Setup Script"
echo "=============================="

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo "❌ Could not detect Linux distribution"
    exit 1
fi

echo "📋 Detected: $OS $VER"

# Function to install dependencies for Ubuntu/Debian
install_ubuntu_deps() {
    echo "📦 Installing Ubuntu/Debian dependencies..."
    sudo apt-get update
    sudo apt-get install -y \
        python3-dev \
        python3-pip \
        python3-venv \
        portaudio19-dev \
        libasound2-dev \
        libportaudio2 \
        libportaudiocpp0 \
        ffmpeg \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        libgcc-s1 \
        build-essential \
        cmake \
        git \
        curl \
        wget
}

# Function to install dependencies for Fedora
install_fedora_deps() {
    echo "📦 Installing Fedora dependencies..."
    sudo dnf update -y
    sudo dnf install -y \
        python3-devel \
        python3-pip \
        portaudio-devel \
        alsa-lib-devel \
        ffmpeg \
        gcc-c++ \
        cmake \
        git \
        curl \
        wget
}

# Function to install dependencies for Arch Linux
install_arch_deps() {
    echo "📦 Installing Arch Linux dependencies..."
    sudo pacman -Syu --noconfirm
    sudo pacman -S --noconfirm \
        python \
        python-pip \
        portaudio \
        alsa-lib \
        ffmpeg \
        base-devel \
        cmake \
        git \
        curl \
        wget
}

# Install dependencies based on distribution
case $ID in
    ubuntu|debian|linuxmint)
        install_ubuntu_deps
        ;;
    fedora)
        install_fedora_deps
        ;;
    arch|manjaro)
        install_arch_deps
        ;;
    *)
        echo "⚠️  Unsupported distribution: $ID"
        echo "Please install the following packages manually:"
        echo "  - python3-dev"
        echo "  - portaudio19-dev"
        echo "  - libasound2-dev"
        echo "  - ffmpeg"
        echo "  - build-essential"
        echo "  - cmake"
        ;;
esac

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install llama-cpp-python with CUDA support if available
echo "🔧 Installing llama-cpp-python..."
if command -v nvidia-smi &> /dev/null; then
    echo "🎮 CUDA detected, installing with GPU support..."
    CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python
else
    echo "💻 No CUDA detected, installing CPU-only version..."
    pip install llama-cpp-python
fi

# Create models directory if it doesn't exist
if [ ! -d "models" ]; then
    echo "📁 Creating models directory..."
    mkdir -p models
fi

# Set up environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    if [ -f "env_example.txt" ]; then
        cp env_example.txt .env
        echo "✅ .env file created from template"
    else
        echo "⚠️  env_example.txt not found, please create .env manually"
    fi
fi

# Set executable permissions for scripts
echo "🔧 Setting executable permissions..."
chmod +x startup.sh
chmod +x startup-mac-linux.sh

echo ""
echo "✅ Linux setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Edit .env file with your settings"
echo "2. Download models to the models/ directory"
echo "3. Run: python main.py"
echo ""
echo "📚 For more information, see README.md"
echo ""
echo "🐧 Happy Linux-ing!" 