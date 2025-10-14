"""
KS PDF Studio - Watermarking System
Advanced watermarking for PDF protection and branding.

Author: Kalponic Studio
Version: 2.0.0
"""

import os
import uuid
from typing import Dict, List, Optional, Union, Tuple, Any
from pathlib import Path
from datetime import datetime
import hashlib
import json

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.colors import Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Image
from reportlab.lib.units import inch

from PIL import Image as PILImage, ImageDraw, ImageFont
import io


class WatermarkConfig:
    """
    Configuration class for watermark settings.
    """

    def __init__(
        self,
        text: str = "DRAFT",
        font_size: int = 60,
        font_color: Tuple[float, float, float, float] = (0.5, 0.5, 0.5, 0.3),
        rotation: int = 45,
        position: str = "center",
        opacity: float = 0.3,
        font_path: Optional[str] = None,
        image_path: Optional[str] = None,
        scale: float = 1.0,
        tile: bool = False,
        pages: Union[str, List[int]] = "all"
    ):
        """
        Initialize watermark configuration.

        Args:
            text: Watermark text
            font_size: Font size for text watermarks
            font_color: RGBA color tuple (0-1 range)
            rotation: Rotation angle in degrees
            position: Position ('center', 'top-left', 'bottom-right', etc.)
            opacity: Opacity (0-1)
            font_path: Path to custom font file
            image_path: Path to image watermark
            scale: Scale factor for image watermarks
            tile: Whether to tile the watermark across the page
            pages: Which pages to apply watermark to ('all' or list of page numbers)
        """
        self.text = text
        self.font_size = font_size
        self.font_color = font_color
        self.rotation = rotation
        self.position = position
        self.opacity = opacity
        self.font_path = font_path
        self.image_path = image_path
        self.scale = scale
        self.tile = tile
        self.pages = pages

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'text': self.text,
            'font_size': self.font_size,
            'font_color': self.font_color,
            'rotation': self.rotation,
            'position': self.position,
            'opacity': self.opacity,
            'font_path': self.font_path,
            'image_path': self.image_path,
            'scale': self.scale,
            'tile': self.tile,
            'pages': self.pages
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WatermarkConfig':
        """Create config from dictionary."""
        return cls(**data)


class DigitalWatermark:
    """
    Invisible digital watermarking using steganography.
    """

    @staticmethod
    def embed_data(image_path: str, data: str, output_path: str) -> bool:
        """
        Embed invisible data in an image using LSB steganography.

        Args:
            image_path: Path to input image
            data: Data to embed
            output_path: Path to save watermarked image

        Returns:
            bool: Success status
        """
        try:
            # Convert data to binary
            binary_data = ''.join(format(ord(char), '08b') for char in data)
            binary_data += '00000000'  # Null terminator

            # Open image
            img = PILImage.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            pixels = list(img.getdata())
            new_pixels = []

            data_index = 0
            for pixel in pixels:
                r, g, b = pixel

                # Embed 1 bit per color channel
                if data_index < len(binary_data):
                    r = (r & ~1) | int(binary_data[data_index])
                    data_index += 1
                if data_index < len(binary_data):
                    g = (g & ~1) | int(binary_data[data_index])
                    data_index += 1
                if data_index < len(binary_data):
                    b = (b & ~1) | int(binary_data[data_index])
                    data_index += 1

                new_pixels.append((r, g, b))

            # Create new image
            new_img = PILImage.new('RGB', img.size)
            new_img.putdata(new_pixels)
            new_img.save(output_path)

            return True

        except Exception as e:
            print(f"Digital watermark embedding failed: {e}")
            return False

    @staticmethod
    def extract_data(image_path: str) -> Optional[str]:
        """
        Extract hidden data from a digitally watermarked image.

        Args:
            image_path: Path to watermarked image

        Returns:
            Optional[str]: Extracted data or None if not found
        """
        try:
            img = PILImage.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            pixels = list(img.getdata())
            binary_data = ''

            for pixel in pixels:
                r, g, b = pixel
                binary_data += str(r & 1)
                binary_data += str(g & 1)
                binary_data += str(b & 1)

            # Convert binary to text
            chars = []
            for i in range(0, len(binary_data) - 8, 8):
                byte = binary_data[i:i+8]
                if byte == '00000000':  # Null terminator
                    break
                chars.append(chr(int(byte, 2)))

            return ''.join(chars)

        except Exception as e:
            print(f"Digital watermark extraction failed: {e}")
            return None


class PDFWatermarker:
    """
    PDF watermarking system for KS PDF Studio.
    """

    def __init__(self):
        """Initialize the PDF watermarker."""
        self.configs: Dict[str, WatermarkConfig] = {}

    def add_watermark_config(self, name: str, config: WatermarkConfig):
        """
        Add a watermark configuration.

        Args:
            name: Configuration name
            config: WatermarkConfig instance
        """
        self.configs[name] = config

    def apply_watermark(
        self,
        input_pdf: str,
        output_pdf: str,
        watermark_name: str,
        page_size: Tuple[float, float] = A4
    ) -> bool:
        """
        Apply watermark to PDF.

        Args:
            input_pdf: Path to input PDF
            output_pdf: Path to output PDF
            watermark_name: Name of watermark configuration
            page_size: PDF page size

        Returns:
            bool: Success status
        """
        if watermark_name not in self.configs:
            print(f"Watermark configuration '{watermark_name}' not found")
            return False

        config = self.configs[watermark_name]

        try:
            # Import here to avoid circular imports
            from reportlab.pdfgen import canvas
            from reportlab.lib import pagesizes
            from PyPDF2 import PdfReader, PdfWriter

            # Read input PDF
            reader = PdfReader(input_pdf)
            writer = PdfWriter()

            # Process each page
            for page_num, page in enumerate(reader.pages):
                if not self._should_apply_to_page(page_num + 1, config.pages):
                    writer.add_page(page)
                    continue

                # Create watermark overlay
                packet = io.BytesIO()
                c = canvas.Canvas(packet, pagesize=page_size)

                # Apply watermark
                self._draw_watermark(c, config, page_size)

                c.save()
                packet.seek(0)

                # Merge with original page
                watermark_pdf = PdfReader(packet)
                if len(watermark_pdf.pages) > 0:
                    watermark_page = watermark_pdf.pages[0]
                    page.merge_page(watermark_page)

                writer.add_page(page)

            # Write output
            with open(output_pdf, 'wb') as f:
                writer.write(f)

            return True

        except Exception as e:
            print(f"PDF watermarking failed: {e}")
            return False

    def _draw_watermark(self, canvas_obj: canvas.Canvas, config: WatermarkConfig,
                       page_size: Tuple[float, float]):
        """
        Draw watermark on canvas.

        Args:
            canvas_obj: ReportLab canvas
            config: Watermark configuration
            page_size: Page size tuple
        """
        width, height = page_size

        # Set opacity
        canvas_obj.setFillColor(Color(*config.font_color))
        canvas_obj.setStrokeColor(Color(*config.font_color))

        if config.image_path and os.path.exists(config.image_path):
            # Image watermark
            self._draw_image_watermark(canvas_obj, config, width, height)
        else:
            # Text watermark
            self._draw_text_watermark(canvas_obj, config, width, height)

    def _draw_text_watermark(self, canvas_obj: canvas.Canvas, config: WatermarkConfig,
                           width: float, height: float):
        """
        Draw text watermark.

        Args:
            canvas_obj: ReportLab canvas
            config: Watermark configuration
            width: Page width
            height: Page height
        """
        canvas_obj.saveState()

        # Set font
        if config.font_path and os.path.exists(config.font_path):
            # Register custom font
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            font_name = f"custom_font_{hash(config.font_path)}"
            pdfmetrics.registerFont(TTFont(font_name, config.font_path))
            canvas_obj.setFont(font_name, config.font_size)
        else:
            canvas_obj.setFont("Helvetica-Bold", config.font_size)

        # Calculate position
        text_width = canvas_obj.stringWidth(config.text, canvas_obj._fontname, config.font_size)
        text_height = config.font_size

        x, y = self._calculate_position(config.position, text_width, text_height, width, height)

        # Apply rotation
        canvas_obj.translate(x, y)
        canvas_obj.rotate(config.rotation)

        if config.tile:
            # Tile watermark across page
            self._tile_text_watermark(canvas_obj, config, width, height)
        else:
            # Single watermark
            canvas_obj.drawString(0, 0, config.text)

        canvas_obj.restoreState()

    def _draw_image_watermark(self, canvas_obj: canvas.Canvas, config: WatermarkConfig,
                            width: float, height: float):
        """
        Draw image watermark.

        Args:
            canvas_obj: ReportLab canvas
            config: Watermark configuration
            width: Page width
            height: Page height
        """
        try:
            # Load image
            img = PILImage.open(config.image_path)
            img_width, img_height = img.size

            # Scale image
            scaled_width = img_width * config.scale
            scaled_height = img_height * config.scale

            # Calculate position
            x, y = self._calculate_position(config.position, scaled_width, scaled_height, width, height)

            # Apply rotation and opacity
            canvas_obj.saveState()
            canvas_obj.translate(x + scaled_width/2, y + scaled_height/2)
            canvas_obj.rotate(config.rotation)
            canvas_obj.translate(-scaled_width/2, -scaled_height/2)

            # Draw image with opacity
            rl_img = Image(config.image_path, scaled_width, scaled_height)
            rl_img.drawOn(canvas_obj, 0, 0)

            canvas_obj.restoreState()

        except Exception as e:
            print(f"Image watermark drawing failed: {e}")
            # Fallback to text watermark
            config.image_path = None
            self._draw_text_watermark(canvas_obj, config, width, height)

    def _tile_text_watermark(self, canvas_obj: canvas.Canvas, config: WatermarkConfig,
                           width: float, height: float):
        """
        Tile text watermark across the page.

        Args:
            canvas_obj: ReportLab canvas
            config: Watermark configuration
            width: Page width
            height: Page height
        """
        text_width = canvas_obj.stringWidth(config.text, canvas_obj._fontname, config.font_size)
        text_height = config.font_size

        # Calculate spacing
        spacing_x = text_width * 1.5
        spacing_y = text_height * 2

        # Calculate number of tiles needed
        num_x = int(width / spacing_x) + 2
        num_y = int(height / spacing_y) + 2

        # Draw tiles
        for i in range(num_x):
            for j in range(num_y):
                x = i * spacing_x - text_width/2
                y = j * spacing_y - text_height/2
                canvas_obj.drawString(x, y, config.text)

    def _calculate_position(self, position: str, item_width: float, item_height: float,
                          page_width: float, page_height: float) -> Tuple[float, float]:
        """
        Calculate watermark position.

        Args:
            position: Position string
            item_width: Watermark item width
            item_height: Watermark item height
            page_width: Page width
            page_height: Page height

        Returns:
            Tuple[float, float]: (x, y) coordinates
        """
        if position == "center":
            x = (page_width - item_width) / 2
            y = (page_height - item_height) / 2
        elif position == "top-left":
            x = item_width / 4
            y = page_height - item_height * 1.25
        elif position == "top-right":
            x = page_width - item_width * 1.25
            y = page_height - item_height * 1.25
        elif position == "bottom-left":
            x = item_width / 4
            y = item_height / 4
        elif position == "bottom-right":
            x = page_width - item_width * 1.25
            y = item_height / 4
        elif position == "top-center":
            x = (page_width - item_width) / 2
            y = page_height - item_height * 1.25
        elif position == "bottom-center":
            x = (page_width - item_width) / 2
            y = item_height / 4
        else:
            # Default to center
            x = (page_width - item_width) / 2
            y = (page_height - item_height) / 2

        return x, y

    def _should_apply_to_page(self, page_num: int, pages_config: Union[str, List[int]]) -> bool:
        """
        Check if watermark should be applied to a page.

        Args:
            page_num: Page number (1-indexed)
            pages_config: Pages configuration

        Returns:
            bool: Whether to apply watermark
        """
        if pages_config == "all":
            return True
        elif isinstance(pages_config, list):
            return page_num in pages_config
        else:
            return False

    def create_license_watermark(self, license_info: Dict[str, Any]) -> WatermarkConfig:
        """
        Create a watermark configuration for license protection.

        Args:
            license_info: License information

        Returns:
            WatermarkConfig: License watermark configuration
        """
        license_text = f"Licensed to: {license_info.get('user', 'Unknown')}\n"
        license_text += f"License: {license_info.get('type', 'Personal')}\n"
        license_text += f"Expires: {license_info.get('expiry', 'Never')}"

        return WatermarkConfig(
            text=license_text,
            font_size=12,
            font_color=(0.7, 0.7, 0.7, 0.8),
            rotation=0,
            position="bottom-center",
            opacity=0.8,
            tile=False
        )

    def create_branding_watermark(self, brand_info: Dict[str, Any]) -> WatermarkConfig:
        """
        Create a watermark configuration for branding.

        Args:
            brand_info: Brand information

        Returns:
            WatermarkConfig: Branding watermark configuration
        """
        brand_text = brand_info.get('text', 'BRAND')
        font_size = brand_info.get('font_size', 48)
        color = brand_info.get('color', (0.2, 0.2, 0.8, 0.2))

        return WatermarkConfig(
            text=brand_text,
            font_size=font_size,
            font_color=color,
            rotation=45,
            position="center",
            opacity=0.2,
            tile=True
        )


class WatermarkManager:
    """
    High-level watermark management for KS PDF Studio.
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize watermark manager.

        Args:
            config_dir: Directory to store watermark configurations
        """
        self.config_dir = Path(config_dir) if config_dir else Path.home() / ".ks_pdf_studio" / "watermarks"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.watermarker = PDFWatermarker()
        self.digital_watermark = DigitalWatermark()

        self._load_configs()

    def _load_configs(self):
        """Load saved watermark configurations."""
        config_file = self.config_dir / "watermarks.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)

                for name, config_data in data.items():
                    config = WatermarkConfig.from_dict(config_data)
                    self.watermarker.add_watermark_config(name, config)

            except Exception as e:
                print(f"Failed to load watermark configs: {e}")

    def _save_configs(self):
        """Save watermark configurations."""
        config_file = self.config_dir / "watermarks.json"
        data = {}

        for name, config in self.watermarker.configs.items():
            data[name] = config.to_dict()

        try:
            with open(config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save watermark configs: {e}")

    def create_watermark(self, name: str, config: WatermarkConfig):
        """
        Create a new watermark configuration.

        Args:
            name: Watermark name
            config: Watermark configuration
        """
        self.watermarker.add_watermark_config(name, config)
        self._save_configs()

    def apply_watermark(self, input_pdf: str, output_pdf: str, watermark_name: str) -> bool:
        """
        Apply watermark to PDF.

        Args:
            input_pdf: Input PDF path
            output_pdf: Output PDF path
            watermark_name: Name of watermark to apply

        Returns:
            bool: Success status
        """
        return self.watermarker.apply_watermark(input_pdf, output_pdf, watermark_name)

    def get_available_watermarks(self) -> List[str]:
        """
        Get list of available watermark configurations.

        Returns:
            List[str]: List of watermark names
        """
        return list(self.watermarker.configs.keys())

    def create_digital_watermark(self, image_path: str, license_data: Dict[str, Any]) -> str:
        """
        Create a digitally watermarked image.

        Args:
            image_path: Path to input image
            license_data: License data to embed

        Returns:
            str: Path to watermarked image
        """
        # Create unique filename
        license_hash = hashlib.md5(json.dumps(license_data, sort_keys=True).encode()).hexdigest()[:8]
        output_path = f"{image_path.rsplit('.', 1)[0]}_watermarked_{license_hash}.{image_path.rsplit('.', 1)[1]}"

        # Embed license data
        license_json = json.dumps(license_data)
        success = self.digital_watermark.embed_data(image_path, license_json, output_path)

        return output_path if success else image_path

    def verify_digital_watermark(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Verify and extract digital watermark from image.

        Args:
            image_path: Path to potentially watermarked image

        Returns:
            Optional[Dict[str, Any]]: Extracted license data or None
        """
        extracted = self.digital_watermark.extract_data(image_path)
        if extracted:
            try:
                return json.loads(extracted)
            except:
                return None
        return None

    def create_premium_watermark(self, user_info: Dict[str, Any]) -> WatermarkConfig:
        """
        Create a premium watermark for paid content.

        Args:
            user_info: User information

        Returns:
            WatermarkConfig: Premium watermark configuration
        """
        watermark_text = f"© {datetime.now().year} {user_info.get('name', 'Content Creator')}\n"
        watermark_text += "Premium Content - All Rights Reserved\n"
        watermark_text += f"Generated by KS PDF Studio - {user_info.get('license', 'Personal')} License"

        return WatermarkConfig(
            text=watermark_text,
            font_size=14,
            font_color=(0.3, 0.3, 0.3, 0.6),
            rotation=0,
            position="bottom-center",
            opacity=0.6,
            tile=False
        )


# Convenience functions
def create_draft_watermark() -> WatermarkConfig:
    """Create a standard draft watermark."""
    return WatermarkConfig(
        text="DRAFT - CONFIDENTIAL",
        font_size=72,
        font_color=(1.0, 0.0, 0.0, 0.3),
        rotation=45,
        position="center",
        opacity=0.3,
        tile=True
    )


def create_sample_watermark() -> WatermarkConfig:
    """Create a sample watermark."""
    return WatermarkConfig(
        text="SAMPLE - NOT FOR DISTRIBUTION",
        font_size=60,
        font_color=(0.0, 0.5, 1.0, 0.4),
        rotation=30,
        position="center",
        opacity=0.4,
        tile=False
    )


def create_brand_watermark(brand_name: str, color: Tuple[float, float, float] = (0.2, 0.4, 0.8)) -> WatermarkConfig:
    """Create a brand watermark."""
    return WatermarkConfig(
        text=brand_name.upper(),
        font_size=48,
        font_color=(*color, 0.2),
        rotation=45,
        position="center",
        opacity=0.2,
        tile=True
    )


if __name__ == "__main__":
    # Test the watermarking system
    watermarker = PDFWatermarker()

    # Add some test configurations
    watermarker.add_watermark_config("draft", create_draft_watermark())
    watermarker.add_watermark_config("sample", create_sample_watermark())
    watermarker.add_watermark_config("brand", create_brand_watermark("KS Studio"))

    print("Watermark configurations created:")
    for name in watermarker.configs.keys():
        print(f"  - {name}")

    # Test digital watermarking
    digital_wm = DigitalWatermark()
    test_data = json.dumps({"license": "premium", "user": "test@example.com", "expiry": "2025-12-31"})

    print(f"\nDigital watermark test data: {test_data}")

    # Note: Would need actual image files to test digital watermarking
    print("Digital watermarking ready for use with image files")