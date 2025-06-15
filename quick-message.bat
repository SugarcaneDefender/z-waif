@echo off
setlocal EnableDelayedExpansion

REM Quick message input script for Z-Waif
REM Usage: quick-message.bat "Your message here"
REM Or just run it and it will prompt for input

if "%~1"=="" (
    echo:
    echo ============================================
    echo           Z-Waif Quick Message
    echo ============================================
    echo:
    set /p MESSAGE="Enter your message: "
    if "!MESSAGE!"=="" (
        echo No message entered. Exiting...
        pause
        exit /b
    )
    echo:
    echo Starting Z-Waif with your message...
    call startup.bat "!MESSAGE!"
) else (
    echo Starting Z-Waif with message: %*
    call startup.bat %*
)

endlocal 