"""Launcher for KS SnapClip

Supports command-line flags to override settings at startup, e.g. --enable-hotkeys, --start-minimized
"""

import argparse
from ui import main


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--enable-hotkeys', action='store_true', help='Enable global hotkeys on startup')
    p.add_argument('--start-minimized', action='store_true', help='Start minimized to tray')
    p.add_argument('--portable', action='store_true', help='Run in portable mode (store settings in app folder)')
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(start_minimized=args.start_minimized, enable_hotkeys=args.enable_hotkeys, portable=args.portable)
