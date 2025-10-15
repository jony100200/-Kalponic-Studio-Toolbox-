"""
Unit tests for KS SnapStudio core functionality.
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch

from ks_snapstudio.core.mask import CircleMask
from ks_snapstudio.core.watermark import WatermarkEngine
from ks_snapstudio.core.composer import BackgroundComposer
from ks_snapstudio.core.exporter import PreviewExporter
from ks_snapstudio.presets.manager import PresetManager


class TestCircleMask:
    """Test circle detection and masking functionality."""

    def setup_method(self):
        self.mask_tool = CircleMask()

    def test_detect_circle_perfect_circle(self):
        """Test circle detection on a perfect synthetic circle."""
        # Create a synthetic image with a perfect circle
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        center = (100, 100)
        radius = 50

        # Draw white circle on black background
        cv2 = pytest.importorskip("cv2")
        cv2.circle(img, center, radius, (255, 255, 255), 2)

        result = self.mask_tool.detect_circle(img)

        assert result is not None
        assert result['confidence'] > 0.5
        assert abs(result['center'][0] - center[0]) < 10
        assert abs(result['center'][1] - center[1]) < 10
        assert abs(result['radius'] - radius) < 5

    def test_detect_circle_no_circle(self):
        """Test circle detection on image with no circles."""
        img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        result = self.mask_tool.detect_circle(img)
        assert result is None

    def test_create_circular_mask(self):
        """Test circular mask creation."""
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        center = (50, 50)
        radius = 30

        mask = self.mask_tool.create_circular_mask(img, center, radius)

        assert mask.shape == (100, 100)
        assert mask.dtype == np.uint8
        assert mask[50, 50] == 255  # Center should be white
        assert mask[50, 80] < 128   # Edge should be semi-transparent

    def test_apply_mask(self):
        """Test mask application to image."""
        # Create test image and mask
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        mask = np.zeros((100, 100), dtype=np.uint8)
        cv2 = pytest.importorskip("cv2")
        cv2.circle(mask, (50, 50), 30, 255, -1)

        result = self.mask_tool.apply_mask(img, mask)

        assert result.shape == (100, 100, 4)  # Should have alpha channel
        assert result[50, 50, 3] == 255  # Center should be opaque
        assert result[0, 0, 3] == 0      # Outside circle should be transparent


class TestWatermarkEngine:
    """Test watermarking and branding functionality."""

    def setup_method(self):
        self.watermark_tool = WatermarkEngine()

    def test_add_brand_ring(self):
        """Test brand ring addition."""
        # Create RGBA test image
        img = np.ones((100, 100, 4), dtype=np.uint8) * 255
        circle_info = {'center': (50, 50), 'radius': 30}

        result = self.watermark_tool.add_brand_ring(img, circle_info)

        assert result.shape == img.shape
        # Ring should be visible around the circle
        assert not np.array_equal(result, img)

    def test_add_watermark_text(self):
        """Test text watermark addition."""
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        text = "TEST"

        result = self.watermark_tool.add_watermark_text(img, text)

        assert result.shape[0] >= img.shape[0]  # May add height for text
        assert result.shape[1] == img.shape[1]
        assert not np.array_equal(result, img)

    def test_add_corner_signature(self):
        """Test corner signature addition."""
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        signature = "KS"

        result = self.watermark_tool.add_corner_signature(img, signature)

        assert result.shape == img.shape
        assert not np.array_equal(result, img)


class TestBackgroundComposer:
    """Test background composition functionality."""

    def setup_method(self):
        self.composer = BackgroundComposer()

    def test_compose_solid_background(self):
        """Test solid background composition."""
        img = np.ones((100, 100, 4), dtype=np.uint8) * 255
        result = self.composer.compose_background(img, 'solid', 'neutral')

        assert result.shape == img.shape
        # Should have applied background where transparent
        assert not np.array_equal(result, img)

    def test_compose_gradient_background(self):
        """Test gradient background composition."""
        img = np.ones((100, 100, 4), dtype=np.uint8) * 255
        result = self.composer.compose_background(img, 'gradient', 'warm')

        assert result.shape == img.shape
        assert not np.array_equal(result, img)

    def test_get_available_palettes(self):
        """Test palette listing."""
        palettes = self.composer.get_available_palettes()
        assert isinstance(palettes, list)
        assert len(palettes) > 0
        assert 'neutral' in palettes

    def test_get_available_backgrounds(self):
        """Test background type listing."""
        backgrounds = self.composer.get_available_backgrounds()
        assert isinstance(backgrounds, list)
        assert len(backgrounds) > 0
        assert 'solid' in backgrounds


class TestPreviewExporter:
    """Test export functionality."""

    def setup_method(self):
        self.exporter = PreviewExporter()

    def test_validate_image_valid(self):
        """Test image validation with valid image."""
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        assert self.exporter._validate_image(img)

    def test_validate_image_invalid(self):
        """Test image validation with invalid images."""
        # Empty image
        assert not self.exporter._validate_image(np.array([]))

        # Wrong dimensions
        assert not self.exporter._validate_image(np.ones((100,), dtype=np.uint8))

        # Wrong channel count
        assert not self.exporter._validate_image(np.ones((100, 100), dtype=np.uint8))

    def test_get_supported_formats(self):
        """Test format listing."""
        formats = self.exporter.get_supported_formats()
        assert isinstance(formats, list)
        assert 'png' in formats
        assert 'jpg' in formats

    @patch('ks_snapstudio.core.exporter.Path')
    def test_estimate_file_size(self, mock_path):
        """Test file size estimation."""
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        size = self.exporter.estimate_file_size(img, 'png')
        assert isinstance(size, int)
        assert size > 0


class TestPresetManager:
    """Test preset management functionality."""

    def setup_method(self):
        self.preset_mgr = PresetManager()

    def test_get_preset(self):
        """Test preset retrieval."""
        preset = self.preset_mgr.get_preset('discord_1024_light')
        assert preset is not None
        assert preset['name'] == 'Discord 1024 Light'
        assert preset['size'] == 1024

    def test_get_all_presets(self):
        """Test all presets retrieval."""
        presets = self.preset_mgr.get_all_presets()
        assert isinstance(presets, dict)
        assert len(presets) > 0

    def test_get_presets_by_platform(self):
        """Test platform-based preset filtering."""
        discord_presets = self.preset_mgr.get_presets_by_platform('discord')
        assert isinstance(discord_presets, list)
        assert len(discord_presets) > 0

    def test_add_custom_preset(self):
        """Test custom preset addition."""
        config = {
            'name': 'Test Preset',
            'size': 512,
            'format': 'png',
            'background': 'solid',
            'palette': 'neutral'
        }

        success = self.preset_mgr.add_custom_preset('test_preset', config)
        assert success

        preset = self.preset_mgr.get_preset('test_preset')
        assert preset is not None
        assert preset['name'] == 'Test Preset'

    def test_preset_summary(self):
        """Test preset summary generation."""
        summary = self.preset_mgr.get_preset_summary()
        assert isinstance(summary, list)
        assert len(summary) > 0

        # Check structure
        item = summary[0]
        assert 'name' in item
        assert 'description' in item
        assert 'size' in item
        assert 'format' in item
        assert 'platform' in item</content>
<parameter name="filePath">E:\__Kalponic Studio Repositories\-Kalponic-Studio-Toolbox-\Apps\KS SnapStudio\tests\unit\test_core.py