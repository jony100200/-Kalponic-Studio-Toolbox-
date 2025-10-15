"""
Configuration management for KS MetaMaker
"""

import yaml
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration class for KS MetaMaker"""

    # Main settings
    main_prefix: str = "kalponic studio background"
    style_preset: str = "cinematic lighting, 4k render"

    # Max tags per category
    max_tags: Dict[str, int] = None

    # Rename pattern
    rename_pattern: str = "{category}_{top_tags}_{YYYYMMDD}_{index}"

    # Model paths
    models: Dict[str, str] = None

    # Performance settings
    performance: Dict[str, Any] = None

    # Export settings
    export: Dict[str, bool] = None

    # UI settings - remember last used folders
    last_input_dir: str = ""
    last_output_dir: str = ""

    def __post_init__(self):
        if self.max_tags is None:
            self.max_tags = {
                "props": 20,
                "backgrounds": 25,
                "characters": 30
            }

        if self.models is None:
            self.models = {
                "tagger": "openclip_vith14.onnx",
                "detector": "yolov11.onnx",
                "captioner": "blip2.onnx"
            }

        if self.performance is None:
            self.performance = {
                "threads": 4,
                "batch_size": 4
            }

        if self.export is None:
            self.export = {
                "paired_txt": True,
                "rename_images": True,
                "package_zip": True,
                "write_metadata": True
            }

    @classmethod
    def from_yaml(cls, config_path: Path) -> 'Config':
        """Load configuration from YAML file"""
        if not config_path.exists():
            # Return default config if file doesn't exist
            return cls()

        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Create config instance with loaded data
        config = cls()

        # Update attributes from YAML
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config

    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from default location"""
        config_dir = Path(__file__).parent.parent.parent / "configs"
        config_file = config_dir / "config.yml"
        return cls.from_yaml(config_file)

    def get_model_path(self, model_type: str) -> Path:
        """Get full path to model file"""
        models_dir = Path(__file__).parent.parent.parent / "models"
        model_name = self.models.get(model_type, "")
        return models_dir / model_name

    def get_preset_config(self, preset_name: str) -> Dict[str, Any]:
        """Load preset configuration"""
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
            "main_prefix": self.main_prefix,
            "style_preset": self.style_preset,
            "max_tags": self.max_tags,
            "rename_pattern": self.rename_pattern,
            "models": self.models,
            "performance": self.performance,
            "export": self.export,
            "last_input_dir": self.last_input_dir,
            "last_output_dir": self.last_output_dir
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False)