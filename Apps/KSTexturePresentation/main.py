"""
Sprite Image Processor - Main Application Entry Point
Following KISS and SOLID principles
"""

from src.ui.main_window import MainWindow
from src.config.settings import Settings

def main():
    """Main application entry point"""
    settings = Settings()
    app = MainWindow(settings)
    app.run()

if __name__ == "__main__":
    main()
