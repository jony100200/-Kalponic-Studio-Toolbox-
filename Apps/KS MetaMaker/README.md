# KS MetaMaker

🧠 **KS MetaMaker** — "Tag. Name. Organize. Simplify."

Automate the understanding, tagging, renaming, and organizing of visual assets (images, textures, props, backgrounds, renders) into structured, dataset-ready folders — all offline and customizable.

## ✨ What's New in v1.0

- **Hardware-Aware AI**: Automatic hardware detection with optimized model loading
- **Optimized OpenCLIP**: ViT-L-14 (307M params) for 50% faster processing than ViT-H-14
- **Production-Ready ONNX**: YOLOv11s and BLIP Large models with validation
- **Smart Memory Management**: Dynamic model loading/unloading based on VRAM
- **Enterprise Model Pipeline**: Download → Convert → Validate → Cleanup system

## 🎯 Purpose

KS MetaMaker is an AI-assisted local utility that:

* **Reads images** from user folders (PNG, JPG, WEBP, etc.)
* **Detects content** using AI: props, backgrounds, characters, objects
* **Generates intelligent tags** with category-specific limits
* **Renames files** with structured patterns (`background_skyline_neon_20251015_001`)
* **Organizes outputs** into category folders (`/Props/`, `/Backgrounds/`, `/Characters/`)
* **Creates paired `.txt` files** for LoRA/dataset training
* **Exports datasets** as ZIP, CSV, or JSON packages

## 🚀 Quick Start

### 1. Installation
```bash
# Clone repository
git clone <repository-url>
cd ks-metamaker

# Install dependencies
pip install -e .
```

### 2. Hardware Setup & Model Download
```bash
python app/main.py
```
- **First launch**: Hardware detection wizard runs automatically
- **Model download**: System downloads and converts optimal AI models
- **Validation**: All models tested before use

### 3. Process Images
```bash
# GUI Mode (Recommended)
python app/main.py

# CLI Mode
ks-metamaker --input ./Unsorted --output ./Output --preset backgrounds --rename true --organize true --export dataset
```

## 🖥️ Hardware-Aware AI System

KS MetaMaker automatically detects your hardware and optimizes AI model usage:

### System Profiles
- **CPU Only**: Lightweight CPU processing
- **Edge (≤4GB VRAM)**: Efficient models, load/unload per image
- **Mid (6-8GB VRAM)**: Balanced performance, keep 2 models loaded
- **Pro (10-12GB VRAM)**: Advanced models, better quality
- **Max (>12GB VRAM)**: Largest models, maximum quality

### Current AI Models

| Component | Model | Size | Purpose |
|-----------|-------|------|---------|
| **Tagging** | OpenCLIP ViT-L-14 | Library | Semantic understanding, tag generation |
| **Detection** | YOLOv11s | 36 MB | Object detection in images |
| **Captioning** | BLIP Large | 1.75 GB | Human-like image descriptions |
| **Quality** | Laplacian Variance | Algorithm | Blur detection, image quality |
| **Duplicates** | Perceptual Hash | Algorithm | Find identical/near-identical images |

**All models run locally with ONNX Runtime** - no internet required after setup!

## 📋 Example Workflow

### Input: Messy folder
```
Unsorted/
├── IMG_1234.jpg
├── screenshot_001.png
├── render_final_v2.png
└── texture_metal_01.jpg
```

### Output: Organized dataset
```
Output/Run_20251015_1430/
├── Backgrounds/
│   ├── background_city_night_20251015_001.jpg
│   ├── background_city_night_20251015_001.txt
│   └── background_urban_street_20251015_002.jpg
├── Props/
│   ├── prop_metal_container_20251015_001.jpg
│   └── prop_metal_container_20251015_001.txt
├── metadata.json
├── tags_summary.csv
└── dataset.zip
```

### Sample .txt content:
```
kalponic studio background, cinematic lighting, night city skyline, neon lights, wet streets, reflections, futuristic, urban, 4k render
```

## ⚙️ Configuration

### Main Config (`configs/config.yml`)
```yaml
main_prefix: "kalponic studio background"
style_preset: "cinematic lighting, 4k render"
max_tags:
  props: 20
  backgrounds: 25
  characters: 30
rename_pattern: "{category}_{top_tags}_{YYYYMMDD}_{index}"
models:
  tagger: "openclip_vith14.onnx"      # Library-based
  detector: "yolov11s.onnx"           # ONNX file
  captioner: "blip_large.onnx"        # ONNX file
```

### Presets (`configs/presets/`)
- `props.yml` - Industrial, mechanical objects
- `backgrounds.yml` - Environments, scenes
- `characters.yml` - Fantasy, realistic figures

## 🔧 Core Features

### 1. **Smart AI Tagging**
- **OpenCLIP ViT-L-14**: Generates semantic tags (photorealistic, texture, detailed, etc.)
- **YOLOv11s**: Detects objects (car, person, bottle, etc.)
- **BLIP Large**: Creates captions for context
- **Category limits**: 10-30 tags based on content type

### 2. **Intelligent Renaming**
- **Template system**: `{category}_{top_tags}_{date}_{counter}`
- **Clean filenames**: Removes invalid characters
- **Batch processing**: Thousands of files at once

### 3. **Auto-Organization**
- **Category detection**: Props, Backgrounds, Characters
- **Date folders**: `Run_YYYYMMDD_HHMM/`
- **Subfolders**: Automatic folder structure

### 4. **Quality Control**
- **Blur detection**: Laplacian variance analysis
- **Duplicate removal**: Perceptual hashing + SSIM
- **Quality filtering**: Configurable thresholds

### 5. **Dataset Export**
- **Paired .txt files**: For LoRA training
- **Metadata JSON**: Complete processing info
- **ZIP packages**: Ready-to-share datasets
- **CSV summaries**: Tag statistics and counts

## 🖼️ GUI Features

- **Drag & Drop**: Drop folders directly onto the interface
- **Live Preview**: See tags before processing
- **Progress Tracking**: Real-time processing status
- **Hardware Monitor**: VRAM and RAM usage
- **Undo System**: Revert renames and moves
- **Batch Processing**: Queue multiple folders

## 💻 CLI Usage

```bash
# Basic processing
ks-metamaker --input ./images --output ./output

# Full pipeline with export
ks-metamaker \
  --input ./Unsorted \
  --output ./Output \
  --preset backgrounds \
  --rename true \
  --organize true \
  --export dataset \
  --threads 4

# Quality filtering
ks-metamaker \
  --input ./images \
  --quality-filter true \
  --duplicate-removal true \
  --min-quality 0.5
```

## 🔧 Technical Details

### AI Pipeline
1. **Ingest**: Load images, hash for duplicates, basic validation
2. **Quality Check**: Blur detection, resolution analysis
3. **AI Processing**: Tag generation with dynamic model loading
4. **Classification**: Category detection (prop/background/character)
5. **Renaming**: Apply templates, clean filenames
6. **Organization**: Move to category folders
7. **Export**: Generate metadata and packages

### Memory Management
- **Dynamic loading**: Models load/unload based on VRAM
- **Batch processing**: Process images in optimal batch sizes
- **GPU acceleration**: ONNX Runtime with CUDA/Metal support
- **CPU fallback**: Automatic fallback for systems without GPU

### Model Validation
- **Download**: Direct from official sources
- **Convert**: PyTorch → ONNX with optimization
- **Validate**: Test inference on dummy data
- **Cleanup**: Remove temporary files automatically

## 📊 Performance

- **Typical speed**: 1-3 seconds per image (GPU), 3-8 seconds (CPU)
- **Batch processing**: 100+ images simultaneously
- **Memory usage**: 2-8GB depending on hardware profile
- **Model size**: ~1.8GB total (optimized for speed)

## 🛠️ Requirements

- **Python**: 3.8+
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB free space (models + processing)
- **OS**: Windows 10+, macOS 10.15+, Linux
- **GPU**: Optional but recommended (any with 2GB+ VRAM)

### Dependencies
```
torch>=2.0.0
onnxruntime>=1.15.0
open_clip_torch>=2.20.0
transformers>=4.30.0
Pillow>=10.0.0
opencv-python>=4.8.0
PyQt6>=6.5.0
```

## 🚨 Troubleshooting

### Common Issues
- **"AI models not found"**: Run hardware setup wizard first
- **"Out of memory"**: Reduce batch size or use CPU mode
- **"Slow processing"**: Check GPU drivers, try different profile
- **"Import errors"**: Run `pip install -e .` again

### Hardware-Specific Tips
- **NVIDIA**: Install CUDA toolkit 11.8+
- **AMD**: Use ROCm-compatible ONNX Runtime
- **Intel**: Use OpenVINO for CPU acceleration
- **Apple Silicon**: ONNX Runtime automatically uses Metal

## 📈 Roadmap

### v1.1 (Soon)
- Color palette extraction
- Advanced duplicate detection
- Tag search and filtering
- Custom model support

### v1.2 (Future)
- GUI template editor
- Multilingual tag support
- Batch processing queues
- Plugin system

### v2.0 (Future)
- Integration with KS Suite
- Cloud processing options
- Advanced AI models
- Team collaboration features

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenCLIP**: For state-of-the-art vision-language models
- **Ultralytics**: For YOLO object detection
- **Salesforce**: For BLIP image captioning
- **ONNX Runtime**: For cross-platform AI acceleration

---

**Built with ❤️ for creators, by creators.** Transform your messy asset folders into organized, AI-tagged datasets ready for training!