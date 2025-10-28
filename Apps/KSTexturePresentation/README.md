# 🚀 SPRITE NEXUS - Dual Mode Icon Processor

A modern Python application for batch processing icons with random backgrounds and creating transparent sprite sheets, featuring a sci-fi dark theme UI designed with KISS and SOLID principles.

## ✨ Features

### 🔀 Icon + Background Merger Mode
- **📁 Folder-Based Processing**: Select entire folders of icons and backgrounds
- **🎯 Smart Icon Merging**: Each icon gets paired with a random background
- **📐 Aspect-Fit Scaling**: Icons maintain aspect ratio and center perfectly
- **🔮 Advanced Spritesheets**: Configurable grid with power-of-2 canvas option
- **⚡ Batch Operations**: Process hundreds of images in one go
- **🎯 Flexible Output Modes**: Choose between Sprite Sheets, Individual PNGs, or Both

### 📋 Sprite Sheet Maker Mode (NEW!)
- **🎯 Transparent Sprite Sheets**: Create sprite sheets from transparent icons only
- **📐 Bottom-Center Alignment**: Sprites positioned at bottom-center of each cell
- **🔧 Smart Scaling**: Auto-scale down oversized sprites while preserving originals
- **📏 Configurable Spacing**: Adjustable grid spacing and bottom margins
- **📋 Multi-Sheet Pagination**: Automatically creates multiple sheets when needed
- **💎 Power-of-2 Canvas**: Optional power-of-2 canvas expansion for game engines

### ✂️ Sprite Sheet Splitter Mode (NEW!)
- **🔄 Reverse Operation**: Split existing sprite sheets back into individual frames
- **📐 Grid-Based Extraction**: Extract frames using configurable row/column grid
- **📁 Single & Batch Processing**: Process individual sheets or entire folders
- **🎯 Smart Naming**: Frames named with row/column coordinates (e.g., `sheet_r01_c01.png`)
- **✅ Dimension Validation**: Ensures sprite sheet dimensions are evenly divisible by grid
- **⚡ Fast Processing**: Efficient cropping and saving of individual frames

### 🎨 Common Features
- **🌌 Sci-Fi Dark Theme**: Modern CustomTkinter interface with futuristic styling
- **🏗️ Clean Architecture**: Modular design following SOLID principles
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

The application features **two processing modes** accessible via tabs:

## 🔀 Mode 1: Icon + Background Merger

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

## 📋 Mode 2: Sprite Sheet Maker (NEW!)

### 📁 Folder Selection
1. **Icons Folder**: Select folder containing transparent icon images
2. **Output Folder**: Choose where to save sprite sheets

### ⚙️ Sprite Sheet Configuration
- **Cell Size**: Size of each cell in pixels (default: 256px)
- **Grid Spacing**: Spacing between cells in pixels (default: 2px)
- **Bottom Margin**: Extra space below sprite in cell (default: 0px)
- **Grid Rows/Columns**: Configure grid layout (default: 8×8)
- **Power-of-2 Canvas**: Optional canvas expansion for game engine compatibility

### 🎯 Sprite Behavior
1. **Load & Sort**: All images loaded and sorted by filename for consistency
2. **Smart Scaling**: Sprites larger than cell size are uniformly scaled down to fit
3. **Bottom-Center Alignment**: Each sprite positioned at bottom-center of its cell
4. **Preserve Transparency**: Full alpha channel preservation throughout process
5. **Auto-Pagination**: Multiple sheets created automatically when needed
6. **Grid Spacing**: Configurable gutters between cells on the sheet

### 📝 Output Files
- **Naming**: `<IconsFolderName>_sheet.png` or `<IconsFolderName>_sheet_N.png` for multiple sheets
- **Format**: PNG with full transparency support
- **Multi-Sheet**: Automatic indexing (_sheet_1, _sheet_2, etc.) for pagination

## ✂️ Mode 3: Sprite Sheet Splitter

### 📁 Input Selection
1. **Input Type**: Choose between Single Sprite Sheet or Folder (Batch Processing)
2. **Input Path**: Select individual sprite sheet file or folder containing multiple sheets
3. **Output Folder**: Choose where to save extracted frames

### ⚙️ Grid Configuration
- **Rows**: Number of rows in the sprite sheet grid (default: 4)
- **Columns**: Number of columns in the sprite sheet grid (default: 4)
- **📊 Grid Info**: Real-time display of total frames per sheet

### 🎯 Processing Behavior
1. **Dimension Validation**: Verifies sprite sheet dimensions are evenly divisible by grid
2. **Frame Extraction**: Crops each frame using calculated grid coordinates
3. **Smart Naming**: Frames named as `<sheet_name>_r<row>_c<col>.png` (zero-padded)
4. **Batch Processing**: Processes all image files in selected folder
5. **Error Handling**: Skips invalid files and reports processing status

### 📝 Output Files
- **Frame Naming**: `<original_name>_r01_c01.png`, `<original_name>_r01_c02.png`, etc.
- **Format**: PNG with preserved transparency and original quality
- **Organization**: All frames saved to selected output folder
- **Batch Mode**: Frames from multiple sheets saved to same output folder

### 📁 Output Formats

#### Icon + Background Merger
- **Sprite Sheets Mode**: Creates paginated spritesheets: `<folder_name>_sheet_1.png`, `<folder_name>_sheet_2.png`, etc.
- **Individual PNGs Mode**: Saves to: `Output/<IconsFolderName>/<icon_stem>.png`
- **Both Mode**: Combines both workflows in a single operation

#### Sprite Sheet Maker
- **Transparent Sheets**: `<IconsFolderName>_sheet.png` or `<IconsFolderName>_sheet_N.png`
- **Pure Transparency**: No backgrounds, just transparent sprites with grid layout
- **Bottom-Center Alignment**: Sprites positioned consistently in each cell

## 🎯 Processing Workflows

### Icon + Background Merger Workflow
1. **Folder Validation**: Ensures all required folders exist and contain valid images
2. **Icon Sorting**: Processes icons in deterministic filename order for consistency
3. **Batch Merge**: Each icon is randomly paired with a background
4. **Aspect-Fit Scaling**: Icons resize to fit target size while maintaining proportions
5. **Perfect Centering**: Icons center on backgrounds with proper alpha compositing
6. **Smart Output**: Creates sprite sheets, individual files, or both based on selected mode

### Sprite Sheet Maker Workflow
1. **Icon Loading**: Loads all transparent icons from folder and sorts by filename
2. **Size Validation**: Checks each sprite against cell size, scales down if needed
3. **Grid Layout**: Calculates optimal grid positioning with spacing
4. **Bottom-Center Placement**: Positions each sprite at bottom-center of its cell
5. **Transparency Preservation**: Maintains full alpha channel throughout process
6. **Auto-Pagination**: Creates multiple sheets when icon count exceeds grid capacity
7. **Power-of-2 Expansion**: Optionally expands canvas to power-of-2 dimensions

### Sprite Sheet Splitter Workflow
1. **Input Validation**: Verifies selected file/folder exists and contains valid images
2. **Grid Compatibility**: Checks sprite sheet dimensions are divisible by row/column grid
3. **Frame Calculation**: Computes frame dimensions and coordinates for each grid cell
4. **Sequential Extraction**: Crops and saves each frame in row-major order
5. **Smart Naming**: Generates coordinate-based filenames for easy identification
6. **Batch Processing**: Repeats process for all sprite sheets in folder mode
7. **Progress Reporting**: Shows success/failure counts and total frames created

## 🛡️ Reliability Features

- **Input Validation**: Comprehensive folder and file validation before processing
- **Deterministic Processing**: Icons sorted by filename for consistent results across both modes
- **Memory Management**: Automatic image cleanup to prevent memory leaks
- **Error Handling**: Graceful handling of corrupted or unsupported files
- **Progress Tracking**: Real-time status updates and detailed result summaries
- **File Versioning**: Smart naming prevents accidental overwrites
- **Threading Safety**: UI remains responsive during large batch operations
- **Dual Mode Support**: Seamless switching between merger and sprite sheet modes

## 🔧 Technical Features

### Icon + Background Merger
- **Random Background Assignment**: Each icon gets unique random background
- **RGBA Normalization**: All images converted to RGBA for consistent processing
- **Aspect-Fit "Contain"**: Icons scale down to fit without cropping
- **Alpha Preservation**: Transparent areas maintain full alpha channel

### Sprite Sheet Maker
- **Smart Scaling**: Only scales down oversized sprites, preserves smaller ones
- **Bottom-Center Alignment**: Consistent sprite positioning in each cell
- **Grid Spacing Control**: Configurable gutters between cells
- **Bottom Margin Support**: Extra space below sprites within cells
- **Power-of-2 Canvas**: Optional expansion for game engine compatibility
- **Multi-Sheet Pagination**: Automatic sheet creation when grid capacity exceeded

### Sprite Sheet Splitter
- **Grid-Based Extraction**: Precise frame extraction using row/column coordinates
- **Dimension Validation**: Ensures even divisibility for clean frame separation
- **Coordinate Naming**: Systematic naming with row/column identifiers
- **Batch Folder Processing**: Processes entire directories of sprite sheets
- **Format Preservation**: Maintains original image format and quality
- **Error Resilience**: Continues processing despite individual file errors

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

## 🎨 Supported Formats

- **Icons & Backgrounds**: PNG, JPG, JPEG, WebP
- **Output**: PNG with full alpha channel support
- **Case-insensitive** file extension matching
- **Transparency**: Full RGBA support in both processing modes

## 🎯 Perfect For

### Icon + Background Merger
- **Game Development**: Creating character/item sprites with consistent backgrounds
- **UI Design**: Batch processing icon sets with uniform styling
- **Asset Pipelines**: Automated sprite generation for large projects

### Sprite Sheet Maker  
- **Game Development**: Creating transparent sprite atlases for characters, items, animations
- **Mobile Apps**: Optimized sprite sheets for memory-efficient rendering
- **Web Development**: Transparent icon sets with consistent grid layout
- **Animation**: Frame-based animation sheets with precise positioning

### Sprite Sheet Splitter
- **Asset Extraction**: Extracting individual frames from existing sprite atlases
- **Animation Breakdown**: Separating animation frames for editing or reuse
- **Legacy Asset Recovery**: Converting old sprite sheets to individual files
- **Cross-Platform Conversion**: Preparing assets for engines requiring individual frames
