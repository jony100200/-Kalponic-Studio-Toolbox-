"""ks-splitter CLI entrypoint.

Small CLI wrapper that will be expanded as the pipeline is implemented.
"""
import argparse
import sys
import os

from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ks-splitter", description="KS Sprite Splitter CLI")
    parser.add_argument("--in", dest="input", required=False, help="Input file or folder")
    parser.add_argument("--out", dest="out", required=False, help="Output folder")
    parser.add_argument("--category", dest="category", default="auto", help="Template category")
    parser.add_argument("--objects", dest="objects", default="sam2", help="Segmentation backend")
    parser.add_argument("--matte", dest="matte", default="modnet", help="Matting backend")
    parser.add_argument("--workers", dest="workers", type=int, default=1, help="Number of workers")
    args = parser.parse_args(argv)

    # Minimal behaviour for now: validate project layout and exit
    root = Path(__file__).resolve().parents[1]
    print(f"KS Sprite Splitter (root={root})")
    print(f"Input: {args.input}, Output: {args.out}, Category: {args.category}")

    # Check configs
    cfg = root / "configs" / "config.yml"
    if not cfg.exists():
        print("ERROR: config.yml missing in configs/")
        return 2

    print("Configuration present. CLI stub executed successfully.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
