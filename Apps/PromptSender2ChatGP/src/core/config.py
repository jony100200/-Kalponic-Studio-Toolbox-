"""
Configuration management for the Prompt Sequencer application.
Handles loading and saving of application settings.
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any
import logging

@dataclass
class AppConfig:
    """Application configuration with default values"""
    
    # Global settings
    target_window: str = ""
    initial_delay: int = 3
    
    # Text mode settings
    text_paste_enter_grace: int = 400
    text_generation_wait: int = 45
    text_jitter_percent: int = 15
    text_auto_enter: bool = True
    
    # Image mode settings
    image_intra_delay: int = 300
    image_paste_enter_grace: int = 400
    image_generation_wait: int = 60
    image_jitter_percent: int = 15
    image_auto_enter: bool = True
    image_repeat_prompt: bool = True
    
    # Paths
    text_input_folder: str = ""
    image_input_folder: str = ""
    global_prompt_file: str = ""
    
    # Queue system
    image_queue_mode: bool = False
    image_queue_items: list = None
    
    _config_file: str = "settings.json"
    
    def __post_init__(self):
        """Load configuration after initialization"""
        if self.image_queue_items is None:
            self.image_queue_items = []
        self.load()
    
    def load(self) -> None:
        """Load configuration from file"""
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
                logging.info("Configuration loaded successfully")
            except Exception as e:
                logging.warning(f"Failed to load configuration: {e}")
    
    def save(self) -> None:
        """Save current configuration to file"""
        try:
            # Convert to dict, excluding private attributes
            config_dict = {k: v for k, v in asdict(self).items() if not k.startswith('_')}
            
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            logging.info("Configuration saved successfully")
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
    
    def get_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {k: v for k, v in asdict(self).items() if not k.startswith('_')}
