@echo off
echo 🚀 Starting Universal Model Launcher V4...
echo ==========================================

REM Change to the correct directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python and add it to PATH.
    pause
    exit /b 1
)

REM Launch the GUI
echo 🎨 Launching GUI interface...
python launch_gui.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo ❌ Application encountered an error.
    pause
)