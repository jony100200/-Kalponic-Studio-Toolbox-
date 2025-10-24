
import argparse
import zipfile
from pathlib import Path
from typing import Callable, Optional


def extract_first_image(
    zip_path: Path,
    output_dir: Optional[Path] = None,
    reporter: Optional[Callable[[str], None]] = None,
) -> Optional[Path]:
    """
    Extracts the first image found in a zip file.

    Args:
        zip_path: Path to the zip file.
        output_dir: Directory to save the extracted image. Defaults to the zip's parent.
        reporter: Optional callable used to emit status messages.

    Returns:
        The path to the extracted image, or None if no image was found or an error occurred.
    """
    reporter = reporter or print
    image_extensions = [".png", ".jpg", ".jpeg", ".gif", ".bmp"]
    target_dir = output_dir or zip_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.is_dir():
                    continue
                if any(file_info.filename.lower().endswith(ext) for ext in image_extensions):
                    image_data = zip_ref.read(file_info.filename)
                    output_filename = zip_path.stem + Path(file_info.filename).suffix
                    output_path = target_dir / output_filename
                    with open(output_path, "wb") as file_handle:
                        file_handle.write(image_data)
                    reporter(f"Extracted '{file_info.filename}' to '{output_path}'")
                    return output_path
    except zipfile.BadZipFile as exc:
        reporter(f"Failed to open '{zip_path}': {exc}")
        return None

    reporter(f"No image found in the zip file: '{zip_path.name}'")
    return None

def main():
    """
    Main function to parse arguments and initiate image extraction.
    """
    parser = argparse.ArgumentParser(
        description="Extract the first image from zip files and save them with the zip file's name."
    )
    parser.add_argument(
        "zip_file",
        nargs="?",
        help="Path to the zip file (optional - if not provided, processes all .zip files in current directory).",
    )
    parser.add_argument(
        "--output",
        "-o",
        dest="output_dir",
        help="Optional directory to store extracted images. Defaults to the same location as each zip file.",
    )
    args = parser.parse_args()

    if args.zip_file:
        zip_paths = [Path(args.zip_file)]
    else:
        # Process all zip files in current directory
        zip_paths = sorted(Path(".").glob("*.zip"))
        if not zip_paths:
            print("No zip files found in current directory.")
            return

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    for zip_path in zip_paths:
        if not zip_path.is_file() or zip_path.suffix.lower() != ".zip":
            print(f"Skipping invalid file: {zip_path}")
            continue
        extract_first_image(zip_path.resolve(), output_dir)

if __name__ == "__main__":
    main()
