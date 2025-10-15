"""
Image ingestion module for KS MetaMaker
"""

from pathlib import Path
from typing import List, Dict
import hashlib
from PIL import Image
import logging

from .quality import QualityAssessor

logger = logging.getLogger(__name__)


class ImageIngester:
    """Handles ingestion of images from input directory"""

    # Supported image formats
    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}

    def __init__(self, enable_quality_filter: bool = True, enable_duplicate_detection: bool = True):
        self.enable_quality_filter = enable_quality_filter
        self.enable_duplicate_detection = enable_duplicate_detection
        self.quality_assessor = QualityAssessor() if enable_quality_filter else None
        self.processed_hashes: Dict[str, Path] = {}

    def ingest(self, input_dir: Path, min_quality_score: float = 0.3) -> List[Path]:
        """Ingest images from input directory with quality filtering"""
        if not input_dir.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")

        # Find all image files
        all_image_paths = self._find_image_files(input_dir)
        logger.info(f"Found {len(all_image_paths)} potential image files")

        # Filter by format and basic validity
        valid_images = self._filter_valid_images(all_image_paths)
        logger.info(f"Found {len(valid_images)} valid image files")

        # Quality filtering
        if self.enable_quality_filter and self.quality_assessor:
            quality_images = self.quality_assessor.filter_quality_images(valid_images, min_quality_score)
            logger.info(f"After quality filtering: {len(quality_images)} images")
        else:
            quality_images = valid_images

        # Duplicate detection
        if self.enable_duplicate_detection:
            unique_images = self._remove_duplicates(quality_images)
            logger.info(f"After duplicate removal: {len(unique_images)} images")
        else:
            unique_images = quality_images

        return unique_images

    def _find_image_files(self, input_dir: Path) -> List[Path]:
        """Find all image files in the input directory recursively"""
        image_paths = set()
        for ext in self.SUPPORTED_FORMATS:
            image_paths.update(input_dir.rglob(f"*{ext}"))
            image_paths.update(input_dir.rglob(f"*{ext.upper()}"))
        return sorted(list(image_paths))

    def _filter_valid_images(self, image_paths: List[Path]) -> List[Path]:
        """Filter out invalid or corrupted image files"""
        valid_images = []
        for path in image_paths:
            try:
                # Try to open the image to verify it's valid
                with Image.open(path) as img:
                    img.verify()
                valid_images.append(path)
            except Exception as e:
                logger.warning(f"Skipping invalid image {path}: {e}")
        return valid_images

    def _remove_duplicates(self, image_paths: List[Path]) -> List[Path]:
        """Remove duplicate images based on perceptual hashing"""
        if not self.quality_assessor:
            return image_paths

        unique_images = []
        seen_hashes = set()

        for path in image_paths:
            try:
                # Get perceptual hash
                image_hash = self.quality_assessor.get_image_hash(path)

                if image_hash not in seen_hashes:
                    seen_hashes.add(image_hash)
                    unique_images.append(path)
                else:
                    logger.info(f"Duplicate image detected and removed: {path}")

            except Exception as e:
                logger.warning(f"Error processing image {path} for duplicates: {e}")
                # Include images that can't be processed to avoid losing data
                unique_images.append(path)

        return unique_images
