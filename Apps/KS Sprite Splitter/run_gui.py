#!/usr/bin/env python3
"""
KS Sprite Splitter - GUI Launcher

Launch the PySide6 graphical user interface for KS Sprite Splitter.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Launch the GUI application."""
    try:
        from app.main_gui import main
        return main()
    except ImportError as e:
        print(f"Error importing GUI: {e}")
        print("Make sure PySide6 is installed: pip install PySide6")
        return 1
    except Exception as e:
        print(f"Error launching GUI: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())