# Batch Image Cleanup Tool - PowerShell Launcher
# This script launches the image cleanup application

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Batch Image Cleanup Tool" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Python version: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.7+ and add it to your PATH" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Check dependencies
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    $depCheck = python -c "import customtkinter, cv2, numpy, PIL; print('✓ All dependencies are available')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host $depCheck -ForegroundColor Green
    } else {
        Write-Host "WARNING: Some dependencies may be missing" -ForegroundColor Yellow
        Write-Host "Installing required packages..." -ForegroundColor Yellow
        pip install customtkinter pillow opencv-python numpy
    }
} catch {
    Write-Host "Dependency check failed, but continuing..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting Batch Image Cleanup Tool..." -ForegroundColor Cyan
Write-Host ""

# Launch the application
try {
    python main.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Application closed successfully" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Application exited with an error" -ForegroundColor Red
        Read-Host "Press Enter to exit"
    }
} catch {
    Write-Host ""
    Write-Host "Failed to start application: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
