#!/usr/bin/env bash
if [[ "$1" == "--help" ]]; then
    echo "Usage: $0 [--help] [--reinstall] [--update-pip] [--keep-logs] [--log-file FILE] [--python-binary BIN] [main_file]"
    echo "Options:"
    echo "  --help          Show this help message and exit"
    echo "  --reinstall     Reinstall dependencies"
    echo "  --update-pip    Update pip"
    echo "  --keep-logs     Appends logs to an old log file instead of overwriting it"
    echo "  --log-file      Specify the log file to use (default: log.txt)"
    echo "  --python-binary Specify the python binary to use (default: python3.11)"
    echo "  main_file       Specify the main file to run (default: main.py)"
    exit 0
fi

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --reinstall)
            export REINSTALL=1
            shift
            ;;
        --update-pip)
            export UPDATE_PIP=1
            shift
            ;;
        --keep-logs)
            export KEEP_LOGS=1
            shift
            ;;
        --log-file)
            export LOG_FILE="$2"
            shift 2
            ;;
        --python-binary)
            export PY="$2"
            shift 2
            ;;
        *)
            if [[ -z "$MAIN_FILE" ]]; then
                export MAIN_FILE="$1"
            else 
                echo "Unknown argument: $1"
                exit 1
            fi
            shift
            ;;
    esac
done

# If no python binary is specified, use python3.11
if [[ -z "$PY" ]]; then
    export PY="python3.11"
fi
# Python version
PYTHON_VERSION=$($PY --version)
if [[ -z "$PYTHON_VERSION" ]]; then
    echo "Python is not installed or not found in PATH."
    exit 1
fi
#? echo "Python Version: $PYTHON_VERSION"
# Parse "Python x.y.z", get y
PYTHON_VERSION=$(echo "$PYTHON_VERSION" | grep "\\..*\\." | cut -d "." -f 2)
#? echo "Python Version: 3.$PYTHON_VERSION"

# Check python version
if [[ "$PYTHON_VERSION" != "11" ]]; then    
    echo "Please use Python 3.11."
    exit 1
fi

# Set script dir to this file's dir
export SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Set the log file path
if [[ -z "$LOG_FILE" ]]; then
    export LOG_FILE="$SCRIPT_DIR/log.txt"
fi
# Move into the script dir
cd "$SCRIPT_DIR"
# Regenerate the log file if it doesn't exist
if [[ "$KEEP_LOGS" != "1" ]]; then
    # Remove the log file if it exists
    if [ -f "$LOG_FILE" ]; then
        rm "$LOG_FILE"
    fi
fi
if [[ ! -f "$LOG_FILE" ]]; then
    # Create the log file if it doesn't exist
    touch "$LOG_FILE"
    if [[ "$KEEP_LOGS" != "1" ]]; then
        echo "Regenerating log file..."
    else 
        echo "Log file not found, creating one at $LOG_FILE!"
    fi
fi
# Put the python version into the log file
echo "Python Version: $($PY --version)" >> "$LOG_FILE"
# Check if the venv should be reinstalled
if [[ "$REINSTALL" == "1" ]]; then
    echo "Reinstalling dependencies..."
    rm -rf venv
fi
# Python venv
if [[ ! -d "venv" ]]; then
    # First install
    echo "Creating venv..."
    $PY -m venv venv
    export REINSTALL=1
fi
# Load the venv
source ./venv/bin/activate

# Run the script with --update-pip ./startup.sh to update pip
if [[ "$UPDATE" == "1" || "$REINSTALL" == "1" ]]; then
    echo "Updating..."
    $PY -m pip install --upgrade pip
    # Install PyTorch, torchvision, and torchaudio from a specific index URL
    $PY -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 >> "$LOG_FILE"
    # Install openai-whisper from the GitHub repository
    $PY -m pip install git+https://github.com/openai/whisper.git >> "$LOG_FILE"
    # Other deps
    # $PY -m pip install -U pywin32 >> "$LOG_FILE"
    $PY -m pip install -r requirements.txt >> "$LOG_FILE"
fi


# if main file somehow still isn't set
if [[ -z "$MAIN_FILE" ]]; then
    export MAIN_FILE="main.py"
fi
# Run the main file
echo "Running $MAIN_FILE..."
$PY "$MAIN_FILE" >> "$LOG_FILE"
echo "Done running $MAIN_FILE!"
# Error handling
echo Z-Waif has stopped running! Likely from an error causing a crash...
echo See the log.txt file for more info!
# Deactivate venv
deactivate
# Pause the script
read -p "Press enter to continue..."
# End of script