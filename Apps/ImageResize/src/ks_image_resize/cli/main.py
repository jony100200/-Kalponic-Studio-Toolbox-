"""
Command Line Interface for KS Image Resize
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from ks_image_resize.config import ConfigManager
from ks_image_resize.core.resizer import ImageResizer


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        stream=sys.stderr  # Use stderr so capsys can capture it
    )


def create_argument_parser():
    """Create command line argument parser."""
    import argparse

    parser = argparse.ArgumentParser(
        description="KS Image Resize - Batch image resizing utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Resize all images in current directory to 800px width
  ks-image-resize . --width 800

  # Resize to 50% of original size
  ks-image-resize input/ output/ --width 50% --height 50%

  # Use preset dimensions
  ks-image-resize input/ --preset medium

  # Verbose output
  ks-image-resize input/ output/ --width 1920 --height 1080 --verbose
        """
    )

    parser.add_argument(
        'input_dir',
        nargs='?',  # Make it optional
        help='Input directory containing images'
    )

    parser.add_argument(
        'output_dir',
        nargs='?',  # Make it optional
        help='Output directory (default: input_dir/resized)'
    )

    parser.add_argument(
        '--width', '-w',
        help='Target width (pixels or percentage, e.g., 800 or 50%%)'
    )

    parser.add_argument(
        '--height',
        help='Target height (pixels or percentage, e.g., 600 or 75%%)'
    )

    parser.add_argument(
        '--preset', '-p',
        choices=['small', 'medium', 'large', 'hd', '4k'],
        help='Use predefined dimensions'
    )

    parser.add_argument(
        '--quality', '-q',
        type=int,
        default=95,
        choices=range(1, 101),
        metavar='[1-100]',
        help='JPEG quality (default: 95)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--list-presets',
        action='store_true',
        help='List available presets and exit'
    )

    return parser


def list_presets(config_manager: ConfigManager):
    """List available presets."""
    print("Available Presets:")
    print("-" * 40)

    for preset in config_manager.config.presets.values():
        size_info = ""
        if preset.width and preset.height:
            size_info = f"({preset.width}x{preset.height})"
        elif preset.width:
            size_info = f"(width: {preset.width})"
        elif preset.height:
            size_info = f"(height: {preset.height})"

        print(f"{preset.name} {size_info}")

    print("\nUsage: ks-image-resize input_dir --preset <name>")


def resolve_dimensions_from_preset(
    preset_name: str,
    config_manager: ConfigManager
) -> tuple[Optional[str], Optional[str]]:
    """Resolve width and height from preset name."""
    # Map CLI preset names to config preset names
    preset_mapping = {
        'small': 'Small (800x600)',
        'medium': 'Medium (1600x1200)',
        'large': 'Large (3840x2160)',
        'hd': 'HD (1920x1080)',
        '4k': '4K (3840x2160)'
    }

    config_preset_name = preset_mapping.get(preset_name, preset_name)
    preset = config_manager.get_preset(config_preset_name)
    if not preset:
        return None, None

    width = str(preset.width) if preset.width else None
    height = str(preset.height) if preset.height else None

    return width, height


def validate_args(args) -> bool:
    """Validate command line arguments."""
    # Must specify either dimensions or preset
    has_dimensions = args.width or args.height
    has_preset = args.preset

    if not has_dimensions and not has_preset:
        print("Error: Must specify either --width/--height or --preset", file=sys.stderr)
        return False

    if has_preset and has_dimensions:
        print("Error: Cannot specify both preset and custom dimensions", file=sys.stderr)
        return False

    # Validate input directory
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: Input directory does not exist: {input_dir}", file=sys.stderr)
        return False

    if not input_dir.is_dir():
        print(f"Error: Input path is not a directory: {input_dir}", file=sys.stderr)
        return False

    # Validate output directory if specified
    if args.output_dir:
        output_dir = Path(args.output_dir)
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error: Cannot create output directory: {e}", file=sys.stderr)
            return False

    return True


def main():
    """Main CLI entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Load configuration
    config_manager = ConfigManager()

    # Handle list presets command
    if args.list_presets:
        list_presets(config_manager)
        return 0

    # Validate that we have an input directory for actual processing
    if not args.input_dir:
        print("Error: input_dir is required for image processing", file=sys.stderr)
        parser.print_help()
        return 1

    # Validate input directory exists
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: Input directory does not exist: {input_dir}", file=sys.stderr)
        return 1

    if not input_dir.is_dir():
        print(f"Error: Input path is not a directory: {input_dir}", file=sys.stderr)
        return 1

    # Validate arguments for actual processing
    has_dimensions = args.width or args.height
    has_preset = args.preset

    if not has_dimensions and not has_preset:
        print("Error: Must specify either --width/--height or --preset", file=sys.stderr)
        return 1

    if has_preset and has_dimensions:
        print("Error: Cannot specify both preset and custom dimensions", file=sys.stderr)
        return 1

    # Resolve dimensions
    width_spec = args.width
    height_spec = args.height

    if args.preset:
        width_spec, height_spec = resolve_dimensions_from_preset(args.preset, config_manager)
        if width_spec is None and height_spec is None:
            print(f"Error: Unknown preset '{args.preset}'", file=sys.stderr)
            return 1

    # Setup directories
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir) if args.output_dir else input_dir / config_manager.config.default_output_subfolder

    # Create resizer
    resizer = ImageResizer(quality=args.quality)

    # Progress callback
    def progress_callback(current: int, total: int, success: int, failure: int):
        print(f"Progress: {current}/{total} (✓{success} ✗{failure})", end='\r', flush=True)

    try:
        logger.info(f"Starting batch resize: {input_dir} -> {output_dir}")
        logger.info(f"Dimensions: width={width_spec}, height={height_spec}")

        success_count, failure_count = resizer.resize_batch(
            input_dir=input_dir,
            output_dir=output_dir,
            width_spec=width_spec or "",
            height_spec=height_spec or "",
            progress_callback=progress_callback
        )

        print()  # New line after progress
        if failure_count == 0:
            print(f"Batch resize completed: ✓{success_count} successful")
        else:
            print(f"Batch resize completed: ✓{success_count} successful, ✗{failure_count} failed")

        if success_count > 0:
            print(f"Resized images saved to: {output_dir}")

        return 0 if failure_count == 0 else 1

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())