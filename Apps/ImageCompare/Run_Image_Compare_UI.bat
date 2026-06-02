@echo off
title Image Compare Tool

cd /d "%~dp0"

echo ==================================
echo Checking UV...
echo ==================================

uv --version >nul 2>&1

if errorlevel 1 (
    echo ERROR: UV is not installed.
    echo Install:
    echo powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    pause
    exit /b
)

echo.
echo Installing dependencies...
echo.

uv pip install ^
customtkinter ^
pillow ^
imagehash ^
opencv-python ^
scikit-image ^
rapidfuzz ^
numpy

echo.
echo Launching...
echo.

uv run image_compare_ui.py

pause