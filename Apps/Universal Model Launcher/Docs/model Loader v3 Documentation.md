# Universal Model Launcher Documentation

## Overview
The Universal Model Launcher is a lightweight, standalone tool designed for loading AI models and managing ports efficiently. It supports multiple interfaces (CLI, GUI, batch scripts) and integrates seamlessly with external applications. The launcher is modular, portable, and optimized for GPU acceleration.

## Features
### General Features
- **Standalone**: No external dependencies beyond Python's standard library.
- **Ultra-light**: Approximately 400 lines of code.
- **Smart Loading**: Sequential model loading with resource management.
- **Port Discovery**: Automatically detects running AI services.
- **Multiple Interfaces**: CLI, GUI, and batch scripts.
- **Integration Ready**: REST API compatibility for external applications.

### Supported Formats
- **GGUF**: Recommended format.
- **GGML**: Legacy format.
- **PyTorch**: `.bin`, `.pth`, `.pt` files.
- **SafeTensors**: Hugging Face format.

### Hardware Support
- **NVIDIA GPUs**: CUDA acceleration via llama.cpp.
- **AMD GPUs**: ROCm support.
- **Intel GPUs**: Basic support.
- **Apple Silicon**: Metal acceleration on macOS.
- **CPU Fallback**: Optimized CPU inference.

## Architecture
The launcher is built with a modular architecture:

```
core/
├── config_manager.py    # Configuration handling
├── model_discovery.py   # Model scanning and analysis
├── fast_loader.py       # Model loading with llama.cpp
├── gpu_detector.py      # Hardware detection
└── ui_manager.py        # Terminal interface
```

## Python Scripts
### `main.py`
- **Purpose**: Entry point for CLI commands.
- **Commands**:
  - `launch`: Load models interactively or directly.
  - `configure`: Set up model directories and default settings.
  - `discover`: Scan directories for available models.
  - `status`: Display system hardware and configuration status.
  - `install`: Install dependencies and set up the launcher.
  - `benchmark`: Measure model loading performance.

### `allema_bridge.py`
- **Purpose**: Standalone port manager and export tool.
- **Features**:
  - Scans for running AI services on common ports.
  - Identifies services like OpenAI-compatible APIs and Ollama.
  - Provides service details including port, URL, type, and API endpoint.

### `fast_loader.py`
- **Purpose**: Ultra-fast model loader CLI.
- **Features**:
  - Finds GGUF models in specified paths.
  - Loads models on available ports with GPU acceleration.
  - Saves state and provides model details including API endpoints.

### `gui_launcher.py`
- **Purpose**: GUI interface for model launching using CustomTkinter.
- **Features**:
  - Provides a graphical interface for model discovery and launching.
  - Integrates core components like `ConfigManager`, `ModelDiscovery`, and `FastLoader`.

### `install.py`
- **Purpose**: Installation script for the Universal Model Launcher.
- **Features**:
  - Checks Python version and UV package manager installation.
  - Installs dependencies and sets up llama.cpp.
  - Creates launcher scripts for easy access.

### `integration_examples.py`
- **Purpose**: Demonstrates integration with loaded models.
- **Features**:
  - Discovers running model servers and retrieves their details.
  - Provides methods to chat with models using OpenAI-compatible APIs.

## Commands
### `launch`
- **Description**: Launch a model with optimized settings.
- **Options**:
  - `--model`: Path to model file.
  - `--config`: Path to config file.
  - `--gpu-layers`: Number of GPU layers.
  - `--context`: Context size.
  - `--port`: Server port.
  - `--host`: Server host.
  - `--interactive`: Interactive mode.

### `configure`
- **Description**: Set up model directories and default settings.

### `discover`
- **Description**: Scan directories for available models.
- **Options**:
  - `--path`: Path to search for models.
  - `--all`: Scan all configured directories.

### `status`
- **Description**: Display system hardware and configuration status.

### `install`
- **Description**: Install dependencies and set up the launcher.

### `benchmark`
- **Description**: Measure model loading performance.
- **Options**:
  - `--runs`: Number of benchmark runs.

## Integration
### Standalone Usage
The launcher works independently as a command-line tool.

### External Apps
Provides REST API compatibility for integration with:
- ComfyUI
- text-generation-webui
- Ollama
- Custom applications

## Troubleshooting
### Common Issues
- **"llama.cpp binary not found"**: Install llama.cpp server binary or use `uv pip install llama-cpp-python`.
- **"No models found"**: Run `uv run python main.py configure` to set up model directories.
- **"GPU not detected"**: Ensure CUDA/ROCm drivers are installed and run `uv run python main.py status`.
- **"Out of memory"**: Reduce GPU layers or context size, or use a smaller quantized model.

### Performance Tips
1. Use quantized models (Q4_K_M recommended).
2. Enable GPU acceleration with appropriate layer count.
3. Adjust context size based on available VRAM/RAM.
4. Use SSD storage for faster model loading.
5. Close other applications to free up resources.

---

🚀 **Ready to launch models at lightning speed!** ⚡
