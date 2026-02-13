@echo off
REM Run KS SnapClip without showing a console using pythonw
set PYW=C:\Python313\pythonw.exe
if not exist "%PYW%" (
  echo pythonw not found at %PYW%
  pause
  exit /b 1
)
start "" "%PYW%" "%~dp0\main.py" --start-minimized --enable-hotkeys
exit /b 0
