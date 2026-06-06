@echo off
echo Starting Prompt Sequencer...

setlocal
set "PY=python"

py -3.11 -c "import customtkinter, sys" >nul 2>&1
if %errorlevel%==0 (
    set "PY=py -3.11"
) else (
    py -3.10 -c "import customtkinter, sys" >nul 2>&1
    if %errorlevel%==0 set "PY=py -3.10"
)

echo Using interpreter: %PY%
%PY% -c "import sys, customtkinter; print('Python', sys.version.split()[0], '| customtkinter', customtkinter.__version__)" 2>nul
if errorlevel 1 (
    echo.
    echo customtkinter is not available for any available Python launcher.
    echo Install it with:
    echo   py -3.11 -m pip install -r requirements.txt
    echo   py -3.10 -m pip install -r requirements.txt
    pause
    exit /b 1
)

%PY% main.py
pause
