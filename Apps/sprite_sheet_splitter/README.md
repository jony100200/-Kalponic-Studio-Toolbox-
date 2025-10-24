# Sprite Sheet Splitter

Split sprite grids into named frames using either a KS-branded UI or the original command-line workflow.

## Install Dependencies

```bash
pip install -r requirements.txt
```

## KS UI (PySide6)

```bash
python ui.py
```

### Highlights
- Process a single sprite sheet or batch an entire folder (with optional recursion).
- Configure grid dimensions via calibrated spin boxes.
- Live activity log and progress indicator styled with the KS Universal UI blueprint.

## Command Line Usage

```bash
python main.py /path/to/input_folder /path/to/output_folder rows cols
```

### Arguments

- `input_folder`: Folder containing sprite sheet images.
- `output_folder`: Destination for generated frames.
- `rows`: Number of rows in the sprite sheet grid.
- `cols`: Number of columns in the sprite sheet grid.

Each sprite sheet is inspected to ensure its dimensions are evenly divisible by the grid. Frames are saved as `<name>_rXX_cYY.<ext>` alongside a short summary when processing completes.
