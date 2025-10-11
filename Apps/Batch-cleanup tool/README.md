# KS Image Cleanup — professional quality fringe removal and edge enhancement

KS Image Cleanup is a professional-grade Python application for removing white fringes/halos and enhancing edges on AI background-removed images. Built with CustomTkinter, OpenCV, and NumPy for precise, production-ready results.

Youtube link : https://www.youtube.com/watch?v=B81_IiHVNGc

## Features

### 🎯 Core Functionality
- **Batch Processing**: Process entire folders of images automatically
- **Advanced Fringe Removal**: Remove white/black halos from AI cutouts
- **Alpha Channel Refinement**: Smooth, feather, and enhance transparency edges
- **Multiple Presets**: White Matte, Black Matte, and Auto detection
- **Professional Results**: Uses OpenCV and NumPy for precise edge processing

### 🖥️ User Interface
- **Modern GUI**: Clean CustomTkinter interface
- **Folder Pickers**: Easy input/output folder selection
- **Real-time Controls**: Sliders for Smooth, Feather, Contrast, and Edge Shift
- **Fringe Fix Settings**: Adjustable band size and strength
- **Progress Tracking**: Live progress bar and status updates
- **Before/After Preview**: Visual confirmation of processing results

### ⚙️ Processing Pipeline
1. **Un-Matte**: Removes background contamination from edges
2. **Alpha Refinement**: Smooths and enhances transparency
3. **Fringe Fix**: Intelligent color replacement at edges
4. **Edge Enhancement**: Precise morphological operations

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Install Dependencies
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install customtkinter>=5.2.0 Pillow>=10.0.0 opencv-python>=4.8.0 numpy>=1.24.0
```

## Usage

### Running the Application

**Option 1: Batch File (Windows - Recommended)**
```batch
.\run_app.bat
```

**Option 2: PowerShell Script (Windows)**
```powershell
.\run_app.ps1
```

**Option 3: Direct Python**
```bash
python main.py
```

### Processing Steps
   - Select input folder containing images to process
   - Select output folder for cleaned images

3. **Configure Settings**:
   - Choose matte preset (White Matte recommended for AI cutouts)
   - Adjust alpha refinement parameters
   - Enable/configure fringe fix

4. **Set Processing Iterations**:
   - Use the "Processing Iterations" field to specify how many times the processing pipeline should run for each image (default is 1, maximum is 10).

5. **Process Images**:
   - Click "Generate Preview" to see a sample result
   - Click "Run Batch" to process all images
   - Processed images saved with "_clean" suffix

## Default Settings

- **Matte Preset**: White Matte
- **Smooth**: 2
- **Feather**: 1  
- **Contrast**: 3.0
- **Shift Edge**: -1
- **Fringe Fix**: Enabled (Band=2, Strength=2)

## Architecture

The application follows SOLID principles with clean separation of concerns:

- `AppUI`: CustomTkinter user interface
- `Controller`: Coordinates UI and processing logic
- `BatchRunner`: Manages multi-threaded batch processing
- `ImageProcessor`: Core image processing algorithms
- `IOHandler`: File input/output operations
- `Config`: Configuration data structures

## Processing Pipeline

For each image:
1. Load image and convert to RGBA
2. **Un-Matte**: Remove background contamination from edges
3. **Refine Alpha**: Smooth → Feather → Contrast → Shift operations
4. **Fringe Fix**: Color inpainting to remove fringe artifacts
5. Save processed image with "_clean" suffix

## Launcher Files

The project includes these recommended launcher files:

- **`run_app.bat`**: Primary Windows batch launcher that starts the app from the project folder
- **`run_app.ps1`**: PowerShell launcher with user-friendly colored output
- **`test_components.py`**: Component test script to verify installation

## Troubleshooting

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- For better performance, use images in PNG format
- Check log file `batch_cleanup.log` for detailed error information
- Use the `test_components.py` script to verify all components are working

## License

This project is provided as-is for educational and personal use.
