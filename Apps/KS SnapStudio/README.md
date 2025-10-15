# KS SnapStudio

**Professional circular preview capture and export tool for 3D materials**

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

KS SnapStudio automatically captures, masks, watermarks, and exports professional circular previews for Substance Sampler, Blender, AI-generated, or scanned materials.

## ✨ Features

- **🎯 One-Click Capture**: Capture from active viewport or area selection
- **⭕ Automatic Circle Detection**: AI-powered circle detection with fallback to manual crop
- **🎨 Professional Branding**: Brand rings, watermarks, and custom backgrounds
- **📦 Batch Processing**: Process entire folders with consistent settings
- **🎭 Multiple Backgrounds**: Solid, gradient, noise, and pattern backgrounds
- **📋 Quick Sharing**: Clipboard export and platform-optimized presets
- **👁️ Live Preview**: Real-time preview with instant feedback
- **⚙️ Preset System**: Built-in presets for Discord, ArtStation, Twitter, and more
- **🌓 Dark UI**: Consistent Kalponic Studio dark theme
- **🔒 Safe Exports**: Metadata removal and size limits for safe sharing

## 🚀 Quick Start

### Installation

```bash
# Install from source
pip install -e .

# Or install with AI features
pip install -e ".[ai]"
```

### GUI Mode (Recommended)

```bash
# Using the launcher
run_snapstudio.bat

# Or directly
python -m ks_snapstudio.ui.app
```

### CLI Mode

```bash
# Capture and process
ks-snapstudio capture

# Batch process directory
ks-snapstudio batch ./materials --preset artstation_2048_dark

# List available presets
ks-snapstudio presets
```

## 📖 Usage Examples

### Basic Screen Capture
```bash
# Capture full screen with default settings
ks-snapstudio capture

# Capture specific area
ks-snapstudio capture --area 100,100,800,600

# Use ArtStation preset
ks-snapstudio capture --preset artstation_2048_dark
```

### Batch Processing
```bash
# Process all images in directory
ks-snapstudio batch ./raw_materials

# Use custom preset and output directory
ks-snapstudio batch ./materials --preset discord_1024_light --output ./previews

# Recursive processing
ks-snapstudio batch ./project --recursive --preset web_hd
```

### Custom Settings
```bash
# High-quality capture with custom background
ks-snapstudio capture \
  --bg gradient \
  --palette warm \
  --quality 100 \
  --output my_material.png
```

## 🎨 Presets

KS SnapStudio includes optimized presets for popular platforms:

| Preset | Size | Platform | Background | Use Case |
|--------|------|----------|------------|----------|
| `discord_1024_light` | 1024px | Discord | Solid | Community sharing |
| `artstation_2048_dark` | 2048px | ArtStation | Gradient | Portfolio showcase |
| `twitter_1200_warm` | 1200px | Twitter/X | Solid | Social media |
| `reddit_1024_cool` | 1024px | Reddit | Noise | Community posts |
| `print_300dpi` | 2000px | Print | Solid | Professional printing |
| `web_hd` | 1920px | Web | Gradient | Online galleries |

## 🖥️ GUI Features

The desktop application provides:

- **📸 Screen Capture**: Monitor selection and area targeting
- **⚙️ Live Processing**: Real-time preview with adjustable settings
- **🎨 Background Composer**: Interactive background selection
- **💾 Export Options**: Multiple formats with quality control
- **📋 Clipboard Integration**: One-click sharing
- **📊 Progress Tracking**: Visual feedback during processing

## 🏗️ Architecture

KS SnapStudio follows SOLID principles with clean separation of concerns:

### Core Components

- **`ScreenCapture`**: Handles screen capture operations using mss
- **`CircleMask`**: OpenCV-based circle detection and masking
- **`WatermarkEngine`**: PIL-based branding and watermarking
- **`BackgroundComposer`**: NumPy-based background generation
- **`PreviewExporter`**: Multi-format export with safety checks
- **`PresetManager`**: Configuration management for platform presets

### Design Principles

- **KISS**: Simple, focused functionality
- **SOLID**: Single responsibility, dependency injection
- **Safety First**: Size limits, metadata removal, error handling
- **Performance**: Async processing, memory efficient

## 🔧 Development

### Project Structure

```
ks-snapstudio/
├── src/ks_snapstudio/
│   ├── __init__.py          # Package initialization
│   ├── core/                # Core processing modules
│   │   ├── capture.py       # Screen capture
│   │   ├── mask.py          # Circle detection/masking
│   │   ├── watermark.py     # Branding/watermarks
│   │   ├── composer.py      # Background composition
│   │   └── exporter.py      # Export functionality
│   ├── ui/                  # Desktop interface
│   │   └── app.py           # PySide6 application
│   ├── cli/                 # Command-line interface
│   │   └── main.py          # Typer CLI
│   ├── presets/             # Preset management
│   │   └── manager.py       # Preset system
│   └── utils/               # Shared utilities
├── tests/                   # Test suite
├── assets/                  # UI assets and icons
├── docs/                    # Documentation
├── pyproject.toml           # Project configuration
├── run_snapstudio.bat       # GUI launcher
├── run_cli.bat             # CLI launcher
└── README.md
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=ks_snapstudio

# Run specific tests
pytest tests/test_capture.py
```

### Building Distribution

```bash
# Build wheel
python -m build

# Install from build
pip install dist/ks_snapstudio-0.1.0-py3-none-any.whl
```

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ Basic screen capture
- ✅ Circle detection and masking
- ✅ Watermarking and branding
- ✅ Background composition
- ✅ Preset system
- ✅ CLI and GUI interfaces

### Phase 2 (Next)
- 🔄 Watch mode for live capture
- 🔄 Custom preset creation
- 🔄 Drag-and-drop file support
- 🔄 Batch processing progress persistence
- 🔄 Image format conversion

### Future Enhancements
- 🤖 Advanced AI circle detection
- 🎨 Custom branding templates
- 🌐 Web interface
- 📱 Mobile companion app
- 🔗 Plugin API for 3D software

## 🤝 Integration

KS SnapStudio is designed to integrate with 3D workflows:

### Supported Applications
- **Substance Designer/Painter**: Direct viewport capture
- **Blender**: Material node capture
- **AI Tools**: Stable Diffusion, Midjourney outputs
- **General**: Any application with circular previews

### Hotkey Integration
Future versions will support global hotkeys for instant capture from within 3D applications.

## 📋 Requirements

### System Requirements
- **OS**: Windows 10+, macOS 10.15+, Linux
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 100MB for installation

### Dependencies
- **Core**: PySide6, OpenCV, Pillow, NumPy, mss
- **Optional AI**: PyTorch, ONNX Runtime
- **Development**: pytest, black, mypy

## 🐛 Troubleshooting

### Common Issues

**"Screen capture failed"**
- Ensure target application is not minimized
- Try different monitor selection
- Check permissions on macOS/Linux

**"Circle not detected"**
- Ensure material preview is clearly visible
- Try adjusting lighting/contrast
- Use manual crop as fallback

**"GUI not starting"**
- Install PySide6: `pip install PySide6`
- Check Python version compatibility
- Try CLI mode first

**"Memory errors with large images"**
- Reduce preset size
- Process images individually
- Close other applications

### Debug Mode

Enable verbose logging:

```bash
# CLI
ks-snapstudio capture --verbose

# GUI
set PYTHONPATH=%~dp0src
python -c "import logging; logging.basicConfig(level=logging.DEBUG)" -m ks_snapstudio.ui.app
```

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Code Style
- Follow PEP 8
- Use type hints
- Add docstrings
- Keep functions focused

## 📞 Support

For issues and questions:
1. Check troubleshooting section
2. Review existing GitHub issues
3. Create detailed bug report
4. Include system info and steps to reproduce

## 🙏 Acknowledgments

- OpenCV community for computer vision tools
- PySide6 team for Qt Python bindings
- mss library for cross-platform screen capture
- Pillow team for image processing

---

**Made with ❤️ by Kalponic Studio**

*Transforming 3D material previews into professional presentations*</content>
<parameter name="filePath">E:\__Kalponic Studio Repositories\-Kalponic-Studio-Toolbox-\Apps\KS SnapStudio\README.md