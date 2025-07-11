@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Z-WAIF Update Package Creator (7-Zip)
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

REM Set output filename (7z format)
set "OUTPUT_FILE=z-waif_update_%VERSION%.7z"

echo Creating update package: %OUTPUT_FILE%
echo.

REM Check for 7-Zip installation in common locations
set "SEVENZIP_FOUND="
set "SEVENZIP_PATH="

REM Check Program Files (x86)
if exist "C:\Program Files (x86)\7-Zip\7z.exe" (
    set "SEVENZIP_PATH=C:\Program Files (x86)\7-Zip\7z.exe"
    set "SEVENZIP_FOUND=1"
    goto :sevenzip_found
)

REM Check Program Files
if exist "C:\Program Files\7-Zip\7z.exe" (
    set "SEVENZIP_PATH=C:\Program Files\7-Zip\7z.exe"
    set "SEVENZIP_FOUND=1"
    goto :sevenzip_found
)

REM Check if 7z command is available
where 7z >nul 2>nul
if %errorlevel% equ 0 (
    set "SEVENZIP_FOUND=1"
    set "USE_CMD=1"
    goto :sevenzip_found
)

REM If not found, show error
echo ERROR: 7-Zip is not installed or not found
echo Please install 7-Zip from: https://www.7-zip.org/
echo.
echo Alternative: Use create_update_package.bat for WinRAR
echo.
pause
exit /b 1

:sevenzip_found
if defined USE_CMD (
    echo Found 7-Zip command line tool
) else (
    echo Found 7-Zip at: %SEVENZIP_PATH%
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
echo create_update_package*.bat
echo create_update_package*.ps1
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
) > exclude_list.txt

echo Exclude list created.
echo.

REM Create the 7z file
echo Creating 7z package...
echo This may take a few minutes depending on project size...
echo.

if defined USE_CMD (
    REM Use command line 7z
    7z a -r -x@exclude_list.txt "%OUTPUT_FILE%" "%PROJECT_DIR%*"
    set "SEVENZIP_SUCCESS=%errorlevel%"
) else (
    REM Use 7-Zip GUI with silent mode
    "%SEVENZIP_PATH%" a -r -x@exclude_list.txt "%OUTPUT_FILE%" "%PROJECT_DIR%*"
    set "SEVENZIP_SUCCESS=%errorlevel%"
)

REM Check if 7z creation was successful
if %SEVENZIP_SUCCESS% equ 0 (
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
    
    echo Ready for distribution!
    echo Note: Recipients will need 7-Zip or WinRAR to extract this file
    echo.
    
    REM Ask if user wants to open the file location
    set /p "OPEN_EXPLORER=Open file location in Explorer? (Y/n): "
    if /i "%OPEN_EXPLORER%"=="" set "OPEN_EXPLORER=Y"
    if /i "%OPEN_EXPLORER%"=="Y" (
        explorer /select,"%PROJECT_DIR%%OUTPUT_FILE%"
    )
) else (
    echo.
    echo ERROR: Failed to create 7z package
    echo Error code: %SEVENZIP_SUCCESS%
    echo Please check if you have write permissions in this directory
    echo.
)

REM Clean up temporary files
del exclude_list.txt >nul 2>nul

echo.
echo Press any key to exit...
pause >nul 