@echo off
rem Single launcher for KS Image Cleanup
rem Usage: double-click this file or run from cmd/powershell

rem Ensure script runs from the application folder
cd /d "%~dp0"

rem Quick python check
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

echo ========================================
echo  KS Image Cleanup
echo ========================================
echo Python: 
python --version
echo.

echo Starting application (logs -> batch_cleanup.log)...
python main.py

exit /b %ERRORLEVEL%
