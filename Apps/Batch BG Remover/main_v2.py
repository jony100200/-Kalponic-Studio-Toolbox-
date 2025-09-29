#!/usr/bin/env python3
"""
Enhanced Batch Background Remover v2.0
Dual-mode system with KISS and SOLID principles

Main entry point for the application.
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ui import MainWindow
from src.config import config


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("bg_remover.log", encoding="utf-8")
        ]
    )
    
    # Reduce noise from some libraries
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def main():
    """Main application entry point."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger("main")
    
    try:
        logger.info("=" * 60)
        logger.info("Starting Enhanced Batch Background Remover v2.0")
        logger.info("Architecture: KISS + SOLID principles")
        logger.info("=" * 60)
        
        # Validate configuration
        if not config.validate_all():
            logger.warning("Configuration validation failed, using defaults")
            config.reset_to_defaults()
        
        # Create and run the application
        app = MainWindow()
        logger.info("Application initialized successfully")
        
        # Show remover info
        remover_info = app.controller.get_remover_info()
        logger.info(f"Active remover: {remover_info.get('name', 'Unknown')}")
        
        # Start the application
        logger.info("Starting GUI application...")
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Application shutting down")
        # Save any configuration changes
        config.save_config()


if __name__ == "__main__":
    main()