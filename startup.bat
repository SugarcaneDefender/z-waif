@echo off
setlocal

REM Get the current directory of the batch file
set "SCRIPT_DIR=%~dp0"

REM Set the log file path
set "LOG_FILE=%SCRIPT_DIR%\log.txt"

REM Change to the script directory
cd /d "%SCRIPT_DIR%"

REM Add all relevant directories to PYTHONPATH for advanced features
set "PYTHONPATH=%SCRIPT_DIR%;%SCRIPT_DIR%utils;%SCRIPT_DIR%API;%PYTHONPATH%"

REM Create and activate the main virtual environment
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate

REM Install PyTorch, torchvision, and torchaudio from a specific index URL
REM python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 2>> "%LOG_FILE%"

REM Install openai-whisper from the GitHub repository
REM python -m pip install git+https://github.com/openai/whisper.git 2>> "%LOG_FILE%"

REM Install Greenlet - SCF (Transferr to V2, was causing issues, check log)
REM python -m pip install --upgrade pip
REM python -m pip install greenlet
REM python -m pip install websockets~=11.0
REM python -m pip install sounddevice
REM python -m pip install opencv-python

REM Install the remaining dependencies from requirements.txt (if not already installed)
if not exist "installed_sentinel.txt" (
    python -m pip install -r requirements.txt 2>> "%LOG_FILE%"
    echo "installed" > installed_sentinel.txt
)

REM Execute the Python script with the correct Python path
set PYTHONPATH=%SCRIPT_DIR%

REM Check if any command line arguments were provided (keep advanced message feature)
if "%~1"=="" (
    echo Starting Z-Waif...
    echo:
    echo You can also start Z-Waif with a message by running:
    echo startup.bat "Your message here"
    echo:
    python main.py 2>> "%LOG_FILE%"
) else (
    echo Starting Z-Waif with message: %*
    echo:
    python main.py %* 2>> "%LOG_FILE%"
)

echo:
echo Z-Waif has stopped running! Likely from an error causing a crash...
echo See the log.txt file for more info!
pause

REM Deactivate the virtual environment
deactivate

REM Display message and prompt user to exit
echo.
echo Batch file execution completed. Press any key to exit.
pause >nul

endlocal
