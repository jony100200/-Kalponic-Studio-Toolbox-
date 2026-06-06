import tkinter as tk
from src.core.config import AppConfig
import logging
import os
from datetime import datetime
import sys


def _load_gui_class():
    try:
        from src.gui.main_window import PromptSequencerGUI
        return PromptSequencerGUI
    except ModuleNotFoundError as exc:
        if exc.name == "customtkinter":
            requirements = os.path.abspath("requirements.txt")
            pip_cmd = f"\"{sys.executable}\" -m pip install -r \"{requirements}\""
            raise RuntimeError(
                "Missing dependency: customtkinter. "
                f"Current interpreter: {sys.executable}\n"
                f"Install app requirements and retry with:\n{pip_cmd}"
            ) from exc
        raise


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
        AppClass = _load_gui_class()
        app = AppClass(config)
        app.run()
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        if isinstance(e, RuntimeError):
            print(f"\n{e}")
            input("Press Enter to close . . .")
        raise

if __name__ == "__main__":
    main()
