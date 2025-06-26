@echo off
setlocal enabledelayedexpansion

REM ==== Auto-detect VRAM if not passed as argument ====
set "VRAM_MB=%1"
if "%VRAM_MB%"=="" (
    echo [⚠] No VRAM passed in. Defaulting to 4096 MB.
    set "VRAM_MB=4096"
)

REM ==== Detect GPU Name ====
for /f "delims=" %%G in ('powershell -command "(Get-CimInstance Win32_VideoController | Sort-Object AdapterRAM -Descending)[0].Name"') do (
    set "GPU_NAME=%%G"
)

REM ==== Choose Recommended Model ====
set "RECOMMENDED=1"
if !VRAM_MB! GEQ 13000 (
    set "RECOMMENDED=2"
) else if !VRAM_MB! GEQ 8000 (
    set "RECOMMENDED=3"
) else if !VRAM_MB! GEQ 6000 (
    set "RECOMMENDED=2"
) else (
    set "RECOMMENDED=4"
)

REM ==== Menu UI ====
echo.
echo ==== Patchline Local Model Loader ====
echo Detected GPU: !GPU_NAME!
echo Detected GPU VRAM: !VRAM_MB! MB
echo Recommended model based on VRAM: !RECOMMENDED!
echo.
echo 1. DeepSeek 1.3B (fastest coder)
echo 2. DeepSeek 6.7B (best for dev tasks)
echo 3. Qwen 2.5-7B (chat/all-rounder)
echo 4. Qwen 1.5-4B (for 4GB VRAM or laptops)
echo 5. ARCHIVED: DeepSeek 33B (for future GPU)
echo.

set /p choice="Select model number to load [Recommended: !RECOMMENDED!]: "
if "!choice!"=="" set choice=!RECOMMENDED!

REM ==== Set Model Paths ====
set "MODEL1=O:\Icons\LocalLLM\models\deepseek-coder-1.3b-instruct.Q4_K_M.gguf"
set "MODEL2=O:\Icons\LocalLLM\models\deepseek-coder-6.7b-instruct.Q4_K_M.gguf"
set "MODEL3=O:\Icons\LocalLLM\models\Qwen2.5-7B.Q4_K_M.gguf"
set "MODEL4=O:\Icons\LocalLLM\models\qwen1_5-4b-chat-q4_k_m.gguf"
set "MODEL5=O:\Icons\LocalLLM\models\deepseek-coder-33b-instruct.Q4_K_M.gguf"


set "MODEL_PATH="
if "!choice!"=="1" set "MODEL_PATH=%MODEL1%"
if "!choice!"=="2" set "MODEL_PATH=%MODEL2%"
if "!choice!"=="3" set "MODEL_PATH=%MODEL3%"
if "!choice!"=="4" set "MODEL_PATH=%MODEL4%"
if "!choice!"=="5" set "MODEL_PATH=%MODEL5%"

if "!MODEL_PATH!"=="" (
    echo [❌] Invalid choice. Exiting.
    pause
    exit /b
)

REM ==== Launch Model Server ====
echo [🚀] Launching: !MODEL_PATH!
cd /d O:\Icons\LocalLLM\llama-server\
start "" cmd /k llama-server.exe --model "!MODEL_PATH!" --port 8080

echo [✔] If the server window closes instantly, check for errors.
echo [ℹ] You can now connect to http://localhost:8080 from your analyzer.
pause
endlocal
