"""
Configuration management for KS MetaMaker
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..profile_manager import ProfileManager, ProfileSchema


@dataclass
class Config:
    """Configuration class for KS MetaMaker"""

    # Profile system
    active_profile: Optional[ProfileSchema] = None
    profile_name: str = "custom"

    # UI settings - remember last used folders
    last_input_dir: str = ""
    last_output_dir: str = ""

    def __post_init__(self):
        # Initialize profile manager
        self._profile_manager = ProfileManager()

        # Load active profile
        if self.profile_name:
            try:
                self.active_profile = self._profile_manager.load_profile(self.profile_name)
            except FileNotFoundError:
                # Fallback to custom profile
                self.active_profile = self._get_default_profile()

    def _get_default_profile(self) -> ProfileSchema:
        """Get default profile when none is specified"""
        from ..profile_manager import ProfileSchema, ProfileType
        return ProfileSchema(
            name="custom",
            description="Default custom profile",
            profile_type=ProfileType.CUSTOM
        )

    # Profile-based property access
    @property
    def main_prefix(self) -> str:
        return self.active_profile.main_prefix if self.active_profile else ""

    @property
    def style_preset(self) -> str:
        return self.active_profile.style_preset if self.active_profile else ""

    @property
    def max_tags(self) -> Dict[str, int]:
        return self.active_profile.max_tags if self.active_profile else {"props": 20, "backgrounds": 25, "characters": 30}

    @property
    def rename_pattern(self) -> str:
        return self.active_profile.rename_pattern if self.active_profile else "{category}_{top_tags}_{YYYYMMDD}_{index}"

    @property
    def models(self) -> Dict[str, str]:
        return self.active_profile.models if self.active_profile else {
            "tagger": "openclip_vith14.onnx",
            "detector": "yolov11.onnx",
            "captioner": "blip2.onnx"
        }

    @property
    def performance(self) -> Dict[str, Any]:
        return self.active_profile.performance if self.active_profile else {
            "threads": 4,
            "batch_size": 4
        }

    @property
    def export(self) -> Dict[str, bool]:
        return self.active_profile.export if self.active_profile else {
            "paired_txt": True,
            "rename_images": True,
            "package_zip": True,
            "write_metadata": True
        }

    @property
    def normalization(self):
        return self.active_profile.normalization if self.active_profile else None

    @property
    def budget(self):
        return self.active_profile.budget if self.active_profile else None

    @classmethod
    def from_yaml(cls, config_path: Path) -> 'Config':
        """Load configuration from YAML file"""
        if not config_path.exists():
            # Return default config if file doesn't exist
            return cls()

        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Create config instance
        config = cls()
        config.profile_name = data.get('profile_name', 'custom')
        config.last_input_dir = data.get('last_input_dir', '')
        config.last_output_dir = data.get('last_output_dir', '')

        # Load the active profile
        try:
            config.active_profile = config._profile_manager.load_profile(config.profile_name)
        except FileNotFoundError:
            config.active_profile = config._get_default_profile()

        return config

    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from default location"""
        config_dir = Path(__file__).parent.parent.parent / "configs"
        config_file = config_dir / "config.yml"
        return cls.from_yaml(config_file)

    def switch_profile(self, profile_name: str) -> None:
        """Switch to a different profile"""
        try:
            self.active_profile = self._profile_manager.load_profile(profile_name)
            self.profile_name = profile_name
        except FileNotFoundError:
            raise ValueError(f"Profile '{profile_name}' not found")

    def get_available_profiles(self) -> list:
        """Get list of available profiles"""
        return self._profile_manager.list_profiles()

    def save_profile(self, profile: ProfileSchema) -> None:
        """Save a profile"""
        self._profile_manager.save_profile(profile)

    def get_model_path(self, model_type: str) -> Path:
        """Get full path to model file"""
        models_dir = Path(__file__).parent.parent.parent / "models"
        model_name = self.models.get(model_type, "")
        return models_dir / model_name

    def get_preset_config(self, preset_name: str) -> Dict[str, Any]:
        """Load preset configuration (legacy support)"""
        config_dir = Path(__file__).parent.parent.parent / "configs" / "presets"
        preset_file = config_dir / f"{preset_name}.yml"

        if preset_file.exists():
            with open(preset_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    def save(self):
        """Save current configuration to file"""
        config_dir = Path(__file__).parent.parent.parent / "configs"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.yml"

        # Convert to dict for YAML serialization
        config_dict = {
            "profile_name": self.profile_name,
            "last_input_dir": self.last_input_dir,
            "last_output_dir": self.last_output_dir
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False)