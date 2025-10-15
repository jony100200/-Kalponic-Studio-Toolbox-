"""
Configuration management for KS Image Resize
"""

import os
from pathlib import Path
from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
import yaml


@dataclass
class ResizePreset:
    """Represents a resize preset configuration."""
    name: str
    width: Optional[int] = None
    height: Optional[int] = None
    description: str = ""

    def to_tuple(self) -> Tuple[Optional[int], Optional[int]]:
        """Convert to tuple format for compatibility."""
        return (self.width, self.height)


@dataclass
class AppConfig:
    """Main application configuration."""
    presets: Dict[str, ResizePreset] = field(default_factory=dict)
    default_output_subfolder: str = "resized"
    supported_formats: list = field(default_factory=lambda: ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'])
    quality: int = 95
    theme: str = "dark"

    def __post_init__(self):
        """Initialize default presets if none provided."""
        if not self.presets:
            self._load_default_presets()

    def _load_default_presets(self):
        """Load default preset configurations."""
        self.presets = {
            "small": ResizePreset(
                name="Small (800x600)",
                width=800,
                height=600,
                description="Standard small size for web thumbnails"
            ),
            "medium": ResizePreset(
                name="Medium (1600x1200)",
                width=1600,
                height=1200,
                description="Medium size for social media and presentations"
            ),
            "large": ResizePreset(
                name="Large (3840x2160)",
                width=3840,
                height=2160,
                description="High resolution for professional printing"
            ),
            "hd": ResizePreset(
                name="HD (1920x1080)",
                width=1920,
                height=1080,
                description="Full HD resolution"
            ),
            "4k": ResizePreset(
                name="4K (3840x2160)",
                width=3840,
                height=2160,
                description="Ultra HD 4K resolution"
            ),
            "custom": ResizePreset(
                name="Custom",
                description="User-defined dimensions"
            )
        }


class ConfigManager:
    """Manages application configuration loading and saving."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or self._get_default_config_dir()
        self.config_file = self.config_dir / "config.yaml"
        self.config = self._load_config()

    def _get_default_config_dir(self) -> Path:
        """Get the default configuration directory."""
        if os.name == 'nt':  # Windows
            base_dir = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        else:  # Unix-like systems
            base_dir = Path.home() / '.config'

        return base_dir / 'ks-image-resize'

    def _load_config(self) -> AppConfig:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                return self._dict_to_config(data)
            except Exception:
                # If loading fails, use defaults
                pass

        return AppConfig()

    def _dict_to_config(self, data: Dict[str, Any]) -> AppConfig:
        """Convert dictionary to AppConfig object."""
        config = AppConfig()

        # Load presets
        if 'presets' in data:
            presets = {}
            for key, preset_data in data['presets'].items():
                presets[key] = ResizePreset(**preset_data)
            config.presets = presets

        # Load other settings
        for key, value in data.items():
            if key != 'presets' and hasattr(config, key):
                setattr(config, key, value)

        return config

    def save_config(self):
        """Save current configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        data = {
            'default_output_subfolder': self.config.default_output_subfolder,
            'supported_formats': self.config.supported_formats,
            'quality': self.config.quality,
            'theme': self.config.theme,
            'presets': {}
        }

        # Convert presets to dict
        for key, preset in self.config.presets.items():
            data['presets'][key] = {
                'name': preset.name,
                'width': preset.width,
                'height': preset.height,
                'description': preset.description
            }

        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_preset_names(self) -> list:
        """Get list of preset names for UI."""
        return [preset.name for preset in self.config.presets.values()]

    def get_preset(self, name: str) -> Optional[ResizePreset]:
        """Get preset by name."""
        for preset in self.config.presets.values():
            if preset.name == name:
                return preset
        return None

    def add_preset(self, preset: ResizePreset):
        """Add a new preset."""
        key = preset.name.lower().replace(' ', '_').replace('(', '').replace(')', '')
        self.config.presets[key] = preset
        self.save_config()

    def remove_preset(self, name: str):
        """Remove a preset by name."""
        keys_to_remove = []
        for key, preset in self.config.presets.items():
            if preset.name == name and key != 'custom':  # Don't remove custom
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.config.presets[key]

        self.save_config()