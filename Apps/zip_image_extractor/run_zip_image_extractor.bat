@echo off
REM KS Zip Image Extractor Launcher
REM Run this batch file to start the KS UI for extracting images from zip archives.

cd /d "%~dp0"

REM Verify Python availability
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.9+ and try again.
    pause
    exit /b 1
)

REM Activate virtual environment if present
if exist ..\venv\Scripts\activate.bat (
    call ..\venv\Scripts\activate.bat
)

REM Launch the PySide6 UI
python ui.py %*
set ERR_LEVEL=%ERRORLEVEL%

REM Deactivate virtual environment if used
if exist ..\venv\Scripts\deactivate.bat (
    call ..\venv\Scripts\deactivate.bat
)

if not "%ERR_LEVEL%"=="0" (
    echo Zip Image Extractor exited with code %ERR_LEVEL%.
)

pause
