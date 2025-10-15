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
3. Download models using `python scripts/download_models.py`
4. Run the application: `python app/main.py`

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