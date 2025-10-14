# KS PDF Extractor Tool

**🔧 Extract PDF content to Text or Markdown files**

Following KS Development Strategy Guide v4.0 principles - "Build smart, stay real, enjoy the process."

## Features

- ✅ Extract text from PDF files
- ✅ Output to plain text (.txt) or Markdown (.md) format
- ✅ Batch processing support
- ✅ Configurable output formatting
- ✅ Clean, modular architecture
- ✅ Cross-platform compatibility
- ✅ **Modern GUI interface** (CustomTkinter)

## Quick Start

### GUI Mode (Recommended for beginners)
```bash
# Run the graphical interface
python gui_app.py
```

### Command Line Mode
```bash
# Extract single PDF to text
python ks_pdf_extract.py --input document.pdf --format txt

# Extract to markdown with custom output name
python ks_pdf_extract.py --input document.pdf --format md --output extracted_content.md

# Batch process all PDFs in a folder
python ks_pdf_extract.py --input ./pdfs/ --format md --batch
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. For GUI mode, also install CustomTkinter:
```bash
pip install customtkinter
```

3. Run the tool:
```bash
# GUI mode (recommended)
python gui_app.py

# CLI mode
python ks_pdf_extract.py --help
```

## Architecture

Following KS modular design principles:

```
KS_PDF_Extractor/
├── core/              # Core extraction logic
├── utils/             # Helper utilities
├── config/            # Configuration management
├── tests/             # Unit tests
├── ks_pdf_extract.py  # Main CLI interface
└── gui_app.py         # Modern GUI interface (CustomTkinter)
```

## Configuration

Customize behavior via `config/settings.json`:

- Output formatting options
- File naming conventions
- Processing preferences
- Quality settings

---

**Built with KS Standards:** Modular • Reusable • User-First • Performance-Focused