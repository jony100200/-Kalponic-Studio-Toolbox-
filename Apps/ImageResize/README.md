# KS Image Resize

A professional batch image resizing utility with both GUI and CLI interfaces, following KISS and SOLID principles.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Batch Processing**: Resize multiple images at once
- **Flexible Dimensions**: Support for absolute pixels or percentage scaling
- **Aspect Ratio Preservation**: Automatically maintain image proportions
- **Multiple Formats**: Support for JPEG, PNG, BMP, TIFF, and WebP
- **Quality Control**: Configurable JPEG compression quality
- **Preset System**: Built-in presets for common sizes (HD, 4K, etc.)
- **Dual Interface**: Both GUI and command-line interfaces
- **Configuration Management**: Persistent user preferences and custom presets
- **Progress Tracking**: Real-time progress updates during batch processing
- **Error Handling**: Robust error handling with detailed logging

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Quick Start

1. Clone or download this repository
2. Navigate to the ImageResize directory
3. Run the installer:

```bash
# Install in development mode
pip install -e .
```

### GUI Installation

For GUI mode, additional dependencies are required:

```bash
pip install Pillow customtkinter PyYAML
```

## Usage

### GUI Mode (Recommended for beginners)

Run the graphical interface:

```bash
# Using the provided batch file (Windows)
run_image_resizer.bat

# Or directly with Python
python -m ks_image_resize.ui.app
```

**GUI Features:**
- Drag-and-drop input/output directory selection
- Live preview of dimension settings
- Preset selection for common sizes
- Real-time progress tracking
- Batch processing with error reporting

### CLI Mode (For automation and scripting)

```bash
# Using the provided batch file (Windows)
run_cli.bat input_dir output_dir --width 800 --height 600

# Or directly with Python
python -m ks_image_resize.cli.main input_dir --width 50%
```

## Command Line Options

```
usage: ks-image-resize [-h] [--width WIDTH] [--height HEIGHT] [--preset PRESET]
                      [--quality QUALITY] [--verbose] [--list-presets]
                      [input_dir] [output_dir]

Batch image resizing utility

positional arguments:
  input_dir             Input directory containing images
  output_dir            Output directory (default: input_dir/resized)

optional arguments:
  -h, --help            Show this help message and exit
  --width WIDTH, -w WIDTH
                        Target width (pixels or percentage, e.g., 800 or 50%)
  --height HEIGHT, -h HEIGHT
                        Target height (pixels or percentage, e.g., 600 or 75%)
  --preset PRESET, -p PRESET
                        Use predefined dimensions (small, medium, large, hd, 4k)
  --quality QUALITY, -q QUALITY
                        JPEG quality (default: 95)
  --verbose, -v         Enable verbose output
  --list-presets        List available presets and exit
```

## Examples

### Basic Resizing

```bash
# Resize to fixed dimensions
ks-image-resize photos/ output/ --width 1920 --height 1080

# Resize maintaining aspect ratio (specify only width)
ks-image-resize photos/ --width 800

# Percentage scaling
ks-image-resize photos/ --width 50% --height 50%
```

### Using Presets

```bash
# List available presets
ks-image-resize --list-presets

# Use HD preset (1920x1080)
ks-image-resize photos/ --preset hd

# Use 4K preset (3840x2160)
ks-image-resize photos/ --preset 4k
```

### Advanced Usage

```bash
# High-quality resizing with verbose output
ks-image-resize photos/ output/ --width 200% --height 200% --quality 100 --verbose

# Batch process with custom output directory
ks-image-resize ./raw_images ./processed --preset large --quality 90
```

## Presets

| Preset | Dimensions | Description |
|--------|------------|-------------|
| small | 800×600 | Standard small size for web thumbnails |
| medium | 1600×1200 | Medium size for social media and presentations |
| large | 3840×2160 | High resolution for professional printing |
| hd | 1920×1080 | Full HD resolution |
| 4k | 3840×2160 | Ultra HD 4K resolution |
| custom | User-defined | Manual dimension input |

## Configuration

The application stores configuration in:
- **Windows**: `%APPDATA%\ks-image-resize\config.yaml`
- **Unix-like**: `~/.config/ks-image-resize/config.yaml`

Configuration includes:
- Custom presets
- Default quality settings
- UI theme preferences
- Default output subfolder name

## Supported Formats

- **JPEG/JPG**: Best for photographs, supports quality settings
- **PNG**: Lossless, best for graphics with transparency
- **BMP**: Uncompressed, largest file sizes
- **TIFF**: High quality, supports layers and metadata
- **WebP**: Modern format with good compression

## Architecture

Following SOLID principles and KISS methodology:

### Single Responsibility Principle
- `ImageResizer`: Handles only image resizing logic
- `ImageResizeApp`: Manages only GUI interactions
- `ConfigManager`: Manages only configuration persistence
- CLI module: Handles only command-line interface

### Open/Closed Principle
- Easy to add new image formats
- Extensible preset system
- Plugin-ready architecture for future enhancements

### Liskov Substitution Principle
- All components can be replaced with compatible implementations
- Interface consistency across modules

### Interface Segregation Principle
- Separate interfaces for GUI and CLI
- Minimal, focused class interfaces

### Dependency Inversion Principle
- High-level modules don't depend on low-level modules
- Dependencies injected through configuration

## Development

### Project Structure

```
ImageResize/
├── src/ks_image_resize/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── core/
│   │   ├── __init__.py
│   │   └── resizer.py     # Core resizing logic
│   ├── ui/
│   │   ├── __init__.py
│   │   └── app.py         # GUI application
│   └── cli/
│       ├── __init__.py
│       └── main.py        # CLI application
├── tests/
│   ├── __init__.py
│   ├── test_resizer.py    # Unit tests
│   └── test_cli.py        # CLI tests
├── pyproject.toml         # Project configuration
├── run_image_resizer.bat  # GUI launcher
├── run_cli.bat           # CLI launcher
└── README.md
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=ks_image_resize

# Run specific test file
pytest tests/test_resizer.py
```

### Building Distribution

```bash
# Build wheel and source distribution
python -m build

# Install from local build
pip install dist/ks_image_resize-0.1.0-py3-none-any.whl
```

## Troubleshooting

### Common Issues

**"Module not found" errors:**
```bash
# Reinstall the package
pip uninstall ks-image-resize
pip install -e .
```

**GUI not starting:**
- Ensure `customtkinter` is installed
- Check Python version compatibility

**Images not processing:**
- Verify input directory contains supported image formats
- Check file permissions
- Ensure output directory is writable

**Memory issues with large images:**
- Process images in smaller batches
- Use percentage scaling instead of absolute dimensions

### Logging

Enable verbose logging for debugging:

```bash
# GUI mode
set PYTHONPATH=%~dp0src
python -c "import logging; logging.basicConfig(level=logging.DEBUG)" -m ks_image_resize.ui.app

# CLI mode
python -m ks_image_resize.cli.main input_dir --width 800 --verbose
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Add docstrings for all public functions and classes
- Keep functions small and focused on single responsibilities

## License

MIT License - see LICENSE file for details

## Changelog

### Version 0.1.0
- Initial release with GUI and CLI interfaces
- Support for multiple image formats
- Preset system for common dimensions
- Configuration management
- Comprehensive test suite
- Proper Python packaging

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review existing issues on GitHub
3. Create a new issue with detailed information

## Roadmap

- [ ] Custom preset management in GUI
- [ ] Drag-and-drop file support
- [ ] Batch processing progress persistence
- [ ] Image format conversion options
- [ ] Advanced resizing algorithms (Lanczos, Bicubic, etc.)
- [ ] GPU acceleration support
- [ ] Plugin system for custom operations