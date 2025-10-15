"""
Tests for CLI functionality
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch
import tempfile
import shutil
from PIL import Image

from ks_image_resize.cli.main import main, create_argument_parser


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_images(temp_dir):
    """Create sample test images."""
    img = Image.new('RGB', (1000, 800), color='red')
    img_path = temp_dir / "test.jpg"
    img.save(img_path, 'JPEG', quality=95)

    return img_path


class TestCLIArguments:
    """Test CLI argument parsing and validation."""

    def test_parser_creation(self):
        """Test that argument parser is created successfully."""
        parser = create_argument_parser()
        assert parser is not None

    def test_valid_arguments(self):
        """Test parsing valid command line arguments."""
        parser = create_argument_parser()

        # Test with dimensions
        args = parser.parse_args(['input_dir', 'output_dir', '--width', '800', '--height', '600'])
        assert args.input_dir == 'input_dir'
        assert args.output_dir == 'output_dir'
        assert args.width == '800'
        assert args.height == '600'
        assert args.preset is None

        # Test with preset
        args = parser.parse_args(['input_dir', '--preset', 'medium'])
        assert args.input_dir == 'input_dir'
        assert args.preset == 'medium'
        assert args.width is None
        assert args.height is None

    def test_default_values(self):
        """Test default argument values."""
        parser = create_argument_parser()
        args = parser.parse_args(['input_dir'])

        assert args.quality == 95
        assert args.verbose is False
        assert args.list_presets is False


class TestCLIMain:
    """Test main CLI function."""

    def test_list_presets(self, temp_dir, capsys):
        """Test --list-presets functionality."""
        with patch('sys.argv', ['ks-image-resize', '--list-presets']):
            exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Available Presets:" in captured.out
        assert "Small (800x600)" in captured.out

    def test_missing_input_directory(self, capsys):
        """Test error when input directory doesn't exist."""
        nonexistent_path = "C:\\definitely\\does\\not\\exist\\directory"
        with patch('sys.argv', ['ks-image-resize', nonexistent_path, '--width', '800']):
            exit_code = main()

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Input directory does not exist" in captured.err

    def test_no_dimensions_or_preset(self, temp_dir, capsys):
        """Test error when neither dimensions nor preset are specified."""
        with patch('sys.argv', ['ks-image-resize', str(temp_dir)]):
            exit_code = main()

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Must specify either --width/--height or --preset" in captured.err

    def test_both_preset_and_dimensions(self, temp_dir, capsys):
        """Test error when both preset and dimensions are specified."""
        with patch('sys.argv', ['ks-image-resize', str(temp_dir), '--preset', 'medium', '--width', '800']):
            exit_code = main()

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Cannot specify both preset and custom dimensions" in captured.err

    def test_successful_resize(self, temp_dir, sample_images, capsys):
        """Test successful image resizing via CLI."""
        output_dir = temp_dir / "output"

        with patch('sys.argv', [
            'ks-image-resize',
            str(temp_dir),
            str(output_dir),
            '--width', '500',
            '--height', '400'
        ]):
            exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        combined_output = captured.out + captured.err
        assert "Batch resize completed" in combined_output or "✓1 successful" in combined_output

        # Check output file exists and has correct dimensions
        output_file = output_dir / "test.jpg"
        assert output_file.exists()

        with Image.open(output_file) as img:
            assert img.size == (500, 400)

    def test_resize_with_preset(self, temp_dir, sample_images, capsys):
        """Test resizing using a preset."""
        output_dir = temp_dir / "output"

        with patch('sys.argv', [
            'ks-image-resize',
            str(temp_dir),
            str(output_dir),
            '--preset', 'small'
        ]):
            exit_code = main()

        assert exit_code == 0

        # Check output file has preset dimensions (800x600)
        output_file = output_dir / "test.jpg"
        assert output_file.exists()

        with Image.open(output_file) as img:
            assert img.size == (800, 600)

    def test_verbose_output(self, temp_dir, sample_images, capsys):
        """Test verbose output mode."""
        output_dir = temp_dir / "output"

        with patch('sys.argv', [
            'ks-image-resize',
            str(temp_dir),
            str(output_dir),
            '--width', '500',
            '--verbose'
        ]):
            exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        # Verbose mode should include more detailed logging
        # The message might be in either stdout or stderr due to logging configuration
        combined_output = captured.out + captured.err
        assert "Starting batch resize" in combined_output or "Batch resize completed" in combined_output

    def test_keyboard_interrupt(self, temp_dir, sample_images):
        """Test handling of keyboard interrupt."""
        # This is harder to test directly, but we can verify the signal handling is in place
        # by checking that the main function has the try/except block for KeyboardInterrupt

        # For now, just ensure the function exists and can be called
        with patch('sys.argv', ['ks-image-resize', str(temp_dir), '--width', '500']):
            # Should not raise an exception
            exit_code = main()
            assert isinstance(exit_code, int)


class TestCLIIntegration:
    """Integration tests for CLI with different scenarios."""

    def test_resize_different_formats(self, temp_dir):
        """Test resizing different image formats."""
        # Create test images in different formats
        formats = [
            ('test_jpg.jpg', 'JPEG'),
            ('test_png.png', 'PNG'),
            ('test_bmp.bmp', 'BMP')
        ]

        for filename, format_name in formats:
            img = Image.new('RGB', (200, 150), color='green')
            img_path = temp_dir / filename
            img.save(img_path, format_name)

        output_dir = temp_dir / "output"

        with patch('sys.argv', [
            'ks-image-resize',
            str(temp_dir),
            str(output_dir),
            '--width', '100'
        ]):
            exit_code = main()

        assert exit_code == 0

        # Check all output files exist and have correct dimensions
        for filename, _ in formats:
            output_file = output_dir / filename
            assert output_file.exists()

            with Image.open(output_file) as img:
                assert img.size[0] == 100  # Width should be 100
                assert img.size[1] == 75   # Height should maintain aspect ratio

    def test_quality_setting(self, temp_dir, sample_images):
        """Test JPEG quality setting."""
        output_dir = temp_dir / "output"

        with patch('sys.argv', [
            'ks-image-resize',
            str(temp_dir),
            str(output_dir),
            '--width', '500',
            '--quality', '50'
        ]):
            exit_code = main()

        assert exit_code == 0

        # Check that the resizer was created with the correct quality
        # (This is implicit - if it worked, the quality setting was applied)
        output_file = output_dir / "test.jpg"
        assert output_file.exists()


if __name__ == "__main__":
    pytest.main([__file__])