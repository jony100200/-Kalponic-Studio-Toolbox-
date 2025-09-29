@echo off
REM run_main_v2.bat - Launch Enhanced Batch Background Remover (main_v2.py)

SETLOCAL ENABLEDELAYEDEXPANSION

REM Try to find a virtual environment in common locations
SET VENV_ACTIVATE=
IF EXIST "%~dp0\.venv\Scripts\activate.bat" SET VENV_ACTIVATE="%~dp0\.venv\Scripts\activate.bat"
IF EXIST "%~dp0\venv\Scripts\activate.bat" SET VENV_ACTIVATE="%~dp0\venv\Scripts\activate.bat"
IF EXIST "%~dp0\env\Scripts\activate.bat" SET VENV_ACTIVATE="%~dp0\env\Scripts\activate.bat"

REM Fallback: check repo root (one level up)
IF NOT DEFINED VENV_ACTIVATE (
    IF EXIST "%~dp0..\.venv\Scripts\activate.bat" SET VENV_ACTIVATE="%~dp0..\.venv\Scripts\activate.bat"
    IF EXIST "%~dp0..\venv\Scripts\activate.bat" SET VENV_ACTIVATE="%~dp0..\venv\Scripts\activate.bat"
)

IF DEFINED VENV_ACTIVATE (
    echo Activating virtual environment: %VENV_ACTIVATE%
    call %VENV_ACTIVATE%
) ELSE (
    echo No local virtual environment found. The system Python will be used.
)

REM Change to script directory
cd /d "%~dp0"

REM Run main_v2.py with python
echo Starting main_v2.py ...
python main_v2.py %*
SET EXIT_CODE=%ERRORLEVEL%

echo Exit code: %EXIT_CODE%
ENDLOCAL
exit /b %EXIT_CODE%
