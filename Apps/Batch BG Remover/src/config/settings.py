"""
Configuration Management
KISS principle: Single source of truth for all settings
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from pathlib import Path
import json


@dataclass
class RemovalSettings:
    """Settings for background removal algorithms."""
    threshold: float = 0.5
    use_jit: bool = False
    model_path: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate settings are within acceptable ranges."""
        return 0.0 <= self.threshold <= 1.0


@dataclass
class UISettings:
    """UI-specific settings."""
    theme: str = "dark"
    show_preview: bool = False
    preview_size: tuple = (128, 128)
    window_geometry: str = "950x700"
    
    def validate(self) -> bool:
        """Validate UI settings."""
        return self.theme in ["dark", "light"] and len(self.preview_size) == 2


@dataclass
class ProcessingSettings:
    """Processing workflow settings."""
    output_format: str = "PNG"
    suffix: str = "_cleaned"
    create_subfolders: bool = True
    max_workers: int = 1
    batch_size: int = 10
    
    def validate(self) -> bool:
        """Validate processing settings."""
        return (self.output_format.upper() in ["PNG", "JPG", "JPEG", "WEBP"] and
                self.max_workers >= 1 and
                self.batch_size >= 1)


class ConfigManager:
    """
    SOLID: Single Responsibility - manages all configuration
    KISS: Simple API for getting/setting config values
    """
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.removal_settings = RemovalSettings()
        self.ui_settings = UISettings()
        self.processing_settings = ProcessingSettings()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Update settings from loaded data
                if 'removal' in data:
                    self._update_dataclass(self.removal_settings, data['removal'])
                if 'ui' in data:
                    self._update_dataclass(self.ui_settings, data['ui'])
                if 'processing' in data:
                    self._update_dataclass(self.processing_settings, data['processing'])
                    
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
    
    def _update_dataclass(self, obj, data: Dict[str, Any]):
        """Update dataclass instance with dictionary data."""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            data = {
                'removal': self.removal_settings.__dict__,
                'ui': self.ui_settings.__dict__,
                'processing': self.processing_settings.__dict__
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def validate_all(self) -> bool:
        """Validate all settings."""
        return (self.removal_settings.validate() and
                self.ui_settings.validate() and
                self.processing_settings.validate())
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.removal_settings = RemovalSettings()
        self.ui_settings = UISettings()
        self.processing_settings = ProcessingSettings()
        self.save_config()


# Global config instance - KISS principle
config = ConfigManager()