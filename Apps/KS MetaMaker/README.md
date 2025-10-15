# KS MetaMaker

🧠 **KS MetaMaker** — "Tag. Name. Organize. Simplify."

Automate the understanding, tagging, renaming, and organizing of visual assets (images, textures, props, backgrounds, renders) into structured, dataset-ready folders — all offline and customizable.

## Purpose

KS MetaMaker is an AI-assisted local utility that:

* Reads images from user folders
* Detects what they contain (props, backgrounds, characters)
* Generates meaningful tags
* Renames files intelligently (prefix, style, tag-based)
* Organizes outputs into category folders
* Creates paired `.txt` files for dataset or LoRA training
* Optionally packages everything for export (zip, CSV, JSON)

## Installation

1. Clone or download this repository
2. Install dependencies: `pip install -e .`
3. **Setup AI Models**: Launch the app and go to `Setup → Hardware & AI Models` to detect your hardware and download optimal AI models
4. Run the application: `python app/main.py`

## Hardware-Aware AI Model Selection

KS MetaMaker automatically detects your system's hardware capabilities and recommends the best AI models for your setup:

### System Profiles
- **CPU Only**: No GPU detected - uses lightweight CPU-optimized models
- **Edge (≤4GB VRAM)**: Low-end GPUs - efficient models for limited VRAM
- **Mid (6-8GB VRAM)**: Mid-range GPUs - balanced performance models
- **Pro (10-12GB VRAM)**: Professional GPUs - advanced models with better quality
- **Max (>12GB VRAM)**: High-end GPUs - largest models for maximum quality

### Recommended Models by Profile

| Profile | Tagging Model | Detection Model | Captioning Model |
|---------|---------------|-----------------|------------------|
| CPU Only | CLIP-ViT-Base | YOLOv8n | BLIP-Image-Captioning-Base |
| Edge | SigLIP-Base | YOLOv8s | BLIP2-2.7B |
| Mid | SigLIP-Base-256 | YOLOv8m | BLIP2-FLAN-T5-XL |
| Pro | EVA-CLIP-8B | YOLOv8l | BLIP2-FLAN-T5-XL |
| Max | CLIP-ViT-H-14 | YOLOv8x | BLIP2-FLAN-T5-XXL |

The setup wizard will show: *"Detected GPU: RTX 3060 (12 GB VRAM). Recommended models: EVA-CLIP-8B, YOLOv8l, BLIP2-FLAN-T5-XL. Do you want to download these now?"*

## Usage

### GUI Mode
```bash
python app/main.py
```

### CLI Mode
```bash
ks-metamaker --input ./Unsorted --output ./Output --preset backgrounds --rename true --organize true --export dataset
```

## Configuration

Edit `configs/config.yml` to customize behavior. Presets are available in `configs/presets/`.

## Features

- **Hardware-Aware AI Setup**: Automatic hardware detection and optimal model selection
- **Smart Auto-Tagging & Captioning**: Template-based tagging with category-specific limits
- **Intelligent Renaming**: Structured naming patterns
- **Auto-Organization**: Move files by detected type
- **Duplicate & Quality Filter**: Remove duplicates and poor-quality images
- **Dataset Export**: Package processed assets for training

## Requirements

- Python 3.8+
- ONNX Runtime compatible hardware
- Sufficient disk space for models (~2GB)

## License

See LICENSE file in the root directory.