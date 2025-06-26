@echo off
setlocal enabledelayedexpansion

echo ==== Detecting GPU VRAM using NVIDIA-SMI ====
python gpu_info.py

REM Load VRAM value from file
set /p VRAM_MB=<temp_vram_value.txt
echo Detected GPU VRAM: !VRAM_MB! MB

REM Call model loader with VRAM as argument
call model_menu.bat !VRAM_MB!

endlocal
pause
