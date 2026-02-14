@echo off
setlocal

python -m unittest discover -s tests -v
if errorlevel 1 exit /b %errorlevel%

python scripts\sync_roadmap.py --apply
if errorlevel 1 exit /b %errorlevel%

python scripts\sync_roadmap.py --check
if errorlevel 1 exit /b %errorlevel%

echo Part completion checks passed and roadmap is in sync.
