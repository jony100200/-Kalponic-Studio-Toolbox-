@echo off
echo ========================================
echo   KS SnapStudio CLI - Command Line Tool
echo ========================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if package is installed
python -c "import ks_snapstudio" >nul 2>&1
if errorlevel 1 (
    echo Installing KS SnapStudio...
    pip install -e . >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Failed to install KS SnapStudio
        echo Try running: pip install -e .
        pause
        exit /b 1
    )
)

REM Pass all arguments to the CLI
python -m ks_snapstudio.cli.main %*

if errorlevel 1 (
    echo.
    echo For help, run: ks-snapstudio --help
    pause
)</content>
<parameter name="filePath">E:\__Kalponic Studio Repositories\-Kalponic-Studio-Toolbox-\Apps\KS SnapStudio\run_cli.bat