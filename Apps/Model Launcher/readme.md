# 🧠 Pathline — Model Picker UI  
**Launch LLMs & Whisper models with zero terminal hassle.**

A Python-based GUI to easily launch local AI models (like GGUF LLMs or Whisper ASR) using a config file or manual selection. No need to type commands or deal with terminal paths—just point, click, and go.

---

## ✨ Features

- 🎯 **One-click launch** for `.gguf` (LLMs) or folder-based models (e.g. Whisper)
- ✅ **Auto compatibility check** (VRAM, RAM, and model size)
- 🗂️ **Load config.json** to auto-fill paths and settings
- 🔝 **Start / Stop server** directly from the UI
- 💡 **Helpful tooltips** for every field
- 🔧 **Python + CustomTkinter** powered, minimal dependencies

---

## 📦 Requirements

- Python 3.8+
- `customtkinter`
- `psutil`

Install with:
```bash
pip install customtkinter psutil
```

---

## 🚀 How to Use

1. Run the UI:

```bash
python model_picker_ui.py
```

2. Select:
   - **Model Type**: `file` for `.gguf` LLMs, `folder` for Whisper or similar
   - **Model Path**: Use the browse button or load a `config.json`

3. ✅ See if your system can handle the model (VRAM & RAM check)

4. Click **Start Server** to launch  
   Click **Stop Server** to kill the process

---

## 🗂️ Config Example (`config.json`)

```json
{
  "model_path": "D:/Models/qwen1_5-4b-chat.gguf",
  "model_type": "file",
  "server_exe": "D:/Apps/llama-server.exe",
  "port": 8085
}
```

---

## 📁 File Overview

- `model_picker_ui.py` — The GUI interface
- `run_model_server.py` — The terminal-based fallback CLI runner
- `config.json` — Example config file
- `start_model_picker.bat` — Windows launcher (optional)

---

## 🤝 License

MIT License — free to use and modify. Credit appreciated.

---

## 💬 Community & Support

Join our Discord: [your Discord invite here]  
Follow for updates: [@KalponicStudio](https://twitter.com/kalponicstudio)
