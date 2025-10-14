"""
KS PDF Studio - Image Handler
Professional image processing for PDF generation.

Author: Kalponic Studio
Version: 2.0.0
"""

import os
import re
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path

from PIL import Image as PILImage, ImageFilter, ImageEnhance
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage

import warnings


class KSImageHandler:
    """
    Professional image processing for KS PDF Studio.

    Features:
    - Automatic image optimization for PDF
    - Size and quality management
    - Format conversion
    - Aspect ratio preservation
    - Compression optimization
    """

    # Supported image formats
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}

    # Default settings
    DEFAULT_MAX_WIDTH = 6 * inch      # 6 inches max width
    DEFAULT_MAX_HEIGHT = 8 * inch     # 8 inches max height
    DEFAULT_DPI = 150                 # Target DPI for PDF
    DEFAULT_QUALITY = 85              # JPEG quality (1-100)

    def __init__(
        self,
        max_width: float = DEFAULT_MAX_WIDTH,
        max_height: float = DEFAULT_MAX_HEIGHT,
        dpi: int = DEFAULT_DPI,
        quality: int = DEFAULT_QUALITY
    ):
        """
        Initialize the image handler.

        Args:
            max_width: Maximum image width in points
            max_height: Maximum image height in points
            dpi: Target DPI for images
            quality: JPEG compression quality
        """
        self.max_width = max_width
        self.max_height = max_height
        self.dpi = dpi
        self.quality = quality

    def process_image(
        self,
        image_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> Dict[str, Union[RLImage, str]]:
        """
        Process an image for PDF inclusion.

        Args:
            image_path: Path to source image
            output_path: Optional path to save processed image
            **kwargs: Additional processing options

        Returns:
            Dict with 'image' (RLImage) and 'path' (str) keys

        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If image format is unsupported
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        if image_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported image format: {image_path.suffix}")

        try:
            # Open and process image
            pil_image = PILImage.open(image_path)

            # Apply processing
            processed_image = self._optimize_image(pil_image, **kwargs)

            # Calculate final dimensions
            final_width, final_height = self._calculate_dimensions(processed_image)

            # Save processed image if output path provided
            if output_path:
                output_path = Path(output_path)
                self._save_image(processed_image, output_path)
                image_for_pdf = str(output_path)
            else:
                image_for_pdf = str(image_path)

            # Create ReportLab Image object
            rl_image = RLImage(image_for_pdf, width=final_width, height=final_height)

            return {
                'image': rl_image,
                'path': image_for_pdf,
                'original_size': pil_image.size,
                'final_size': (final_width, final_height),
                'format': processed_image.format or image_path.suffix[1:].upper()
            }

        except Exception as e:
            raise RuntimeError(f"Failed to process image {image_path}: {e}")

    def _optimize_image(self, pil_image: PILImage.Image, **kwargs) -> PILImage.Image:
        """
        Optimize image for PDF inclusion.

        Args:
            pil_image: PIL Image object
            **kwargs: Processing options

        Returns:
            Optimized PIL Image
        """
        # Convert to RGB if necessary (PDF doesn't support transparency well)
        if pil_image.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = PILImage.new('RGB', pil_image.size, (255, 255, 255))
            if pil_image.mode == 'P':
                pil_image = pil_image.convert('RGBA')
            background.paste(pil_image, mask=pil_image.split()[-1] if pil_image.mode == 'RGBA' else None)
            pil_image = background
        elif pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Resize if too large
        pil_image = self._resize_image(pil_image)

        # Apply enhancements if requested
        if kwargs.get('enhance', False):
            pil_image = self._enhance_image(pil_image, **kwargs)

        # Apply filters if requested
        if kwargs.get('filter'):
            pil_image = self._apply_filter(pil_image, kwargs['filter'])

        return pil_image

    def _resize_image(self, pil_image: PILImage.Image) -> PILImage.Image:
        """Resize image while maintaining aspect ratio."""
        width, height = pil_image.size
        aspect_ratio = height / width

        # Calculate new dimensions
        if width > self.max_width:
            new_width = self.max_width
            new_height = new_width * aspect_ratio
        else:
            new_width = width
            new_height = height

        # Check height constraint
        if new_height > self.max_height:
            new_height = self.max_height
            new_width = new_height / aspect_ratio

        # Only resize if necessary
        if new_width != width or new_height != height:
            # Use high-quality resampling
            pil_image = pil_image.resize(
                (int(new_width), int(new_height)),
                PILImage.Resampling.LANCZOS
            )

        return pil_image

    def _calculate_dimensions(self, pil_image: PILImage.Image) -> Tuple[float, float]:
        """Calculate final dimensions in points for PDF."""
        width, height = pil_image.size

        # Convert pixels to points (72 points per inch)
        # Assume 150 DPI for calculation
        width_points = (width / self.dpi) * 72
        height_points = (height / self.dpi) * 72

        return width_points, height_points

    def _enhance_image(self, pil_image: PILImage.Image, **kwargs) -> PILImage.Image:
        """Apply image enhancements."""
        # Contrast enhancement
        if 'contrast' in kwargs:
            enhancer = ImageEnhance.Contrast(pil_image)
            pil_image = enhancer.enhance(kwargs['contrast'])

        # Brightness enhancement
        if 'brightness' in kwargs:
            enhancer = ImageEnhance.Brightness(pil_image)
            pil_image = enhancer.enhance(kwargs['brightness'])

        # Sharpness enhancement
        if 'sharpness' in kwargs:
            enhancer = ImageEnhance.Sharpness(pil_image)
            pil_image = enhancer.enhance(kwargs['sharpness'])

        return pil_image

    def _apply_filter(self, pil_image: PILImage.Image, filter_name: str) -> PILImage.Image:
        """Apply image filters."""
        filter_map = {
            'blur': ImageFilter.BLUR,
            'sharpen': ImageFilter.UnsharpMask,
            'smooth': ImageFilter.SMOOTH,
            'detail': ImageFilter.DETAIL,
        }

        if filter_name in filter_map:
            pil_image = pil_image.filter(filter_map[filter_name])

        return pil_image

    def _save_image(self, pil_image: PILImage.Image, output_path: Path) -> None:
        """Save processed image with optimization."""
        # Determine format
        if output_path.suffix.lower() in ['.jpg', '.jpeg']:
            # Save as JPEG with quality optimization
            pil_image.save(output_path, 'JPEG', quality=self.quality, optimize=True)
        elif output_path.suffix.lower() == '.png':
            # Save as PNG with optimization
            pil_image.save(output_path, 'PNG', optimize=True)
        else:
            # Save in original format
            pil_image.save(output_path)

    def batch_process_images(
        self,
        image_paths: List[Union[str, Path]],
        output_dir: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> List[Dict[str, Union[RLImage, str]]]:
        """
        Process multiple images in batch.

        Args:
            image_paths: List of image paths
            output_dir: Directory to save processed images
            **kwargs: Processing options

        Returns:
            List of processed image dictionaries
        """
        results = []

        for image_path in image_paths:
            try:
                # Determine output path
                output_path = None
                if output_dir:
                    output_dir = Path(output_dir)
                    output_dir.mkdir(exist_ok=True)
                    output_path = output_dir / f"processed_{Path(image_path).name}"

                # Process image
                result = self.process_image(image_path, output_path, **kwargs)
                results.append(result)

            except Exception as e:
                warnings.warn(f"Failed to process {image_path}: {e}")
                continue

        return results

    def validate_image(self, image_path: Union[str, Path]) -> Dict[str, Union[bool, str, Tuple[int, int]]]:
        """
        Validate an image for PDF processing.

        Args:
            image_path: Path to image file

        Returns:
            Dict with validation results
        """
        image_path = Path(image_path)

        result = {
            'valid': False,
            'exists': image_path.exists(),
            'supported_format': False,
            'readable': False,
            'size': None,
            'warnings': []
        }

        if not result['exists']:
            result['error'] = 'File not found'
            return result

        if image_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            result['error'] = f'Unsupported format: {image_path.suffix}'
            return result

        result['supported_format'] = True

        try:
            with PILImage.open(image_path) as img:
                result['readable'] = True
                result['size'] = img.size
                result['mode'] = img.mode
                result['format'] = img.format

                # Check for potential issues
                if img.size[0] > 5000 or img.size[1] > 5000:
                    result['warnings'].append('Very large image - may impact PDF performance')

                if img.mode == 'P':
                    result['warnings'].append('Indexed color image - will be converted to RGB')

                if 'transparency' in img.info:
                    result['warnings'].append('Image has transparency - will be flattened')

                result['valid'] = True

        except Exception as e:
            result['error'] = f'Cannot read image: {e}'

        return result

    def get_image_info(self, image_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get detailed information about an image.

        Args:
            image_path: Path to image file

        Returns:
            Dict with image information
        """
        validation = self.validate_image(image_path)

        if not validation['valid']:
            return validation

        info = validation.copy()

        # Add additional processing info
        size = info['size']
        width, height = size

        info.update({
            'aspect_ratio': height / width if width > 0 else 0,
            'estimated_pdf_size': self._calculate_dimensions(PILImage.new('RGB', size)),
            'file_size_mb': os.path.getsize(image_path) / (1024 * 1024),
            'processing_needed': any([
                width > self.max_width,
                height > self.max_height,
                info['mode'] != 'RGB'
            ])
        })

        return info

    def _calculate_dimensions(self, pil_image: PILImage.Image) -> Tuple[float, float]:
        """Calculate PDF dimensions for a PIL image."""
        width, height = pil_image.size
        width_points = (width / self.dpi) * 72
        height_points = (height / self.dpi) * 72
        return width_points, height_points


class ImageProcessor:
    """Utility class for image processing operations."""

    @staticmethod
    def extract_images_from_markdown(markdown_content: str) -> List[str]:
        """Extract image paths from markdown content."""
        # Regex to find markdown image syntax ![alt](path)
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        matches = re.findall(image_pattern, markdown_content)
        return [match[1] for match in matches]

    @staticmethod
    def validate_image_paths(image_paths: List[str], base_dir: Optional[Path] = None) -> Dict[str, bool]:
        """Validate that image paths exist."""
        results = {}

        for path in image_paths:
            # Skip URLs
            if path.startswith(('http://', 'https://')):
                results[path] = True
                continue

            # Check local paths
            full_path = Path(base_dir) / path if base_dir else Path(path)
            results[path] = full_path.exists()

        return results

    @staticmethod
    def get_image_dimensions(image_path: Union[str, Path]) -> Optional[Tuple[int, int]]:
        """Get image dimensions without loading the full image."""
        try:
            with PILImage.open(image_path) as img:
                return img.size
        except:
            return None


# Convenience functions
def process_image_for_pdf(
    image_path: Union[str, Path],
    **kwargs
) -> Dict[str, Union[RLImage, str]]:
    """Quick function to process a single image for PDF."""
    handler = KSImageHandler(**kwargs)
    return handler.process_image(image_path)


def batch_process_images(
    image_paths: List[Union[str, Path]],
    **kwargs
) -> List[Dict[str, Union[RLImage, str]]]:
    """Quick function to batch process images."""
    handler = KSImageHandler(**kwargs)
    return handler.batch_process_images(image_paths)


if __name__ == "__main__":
    # Test the image handler
    handler = KSImageHandler()

    # Test with a sample image (assuming one exists)
    test_images = [
        "sample_image.jpg",  # Replace with actual test image
        "diagram.png",
        "screenshot.gif"
    ]

    for img_path in test_images:
        if os.path.exists(img_path):
            print(f"Processing {img_path}...")
            try:
                result = handler.process_image(img_path)
                print(f"✅ Processed: {result['path']}")
                print(f"   Original: {result['original_size']}")
                print(f"   Final: {result['final_size']}")
            except Exception as e:
                print(f"❌ Failed: {e}")
        else:
            print(f"⚠️  Image not found: {img_path}")

    print("Image processing test complete!")