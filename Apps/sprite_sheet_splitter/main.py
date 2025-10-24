import argparse
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence

from PIL import Image

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}


def split_sprite_sheet(
    image_path: Path,
    output_dir: Path,
    rows: int,
    cols: int,
    reporter: Optional[Callable[[str], None]] = None,
) -> List[Path]:
    """
    Splits a sprite sheet into individual frames.

    Args:
        image_path: Path to the sprite sheet image.
        output_dir: Directory to save the frames.
        rows: Number of rows in the sprite sheet.
        cols: Number of columns in the sprite sheet.
        reporter: Optional callable used to emit status messages.

    Returns:
        A list of generated frame paths. Empty if the operation failed.
    """
    reporter = reporter or print
    frames: List[Path] = []

    if rows <= 0 or cols <= 0:
        reporter(f"Skipping '{image_path.name}': rows and cols must be greater than zero.")
        return frames

    try:
        with Image.open(image_path) as img:
            width, height = img.size

            if width % cols != 0 or height % rows != 0:
                reporter(
                    f"Skipping '{image_path.name}': dimensions ({width}x{height}) "
                    f"are not divisible by {rows} row(s) and {cols} column(s)."
                )
                return frames

            frame_width = width // cols
            frame_height = height // rows

            output_dir.mkdir(parents=True, exist_ok=True)

            for row in range(rows):
                for col in range(cols):
                    left = col * frame_width
                    top = row * frame_height
                    right = left + frame_width
                    bottom = top + frame_height

                    frame = img.crop((left, top, right, bottom))
                    frame_filename = f"{image_path.stem}_r{row+1:02d}_c{col+1:02d}{image_path.suffix}"
                    frame_path = output_dir / frame_filename
                    frame.save(frame_path)
                    frames.append(frame_path)

            reporter(f"Split '{image_path.name}' into {rows * cols} frame(s).")
    except Exception as exc:  # pragma: no cover - defensive catch
        reporter(f"Error processing '{image_path.name}': {exc}")

    return frames


def process_sprite_sheets(
    image_paths: Sequence[Path],
    output_dir: Path,
    rows: int,
    cols: int,
    reporter: Optional[Callable[[str], None]] = None,
) -> int:
    """
    Process a batch of sprite sheets.

    Returns:
        Count of sprite sheets that produced at least one frame.
    """
    reporter = reporter or print
    output_dir.mkdir(parents=True, exist_ok=True)
    processed = 0

    for image_path in image_paths:
        frames = split_sprite_sheet(image_path, output_dir, rows, cols, reporter)
        if frames:
            processed += 1

    return processed


def iter_sprite_sheets(directory: Path) -> Iterable[Path]:
    """Yield image files inside a directory that look like sprite sheets."""
    for candidate in sorted(directory.iterdir()):
        if candidate.is_file() and candidate.suffix.lower() in IMAGE_EXTENSIONS:
            yield candidate


def main() -> None:
    """
    Main function to parse arguments and initiate sprite sheet splitting.
    """
    parser = argparse.ArgumentParser(description="Split sprite sheets into frames.")
    parser.add_argument("input_folder", help="Path to the folder containing sprite sheets.")
    parser.add_argument("output_folder", help="Path to the folder to save the frames.")
    parser.add_argument("rows", type=int, help="Number of rows in the sprite sheets.")
    parser.add_argument("cols", type=int, help="Number of columns in the sprite sheets.")
    args = parser.parse_args()

    input_dir = Path(args.input_folder)
    output_dir = Path(args.output_folder)

    if not input_dir.is_dir():
        print("Error: Input folder not found.")
        return

    sprite_sheets = list(iter_sprite_sheets(input_dir))
    if not sprite_sheets:
        print("No sprite sheet images found in input folder.")
        return

    processed = process_sprite_sheets(sprite_sheets, output_dir, args.rows, args.cols)
    print(f"Completed splitting {processed} sprite sheet(s).")


if __name__ == "__main__":
    main()
