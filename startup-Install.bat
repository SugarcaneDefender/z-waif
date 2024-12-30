@echo off
setlocal

REM Get the current directory of the batch file
set "SCRIPT_DIR=%~dp0"

REM Set the log file path
set "LOG_FILE=%SCRIPT_DIR%\log.txt"

REM Change to the script directory
cd /d "%SCRIPT_DIR%"

REM Create and activate the main virtual environment
python -m venv venv
call venv\Scripts\activate


REM Uncomment / Delete the "REM" in the line below - it may fix some issues you have with your install
REM python -m pip install --upgrade pip


REM Install PyTorch, torchvision, and torchaudio from a specific index URL
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 2>> "%LOG_FILE%"

REM Install openai-whisper from the GitHub repository
python -m pip install git+https://github.com/openai/whisper.git 2>> "%LOG_FILE%"

REM Needed upgrades that won't install normally
python -m pip install --upgrade pywin32

REM Install the remaining dependencies from requirements.txt
python -m pip install -r requirements.txt 2>> "%LOG_FILE%"

echo
pause

REM Execute the Python script (replace "main.py" with the actual file name)
python main.py 2>> "%LOG_FILE%"

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
