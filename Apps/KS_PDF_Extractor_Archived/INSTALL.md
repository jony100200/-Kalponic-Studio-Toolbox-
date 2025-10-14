# KS PDF Extractor - Installation & Setup Guide

## Quick Installation

1. **Clone or download** the KS_PDF_Extractor folder
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Test the installation**:
   ```bash
   python ks_pdf_extract.py --help
   ```

## Detailed Setup

### Prerequisites

- **Python 3.7+** (recommended: Python 3.9+)
- **pip** (Python package installer)

### Step-by-Step Installation

1. **Navigate to the tool directory**:
   ```bash
   cd KS_PDF_Extractor
   ```

2. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**:
   ```bash
   python ks_pdf_extract.py --show-config
   ```

### Dependencies Explained

- **PyPDF2**: Core PDF reading library
- **pdfplumber**: Advanced PDF text extraction (more accurate)
- **chardet**: Character encoding detection

### Alternative Installation Methods

#### Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv ks_pdf_env

# Activate it (Windows)
ks_pdf_env\Scripts\activate

# Activate it (macOS/Linux)
source ks_pdf_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Using conda

```bash
# Create conda environment
conda create -n ks_pdf python=3.9

# Activate environment
conda activate ks_pdf

# Install dependencies
pip install -r requirements.txt
```

## Configuration

The tool creates a default configuration file at `config/settings.json`. You can modify this file to customize behavior:

```json
{
  "extraction": {
    "method": "pdfplumber",
    "preserve_formatting": true,
    "clean_text": true
  },
  "output": {
    "default_format": "md",
    "add_stats": true
  }
}
```

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'PyPDF2'**
   ```bash
   pip install PyPDF2 pdfplumber
   ```

2. **Permission denied errors**
   - Run terminal as administrator (Windows)
   - Use `sudo` for system-wide installs (macOS/Linux)
   - Use virtual environments instead

3. **Python not found**
   - Ensure Python is in your PATH
   - Try `python3` instead of `python`
   - Reinstall Python with "Add to PATH" option

4. **Tool runs but no output**
   - Check if input PDF exists
   - Verify PDF is not corrupted
   - Try with `--verbose` flag

### Platform-Specific Notes

#### Windows
- Use PowerShell or Command Prompt
- Backslashes in paths: `C:\Users\...`
- May need to run as administrator

#### macOS/Linux
- Use Terminal
- Forward slashes in paths: `/home/user/...`
- May need `python3` instead of `python`

## Performance Optimization

### For Large PDFs
- Increase chunk_size in config
- Consider batch processing
- Use SSD storage for temp files

### For Batch Processing
- Enable parallel processing in config
- Adjust max_workers based on CPU cores
- Monitor memory usage

## Usage Examples

See the main README.md for detailed usage examples.

## Getting Help

1. **Show help**: `python ks_pdf_extract.py --help`
2. **Show config**: `python ks_pdf_extract.py --show-config`
3. **Verbose output**: `python ks_pdf_extract.py --input file.pdf --verbose`
4. **Interactive mode**: `python ks_pdf_extract.py --interactive`

## Updates

To update the tool:
1. Download the latest version
2. Replace the old files
3. Run `pip install -r requirements.txt` to update dependencies
4. Your configuration will be preserved