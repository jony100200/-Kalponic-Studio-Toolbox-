"""
Tests for pipeline processing functionality.
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
from ks_splitter.pipeline import SpriteProcessor, PipelineRunner


class TestSpriteProcessor:
    """Test the SpriteProcessor class."""

    def test_processor_initialization(self):
        """Test processor initializes with correct backends."""
        config = {
            'objects_backend': 'mock',
            'matte_backend': 'mock',
            'parts_backend': 'mock'
        }

        processor = SpriteProcessor(config)
        assert processor.segmenter is not None
        assert processor.matter is not None
        assert processor.part_splitter is not None

    def test_process_image(self):
        """Test end-to-end image processing."""
        config = {
            'objects_backend': 'mock',
            'matte_backend': 'mock',
            'parts_backend': 'mock',
            'export': {'write_previews': True},
            'templates_dir': 'templates'
        }

        processor = SpriteProcessor(config)

        # Create a temporary test image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            test_image_path = temp_file.name
            # Create a simple test image and save it
            test_image = (np.random.rand(64, 64, 3) * 255).astype(np.uint8)
            import cv2
            cv2.imwrite(test_image_path, cv2.cvtColor(test_image, cv2.COLOR_RGB2BGR))

        try:
            # Process the image
            result = processor.process_image(test_image_path, 'tree')

            # Check result structure
            assert isinstance(result, dict)
            assert 'instances' in result
            assert len(result['instances']) > 0

            # Check that the first instance has parts and mattes
            first_instance = result['instances'][0]
            assert 'parts' in first_instance
            assert 'mattes' in first_instance

            # Check that parts were created
            assert len(first_instance['parts']) > 0

            # Check that mattes were created
            assert len(first_instance['mattes']) > 0

        finally:
            # Clean up
            Path(test_image_path).unlink()


class TestPipelineRunner:
    """Test the PipelineRunner class."""

    def test_runner_initialization(self):
        """Test runner initializes correctly."""
        config = {
            'objects_backend': 'mock',
            'matte_backend': 'mock',
            'parts_backend': 'mock'
        }

        runner = PipelineRunner(config)
        assert runner.config == config
        assert runner.processor is not None

    def test_run_pipeline(self):
        """Test full pipeline execution."""
        config = {
            'objects_backend': 'mock',
            'matte_backend': 'mock',
            'parts_backend': 'mock',
            'export': {'write_previews': True},
            'templates_dir': 'templates'
        }

        runner = PipelineRunner(config)

        # Create a temporary test image
        test_image_path = Path(tempfile.gettempdir()) / 'test_sprite.png'
        test_image = (np.random.rand(64, 64, 3) * 255).astype(np.uint8)

        try:
            # Save test image
            import cv2
            cv2.imwrite(str(test_image_path), cv2.cvtColor(test_image, cv2.COLOR_RGB2BGR))

            # Create output directory
            output_dir = Path(tempfile.gettempdir()) / 'test_output'

            # Run pipeline
            run_dir_path = runner.run(str(test_image_path), str(output_dir), 'tree')

            # Check that run directory was returned and exists
            run_dir = Path(run_dir_path)
            assert run_dir.exists()

            # Check that separated directory exists
            separated_dir = run_dir / 'Separated'
            assert separated_dir.exists()

            # Check that at least some output files were created
            sprite_dir = separated_dir / test_image_path.stem
            assert sprite_dir.exists()

            files = list(sprite_dir.glob('*.png'))
            assert len(files) > 0  # Should have at least color.png

        finally:
            # Clean up
            if test_image_path.exists():
                test_image_path.unlink()
            import shutil
            if output_dir.exists():
                shutil.rmtree(output_dir)