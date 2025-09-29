echo Starting main_v2.py ...
echo Exit code: %EXIT_CODE%
@echo off
REM run_main_v2.bat - Simple launcher for Enhanced Batch Background Remover (main_v2.py)

REM Change to script directory
cd /d "%~dp0"

REM Ensure python is available on PATH
where python >nul 2>nul
if errorlevel 1 (
    echo Python executable not found in PATH. Please install Python or add it to PATH.
    pause
    exit /b 1
)

echo Starting main_v2.py using system Python...
python main_v2.py %*
SET EXIT_CODE=%ERRORLEVEL%

echo Exit code: %EXIT_CODE%
exit /b %EXIT_CODE%
