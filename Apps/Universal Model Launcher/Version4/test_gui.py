"""
🚀 GUI Launcher Script
======================
Role: Test launcher for the PySide6 sci-fi interface
SOLID: Single responsibility for GUI testing
"""

import sys
import os
from pathlib import Path

# Add Version4 to Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

def test_gui():
    """🧪 Test the GUI components"""
    try:
        from GUI.main_window import main
        print("✅ Starting Universal Model Launcher V4 GUI...")
        main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure PySide6 is installed: pip install PySide6")
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")

if __name__ == "__main__":
    test_gui()
