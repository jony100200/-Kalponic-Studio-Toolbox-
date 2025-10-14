@echo off
REM KS PDF Extractor GUI Launcher
REM =============================
REM 
REM This batch file launches the KS PDF Extractor GUI
REM Make sure Python and dependencies are installed

echo Starting KS PDF Extractor GUI...
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if CustomTkinter is installed
python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo Installing CustomTkinter...
    pip install customtkinter
    if errorlevel 1 (
        echo ERROR: Failed to install CustomTkinter
        echo Please run: pip install customtkinter
        pause
        exit /b 1
    )
)

REM Launch the GUI
echo Launching GUI...
python gui_app.py

pause