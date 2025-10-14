# KS Seamless Checker

A polished desktop application for checking image seamlessness (tileability) with batch processing, visual previews, and comprehensive results management.

## Features

### Core Functionality
- **Seam Detection**: Advanced algorithm using edge MSE analysis to determine if images tile seamlessly
- **Batch Processing**: Process entire folders or individual image files
- **Visual Previews**: Generate and display 2x2 tiled previews to visually verify seamlessness
- **Results Table**: Sortable table with thumbnails, filenames, and seamless status

### User Interface
- **Dark Theme**: Custom muted dark UI with configurable accent color (#C49A6C)
- **Frameless Window**: Modern window design with custom header bar and drag functionality
- **Floating Preview Window**: Resizable, zoomable preview with pan and navigation controls
- **Status Bar**: Real-time progress tracking and status updates
- **Drag & Drop**: Support for dropping folders directly onto the interface

### Advanced Features
- **Memory Management**: Configurable preview modes (memory-only or disk-cached)
- **Thumbnail Optimization**: Adjustable thumbnail sizes and memory limits
### Advanced Features
- **Memory Management**: Configurable preview modes (memory-only or disk-cached)
- **Thumbnail Optimization**: Adjustable thumbnail sizes and memory limits
- **AI-Powered Detection**: Optional EfficientNet-B0 classification for improved seamless detection accuracy (hybrid with SSIM)
- **CSV Export**: Export batch results with seamless image placeholders
- **Settings Dialog**: Comprehensive configuration for all processing options
- **Threaded Processing**: Non-blocking batch processing with progress updates
- **Settings Dialog**: Comprehensive configuration for all processing options
- **Threaded Processing**: Non-blocking batch processing with progress updates

### Technical Details
- **Supported Formats**: PNG, JPG, JPEG, BMP, TIFF
- **Performance**: Optimized for large batches with memory-efficient processing
- **Cross-Platform**: Windows-compatible with Python 3.13

## Installation

### Requirements
- Python 3.13+
- Dependencies: PySide6, OpenCV, Pillow, NumPy

### Setup
1. Clone or download the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```
   Or use the provided batch file:
   ```bash
   run_app.bat
   ```

## Usage

### Basic Workflow
1. **Select Input**: Use the folder browse button or drag-and-drop a folder containing images
2. **Configure Settings**: Click the settings gear icon to adjust processing parameters
3. **Process Batch**: Click "Process Batch" to analyze all images
4. **Review Results**: View thumbnails and status in the results table
5. **Export Results**: Use "Export CSV" to save batch results for further processing

### Preview Features
- **Inline Thumbnails**: Small previews in the results table
- **Floating Preview**: Double-click table rows or click preview button for full-size view
- **Zoom & Pan**: Use mouse wheel to zoom, drag to pan in preview window
- **Navigation**: Next/Previous buttons to browse through batch results

### Configuration Options
Edit `config.json` or use the Settings dialog to configure:
- `seam_threshold`: Sensitivity for seam detection (default: 10)
- `preview_mode`: "memory" or "disk" for preview storage
- `thumbnail_only_in_memory`: Keep thumbnails in memory only
- `thumbnail_max_size`: Maximum thumbnail dimension
- `auto_start_on_drop`: Automatically start processing when folder is dropped
- `accent_color`: UI accent color (hex format)

## Testing

Run the visual smoke test to verify UI functionality:
```bash
python test_smoke.py
```

Run unit tests for core functionality:
```bash
python -m pytest tests/
```

## Architecture

- `src/image_checker.py`: Core seam detection and preview generation
- `src/batch_processor.py`: Batch processing logic and CSV export
- `src/gui.py`: Main PySide6 interface and UI components
- `config.json`: Application configuration
- `tests/`: Unit tests and smoke tests

## Development

The application uses a modular architecture with separate concerns:
- Image processing logic isolated from UI
- Threaded processing for responsive interface
- Configurable settings with JSON persistence
- Comprehensive error handling and user feedback