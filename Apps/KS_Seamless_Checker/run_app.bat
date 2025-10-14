@echo off
setlocal

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python and add it to your PATH.
    pause
    exit /b 1
)

REM Check if main.py exists
if not exist "main.py" (
    echo Error: main.py not found in %SCRIPT_DIR%
    pause
    exit /b 1
)

REM Run the application
echo Starting KS Seamless Checker...
python main.py

REM Check if the app started successfully
if errorlevel 1 (
    echo Error: Failed to start the application.
    pause
) else (
    echo Application exited successfully.
)

endlocal