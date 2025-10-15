"""
Core image resizing functionality for KS Image Resize
"""

import os
from pathlib import Path
from typing import Callable, Optional, Tuple, List
from PIL import Image, ImageOps
import logging

logger = logging.getLogger(__name__)


class ImageResizer:
    """
    Handles image resizing operations with proper error handling and logging.
    Follows Single Responsibility Principle - only handles resizing logic.
    """

    def __init__(self, quality: int = 95):
        self.quality = quality

    @staticmethod
    def _parse_dimension(value: str) -> Optional[Tuple[str, float]]:
        """
        Parse dimension string into (type, value) tuple.

        Args:
            value: String like "800" or "50%"

        Returns:
            Tuple of (type, value) where type is 'abs' or 'pct', or None if invalid
        """
        if not value or not value.strip():
            return None

        value = value.strip()

        if value.endswith('%'):
            try:
                pct = float(value.rstrip('%')) / 100.0
                if 0 < pct <= 10.0:  # Allow up to 1000% scaling
                    return ('pct', pct)
                else:
                    logger.warning(f"Percentage {value} is out of reasonable range (0-1000%)")
                    return None
            except ValueError:
                logger.error(f"Invalid percentage format: {value}")
                return None

        try:
            abs_val = int(value)
            if abs_val > 0:
                return ('abs', abs_val)
            else:
                logger.warning(f"Absolute dimension must be positive: {value}")
                return None
        except ValueError:
            logger.error(f"Invalid dimension format: {value}")
            return None

    @staticmethod
    def _compute_target_dimension(
        src_dim: int,
        parsed_dim: Optional[Tuple[str, float]]
    ) -> Optional[int]:
        """
        Compute target dimension from source dimension and parsed dimension spec.

        Args:
            src_dim: Source dimension (width or height)
            parsed_dim: Parsed dimension specification

        Returns:
            Target dimension or None
        """
        if parsed_dim is None:
            return None

        typ, val = parsed_dim
        if typ == 'pct':
            return max(1, int(src_dim * val))
        return max(1, int(val))

    def _resize_single_image(
        self,
        src_path: Path,
        dest_path: Path,
        target_width: Optional[int],
        target_height: Optional[int]
    ) -> bool:
        """
        Resize a single image.

        Args:
            src_path: Source image path
            dest_path: Destination image path
            target_width: Target width or None
            target_height: Target height or None

        Returns:
            True if successful, False otherwise
        """
        try:
            with Image.open(src_path) as img:
                # Apply EXIF orientation correction
                img = ImageOps.exif_transpose(img)
                src_width, src_height = img.size

                # Use provided target dimensions directly
                final_width = target_width
                final_height = target_height

                # Preserve aspect ratio if one dimension is missing
                if final_width is None and final_height is not None:
                    final_width = max(1, int(src_width * (final_height / src_height)))
                elif final_height is None and final_width is not None:
                    final_height = max(1, int(src_height * (final_width / src_width)))
                elif final_width is None and final_height is None:
                    final_width, final_height = src_width, src_height

                # Resize image
                resized = img.resize((final_width, final_height), Image.LANCZOS)

                # Handle different image modes for saving
                ext = dest_path.suffix.lower()
                save_kwargs = {}

                if ext in ('.jpg', '.jpeg'):
                    save_kwargs['quality'] = self.quality
                    # Convert RGBA/P to RGB for JPEG
                    if resized.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new("RGB", resized.size, (255, 255, 255))
                        background.paste(resized, mask=resized.split()[-1] if resized.mode == 'RGBA' else resized)
                        background.save(dest_path, **save_kwargs)
                    else:
                        resized.save(dest_path, **save_kwargs)
                else:
                    # For other formats, save as-is
                    if ext in ('.jpg', '.jpeg'):
                        save_kwargs['quality'] = self.quality
                    resized.save(dest_path, **save_kwargs)

                logger.debug(f"Resized {src_path} to {dest_path} ({final_width}x{final_height})")
                return True

        except Exception as e:
            logger.error(f"Failed to resize {src_path}: {e}")
            return False

    def resize_batch(
        self,
        input_dir: Path,
        output_dir: Path,
        width_spec: str = "",
        height_spec: str = "",
        progress_callback: Optional[Callable[[int, int, int, int], None]] = None
    ) -> Tuple[int, int]:
        """
        Resize all supported images in a directory.

        Args:
            input_dir: Input directory containing images
            output_dir: Output directory for resized images
            width_spec: Width specification ("800" or "50%")
            height_spec: Height specification ("600" or "75%")
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (success_count, failure_count)
        """
        # Parse dimension specifications
        width_parsed = self._parse_dimension(width_spec)
        height_parsed = self._parse_dimension(height_spec)

        if width_parsed is None and height_parsed is None:
            raise ValueError("At least one dimension (width or height) must be specified")

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Find supported image files
        supported_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
        image_files = [
            f for f in input_dir.iterdir()
            if f.is_file() and f.suffix.lower() in supported_exts
        ]

        if not image_files:
            logger.warning(f"No supported image files found in {input_dir}")
            return 0, 0

        total_files = len(image_files)
        success_count = 0
        failure_count = 0

        logger.info(f"Starting batch resize of {total_files} images from {input_dir} to {output_dir}")

        for i, src_file in enumerate(image_files, 1):
            dest_file = output_dir / src_file.name

            try:
                # Compute target dimensions for this specific image
                with Image.open(src_file) as img:
                    img = ImageOps.exif_transpose(img)
                    src_width, src_height = img.size

                    target_width = self._compute_target_dimension(src_width, width_parsed)
                    target_height = self._compute_target_dimension(src_height, height_parsed)

                if self._resize_single_image(src_file, dest_file, target_width, target_height):
                    success_count += 1
                else:
                    failure_count += 1

            except Exception as e:
                logger.error(f"Failed to process {src_file}: {e}")
                failure_count += 1

            # Report progress
            if progress_callback:
                progress_callback(i, total_files, success_count, failure_count)

        logger.info(f"Batch resize completed: {success_count} successful, {failure_count} failed")
        return success_count, failure_count

    def get_supported_formats(self) -> List[str]:
        """Get list of supported image formats."""
        return ['PNG', 'JPEG', 'BMP', 'TIFF', 'WebP']

    def validate_dimensions(self, width_spec: str, height_spec: str) -> bool:
        """
        Validate dimension specifications.

        Args:
            width_spec: Width specification
            height_spec: Height specification

        Returns:
            True if at least one dimension is valid
        """
        width_parsed = self._parse_dimension(width_spec)
        height_parsed = self._parse_dimension(height_spec)
        return width_parsed is not None or height_parsed is not None