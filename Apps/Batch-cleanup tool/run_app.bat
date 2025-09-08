@echo off
REM Batch Image Cleanup Tool - Launcher
REM This script launches the image cleanup application

echo ========================================
echo  Batch Image Cleanup Tool
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and add it to your PATH
    echo.
    pause
    exit /b 1
)

REM Display Python version
echo Python version:
python --version
echo.

REM Check if required packages are installed
echo Checking dependencies...
python -c "import customtkinter, cv2, numpy, PIL; print('✓ All dependencies are available')" 2>nul
if errorlevel 1 (
    echo WARNING: Some dependencies may be missing
    echo Installing required packages...
    echo.
    pip install customtkinter pillow opencv-python numpy
    echo.
)

REM Launch the application
echo Starting Batch Image Cleanup Tool...
echo.
python main.py

REM Handle exit
if errorlevel 1 (
    echo.
    echo Application exited with an error
    pause
) else (
    echo.
    echo Application closed successfully
)
