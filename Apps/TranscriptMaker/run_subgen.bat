@echo off
REM === Set Hugging Face model cache location ===
set HF_HOME=E:\AI Apps\SubtitleMaker\huggingface_cache

REM === Set CUDA DLL paths for PyTorch to find CuDNN and cuBLAS ===
set PATH=E:\AI Apps\SubtitleMaker\whisperenv\Lib\site-packages\nvidia\cublas\bin;E:\AI Apps\SubtitleMaker\whisperenv\Lib\site-packages\nvidia\cudnn\bin;%PATH%

REM === Activate the Python virtual environment ===
call "E:\AI Apps\SubtitleMaker\whisperenv\Scripts\activate.bat"

REM === Run the subtitle generation script ===
python BatchTranscribe.py

REM === Pause so you can see any messages or errors ===
pause
