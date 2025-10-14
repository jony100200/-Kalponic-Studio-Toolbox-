"""ks-splitter CLI entrypoint.

Command-line interface for KS Sprite Splitter.
"""
import argparse
import sys
import os
from pathlib import Path
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ks_splitter.pipeline import PipelineRunner


def load_config(config_path: str = None) -> dict:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'configs' / 'config.yml'

    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Could not load config {config_path}: {e}")
        return {}


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ks-splitter",
        description="KS Sprite Splitter - Auto-separate 2D sprites into semantic parts"
    )
    parser.add_argument(
        '--in', '--input', dest='input', required=True,
        help='Input image file or directory containing images'
    )
    parser.add_argument(
        '--out', '--output', dest='output', default='runs',
        help='Output directory for results (default: runs)'
    )
    parser.add_argument(
        '--category', dest='category', default='auto',
        choices=['auto', 'tree', 'flag', 'char', 'arch', 'vfx'],
        help='Template category to use (default: auto)'
    )
    parser.add_argument(
        '--objects', dest='objects_backend', default=None,
        help='Override segmentation backend'
    )
    parser.add_argument(
        '--matte', dest='matte_backend', default=None,
        help='Override matting backend'
    )
    parser.add_argument(
        '--parts', dest='parts_backend', default=None,
        help='Override parts backend'
    )
    parser.add_argument(
        '--workers', dest='workers', type=int, default=None,
        help='Number of worker threads'
    )
    parser.add_argument(
        '--config', dest='config_path',
        help='Path to config.yml file'
    )
    parser.add_argument(
        '--preview', dest='write_previews', action='store_true', default=None,
        help='Write preview images'
    )

    args = parser.parse_args(argv)

    # Load configuration
    config = load_config(args.config_path)

    # Override config with command line args
    if args.objects_backend:
        config['objects_backend'] = args.objects_backend
    if args.matte_backend:
        config['matte_backend'] = args.matte_backend
    if args.parts_backend:
        config['parts_backend'] = args.parts_backend
    if args.workers:
        config['performance']['workers'] = args.workers
    if args.write_previews is not None:
        config['export']['write_previews'] = args.write_previews

    # Set defaults for missing config
    config.setdefault('objects_backend', 'mock')
    config.setdefault('matte_backend', 'mock')
    config.setdefault('parts_backend', 'mock')
    config.setdefault('performance', {}).setdefault('workers', 1)
    config.setdefault('export', {}).setdefault('write_previews', True)
    config.setdefault('templates_dir', 'templates')

    print("KS Sprite Splitter")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Category: {args.category}")
    print(f"Backends: {config['objects_backend']}/{config['matte_backend']}/{config['parts_backend']}")
    print()

    # Check input exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input path does not exist: {args.input}")
        return 1

    # Create output directory
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        # Run pipeline
        runner = PipelineRunner(config)
        run_dir = runner.run(str(input_path), str(output_path), args.category)

        print(f"\n✅ Processing complete!")
        print(f"Results saved to: {run_dir}")
        return 0

    except Exception as e:
        print(f"ERROR: Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
