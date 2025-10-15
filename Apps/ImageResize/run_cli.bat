@echo off
echo ========================================
echo   KS Image Resize CLI - Command Line Tool
echo ========================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from https://python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

REM Install the package in development mode if not already installed
echo Checking if ks-image-resize is installed...
python -c "import ks_image_resize" >nul 2>&1
if errorlevel 1 (
    echo Installing KS Image Resize...
    pip install -e .
    if errorlevel 1 (
        echo ERROR: Failed to install KS Image Resize
        echo Please run: pip install -e .
        pause
        exit /b 1
    )
    echo.
)

REM Check if required dependencies are available
echo Checking required dependencies...
python -c "import PIL, yaml" >nul 2>&1
if errorlevel 1 (
    echo Installing required dependencies...
    pip install Pillow PyYAML
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo Please run: pip install Pillow PyYAML
        pause
        exit /b 1
    )
    echo.
)

REM Run the CLI with all passed arguments
echo Running KS Image Resize CLI...
echo.
python -m ks_image_resize.cli.main %*

REM Preserve the exit code
exit /b %errorlevel%