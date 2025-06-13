@echo off
setlocal

REM Get the current directory of the batch file
set "SCRIPT_DIR=%~dp0"

REM Set the log file path
set "LOG_FILE=%SCRIPT_DIR%\log.txt"

REM Change to the script directory
cd /d "%SCRIPT_DIR%"

REM Add all relevant directories to PYTHONPATH
set "PYTHONPATH=%SCRIPT_DIR%;%SCRIPT_DIR%utils;%SCRIPT_DIR%API;%PYTHONPATH%"

REM Create and activate the main virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements if needed
echo Checking and installing requirements...
pip install -r requirements.txt

REM Execute the Python script with the correct Python path
set PYTHONPATH=%SCRIPT_DIR%
echo Starting Z-Waif...
python main.py 2> "%LOG_FILE%"

echo:
echo Z-Waif has stopped running! Likely from an error causing a crash...
echo See the log.txt file for more info!
pause

REM Deactivate the virtual environment
call venv\Scripts\deactivate.bat

REM Display message and prompt user to exit
echo.
echo Batch file execution completed. Press any key to exit.
pause >nul

endlocal
