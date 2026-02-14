import logging
import os
from datetime import datetime

from src.automation.factory import build_automation
from src.core.config import AppConfig
from src.core.sequencer import VSCodeSequencer
from src.gui.main_window import VSCodePromptSenderGUI


def setup_logging():
    os.makedirs("logs", exist_ok=True)
    filename = f"ks_codeops_{datetime.now().strftime('%Y%m%d')}.log"
    path = os.path.join("logs", filename)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler(path), logging.StreamHandler()],
    )


def main():
    setup_logging()
    config = AppConfig()
    automation = build_automation(config)
    sequencer = VSCodeSequencer(automation, config)
    app = VSCodePromptSenderGUI(config, sequencer)
    app.run()


if __name__ == "__main__":
    main()
