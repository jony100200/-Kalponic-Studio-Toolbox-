"""
Configuration management for the Prompt Sequencer application.
Handles loading and saving of application settings.
"""

import json
import os
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List
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
    image_intra_delay: int = 3000
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

    # Safety and execution controls
    dry_run: bool = False
    paste_max_retries: int = 3
    paste_retry_delay: float = 0.5
    focus_retries: int = 3
    enable_error_screenshots: bool = True
    error_screenshot_dir: str = "logs/error_screenshots"

    # Advanced features
    skip_duplicates: bool = False
    prompt_variables_enabled: bool = True
    queue_snapshot_enabled: bool = True
    queue_snapshot_file: str = "logs/queue_snapshot.json"
    auto_resume_queue_from_snapshot: bool = False

    # Saved presets
    profiles: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    _config_file: str = "settings.json"
    
    def __post_init__(self):
        """Load configuration after initialization"""
        if self.image_queue_items is None:
            self.image_queue_items = []
        if self.profiles is None:
            self.profiles = {}
        self.load()
        self.sanitize()
    
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
                self.sanitize()
            except Exception as e:
                logging.warning(f"Failed to load configuration: {e}")
    
    def save(self) -> None:
        """Save current configuration to file"""
        try:
            self.sanitize()
            # Convert to dict, excluding private attributes
            config_dict = {k: v for k, v in asdict(self).items() if not k.startswith('_')}

            temp_file = f"{self._config_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            os.replace(temp_file, self._config_file)
            logging.info("Configuration saved successfully")
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
    
    def get_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {k: v for k, v in asdict(self).items() if not k.startswith('_')}

    def sanitize(self) -> None:
        """Clamp and normalize configuration values to safe ranges."""
        self.initial_delay = self._clamp_int(self.initial_delay, 0, 600, 3)

        self.text_paste_enter_grace = self._clamp_int(self.text_paste_enter_grace, 0, 30000, 400)
        self.text_generation_wait = self._clamp_int(self.text_generation_wait, 0, 7200, 45)
        self.text_jitter_percent = self._clamp_int(self.text_jitter_percent, 0, 100, 15)
        self.text_auto_enter = bool(self.text_auto_enter)

        self.image_intra_delay = self._clamp_int(self.image_intra_delay, 0, 30000, 3000)
        self.image_paste_enter_grace = self._clamp_int(self.image_paste_enter_grace, 0, 30000, 400)
        self.image_generation_wait = self._clamp_int(self.image_generation_wait, 0, 7200, 60)
        self.image_jitter_percent = self._clamp_int(self.image_jitter_percent, 0, 100, 15)
        self.image_auto_enter = bool(self.image_auto_enter)
        self.image_repeat_prompt = bool(self.image_repeat_prompt)

        self.image_queue_mode = bool(self.image_queue_mode)
        if not isinstance(self.image_queue_items, list):
            self.image_queue_items = []

        self.dry_run = bool(self.dry_run)
        self.paste_max_retries = self._clamp_int(self.paste_max_retries, 1, 10, 3)
        self.paste_retry_delay = self._clamp_float(self.paste_retry_delay, 0.05, 10.0, 0.5)
        self.focus_retries = self._clamp_int(self.focus_retries, 1, 10, 3)
        self.enable_error_screenshots = bool(self.enable_error_screenshots)

        self.skip_duplicates = bool(self.skip_duplicates)
        self.prompt_variables_enabled = bool(self.prompt_variables_enabled)
        self.queue_snapshot_enabled = bool(self.queue_snapshot_enabled)
        self.auto_resume_queue_from_snapshot = bool(self.auto_resume_queue_from_snapshot)

        self.error_screenshot_dir = str(self.error_screenshot_dir or "logs/error_screenshots")
        self.queue_snapshot_file = str(self.queue_snapshot_file or "logs/queue_snapshot.json")

        self.target_window = str(self.target_window or "")
        self.text_input_folder = str(self.text_input_folder or "")
        self.image_input_folder = str(self.image_input_folder or "")
        self.global_prompt_file = str(self.global_prompt_file or "")

        if not isinstance(self.profiles, dict):
            self.profiles = {}

    def save_profile(self, name: str) -> bool:
        """Save the current settings as a named profile."""
        profile_name = (name or "").strip()
        if not profile_name:
            return False

        self.sanitize()
        snapshot = self.get_dict()
        snapshot.pop("profiles", None)
        self.profiles[profile_name] = snapshot
        return True

    def apply_profile(self, name: str) -> bool:
        """Apply a previously saved profile."""
        profile_name = (name or "").strip()
        if not profile_name:
            return False

        profile = self.profiles.get(profile_name)
        if not isinstance(profile, dict):
            return False

        for key, value in profile.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.sanitize()
        return True

    def list_profiles(self) -> List[str]:
        """Return available profile names."""
        return sorted(self.profiles.keys())

    @staticmethod
    def _clamp_int(value: Any, min_value: int, max_value: int, default: int) -> int:
        """Convert to int and clamp to range."""
        try:
            parsed = int(value)
        except Exception:
            parsed = default
        return max(min_value, min(max_value, parsed))

    @staticmethod
    def _clamp_float(value: Any, min_value: float, max_value: float, default: float) -> float:
        """Convert to float and clamp to range."""
        try:
            parsed = float(value)
        except Exception:
            parsed = default
        return max(min_value, min(max_value, parsed))
