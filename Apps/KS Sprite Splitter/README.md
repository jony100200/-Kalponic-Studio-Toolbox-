# KS Sprite Splitter

Auto-separate 2D sprites into semantic parts with soft mattes and channel-packed maps.

## Features

- **AI-Powered Segmentation**: Uses OpenCV GrabCut and morphological operations for precise sprite segmentation
- **Intelligent Part Splitting**: K-means clustering for semantic part separation
- **Soft Matting**: Guided filter matting for smooth alpha channels
- **Multiple Backends**: Choose between mock (fast) and real (accurate) processing backends
- **Template System**: Pre-configured templates for different sprite categories (trees, flags, characters, etc.)
- **Dual Interface**: Both command-line and modern GUI interfaces
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Quickstart

### Installation

1. Install dependencies (recommended in a virtualenv):

```bash
pip install -r requirements.txt
```

For GUI support, also install:

```bash
pip install PySide6 QDarkStyle
```

### GUI Interface (Recommended)

Launch the modern PySide6 GUI:

```bash
python run_gui.py
```

Or use the installed entry point:

```bash
ks-splitter-gui
```

The GUI provides:
- Drag-and-drop file selection
- Real-time preview of input sprites
- Backend configuration (mock/real processing)
- Template selection for different sprite types
- Progress tracking and result preview
- Dark theme matching VS Code aesthetics

### Keyboard Shortcuts

The GUI supports the following keyboard shortcuts for improved productivity:

- **Ctrl+O**: Open sprite file
- **Ctrl+D**: Select output directory
- **Ctrl+P**: Process sprite
- **Ctrl+C**: Cancel processing
- **Ctrl+T**: Toggle between light and dark themes
- **Ctrl+Q**: Exit application
- **F1**: Show help and usage instructions

**Accessibility Shortcuts:**
- **Alt+I**: Focus input file field
- **Alt+O**: Focus output directory field
- **Alt+P**: Focus process button

### Command Line Interface

Process sprites via command line:

```bash
python -m cli.ks_splitter --input path/to/sprite.png --output runs/ --category tree
```

Available categories: `tree`, `flag`, `char`, `arch`, `vfx`

## Architecture

### Core Components

- **Pipeline**: Orchestrates the segmentation → matting → part splitting workflow
- **Backends**: Pluggable processing engines (mock for testing, real for production)
- **Templates**: YAML configurations defining sprite categories and processing parameters
- **Protocols**: Type-safe interfaces ensuring backend compatibility

### Processing Pipeline

1. **Object Segmentation**: Separates foreground sprite from background
2. **Alpha Matting**: Creates smooth soft mattes for transparency
3. **Part Clustering**: Groups pixels into semantic parts using k-means
4. **Output Generation**: Produces channel-packed maps and individual part images

## Configuration

Edit `configs/config.yml` to configure backends:

```yaml
objects_backend: opencv      # mock, opencv
matte_backend: guided        # mock, guided
parts_backend: heuristic     # mock, heuristic
```

## Templates

Pre-configured templates in `templates/`:

- **tree**: Natural objects with branches/leaves
- **flag**: Fabric/cloth objects with wind effects
- **char**: Character sprites with limbs/torso
- **arch**: Architectural elements
- **vfx**: Special effects and particles

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Adding New Backends

Implement the protocol interfaces in `ks_splitter/`:

```python
from ks_splitter.segment import ObjectSegmenter

class MySegmenter(ObjectSegmenter):
    def segment(self, image: np.ndarray) -> np.ndarray:
        # Your segmentation logic here
        pass
```

### Building Distribution

```bash
pip install build
python -m build
```

## License

MIT License - see LICENSE file for details.
