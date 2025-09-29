"""
KS Image Cleanup - Main Entry Point
Professional quality fringe removal and edge enhancement for AI-removed backgrounds.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.app_ui import AppUI
from src.controller import Controller

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('batch_cleanup.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main application entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Create controller and UI
        controller = Controller()
        app = AppUI(controller)

        logger.info("Starting KS Image Cleanup — professional quality fringe removal and edge enhancement")
        app.run()

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    main()
