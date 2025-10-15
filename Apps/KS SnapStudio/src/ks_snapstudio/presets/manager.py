"""
Preset management for KS SnapStudio.
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PresetManager:
    """Manages export presets for different platforms and use cases."""

    def __init__(self):
        self._presets = {}
        self._load_default_presets()

    def _load_default_presets(self):
        """Load built-in presets."""
        self._presets = {
            # Social Media Platforms
            "discord_1024_light": {
                "name": "Discord 1024 Light",
                "description": "Discord material preview (1024px, light theme)",
                "size": 1024,
                "format": "png",
                "background": "solid",
                "palette": "neutral",
                "watermark": True,
                "brand_ring": True,
                "quality": 95,
                "metadata": {
                    "platform": "discord",
                    "theme": "light"
                }
            },
            "artstation_2048_dark": {
                "name": "ArtStation 2048 Dark",
                "description": "ArtStation portfolio preview (2048px, dark theme)",
                "size": 2048,
                "format": "png",
                "background": "gradient",
                "palette": "dark",
                "watermark": True,
                "brand_ring": True,
                "quality": 100,
                "metadata": {
                    "platform": "artstation",
                    "theme": "dark"
                }
            },
            "twitter_1200_warm": {
                "name": "Twitter/X 1200 Warm",
                "description": "Twitter material showcase (1200px, warm tones)",
                "size": 1200,
                "format": "jpg",
                "background": "solid",
                "palette": "warm",
                "watermark": True,
                "brand_ring": False,
                "quality": 90,
                "metadata": {
                    "platform": "twitter",
                    "theme": "warm"
                }
            },
            "reddit_1024_cool": {
                "name": "Reddit 1024 Cool",
                "description": "Reddit material post (1024px, cool tones)",
                "size": 1024,
                "format": "png",
                "background": "noise",
                "palette": "cool",
                "watermark": True,
                "brand_ring": False,
                "quality": 95,
                "metadata": {
                    "platform": "reddit",
                    "theme": "cool"
                }
            },

            # Professional Standards
            "print_300dpi": {
                "name": "Print 300 DPI",
                "description": "High-res print quality (300 DPI)",
                "size": 2000,  # ~6.5 inches at 300 DPI
                "format": "tiff",
                "background": "solid",
                "palette": "neutral",
                "watermark": False,
                "brand_ring": False,
                "quality": 100,
                "metadata": {
                    "use": "print",
                    "dpi": 300
                }
            },
            "web_hd": {
                "name": "Web HD",
                "description": "High-quality web display (1920px)",
                "size": 1920,
                "format": "webp",
                "background": "gradient",
                "palette": "neutral",
                "watermark": True,
                "brand_ring": True,
                "quality": 95,
                "metadata": {
                    "use": "web",
                    "quality": "hd"
                }
            },

            # Development & Testing
            "dev_small": {
                "name": "Dev Small",
                "description": "Small test preview (512px)",
                "size": 512,
                "format": "png",
                "background": "solid",
                "palette": "neutral",
                "watermark": False,
                "brand_ring": False,
                "quality": 90,
                "metadata": {
                    "use": "development"
                }
            },
            "dev_large": {
                "name": "Dev Large",
                "description": "Large test preview (2048px)",
                "size": 2048,
                "format": "png",
                "background": "checkerboard",
                "palette": "neutral",
                "watermark": True,
                "brand_ring": True,
                "quality": 100,
                "metadata": {
                    "use": "development"
                }
            }
        }

        logger.info(f"Loaded {len(self._presets)} default presets")

    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a preset by name."""
        return self._presets.get(name)

    def get_all_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get all available presets."""
        return self._presets.copy()

    def get_presets_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """Get presets for a specific platform."""
        return [
            preset for preset in self._presets.values()
            if preset.get('metadata', {}).get('platform') == platform
        ]

    def get_presets_by_use(self, use: str) -> List[Dict[str, Any]]:
        """Get presets for a specific use case."""
        return [
            preset for preset in self._presets.values()
            if preset.get('metadata', {}).get('use') == use
        ]

    def add_custom_preset(self, name: str, config: Dict[str, Any]) -> bool:
        """Add a custom preset."""
        try:
            # Validate required fields
            required_fields = ['name', 'size', 'format']
            for field in required_fields:
                if field not in config:
                    logger.error(f"Custom preset missing required field: {field}")
                    return False

            # Validate format
            valid_formats = ['png', 'jpg', 'jpeg', 'webp', 'tiff']
            if config['format'].lower() not in valid_formats:
                logger.error(f"Invalid format: {config['format']}")
                return False

            # Validate size
            if not isinstance(config['size'], int) or config['size'] <= 0:
                logger.error(f"Invalid size: {config['size']}")
                return False

            self._presets[name] = config
            logger.info(f"Added custom preset: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add custom preset {name}: {e}")
            return False

    def remove_preset(self, name: str) -> bool:
        """Remove a preset."""
        if name in self._presets:
            del self._presets[name]
            logger.info(f"Removed preset: {name}")
            return True
        return False

    def save_presets(self, filepath: Path) -> bool:
        """Save presets to JSON file."""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(self._presets, f, indent=2)
            logger.info(f"Saved presets to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save presets: {e}")
            return False

    def load_presets(self, filepath: Path) -> bool:
        """Load presets from JSON file."""
        try:
            with open(filepath, 'r') as f:
                custom_presets = json.load(f)

            # Merge with defaults (custom presets take precedence)
            self._presets.update(custom_presets)
            logger.info(f"Loaded {len(custom_presets)} presets from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load presets: {e}")
            return False

    def get_preset_names(self) -> List[str]:
        """Get list of all preset names."""
        return list(self._presets.keys())

    def get_preset_summary(self) -> List[Dict[str, str]]:
        """Get a summary of all presets."""
        return [
            {
                'name': name,
                'description': config.get('description', ''),
                'size': str(config.get('size', 'N/A')),
                'format': config.get('format', 'N/A'),
                'platform': config.get('metadata', {}).get('platform', 'general')
            }
            for name, config in self._presets.items()
        ]

    def create_platform_preset(self, platform: str, size: int,
                             theme: str = "neutral", **kwargs) -> str:
        """
        Create a new preset for a specific platform.

        Returns the preset name.
        """
        preset_name = f"{platform}_{size}_{theme}"

        config = {
            "name": f"{platform.title()} {size} {theme.title()}",
            "description": f"{platform.title()} material preview ({size}px, {theme} theme)",
            "size": size,
            "format": "png",
            "background": "solid",
            "palette": theme,
            "watermark": True,
            "brand_ring": True,
            "quality": 95,
            "metadata": {
                "platform": platform,
                "theme": theme
            }
        }

        # Override with any additional kwargs
        config.update(kwargs)

        self.add_custom_preset(preset_name, config)
        return preset_name</content>
<parameter name="filePath">E:\__Kalponic Studio Repositories\-Kalponic-Studio-Toolbox-\Apps\KS SnapStudio\src\ks_snapstudio\presets\manager.py