@echo off
echo Starting Batch Image Resizer...
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking required packages...
python -c "import PIL, customtkinter" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install Pillow customtkinter
    if errorlevel 1 (
        echo ERROR: Failed to install required packages
        echo Please run: pip install Pillow customtkinter
        pause
        exit /b 1
    )
)

REM Run the image resizer
echo Launching Image Resizer GUI...
python ImageResize.py

REM If there was an error, keep the window open
if errorlevel 1 (
    echo.
    echo ERROR: The application encountered an error
    pause
)