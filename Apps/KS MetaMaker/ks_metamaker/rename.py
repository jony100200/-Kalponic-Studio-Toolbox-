"""
File renaming module for KS MetaMaker
"""

from pathlib import Path
from typing import List
import re
import logging
from datetime import datetime

from .utils.config import Config

logger = logging.getLogger(__name__)


class FileRenamer:
    """Handles intelligent file renaming based on tags and templates"""

    def __init__(self, config: Config):
        self.config = config

    def rename(self, file_path: Path, tags: List[str]) -> Path:
        """
        Rename file based on tags and configuration template

        Args:
            file_path: Original file path
            tags: List of tags for the file

        Returns:
            New file path (not moved yet, just renamed)
        """
        try:
            # Get the template
            template = self.config.rename_pattern

            # Extract components from template
            new_name = self._apply_template(template, file_path, tags)

            # Clean the filename
            new_name = self._clean_filename(new_name)

            # Create new path with same directory but new name
            new_path = file_path.parent / f"{new_name}{file_path.suffix}"

            # Handle duplicates by adding counter
            counter = 1
            while new_path.exists():
                stem = new_name
                new_name_with_counter = f"{stem}_{counter}"
                new_path = file_path.parent / f"{new_name_with_counter}{file_path.suffix}"
                counter += 1

            # Actually rename/move the file
            import shutil
            shutil.move(str(file_path), str(new_path))

            logger.info(f"Renamed {file_path.name} -> {new_path.name}")
            return new_path

        except Exception as e:
            logger.error(f"Failed to rename {file_path}: {e}")
            return file_path

    def _apply_template(self, template: str, file_path: Path, tags: List[str]) -> str:
        """Apply template variables to generate new filename"""
        # Current date
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M")

        # Extract category from tags (first tag is usually category-related)
        category = "unknown"
        if tags:
            first_tag = tags[0].lower()
            if "background" in first_tag:
                category = "background"
            elif "prop" in first_tag or "object" in first_tag:
                category = "prop"
            elif "character" in first_tag or "person" in first_tag:
                category = "character"

        # Top tags (excluding the main prefix)
        filtered_tags = [tag for tag in tags[1:] if tag not in self.config.style_preset.split(', ')]
        top_tags = "_".join(filtered_tags[:3])  # First 3 tags

        # Replace template variables
        result = template
        result = result.replace("{category}", category)
        result = result.replace("{top_tags}", top_tags)
        result = result.replace("{YYYYMMDD}", date_str)
        result = result.replace("{index}", "001")  # Will be handled by duplicate check

        return result

    def _clean_filename(self, filename: str) -> str:
        """Clean filename to be filesystem-safe"""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Remove multiple underscores
        while '__' in filename:
            filename = filename.replace('__', '_')

        # Remove leading/trailing underscores and spaces
        filename = filename.strip('_ ')

        # Limit length
        if len(filename) > 100:
            filename = filename[:100].strip('_ ')

        return filename