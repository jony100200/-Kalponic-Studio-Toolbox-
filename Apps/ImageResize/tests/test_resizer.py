"""
Tests for KS Image Resize
"""

import pytest
import tempfile
from pathlib import Path
from PIL import Image
import shutil

from ks_image_resize.config import ConfigManager, ResizePreset, AppConfig
from ks_image_resize.core.resizer import ImageResizer


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_images(temp_dir):
    """Create sample test images."""
    # Create a simple test image
    img = Image.new('RGB', (1000, 800), color='red')
    img_path = temp_dir / "test_image.jpg"
    img.save(img_path, 'JPEG', quality=95)

    # Create another image with different dimensions
    img2 = Image.new('RGB', (800, 600), color='blue')
    img2_path = temp_dir / "test_image2.png"
    img2.save(img2_path, 'PNG')

    return [img_path, img2_path]


class TestConfigManager:
    """Test configuration management functionality."""

    def test_default_config(self, temp_dir):
        """Test loading default configuration."""
        config_manager = ConfigManager(temp_dir)
        assert config_manager.config.quality == 95
        assert config_manager.config.theme == "dark"
        assert len(config_manager.config.presets) > 0

    def test_preset_management(self, temp_dir):
        """Test preset creation and retrieval."""
        config_manager = ConfigManager(temp_dir)

        # Test getting preset names
        names = config_manager.get_preset_names()
        assert "Custom" in names
        assert "Small (800x600)" in names

        # Test getting specific preset
        preset = config_manager.get_preset("Small (800x600)")
        assert preset is not None
        assert preset.width == 800
        assert preset.height == 600

    def test_config_persistence(self, temp_dir):
        """Test saving and loading configuration."""
        config_manager = ConfigManager(temp_dir)

        # Modify config
        config_manager.config.quality = 85
        config_manager.save_config()

        # Load in new instance
        new_config_manager = ConfigManager(temp_dir)
        assert new_config_manager.config.quality == 85


class TestImageResizer:
    """Test core image resizing functionality."""

    def test_parse_dimension_absolute(self):
        """Test parsing absolute dimensions."""
        resizer = ImageResizer()

        # Test valid absolute values
        assert resizer._parse_dimension("800") == ('abs', 800)
        assert resizer._parse_dimension("  600  ") == ('abs', 600)

        # Test invalid values
        assert resizer._parse_dimension("") is None
        assert resizer._parse_dimension("abc") is None
        assert resizer._parse_dimension("0") is None

    def test_parse_dimension_percentage(self):
        """Test parsing percentage dimensions."""
        resizer = ImageResizer()

        # Test valid percentages
        assert resizer._parse_dimension("50%") == ('pct', 0.5)
        assert resizer._parse_dimension("200%") == ('pct', 2.0)

        # Test invalid percentages
        assert resizer._parse_dimension("1500%") is None  # Too high
        assert resizer._parse_dimension("0%") is None     # Too low
        assert resizer._parse_dimension("%") is None      # Invalid format

    def test_compute_target_dimension(self):
        """Test computing target dimensions."""
        resizer = ImageResizer()

        # Test absolute dimension
        assert resizer._compute_target_dimension(1000, ('abs', 800)) == 800

        # Test percentage dimension
        assert resizer._compute_target_dimension(1000, ('pct', 0.5)) == 500

        # Test None input
        assert resizer._compute_target_dimension(1000, None) is None

    def test_validate_dimensions(self):
        """Test dimension validation."""
        resizer = ImageResizer()

        # Valid cases
        assert resizer.validate_dimensions("800", "") == True
        assert resizer.validate_dimensions("", "600") == True
        assert resizer.validate_dimensions("50%", "75%") == True

        # Invalid cases
        assert resizer.validate_dimensions("", "") == False
        assert resizer.validate_dimensions("invalid", "") == False

    def test_resize_batch_basic(self, temp_dir, sample_images):
        """Test basic batch resizing functionality."""
        resizer = ImageResizer()
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Test resizing to absolute dimensions
        success, failure = resizer.resize_batch(
            input_dir=temp_dir,
            output_dir=output_dir,
            width_spec="500",
            height_spec="400"
        )

        assert success == 2  # Two images processed
        assert failure == 0

        # Check output files exist
        output_files = list(output_dir.glob("*"))
        assert len(output_files) == 2

        # Check dimensions of resized images
        for output_file in output_files:
            with Image.open(output_file) as img:
                assert img.size == (500, 400)

    def test_resize_batch_percentage(self, temp_dir, sample_images):
        """Test batch resizing with percentage dimensions."""
        resizer = ImageResizer()
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Test resizing to 50% of original size
        success, failure = resizer.resize_batch(
            input_dir=temp_dir,
            output_dir=output_dir,
            width_spec="50%",
            height_spec="50%"
        )

        assert success == 2
        assert failure == 0

        # Check output dimensions
        output_files = list(output_dir.glob("*"))
        assert len(output_files) == 2

        # First image should be 500x400 (50% of 1000x800)
        img1_output = output_dir / "test_image.jpg"
        with Image.open(img1_output) as img:
            assert img.size == (500, 400)

        # Second image should be 400x300 (50% of 800x600)
        img2_output = output_dir / "test_image2.png"
        with Image.open(img2_output) as img:
            assert img.size == (400, 300)

    def test_resize_batch_aspect_ratio_preservation(self, temp_dir, sample_images):
        """Test aspect ratio preservation when only one dimension is specified."""
        resizer = ImageResizer()
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Test resizing with only width specified (should preserve aspect ratio)
        success, failure = resizer.resize_batch(
            input_dir=temp_dir,
            output_dir=output_dir,
            width_spec="500",
            height_spec=""
        )

        assert success == 2
        assert failure == 0

        # Check output dimensions preserve aspect ratio
        output_files = list(output_dir.glob("*"))
        assert len(output_files) == 2

        # First image: 1000x800 -> 500x? (should be 500x400 to preserve 1.25 ratio)
        img1_output = output_dir / "test_image.jpg"
        with Image.open(img1_output) as img:
            width, height = img.size
            assert width == 500
            assert abs(height - 400) <= 1  # Allow small rounding differences

    def test_resize_batch_no_valid_images(self, temp_dir):
        """Test behavior when no valid images are found."""
        resizer = ImageResizer()
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Create a text file instead of images
        text_file = temp_dir / "not_an_image.txt"
        text_file.write_text("This is not an image")

        success, failure = resizer.resize_batch(
            input_dir=temp_dir,
            output_dir=output_dir,
            width_spec="500",
            height_spec="400"
        )

        assert success == 0
        assert failure == 0  # No failures, just no valid images

    def test_resize_batch_invalid_dimensions(self, temp_dir, sample_images):
        """Test error handling for invalid dimensions."""
        resizer = ImageResizer()
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Test with no dimensions specified
        with pytest.raises(ValueError, match="At least one dimension"):
            resizer.resize_batch(
                input_dir=temp_dir,
                output_dir=output_dir,
                width_spec="",
                height_spec=""
            )


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_full_workflow(self, temp_dir, sample_images):
        """Test complete workflow from config to resizing."""
        # Setup
        config_manager = ConfigManager(temp_dir)
        resizer = ImageResizer(quality=config_manager.config.quality)
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Use a preset from config
        preset = config_manager.get_preset("Small (800x600)")
        assert preset is not None

        # Resize using preset dimensions
        success, failure = resizer.resize_batch(
            input_dir=temp_dir,
            output_dir=output_dir,
            width_spec=str(preset.width),
            height_spec=str(preset.height)
        )

        assert success == 2
        assert failure == 0

        # Verify results
        output_files = list(output_dir.glob("*"))
        assert len(output_files) == 2

        for output_file in output_files:
            with Image.open(output_file) as img:
                assert img.size == (800, 600)


if __name__ == "__main__":
    pytest.main([__file__])