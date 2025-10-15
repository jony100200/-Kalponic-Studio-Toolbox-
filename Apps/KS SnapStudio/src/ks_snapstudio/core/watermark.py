"""
Watermarking and branding functionality for KS SnapStudio.
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple, Dict, Any, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class WatermarkEngine:
    """Handles watermarking, branding rings, and text overlays."""

    def __init__(self):
        self._default_font = None
        self._brand_colors = {
            'primary': (64, 128, 255),    # Blue
            'secondary': (255, 255, 255), # White
            'accent': (255, 128, 64),     # Orange
            'dark': (32, 32, 32)          # Dark gray
        }

    def add_brand_ring(self, image: np.ndarray,
                       circle_info: Dict[str, Any],
                       ring_width: int = 8,
                       ring_color: Tuple[int, int, int] = None) -> np.ndarray:
        """
        Add a branded ring around the circular preview.

        Args:
            image: Input image with alpha channel
            circle_info: Dict with 'center' and 'radius'
            ring_width: Width of the brand ring
            ring_color: RGB color tuple, defaults to brand blue

        Returns:
            Image with brand ring added
        """
        if ring_color is None:
            ring_color = self._brand_colors['primary']

        result = image.copy()
        center = circle_info['center']
        radius = circle_info['radius']

        # Create ring mask (outer ring minus inner circle)
        height, width = image.shape[:2]

        # Outer circle
        outer_mask = np.zeros((height, width), dtype=np.uint8)
        cv2.circle(outer_mask, center, radius + ring_width, 255, -1)

        # Inner circle (to subtract)
        inner_mask = np.zeros((height, width), dtype=np.uint8)
        cv2.circle(inner_mask, center, radius, 255, -1)

        # Ring mask = outer - inner
        ring_mask = cv2.subtract(outer_mask, inner_mask)

        # Apply ring color where mask is active
        ring_overlay = np.full_like(result, ring_color, dtype=np.uint8)
        ring_overlay[:, :, 3] = ring_mask  # Set alpha to ring mask

        # Composite ring over image
        result = self._composite_images(result, ring_overlay)

        return result

    def add_watermark_text(self, image: np.ndarray,
                          text: str,
                          position: str = "bottom_right",
                          font_size: int = 12,
                          color: Tuple[int, int, int] = None,
                          opacity: float = 0.7) -> np.ndarray:
        """
        Add watermark text to the image.

        Args:
            image: Input image
            text: Watermark text
            position: Position ("top_left", "top_right", "bottom_left", "bottom_right")
            font_size: Font size in pixels
            color: RGB color tuple
            opacity: Text opacity (0-1)

        Returns:
            Image with watermark text
        """
        if color is None:
            color = self._brand_colors['secondary']

        # Convert to PIL for text rendering
        pil_image = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_image, 'RGBA')

        # Get font
        font = self._get_font(font_size)

        # Calculate text position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        height, width = image.shape[:2]
        margin = 10

        if position == "top_left":
            x, y = margin, margin
        elif position == "top_right":
            x, y = width - text_width - margin, margin
        elif position == "bottom_left":
            x, y = margin, height - text_height - margin
        else:  # bottom_right
            x, y = width - text_width - margin, height - text_height - margin

        # Draw text with opacity
        rgba_color = color + (int(255 * opacity),)
        draw.text((x, y), text, fill=rgba_color, font=font)

        # Convert back to numpy array
        return np.array(pil_image)

    def add_corner_signature(self, image: np.ndarray,
                           signature: str = "KS",
                           size: int = 24,
                           position: str = "bottom_right") -> np.ndarray:
        """
        Add a small signature/corner mark.

        Args:
            image: Input image
            signature: Short signature text
            size: Size of the signature
            position: Corner position

        Returns:
            Image with signature added
        """
        return self.add_watermark_text(
            image,
            signature,
            position=position,
            font_size=size,
            color=self._brand_colors['primary'],
            opacity=0.8
        )

    def add_metadata_strip(self, image: np.ndarray,
                          metadata: Dict[str, str],
                          height: int = 30,
                          bg_color: Tuple[int, int, int] = None,
                          text_color: Tuple[int, int, int] = None) -> np.ndarray:
        """
        Add a metadata strip at the bottom of the image.

        Args:
            image: Input image
            metadata: Dict of key-value metadata pairs
            height: Height of the metadata strip
            bg_color: Background color for the strip
            text_color: Text color

        Returns:
            Image with metadata strip
        """
        if bg_color is None:
            bg_color = self._brand_colors['dark']
        if text_color is None:
            text_color = self._brand_colors['secondary']

        height_img, width_img = image.shape[:2]

        # Create metadata strip
        strip = np.full((height, width_img, 4), bg_color + (255,), dtype=np.uint8)

        # Convert to PIL for text
        pil_strip = Image.fromarray(strip)
        draw = ImageDraw.Draw(pil_strip)

        font = self._get_font(max(8, height - 8))

        # Format metadata text
        metadata_text = " | ".join(f"{k}: {v}" for k, v in metadata.items())

        # Draw text centered
        bbox = draw.textbbox((0, 0), metadata_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width_img - text_width) // 2
        y = (height - text_height) // 2

        draw.text((x, y), metadata_text, fill=text_color, font=font)

        # Convert back and composite
        strip = np.array(pil_strip)

        # Create new image with space for strip
        new_image = np.zeros((height_img + height, width_img, 4), dtype=np.uint8)

        # Copy original image
        new_image[:height_img] = image

        # Add strip at bottom
        new_image[height_img:] = strip

        return new_image

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get font for text rendering."""
        try:
            # Try to use a system font
            return ImageFont.truetype("arial.ttf", size)
        except OSError:
            try:
                return ImageFont.truetype("DejaVuSans.ttf", size)
            except OSError:
                # Fallback to default
                return ImageFont.load_default()

    def _composite_images(self, base: np.ndarray, overlay: np.ndarray) -> np.ndarray:
        """Composite two images with alpha blending."""
        # Ensure both images have alpha channels
        if base.shape[2] == 3:
            base = np.dstack([base, np.full(base.shape[:2], 255, dtype=np.uint8)])
        if overlay.shape[2] == 3:
            overlay = np.dstack([overlay, np.full(overlay.shape[:2], 255, dtype=np.uint8)])

        # Normalize alpha channels
        base_alpha = base[:, :, 3].astype(np.float32) / 255.0
        overlay_alpha = overlay[:, :, 3].astype(np.float32) / 255.0

        # Composite RGB channels
        result = np.zeros_like(base)
        for c in range(3):
            result[:, :, c] = (
                base[:, :, c] * base_alpha * (1 - overlay_alpha) +
                overlay[:, :, c] * overlay_alpha
            )

        # Composite alpha channel
        result[:, :, 3] = (base_alpha + overlay_alpha * (1 - base_alpha)) * 255

        return result.astype(np.uint8)

    def set_brand_colors(self, colors: Dict[str, Tuple[int, int, int]]):
        """Update brand colors."""
        self._brand_colors.update(colors)
        logger.info(f"Updated brand colors: {self._brand_colors}")</content>
<parameter name="filePath">E:\__Kalponic Studio Repositories\-Kalponic-Studio-Toolbox-\Apps\KS SnapStudio\src\ks_snapstudio\core\watermark.py