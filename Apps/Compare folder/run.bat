@echo off
echo Starting Folder Comparison Tool...
echo.
python "%~dp0folder_compare.py"
if errorlevel 1 (
    echo.
    echo Error: Failed to launch the application.
    echo Make sure Python and customtkinter are installed.
    pause
)
