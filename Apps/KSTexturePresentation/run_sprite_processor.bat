@echo off
REM Run Sprite Nexus (main.py) using the project's virtual environment if available.
REM Place this file in the repository root and run it from a cmd/powershell prompt.

SETLOCAL ENABLEEXTENSIONS
REM Change to the directory where this batch file lives
PUSHD "%~dp0"

REM Prefer the venv python if it exists
IF EXIST ".venv\Scripts\python.exe" (
    echo Using virtualenv python at .venv\Scripts\python.exe
    ".venv\Scripts\python.exe" main.py %*
) ELSE (
    echo Virtual environment python not found at .venv\Scripts\python.exe
    echo Falling back to system python in PATH
    python main.py %*
)

POPD
ENDLOCAL
EXIT /B %ERRORLEVEL%
