"""
Export functionality for KS SnapStudio.
"""

import cv2
import numpy as np
from PIL import Image
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PreviewExporter:
    """Handles exporting previews in various formats with metadata."""

    def __init__(self):
        self._supported_formats = {
            'png': self._export_png,
            'jpg': self._export_jpg,
            'jpeg': self._export_jpg,
            'webp': self._export_webp,
            'tiff': self._export_tiff,
        }

        # Size limits for safety
        self._max_dimension = 2048  # 2K limit
        self._max_file_size_mb = 10

    def export_preview(self, image: np.ndarray,
                      output_path: Path,
                      format_override: Optional[str] = None,
                      quality: int = 95,
                      metadata: Optional[Dict[str, Any]] = None,
                      resize_to_safe: bool = True) -> bool:
        """
        Export a preview image with safety checks and metadata.

        Args:
            image: Input image (RGB or RGBA)
            output_path: Output file path
            format_override: Force specific format (png, jpg, etc.)
            quality: JPEG/WebP quality (1-100)
            metadata: Additional metadata to embed
            resize_to_safe: Resize if dimensions exceed safety limits

        Returns:
            True if export successful
        """
        try:
            # Safety checks
            if not self._validate_image(image):
                logger.error("Image validation failed")
                return False

            # Resize if needed
            if resize_to_safe:
                image = self._ensure_safe_size(image)

            # Determine format
            if format_override:
                format_name = format_override.lower()
            else:
                format_name = output_path.suffix[1:].lower()  # Remove the dot

            if format_name not in self._supported_formats:
                logger.error(f"Unsupported format: {format_name}")
                return False

            # Prepare metadata
            if metadata is None:
                metadata = {}

            metadata.update({
                'exported_by': 'KS SnapStudio',
                'exported_at': datetime.now().isoformat(),
                'original_size': f"{image.shape[1]}x{image.shape[0]}",
            })

            # Export using appropriate method
            exporter = self._supported_formats[format_name]
            success = exporter(image, output_path, quality, metadata)

            if success:
                logger.info(f"Exported preview to {output_path} ({format_name})")
            else:
                logger.error(f"Export failed for {output_path}")

            return success

        except Exception as e:
            logger.error(f"Export error: {e}")
            return False

    def batch_export(self, images: List[np.ndarray],
                    output_dir: Path,
                    base_name: str = "preview",
                    format_name: str = "png",
                    quality: int = 95,
                    naming_pattern: str = "{base}_{index:03d}",
                    metadata: Optional[Dict[str, Any]] = None) -> List[Path]:
        """
        Export multiple images in batch.

        Args:
            images: List of images to export
            output_dir: Output directory
            base_name: Base name for files
            format_name: Export format
            quality: Export quality
            naming_pattern: Naming pattern with {base}, {index}, {timestamp}
            metadata: Base metadata for all exports

        Returns:
            List of exported file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        exported_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for i, image in enumerate(images):
            # Generate filename
            filename = naming_pattern.format(
                base=base_name,
                index=i+1,
                timestamp=timestamp
            )
            output_path = output_dir / f"{filename}.{format_name}"

            # Add per-image metadata
            image_metadata = metadata.copy() if metadata else {}
            image_metadata['batch_index'] = i + 1
            image_metadata['batch_total'] = len(images)

            # Export
            if self.export_preview(image, output_path, format_name, quality, image_metadata):
                exported_files.append(output_path)

        logger.info(f"Batch exported {len(exported_files)}/{len(images)} images")
        return exported_files

    def export_with_variants(self, image: np.ndarray,
                           output_dir: Path,
                           base_name: str,
                           variants: List[Dict[str, Any]]) -> List[Path]:
        """
        Export the same image in multiple variants.

        Args:
            image: Input image
            output_dir: Output directory
            base_name: Base name
            variants: List of variant configs (format, size, quality, etc.)

        Returns:
            List of exported file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        exported_files = []

        for variant in variants:
            format_name = variant.get('format', 'png')
            size = variant.get('size')
            quality = variant.get('quality', 95)
            suffix = variant.get('suffix', f"_{format_name}")

            # Resize if needed
            export_image = image
            if size:
                export_image = self._resize_image(image, size)

            # Generate filename
            filename = f"{base_name}{suffix}.{format_name}"
            output_path = output_dir / filename

            # Export
            metadata = variant.get('metadata', {})
            if self.export_preview(export_image, output_path, format_name, quality, metadata):
                exported_files.append(output_path)

        return exported_files

    def _validate_image(self, image: np.ndarray) -> bool:
        """Validate image before export."""
        if image is None or image.size == 0:
            return False

        if len(image.shape) not in [3, 4]:
            return False

        height, width = image.shape[:2]
        if width <= 0 or height <= 0 or width > 10000 or height > 10000:
            return False

        return True

    def _ensure_safe_size(self, image: np.ndarray) -> np.ndarray:
        """Resize image to safe dimensions if needed."""
        height, width = image.shape[:2]

        if width <= self._max_dimension and height <= self._max_dimension:
            return image

        # Calculate scale factor
        scale = self._max_dimension / max(width, height)

        new_width = int(width * scale)
        new_height = int(height * scale)

        # Resize using OpenCV
        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

        logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        return resized

    def _resize_image(self, image: np.ndarray, size: Union[int, Tuple[int, int]]) -> np.ndarray:
        """Resize image to specific dimensions."""
        if isinstance(size, int):
            # Square resize
            height, width = image.shape[:2]
            if width > height:
                new_width = size
                new_height = int(height * size / width)
            else:
                new_height = size
                new_width = int(width * size / height)
        else:
            new_width, new_height = size

        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        return resized

    def _export_png(self, image: np.ndarray, path: Path, quality: int, metadata: Dict[str, Any]) -> bool:
        """Export as PNG."""
        try:
            pil_image = Image.fromarray(image)
            pil_image.save(path, 'PNG')
            return True
        except Exception as e:
            logger.error(f"PNG export failed: {e}")
            return False

    def _export_jpg(self, image: np.ndarray, path: Path, quality: int, metadata: Dict[str, Any]) -> bool:
        """Export as JPEG."""
        try:
            # Convert RGBA to RGB if needed
            if image.shape[2] == 4:
                # Composite on white background
                rgb_image = image[:, :, :3]
                alpha = image[:, :, 3:4] / 255.0
                white_bg = np.full_like(rgb_image, 255)
                rgb_image = (rgb_image * alpha + white_bg * (1 - alpha)).astype(np.uint8)
            else:
                rgb_image = image

            pil_image = Image.fromarray(rgb_image)
            pil_image.save(path, 'JPEG', quality=quality, optimize=True)
            return True
        except Exception as e:
            logger.error(f"JPEG export failed: {e}")
            return False

    def _export_webp(self, image: np.ndarray, path: Path, quality: int, metadata: Dict[str, Any]) -> bool:
        """Export as WebP."""
        try:
            pil_image = Image.fromarray(image)
            pil_image.save(path, 'WebP', quality=quality)
            return True
        except Exception as e:
            logger.error(f"WebP export failed: {e}")
            return False

    def _export_tiff(self, image: np.ndarray, path: Path, quality: int, metadata: Dict[str, Any]) -> bool:
        """Export as TIFF."""
        try:
            pil_image = Image.fromarray(image)
            pil_image.save(path, 'TIFF', compression='lzw')
            return True
        except Exception as e:
            logger.error(f"TIFF export failed: {e}")
            return False

    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return list(self._supported_formats.keys())

    def estimate_file_size(self, image: np.ndarray, format_name: str, quality: int = 95) -> int:
        """Estimate file size for given format and quality."""
        # This is a rough estimate - actual implementation would need to export to temp file
        height, width = image.shape[:2]
        channels = image.shape[2]

        # Rough bytes per pixel estimates
        bpp_estimates = {
            'png': channels * 1.5,  # PNG is lossless but compressed
            'jpg': 0.3,  # JPEG compression
            'jpeg': 0.3,
            'webp': 0.4,
            'tiff': channels * 2.0,  # TIFF with LZW compression
        }

        bpp = bpp_estimates.get(format_name.lower(), 1.0)
        estimated_bytes = int(height * width * bpp)

        # Adjust for quality
        if format_name.lower() in ['jpg', 'jpeg', 'webp']:
            quality_factor = quality / 100.0
            estimated_bytes = int(estimated_bytes * (2.0 - quality_factor))

        return estimated_bytes</content>
<parameter name="filePath">E:\__Kalponic Studio Repositories\-Kalponic-Studio-Toolbox-\Apps\KS SnapStudio\src\ks_snapstudio\core\exporter.py