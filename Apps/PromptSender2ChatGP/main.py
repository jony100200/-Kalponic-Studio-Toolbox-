import tkinter as tk
from src.gui.main_window import PromptSequencerGUI
from src.core.config import AppConfig
import logging
import os
from datetime import datetime

def setup_logging():
    """Setup logging configuration"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_filename = f"prompt_sequencer_{datetime.now().strftime('%Y%m%d')}.log"
    log_path = os.path.join(log_dir, log_filename)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )

def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config = AppConfig()
        
        # Create and run the GUI
        app = PromptSequencerGUI(config)
        app.run()
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        raise

if __name__ == "__main__":
    main()
