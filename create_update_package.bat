@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Z-WAIF Update Package Creator
echo ========================================
echo.

REM Get current directory
set "PROJECT_DIR=%~dp0"
set "PROJECT_NAME=z-waif"

REM Get current date and time for versioning
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YEAR=%dt:~2,2%"
set "MONTH=%dt:~4,2%"
set "DAY=%dt:~6,2%"
set "HOUR=%dt:~8,2%"
set "MINUTE=%dt:~10,2%"
set "VERSION=%YEAR%%MONTH%%DAY%_%HOUR%%MINUTE%"

REM Set output filename
set "OUTPUT_FILE=z-waif_update_%VERSION%.rar"

echo Creating update package: %OUTPUT_FILE%
echo.

REM Check for WinRAR installation in common locations
set "WINRAR_FOUND="
set "WINRAR_PATH="

REM Check Program Files (x86)
if exist "C:\Program Files (x86)\WinRAR\WinRAR.exe" (
    set "WINRAR_PATH=C:\Program Files (x86)\WinRAR\WinRAR.exe"
    set "WINRAR_FOUND=1"
    goto :winrar_found
)

REM Check Program Files
if exist "C:\Program Files\WinRAR\WinRAR.exe" (
    set "WINRAR_PATH=C:\Program Files\WinRAR\WinRAR.exe"
    set "WINRAR_FOUND=1"
    goto :winrar_found
)

REM Check if rar command is available
where rar >nul 2>nul
if %errorlevel% equ 0 (
    set "WINRAR_FOUND=1"
    set "USE_CMD=1"
    goto :winrar_found
)

REM If not found, show error
echo ERROR: WinRAR is not installed or not found
echo Please install WinRAR from: https://www.win-rar.com/
echo.
pause
exit /b 1

:winrar_found
if defined USE_CMD (
    echo Found WinRAR command line tool
) else (
    echo Found WinRAR at: %WINRAR_PATH%
)
echo.

REM Create temporary exclude file
echo Creating exclude list...
(
echo *.pyc
echo __pycache__
echo .git
echo .gitignore
echo .env
echo .envrc
echo venv
echo logs
echo Logs
echo *.log
echo *.tmp
echo *.temp
echo .DS_Store
echo Thumbs.db
echo desktop.ini
echo *.bak
echo *.backup
echo test_*.py
echo *_test.py
echo update_pip.bat
echo create_update_package.bat
echo create_update_package.ps1
echo test_rvc_connection.py
echo *.rar
echo *.zip
echo *.7z
echo node_modules
echo .vscode
echo .idea
echo *.swp
echo *.swo
echo *~
echo .pytest_cache
echo .coverage
echo htmlcov
echo .tox
echo .mypy_cache
echo .ruff_cache
echo .black_cache
echo .isort.cfg
echo .flake8
echo .pylintrc
echo .pre-commit-config.yaml
echo .github
echo .gitlab-ci.yml
echo .travis.yml
echo .appveyor.yml
echo .circleci
echo .azure-pipelines.yml
echo .jenkins
echo .drone.yml
echo .woodpecker.yml
echo .gitea
echo .gitea-workflows
echo .gitea-actions
echo .gitea-templates
echo .gitea-issues
echo .gitea-pulls
echo .gitea-releases
echo .gitea-wiki
echo .gitea-pages
echo .gitea-mirrors
echo .gitea-hooks
echo .gitea-keys
echo .gitea-tokens
echo .gitea-users
echo .gitea-orgs
echo .gitea-teams
echo .gitea-repos
echo .gitea-packages
echo .gitea-actions
echo .gitea-workflows
echo .gitea-templates
echo .gitea-issues
echo .gitea-pulls
echo .gitea-releases
echo .gitea-wiki
echo .gitea-pages
echo .gitea-mirrors
echo .gitea-hooks
echo .gitea-keys
echo .gitea-tokens
echo .gitea-users
echo .gitea-orgs
echo .gitea-teams
echo .gitea-repos
echo .gitea-packages
) > exclude_list.txt

echo Exclude list created.
echo.

REM Check if output file already exists and remove it
if exist "%OUTPUT_FILE%" (
    echo Removing existing file: %OUTPUT_FILE%
    del "%OUTPUT_FILE%" >nul 2>nul
    if exist "%OUTPUT_FILE%" (
        echo ERROR: Cannot remove existing file. It may be in use.
        echo Please close any programs that might be using the file and try again.
        pause
        exit /b 1
    )
)

REM Check if WinRAR is already running
tasklist /FI "IMAGENAME eq WinRAR.exe" 2>NUL | find /I /N "WinRAR.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo WARNING: WinRAR is already running. Please close it and try again.
    echo.
    set /p "CONTINUE=Continue anyway? (y/N): "
    if /i not "%CONTINUE%"=="y" (
        echo Operation cancelled.
        pause
        exit /b 1
    )
)

REM Create the RAR file
echo Creating RAR package...
echo This may take a few minutes depending on project size...
echo.

if defined USE_CMD (
    REM Use command line rar - explicitly create single file without splitting
    rar a -r -x@exclude_list.txt -v- "%OUTPUT_FILE%" "%PROJECT_DIR%*"
    set "RAR_SUCCESS=%errorlevel%"
) else (
    REM Use WinRAR GUI with silent mode - explicitly create single file without splitting
    "%WINRAR_PATH%" a -r -x@exclude_list.txt -ep1 -v- "%OUTPUT_FILE%" "%PROJECT_DIR%*"
    set "RAR_SUCCESS=%errorlevel%"
)

REM Check if RAR file was actually created (WinRAR error code 1 is often just warnings)
if exist "%OUTPUT_FILE%" (
    REM Wait a moment to ensure file is fully written
    timeout /t 2 /nobreak >nul
    echo.
    echo ========================================
    echo SUCCESS: Update package created!
    echo ========================================
    echo.
    echo Package: %OUTPUT_FILE%
    echo Location: %PROJECT_DIR%%OUTPUT_FILE%
    echo.
    
    REM Get file size
    for %%A in ("%OUTPUT_FILE%") do set "SIZE=%%~zA"
    set /a "SIZE_MB=%SIZE% / 1048576"
    echo Size: %SIZE_MB% MB
    echo.
    
    echo Package contents:
    echo - All source code and configuration files
    echo - Documentation and guides
    echo - Preset configurations
    echo - Excluded: temporary files, logs, virtual environments
    echo.
    
    if %RAR_SUCCESS% neq 0 (
        echo Note: WinRAR completed with warnings (error code: %RAR_SUCCESS%)
        echo This is usually normal and the package is still valid.
        echo.
    )
    
    echo Ready for distribution!
    
    REM Ask if user wants to open the file location
    set /p "OPEN_EXPLORER=Open file location in Explorer? (Y/n): "
    if /i "%OPEN_EXPLORER%"=="" set "OPEN_EXPLORER=Y"
    if /i "%OPEN_EXPLORER%"=="Y" (
        explorer /select,"%PROJECT_DIR%%OUTPUT_FILE%"
    )
) else (
    echo.
    echo ERROR: Failed to create RAR package
    echo Error code: %RAR_SUCCESS%
    echo Please check if you have write permissions in this directory
    echo.
)

REM Clean up temporary files
del exclude_list.txt >nul 2>nul

echo.
echo Press any key to exit...
pause >nul 