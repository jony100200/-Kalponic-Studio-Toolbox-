"""
File organization module for KS MetaMaker
"""

from pathlib import Path
from typing import List
import shutil
import logging
from datetime import datetime

from .utils.config import Config

logger = logging.getLogger(__name__)


class FileOrganizer:
    """Handles moving files into organized folder structure"""

    def __init__(self, config: Config, output_dir: Path = None):
        self.config = config
        self.output_dir = output_dir

    def organize(self, file_path: Path, category: str) -> Path:
        """
        Move file to appropriate category folder

        Args:
            file_path: Current file path
            category: Category (props, backgrounds, characters)

        Returns:
            New organized file path
        """
        try:
            # Determine output directory
            output_base = self.output_dir if self.output_dir else self._get_output_base()

            # Create category folder
            category_folder = self._get_category_folder(category)
            target_dir = output_base / category_folder
            target_dir.mkdir(parents=True, exist_ok=True)

            # Move file
            target_path = target_dir / file_path.name

            # Handle duplicates
            counter = 1
            while target_path.exists():
                stem = target_path.stem
                suffix = target_path.suffix
                new_name = f"{stem}_{counter}{suffix}"
                target_path = target_dir / new_name
                counter += 1

            # Move the file
            shutil.move(str(file_path), str(target_path))

            logger.info(f"Organized {file_path} -> {target_path}")
            return target_path

        except Exception as e:
            logger.error(f"Failed to organize {file_path}: {e}")
            return file_path

    def _get_output_base(self) -> Path:
        """Get base output directory"""
        # For now, use a default output directory
        # In the full app, this would be configurable
        output_dir = Path(__file__).parent.parent / "output"
        run_dir = output_dir / f"Run_{datetime.now().strftime('%Y%m%d_%H%M')}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _get_category_folder(self, category: str) -> str:
        """Get folder name for category"""
        category_map = {
            "props": "Props",
            "prop": "Props",
            "object": "Props",
            "backgrounds": "Backgrounds",
            "background": "Backgrounds",
            "scene": "Backgrounds",
            "characters": "Characters",
            "character": "Characters",
            "person": "Characters",
            "unknown": "Unknown"
        }

        return category_map.get(category.lower(), "Unknown")