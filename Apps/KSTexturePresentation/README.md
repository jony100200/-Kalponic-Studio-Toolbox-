# 🚀 SPRITE NEXUS - Batch Icon Processor

A modern Python application for batch processing icons with random backgrounds and creating spritesheets, featuring a sci-fi dark theme UI designed with KISS and SOLID principles.

## ✨ Features

- **📁 Folder-Based Processing**: Select entire folders of icons and backgrounds
- **🎯 Smart Icon Merging**: Each icon gets paired with a random background
- **📐 Aspect-Fit Scaling**: Icons maintain aspect ratio and center perfectly
- **🔮 Advanced Spritesheets**: Configurable grid with power-of-2 canvas option
- **⚡ Batch Operations**: Process hundreds of images in one go
- **🌌 Sci-Fi Dark Theme**: Modern CustomTkinter interface with futuristic styling
- **🏗️ Clean Architecture**: Modular design following SOLID principles
- **🎯 Flexible Output Modes**: Choose between Sprite Sheets, Individual PNGs, or Both
- **📝 Smart Versioning**: Automatic file naming with version numbers when needed
- **📊 Index Generation**: Creates JSON index files for individual PNG collections

## 🚀 Perfect For

- **Game Development**: Creating character/item sprite sheets with automatic pagination
- **UI Design**: Batch processing icon sets with consistent backgrounds  
- **Asset Pipelines**: Automated sprite generation for large projects with multi-sheet support
- **Texture Creation**: Combining elements for procedural textures
- **Mobile Apps**: Generating icon sets with uniform backgrounds
- **Web Development**: Creating consistent image assets at scale

## 🛠️ Installation

```bash
pip install -r requirements.txt
```

## 🚀 Usage

Launch the application:
```bash
python main.py
```

Or use the VS Code task: **"Run Sprite Processor"**

### 📁 Folder Selection
1. **Icon Folder**: Select folder containing your icon images
2. **Background Folder**: Select folder containing background textures
3. **Output Folder**: Choose where to save processed images

### ⚙️ Processing Configuration
- **Output Size**: Choose from presets (32x32 to 1024x1024) or set custom dimensions
- **🎯 Output Mode**: Choose your preferred output format:
  - **Sprite Sheets**: Create paginated spritesheets with automatic naming
  - **Individual PNGs**: Save each merged icon separately with index.json
  - **Both**: Generate both sprite sheets and individual files in one pass
- **Real-time Scanning**: See icon/background counts as you select folders

### 🔮 Spritesheet Matrix
- **Grid Layout**: Enter exact rows and columns using number input fields
- **📊 Multi-sheet Support**: Automatically creates multiple sheets when icons exceed grid capacity
- **📝 Smart Naming**: Uses icon folder name as base (e.g., "fire_sheet_1.png", "fire_sheet_2.png")
- **🔄 Version Control**: Adds _v2, _v3 suffixes if files already exist
- **Power-of-2 Canvas**: Auto-expand canvas to next power of 2 (up to 2048px)
- **🎯 Perfect Pagination**: Distributes images optimally across multiple sheets

### 📁 Output Formats

#### Sprite Sheets Mode
- Creates paginated spritesheets: `<folder_name>_sheet_1.png`, `<folder_name>_sheet_2.png`, etc.
- Automatic versioning if files exist: `<folder_name>_sheet_1_v2.png`
- JSON metadata files with grid information

#### Individual PNGs Mode
- Saves to: `Output/<IconsFolderName>/<icon_stem>.png`
- Automatic numbering for duplicates: `icon_1.png`, `icon_2.png`
- Creates `index.json` with file list and metadata

#### Both Mode
- Combines both workflows in a single operation
- Optimized processing to avoid duplicate work
- Complete asset pipeline solution

## 🎯 Processing Workflow

1. **Folder Validation**: Ensures all required folders exist and contain valid images
2. **Icon Sorting**: Processes icons in deterministic filename order for consistency
3. **Batch Merge**: Each icon is randomly paired with a background
4. **Aspect-Fit Scaling**: Icons resize to fit target size while maintaining proportions
5. **Perfect Centering**: Icons center on backgrounds with proper alpha compositing
6. **Smart Output**: Creates sprite sheets, individual files, or both based on selected mode
7. **Memory Management**: Properly closes images to prevent memory leaks
8. **Progress Logging**: Real-time feedback and error handling throughout the process

## 🛡️ Reliability Features

- **Input Validation**: Comprehensive folder and file validation before processing
- **Deterministic Processing**: Icons sorted by filename for consistent results
- **Memory Management**: Automatic image cleanup to prevent memory leaks
- **Error Handling**: Graceful handling of corrupted or unsupported files
- **Progress Tracking**: Real-time status updates and detailed result summaries
- **File Versioning**: Smart naming prevents accidental overwrites
- **Threading Safety**: UI remains responsive during large batch operations

## 🏗️ Architecture

Clean modular structure following SOLID principles:

```
src/
├── config/
│   └── settings.py           # 🎛️ App settings & size presets
├── services/
│   ├── image_processor.py    # 🖼️ Batch processing & aspect-fit logic
│   └── file_service.py       # 📁 File system operations
└── ui/
    └── main_window.py        # 🎨 Sci-fi CustomTkinter interface
```

## 📋 Requirements

- **Python 3.8+**
- **Pillow** (Advanced image processing)
- **CustomTkinter** (Modern dark theme UI)

## 🎨 Supported Formats

- **Icons & Backgrounds**: PNG, JPG, JPEG, WebP
- **Output**: PNG with full alpha channel support
- **Case-insensitive** file extension matching

## 🔧 Technical Features

- **Random Background Assignment**: Each icon gets unique random background
- **RGBA Normalization**: All images converted to RGBA for consistent processing
- **Aspect-Fit "Contain"**: Icons scale down to fit without cropping
- **Alpha Preservation**: Transparent areas maintain full alpha channel
- **Power-of-2 Canvas**: Optional expansion for game engine compatibility
- **Deterministic Ordering**: Icons processed in sorted filename order

## � Perfect For

- **Game Development**: Creating character/item sprite sheets
- **UI Design**: Batch processing icon sets with consistent backgrounds
- **Asset Pipelines**: Automated sprite generation for large projects
- **Texture Creation**: Combining elements for procedural textures
