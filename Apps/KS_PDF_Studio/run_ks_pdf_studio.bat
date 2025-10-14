@echo off
REM KS PDF Studio Launcher
REM Version 2.0.0
REM Author: Kalponic Studio

echo ========================================
echo   KS PDF Studio v2.0 - AI-Powered Tutorial Creation
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://python.org
    echo.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%

REM Change to the script directory
cd /d "%~dp0"

echo.
echo Starting KS PDF Studio...
echo.

REM Launch the application
python src/main_gui.py

REM Check if application exited successfully
if errorlevel 1 (
    echo.
    echo ERROR: KS PDF Studio exited with error code %errorlevel%
    echo.
    pause
) else (
    echo.
    echo KS PDF Studio closed successfully.
)

echo.
pause