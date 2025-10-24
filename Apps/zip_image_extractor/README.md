
# Zip Image Extractor

Choose between a command-line workflow or a Kalponic Studio themed UI to extract the first image from one or more zip archives. Each extracted image is saved with the originating archive's filename.

## KS UI (PySide6)

```bash
python ui.py
```

### Features
- Process a single archive or an entire folder of zip files (with optional recursion).
- Optional output directory override.
- Live activity log and progress indicator implemented with the KS Universal UI System tokens.

## Command Line Usage

```bash
python main.py /path/to/your/file.zip
python main.py --output extracted /path/to/your/file.zip
python main.py            # processes all zip files in the current directory
```

## Description

The tool looks for the first file with an image extension (`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`) inside each zip file. If an image is found it is extracted to the selected output directory (defaults to the archive's folder) and saved with the archive's stem.

For example, if you have a file named `MyImages.zip` containing `images/preview.png`, running the script will create `MyImages.png` alongside the archive (or in the folder you specify with `--output`).
