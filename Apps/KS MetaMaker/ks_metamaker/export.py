"""
Dataset export module for KS MetaMaker
"""

from pathlib import Path
from typing import List
import json
import csv
import logging
from datetime import datetime

from .utils.config import Config

logger = logging.getLogger(__name__)


class DatasetExporter:
    """Handles exporting processed images and metadata"""

    def __init__(self, config: Config):
        self.config = config
        self.metadata = {
            "run_timestamp": datetime.now().isoformat(),
            "total_files": 0,
            "categories": {},
            "tags_summary": {}
        }

    def export(self, image_path: Path, tags: List[str]):
        """
        Export image with paired text file and update metadata

        Args:
            image_path: Path to the processed image
            tags: List of tags for the image
        """
        try:
            if self.config.export.get("paired_txt", True):
                self._create_paired_txt(image_path, tags)

            if self.config.export.get("write_metadata", True):
                self._update_metadata(image_path, tags)

            logger.info(f"Exported data for {image_path.name}")

        except Exception as e:
            logger.error(f"Failed to export {image_path}: {e}")

    def finalize_export(self, output_dir: Path):
        """Finalize export by writing summary files"""
        try:
            if self.config.export.get("write_metadata", True):
                self._write_metadata_file(output_dir)

            if self.config.export.get("package_zip", False):
                self._create_zip_package(output_dir)

            logger.info("Export finalized")

        except Exception as e:
            logger.error(f"Failed to finalize export: {e}")

    def _create_paired_txt(self, image_path: Path, tags: List[str]):
        """Create paired .txt file with tags"""
        txt_path = image_path.with_suffix('.txt')

        # Format tags as comma-separated string
        tag_string = ", ".join(tags)

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(tag_string)

        logger.debug(f"Created paired txt: {txt_path}")

    def _update_metadata(self, image_path: Path, tags: List[str]):
        """Update metadata with file information"""
        self.metadata["total_files"] += 1

        # Update category counts
        category = self._extract_category(image_path)
        if category not in self.metadata["categories"]:
            self.metadata["categories"][category] = 0
        self.metadata["categories"][category] += 1

        # Update tag summary
        for tag in tags:
            if tag not in self.metadata["tags_summary"]:
                self.metadata["tags_summary"][tag] = 0
            self.metadata["tags_summary"][tag] += 1

    def _write_metadata_file(self, output_dir: Path):
        """Write metadata JSON file"""
        metadata_path = output_dir / "metadata.json"

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

        # Also write CSV summary
        csv_path = output_dir / "tags_summary.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Tag", "Count"])
            for tag, count in sorted(self.metadata["tags_summary"].items(), key=lambda x: x[1], reverse=True):
                writer.writerow([tag, count])

        logger.info(f"Metadata written to {metadata_path}")

    def _create_zip_package(self, output_dir: Path):
        """Create ZIP package of the dataset (placeholder)"""
        # TODO: Implement ZIP creation
        logger.info("ZIP package creation not yet implemented")

    def _extract_category(self, image_path: Path) -> str:
        """Extract category from file path"""
        # Get the immediate parent directory name
        return image_path.parent.name