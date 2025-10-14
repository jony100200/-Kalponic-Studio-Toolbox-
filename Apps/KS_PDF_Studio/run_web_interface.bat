@echo off
echo ========================================
echo   KS PDF Studio Web Interface
echo   Browser-Based Tutorial Creation
echo ========================================
echo.

cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if requirements are installed
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found
    echo Please ensure you're running from the KS_PDF_Studio directory
    pause
    exit /b 1
)

echo Installing/updating dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Starting KS PDF Studio Web Interface...
echo Access at: http://localhost:8080
echo Press Ctrl+C to stop the server
echo.

python web_interface.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start web interface
    echo Check the error messages above for details
    pause
)

echo.
echo KS PDF Studio Web Interface stopped.
pause